"""H5: synthetic resume OR bounded frozen-policy train integration; never market learning."""

import argparse
import json
import subprocess
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

from btc_risk_rl.agents.checkpoint import digest, load_checkpoint, provenance, save_checkpoint
from btc_risk_rl.agents.collector import ARRAYS, Collector
from btc_risk_rl.agents.market_source import TrainingMarket
from btc_risk_rl.agents.models import Actor, FrozenPolicy, fingerprint
from btc_risk_rl.agents.synthetic import SyntheticMarket, SyntheticSettings
from btc_risk_rl.agents.telemetry import Telemetry
from btc_risk_rl.agents.trainer import SyntheticExperiment
from btc_risk_rl.config import load_config, utc_ms


def equal_tree(a, b):
    if isinstance(a, torch.Tensor):
        assert torch.equal(a, b)
    elif isinstance(a, dict):
        assert a.keys() == b.keys()
        for key in a:
            equal_tree(a[key], b[key])
    elif isinstance(a, (list, tuple)):
        assert len(a) == len(b)
        for x, y in zip(a, b):
            equal_tree(x, y)
    else:
        assert a == b


def synthetic(config, output):
    source = SyntheticMarket(config)
    settings = replace(SyntheticSettings(), n_a=1, n_q=2, n_b=2, actor_epochs=1, critic_epochs=1)
    continuous = SyntheticExperiment(source, settings, condition="C5", run_id="h5-resume")
    reference = continuous.run()
    partial = SyntheticExperiment(
        source, settings, condition="C5", run_id="h5-resume", journal=output / "journal"
    )
    partial.run(pause_after=1)
    manifest = save_checkpoint(partial, output / "checkpoint")
    restored = load_checkpoint(output / "checkpoint", source, journal=output / "journal")
    resumed = restored.run()
    for name in ("actor", "critic", "actor_optimizer", "critic_optimizer"):
        equal_tree(getattr(continuous, name).state_dict(), getattr(restored, name).state_dict())
    for key in (
        "events",
        "audits",
        "transitions",
        "trajectories",
        "actor_updates",
        "critic_updates",
    ):
        equal_tree(reference[key], resumed[key])
    assert continuous.eta == restored.eta and continuous.multiplier == restored.multiplier
    for expected, actual in zip(continuous.batches[-len(restored.batches) :], restored.batches):
        for x, y in zip(expected, actual):
            assert x.realization == y.realization and x.policy_version == y.policy_version
            for key in ARRAYS:
                np.testing.assert_array_equal(getattr(x, key), getattr(y, key))
    return dict(
        profile="synthetic",
        provenance=provenance(source),
        continuous=reference,
        resumed=resumed,
        exact_resume=True,
        checkpoint_state_sha256=manifest["state_sha256"],
        checkpoint_save_seconds=manifest["checkpoint_wall_seconds"],
        note="Each logical run consumes 12 trajectories / 2160 transitions; verification executes both.",
    )


def market(config):
    # Fixed, preregistered technical probe: no reward-driven selection or optimizer.
    seed, count = 20260923, 3
    prepared = Path("data/processed/segmented-B-h1")
    anchor = Path("docs/evidence/segmented-h1/manifest.json")
    started = time.monotonic()
    source = TrainingMarket(config, prepared, expected_manifest=digest(anchor))
    load_seconds = time.monotonic() - started
    assert len(source.route_ids) == 7048
    actor = Actor(hidden=8, seed=seed)  # Test configuration, NOT pilot parameters.
    before = fingerprint(actor)
    collector = Collector(source, seed=seed, run_id="h5-frozen-market-probe")
    telemetry = Telemetry()
    with telemetry.measure("frozen_collection", 0, collector):
        batch = collector.collect(
            FrozenPolicy(actor, generation=0), role="A", iteration=0, count=count, fragment_steps=60
        )
    expected = np.random.default_rng(np.random.SeedSequence([seed, 1, 0, 0])).choice(
        source.route_ids, count
    )
    assert [int(t.route_id.split(":")[1]) for t in batch] == list(expected)
    assert fingerprint(actor) == before
    assert all(t.times[-1] < utc_ms(config.data.validation_start) for t in batch)
    assert source.audit["normalizer_refitted"] is False
    for name, sha in source.identity()["files"].items():
        assert digest(prepared / name) == sha
    return dict(
        profile=source.profile,
        provenance=provenance(source),
        seed=seed,
        accepted_starts=len(source.route_ids),
        sampled_ids=expected.tolist(),
        trajectories=collector.trajectories,
        transitions=collector.transitions,
        actor_updates=0,
        critic_updates=0,
        actor_before=before,
        actor_after=fingerprint(actor),
        load_and_integrity_seconds=load_seconds,
        telemetry=telemetry.records,
        diagnostics=collector.diagnostics,
        trajectories_audit=[
            dict(
                route=t.route_id,
                realization=t.realization,
                policy=t.policy_version,
                first_ms=int(t.times[0]),
                last_ms=int(t.times[-1]),
            )
            for t in batch
        ],
        normalizer_refitted=False,
        product_hashes_unchanged=True,
        interpretation="Technical collection only; NOT a validated market training time estimate",
        validation_observations_loaded=False,
        shared_h1_files_hashed_in_full=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=["synthetic", "market-integration"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    if torch.version.cuda is not None:
        raise RuntimeError("CPU-only runtime required")
    config = load_config(Path("configs/initial.toml"))
    result = synthetic(config, args.output) if args.profile == "synthetic" else market(config)
    result.update(
        status="passed",
        utc=datetime.now(timezone.utc).isoformat(),
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        git_status=subprocess.check_output(["git", "status", "--short"], text=True),
        market_optimization_executed=False,
        final_test_accessed=False,
    )
    with (args.output / "results.json").open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps(dict(status="passed", profile=args.profile, output=str(args.output))))


if __name__ == "__main__":
    main()
