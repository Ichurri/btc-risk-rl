"""P2 supervisor: synthetic exerciser and inactive accepted-training route."""

import argparse
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

import torch

from btc_risk_rl.agents.checkpoint import (
    load_checkpoint,
    provenance,
    save_checkpoint,
    validate_state,
)
from btc_risk_rl.agents.synthetic import SyntheticMarket
from btc_risk_rl.agents.trainer import SyntheticExperiment
from btc_risk_rl.config import load_config
from btc_risk_rl.pilots.budget import CAPS
from btc_risk_rl.pilots.diagnostics import warnings
from btc_risk_rl.pilots.p2 import Diagnostic, P2SyntheticSettings, file_hash, tree_hash
from btc_risk_rl.pilots.p2_budget import P2Ledger
from btc_risk_rl.pilots.shared_budget import SharedBudget
from btc_risk_rl.pilots.supervisor import supervise
from btc_risk_rl.pilots.worker import write_json

SYNTHETIC_ROOT = Path(__file__).resolve().parents[3] / "artifacts" / "p2-approved-v1-synthetic"


def counts(run):
    return dict(
        trajectories=run.collector.trajectories,
        transitions=run.collector.transitions,
        diagnostic_trajectories=run.diagnostic.collector.trajectories,
        diagnostic_transitions=run.diagnostic.collector.transitions,
        actor_updates=run.actor_updates,
        critic_updates=run.critic_updates,
    )


def complete_unit(source, settings, *, root, condition, run_id, unit, previous=None,
                  permit=None, n_d=None):
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.pilots.p2_market import P2MarketPermit, P2MarketSettings
    if type(source) is SyntheticMarket and type(settings) is P2SyntheticSettings:
        if permit is not None:
            raise PermissionError("Synthetic P2 cannot use market permit")
        n_d = 2 if n_d is None else n_d
    elif type(source) is TrainingMarket and type(settings) is P2MarketSettings:
        if type(permit) is not P2MarketPermit:
            raise PermissionError("P2 market unit requires registered lease")
        permit.validate(settings, condition, run_id)
        n_d = 64 if n_d is None else n_d
        if n_d != 64:
            raise ValueError("P2 historical diagnostic must use D=64")
    else:
        raise PermissionError("Unknown P2 source/settings profile")
    if type(unit) is not int or not 0 <= unit <= settings.iterations:
        raise ValueError("Invalid unit")
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    run = None
    try:
        if unit == 0:
            if previous is not None:
                raise ValueError("Q0 cannot resume")
            run = SyntheticExperiment(
                source,
                settings,
                condition=condition,
                run_id=run_id,
                journal=root / "journal",
                diagnostic=Diagnostic(root / "D", n=n_d),
                permit=permit,
            )
            before = dict.fromkeys(counts(run), 0)
        else:
            if previous is None:
                raise ValueError("Complete preceding checkpoint required")
            run = load_checkpoint(previous, source, journal=root / "journal", permit=permit)
            if (
                run.settings != settings
                or run.condition != condition
                or run.collector.run_id != run_id
                or run.next_iteration != unit - 1
                or run.diagnostic is None
                or run.diagnostic.n != n_d
            ):
                raise ValueError("Wrong P2 continuation")
            before = counts(run)
        run.diagnostic.phase_marker = root / f"phase-{unit}.json"

        def progress():
            path = root / "progress.tmp"
            path.write_text(json.dumps(dict(unit=unit, counters=counts(run), phase=run.phase)))
            os.replace(path, root / "progress.json")

        run.collector.progress = progress
        run.diagnostic.progress = progress
        start = time.monotonic()
        report = run.run(pause_after=unit)
        progress()
        validate_state(run)
        duration = time.monotonic() - start
        marker = root / f"closing-{unit}.json"
        write_json(
            root / f"closing-{unit}.tmp",
            dict(work_done_monotonic=time.monotonic(), work_done_utc=time.time()),
        )
        os.rename(root / f"closing-{unit}.tmp", marker)
        point = root / f"checkpoint-{unit}"
        start = time.monotonic()
        manifest = save_checkpoint(run, point)
        from btc_risk_rl.pilots.p2_metrics import learning_rates

        result = dict(
            learning_rates=learning_rates(report),
            status="passed",
            unit=unit,
            checkpoint=str(point),
            checkpoint_sha256=manifest["state_sha256"],
            resources={k: v - before[k] for k, v in counts(run).items()},
            algorithm_seconds=duration,
            save_seconds=time.monotonic() - start,
            warnings=warnings(report),
            report=report,
        )
        write_json(root / f"unit-{unit}.json", result)
        return result
    except BaseException as exc:
        path = root / f"failure-{unit}.json"
        if not path.exists():
            write_json(
                path,
                dict(
                    error=str(exc),
                    counters=counts(run) if run else None,
                    resource_interpretation="cumulative_completed_and_partial_transitions",
                ),
            )
        raise


