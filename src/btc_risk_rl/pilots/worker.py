"""One supervised, complete Q0 or Q/A/B iteration, using the existing algorithm."""

import argparse
import json
import os
import time
from pathlib import Path

import torch

from btc_risk_rl.agents.checkpoint import digest, load_checkpoint, save_checkpoint, validate_state
from btc_risk_rl.agents.market_source import TrainingMarket
from btc_risk_rl.agents.trainer import SyntheticExperiment
from btc_risk_rl.config import load_config
from btc_risk_rl.pilots.diagnostics import warnings
from btc_risk_rl.pilots.protocol import CAMPAIGN, ROOT, P0Settings, Permit, roster

COUNTERS = ("trajectories", "transitions", "actor_updates", "critic_updates")


def counters(run):
    return dict(
        trajectories=run.collector.trajectories,
        transitions=run.collector.transitions,
        actor_updates=run.actor_updates,
        critic_updates=run.critic_updates,
    )


def write_json(path, value):
    with Path(path).open("x") as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def complete_unit(source, settings, *, condition, run_id, root, unit, previous=None, permit=None):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    journal = root / "journal"
    run = None
    before = dict.fromkeys(COUNTERS, 0)
    try:
        if unit == 0:
            if previous is not None:
                raise ValueError("Q0 cannot resume a prior checkpoint")
            run = SyntheticExperiment(
                source, settings, condition=condition, run_id=run_id, journal=journal, permit=permit
            )
        else:
            if previous is None:
                raise ValueError("Complete previous boundary required")
            run = load_checkpoint(previous, source, journal=journal, permit=permit)
            if (
                run.next_iteration != unit - 1
                or run.settings != settings
                or run.condition != condition
            ):
                raise ValueError("Checkpoint not next authorized unit")
            if run.collector.run_id != run_id:
                raise ValueError("Wrong checkpoint run")
            before = counters(run)

        # Operational heartbeat, not immutable scientific evidence. Exact on normal failure;
        # at SIGKILL this is a lower bound and current trajectory may be partial.
        def heartbeat():
            temp = root / "progress.tmp"
            temp.write_text(json.dumps(dict(unit=unit, phase=run.phase, counters=counters(run))))
            os.replace(temp, root / "progress.json")

        run.collector.progress = heartbeat
        heartbeat()
        start = time.monotonic()
        report = run.run(pause_after=unit)
        algorithm_seconds = time.monotonic() - start
        heartbeat()
        warning_list = warnings(report)
        validate_state(run)
        marker = root / f"closing-{unit}.json"
        temporary_marker = root / f"closing-{unit}.tmp"
        write_json(
            temporary_marker, dict(work_done_monotonic=time.monotonic(), work_done_utc=time.time())
        )
        os.rename(temporary_marker, marker)
        point = root / f"checkpoint-{unit}"
        save_started = time.monotonic()
        manifest = save_checkpoint(run, point)
        save_seconds = time.monotonic() - save_started
        result = dict(
            status="passed",
            unit=unit,
            checkpoint=str(point.resolve()),
            checkpoint_sha256=manifest["state_sha256"],
            resources={k: counters(run)[k] - before[k] for k in COUNTERS},
            algorithm_seconds=algorithm_seconds,
            save_seconds=save_seconds,
            warnings=warning_list,
            report=report,
        )
        write_json(root / f"unit-{unit}.json", result)
        return result
    except BaseException as exc:
        error = dict(
            status="failed",
            unit=unit,
            error=f"{type(exc).__name__}: {exc}",
            diagnostic=getattr(exc, "diagnostic", None),
            counters=counters(run) if run else None,
        )
        write_json(root / f"failure-{unit}.json", error)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    if torch.version.cuda is not None:
        raise RuntimeError("P0 requires CPU-only PyTorch")
    state = json.loads((CAMPAIGN / "ledger.jsonl").read_text().splitlines()[-1])
    index = state["cursor"]
    seed, condition = roster()[index]
    run_id = f"run-{index:02d}-{condition}"
    settings, permit = P0Settings(seed=seed), Permit(args.token)
    permit.validate(settings, condition, run_id)
    pending = state["pending"]
    root = CAMPAIGN / run_id
    config = load_config(ROOT / "configs/initial.toml")
    source = TrainingMarket(
        config,
        ROOT / "data/processed/segmented-B-h1",
        expected_manifest=digest(ROOT / "docs/evidence/segmented-h1/manifest.json"),
    )
    result = complete_unit(
        source,
        settings,
        condition=condition,
        run_id=run_id,
        root=root,
        unit=pending["unit"],
        previous=pending["previous"],
        permit=permit,
    )
    print(json.dumps(dict(status=result["status"], run=run_id, unit=pending["unit"])), flush=True)


if __name__ == "__main__":
    main()