def run_synthetic(output, config):
    """Nine tiny fixtures, K10/D2; not the approved market batch sizes or timing."""
    return _run_campaign(output, config, market=False)


def run_market(protocol):
    """Run the registered training-only P2 campaign under the global supervisor."""
    from btc_risk_rl.pilots.p2_market import CONFIG, MARKET_CAMPAIGN, P2MarketPermit
    P2MarketPermit.require_registration(protocol)
    return _run_campaign(MARKET_CAMPAIGN, CONFIG, market=True)


def _run_campaign(output, config, *, market):
    entered, active_start = time.time(), time.monotonic()
    root = Path(output).resolve()
    from btc_risk_rl.pilots.p2_market import (
        ACCEPTED_MANIFEST_SHA,
        MARKET_CAMPAIGN,
        PREPARED,
        PROTOCOL_SHA,
        P2MarketPermit,
        P2MarketSettings,
    )
    from btc_risk_rl.pilots.p2_market import (
        roster as market_roster,
    )
    if market:
        P2MarketPermit.require_registration()
    canonical = MARKET_CAMPAIGN if market else SYNTHETIC_ROOT
    if root != canonical:
        raise ValueError("P2 requires canonical global-budget output: " + str(canonical))
    with SharedBudget(root.parent, root.name, now=entered) as shared:
        from btc_risk_rl.agents.market_source import TrainingMarket
        cfg = load_config(Path(config))
        source = (
            TrainingMarket(cfg, PREPARED, expected_manifest=ACCEPTED_MANIFEST_SHA)
            if market else SyntheticMarket(cfg)
        )
        identity = dict(
            profile="p2_market_only" if market else "p2_synthetic_only",
            config=str(Path(config).resolve()), code=provenance(source),
            protocol_sha256=PROTOCOL_SHA, diagnostic_n=64 if market else 2,
            runner=file_hash(Path(__file__)),
        )
        with P2Ledger(
            root, now=entered, identity=identity, external_seconds=shared.external_seconds
        ) as ledger:
            if ledger.state["status"] == "completed":
                return ledger.state
            try:
                # Same CPU/memory/disk preflight as P0, no source loader.
                from btc_risk_rl.pilots.runner import preflight

                preflight(root, approve=lambda: None)
                ledger.preflight_done(time.time())
                roster = market_roster() if market else [
                    (s, c)
                    for s, order in (
                        (610031, ("C0", "C5", "C10")),
                        (610047, ("C5", "C10", "C0")),
                        (610081, ("C10", "C0", "C5")),
                    )
                    for c in order
                ]
                while ledger.state["cursor"] < len(roster):
                    idx = ledger.state["cursor"]
                    seed, condition = roster[idx]
                    run_id = f"run-{idx:02d}-{condition}"
                    prior = ledger.state["runs"].get(run_id, {})
                    unit = prior.get("next_unit", 0)
                    kind = "q0" if unit == 0 else "iteration"
                    if ledger.admit(condition, kind, time.time()) != "start":
                        return ledger.state
                    work = root / run_id
                    work.mkdir(exist_ok=True)
                    settings = (P2MarketSettings(seed=seed) if market else
                        P2SyntheticSettings(seed=seed, iterations=10, hidden=4,
                                            n_a=1, n_q=2, n_b=2, actor_epochs=1))
                    token = __import__("uuid").uuid4().hex
                    request = dict(
                        settings=asdict(settings),
                        config=str(Path(config).resolve()),
                        root=str(work),
                        condition=condition,
                        run_id=run_id,
                        unit=unit,
                        previous=prior.get("checkpoint"),
                        token=token if market else None,
                    )
                    request_path = work / f"request-{unit}.json"
                    write_json(request_path, request)
                    ledger.begin(run_id, kind, time.time())
                    ledger.state["pending"].update(
                        unit=unit, request_sha256=file_hash(request_path),
                        token=token if market else None,
                        supervisor_pid=os.getpid() if market else None,
                    )
                    ledger.persist(time.time())
                    cap = min(CAPS[kind], ledger.day["work_deadline"] - time.time())
                    result = supervise(
                        [
                            sys.executable,
                            "-m",
                            "btc_risk_rl.pilots.p2_runner",
                            "--market-request" if market else "--synthetic-request",
                            str(request_path),
                        ],
                        output=work / f"worker-{unit}.log",
                        seconds=cap,
                        rss_limit=10 * 1024**3,
                        env=dict(
                            os.environ,
                            OMP_NUM_THREADS="1",
                            OPENBLAS_NUM_THREADS="1",
                            MKL_NUM_THREADS="1",
                            NUMEXPR_NUM_THREADS="1",
                        ),
                        closing_marker=work / f"closing-{unit}.json",
                        phase_marker=work / f"phase-{unit}.json",
                        closing_seconds=ledger.day["hard_deadline"] - time.time(),
                    )
                    if result["status"] != "passed":
                        from btc_risk_rl.pilots.runner import partial_failure

                        partial = partial_failure(ledger, work, unit)
                        for key, value in partial["partial_resources"].items():
                            for totals in (
                                ledger.state["resources"],
                                ledger.state["runs"][run_id]["resources"],
                            ):
                                totals[key] = totals.get(key, 0) + value
                        ledger.fail(
                            time.time(), "P2 supervised unit failed", supervisor=result, **partial
                        )
                        return ledger.state
                    payload = json.loads((work / f"unit-{unit}.json").read_text())
                    n_a, n_q, n_b, n_d = (
                        settings.n_a, settings.n_q, settings.n_b, 64 if market else 2
                    )
                    minibatches = (n_a + settings.minibatch - 1) // settings.minibatch
                    expected = dict(
                        trajectories=n_q if unit == 0 else n_a+n_q+n_b,
                        transitions=180*(n_q if unit == 0 else n_a+n_q+n_b),
                        diagnostic_trajectories=0 if unit == 0 else n_d,
                        diagnostic_transitions=0 if unit == 0 else 180*n_d,
                        actor_updates=0 if unit == 0 else settings.actor_epochs*minibatches,
                        critic_updates=0 if unit == 0 else settings.critic_epochs*minibatches,
                    )
                    if payload["resources"] != expected or payload["unit"] != unit:
                        raise ValueError("P2 worker resource mismatch")
                    ledger.finish(
                        time.time(),
                        resources=payload["resources"],
                        condition=condition,
                        checkpoint=payload["checkpoint"],
                        checkpoint_sha256=payload["checkpoint_sha256"],
                        work_seconds=result["work_seconds"],
                        work_ended=result["work_ended"],
                        supervisor=result,
                    )
                ledger.state["status"] = "completed"
                return ledger.state
            except BaseException as exc:
                if ledger.state["status"] not in {"failed", "incomplete"}:
                    ledger.fail(time.time(), str(exc))
                raise
            finally:
                ledger.day["active_seconds"] += time.monotonic() - active_start
                ledger.day["charged_wall_seconds"] = max(
                    ledger.day.get("charged_wall_seconds", 0),
                    time.time() - ledger.day["started_utc_epoch"],
                )
                if time.time() > ledger.day["hard_deadline"]:
                    ledger.state["status"] = "failed"
                    ledger.state["deadline_violation"] = True
                ledger.persist(time.time())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    requests = parser.add_mutually_exclusive_group(required=True)
    requests.add_argument("--synthetic-request")
    requests.add_argument("--market-request")
    args = parser.parse_args()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    if torch.version.cuda is not None:
        raise ValueError("CPU-only PyTorch required")
    if args.market_request:
        from btc_risk_rl.agents.market_source import TrainingMarket
        from btc_risk_rl.pilots.p2_market import (
            ACCEPTED_MANIFEST_SHA,
            CONFIG,
            PREPARED,
            P2MarketPermit,
            P2MarketSettings,
        )
        P2MarketPermit.require_registration()  # Before even reading a request file.
    request = json.loads(Path(args.market_request or args.synthetic_request).read_text())
    settings = (P2MarketSettings if args.market_request else P2SyntheticSettings)(
        **request.pop("settings"))
    config_path = Path(request.pop("config"))
    if args.market_request and config_path.resolve() != CONFIG.resolve():
        raise PermissionError("P2 worker requires canonical training configuration")
    config = load_config(config_path)
    if args.market_request:
        permit = P2MarketPermit(request.pop("token"))
        permit.validate(settings, request["condition"], request["run_id"])
        source = TrainingMarket(config, PREPARED, expected_manifest=ACCEPTED_MANIFEST_SHA)
    else:
        request.pop("token", None)
        permit = None
        source = SyntheticMarket(config)
    result = complete_unit(source, settings, permit=permit, **request)
    print(
        json.dumps(
            dict(
                status=result["status"],
                resources=result["resources"],
                report_sha256=tree_hash(result["report"]),
            )
        )
    )


if __name__ == "__main__":
    main()
