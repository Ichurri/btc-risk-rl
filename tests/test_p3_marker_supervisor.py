"""Prospective P3 metadata gates exercised without historical market data."""

import hashlib
import json
import math
import shutil
import time
from dataclasses import asdict
from pathlib import Path

import pytest
import torch

from btc_risk_rl.agents.market_marker import market_training_executed
from btc_risk_rl.pilots.p2 import P2SyntheticSettings
from btc_risk_rl.pilots.p2r_market import P2RMarketSettings
from btc_risk_rl.pilots.p2r_units import _expected, _verify_completion


@pytest.mark.parametrize(
    ("source_profile", "actor_updates", "critic_updates", "expected"),
    [
        ("synthetic", 0, 0, False),
        ("synthetic", 8, 16, False),
        ("accepted_train_collection_only", 0, 0, False),
        ("accepted_train_collection_only", 8, 0, False),
        ("accepted_train_collection_only", 0, 16, False),
        ("accepted_train_collection_only", 8, 16, True),
        ("validation", 8, 16, False),
        ("final", 8, 16, False),
    ],
)
def test_marker_uses_source_and_both_completed_optimizers(
    source_profile, actor_updates, critic_updates, expected,
):
    assert market_training_executed(source_profile, actor_updates, critic_updates) is expected


@pytest.mark.parametrize("bad_count", [-1, True, 1.5, None])
def test_marker_rejects_invalid_counters(bad_count):
    with pytest.raises(ValueError, match="optimizer counters"):
        market_training_executed("accepted_train_collection_only", bad_count, 1)


def fixture_completion(tmp_path, *, training, unit, marker):
    """Fabricate a complete checkpoint envelope; never open a market source."""
    settings = (
        P2RMarketSettings(seed=610031) if training else
        P2SyntheticSettings(seed=610031, iterations=1, hidden=4, n_a=1,
                            n_q=2, n_b=2, actor_epochs=1, critic_epochs=4)
    )
    source_profile = "accepted_train_collection_only" if training else "synthetic"
    run_id, condition = "run-00-C5", "C5"
    work = tmp_path / f"{'train-fixture' if training else 'synthetic-fixture'}-{unit}"
    work.mkdir(parents=True)
    point = work / f"checkpoint-{unit}"
    point.mkdir()
    boundary = "after_q0" if unit == 0 else "after_dual_and_D"
    batches = math.ceil(settings.n_a / settings.minibatch)
    actor = unit * settings.actor_epochs * batches
    critic = unit * settings.critic_epochs * batches
    learn = settings.n_q + unit * (settings.n_a + settings.n_q + settings.n_b)
    diagnostic_n = 64 if training else 2

    def optimizer(steps):
        return {"state": {} if not steps else {0: {"step": torch.tensor(float(steps))}}}

    state = dict(
        attrs=dict(actor_updates=actor, critic_updates=critic,
                   next_iteration=unit, boundary=boundary),
        collector=dict(trajectories=learn, transitions=180 * learn),
        diagnostic=dict(trajectories=unit * diagnostic_n,
                        transitions=180 * unit * diagnostic_n),
        actor_optimizer=optimizer(actor), critic_optimizer=optimizer(critic),
    )
    torch.save(state, point / "state.pt")
    state_sha = hashlib.sha256((point / "state.pt").read_bytes()).hexdigest()
    provenance = dict(data=dict(profile=source_profile), threads=1, deterministic=True)
    manifest = dict(state_sha256=state_sha, boundary=boundary,
                    schema_version="p2_complete_boundary_v1", profile=settings.purpose,
                    provenance=provenance, settings=asdict(settings),
                    condition=condition, run_id=run_id)
    (point / "manifest.json").write_text(json.dumps(manifest))
    report = dict(status="passed", purpose=settings.purpose, condition=condition,
                  market_training_executed=marker, actor_updates=actor,
                  critic_updates=critic, next_iteration=unit, boundary=boundary,
                  trajectories=learn, transitions=180 * learn)
    payload = dict(status="passed", unit=unit, resources=_expected(settings, unit, diagnostic_n),
                   checkpoint=str(point), checkpoint_sha256=state_sha, report=report)
    (work / f"unit-{unit}.json").write_text(json.dumps(payload))
    return work, settings, condition, run_id, provenance, diagnostic_n, payload, state


@pytest.mark.parametrize("training", [False, True])
@pytest.mark.parametrize("unit", [0, 1])
def test_supervisor_marker_matrix_with_synthetic_checkpoint_fixtures(tmp_path, training, unit):
    expected = training and unit == 1
    args = fixture_completion(tmp_path, training=training, unit=unit, marker=expected)
    work, settings, condition, run_id, provenance, diagnostic_n, _, _ = args
    _, boundary = _verify_completion(work, unit, settings, condition, run_id,
                                     {"status": "passed"}, provenance, diagnostic_n)
    assert boundary == ("after_q0" if unit == 0 else "after_dual_and_D")
    payload = json.loads((work / f"unit-{unit}.json").read_text())
    payload["report"]["market_training_executed"] = not expected
    (work / f"unit-{unit}.json").write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="market training marker"):
        _verify_completion(work, unit, settings, condition, run_id,
                           {"status": "passed"}, provenance, diagnostic_n)


@pytest.mark.parametrize("field", ["report", "checkpoint"])
def test_supervisor_rejects_counter_mismatch_before_accepting(tmp_path, field):
    args = fixture_completion(tmp_path, training=True, unit=1, marker=True)
    work, settings, condition, run_id, provenance, diagnostic_n, payload, state = args
    if field == "report":
        payload["report"]["actor_updates"] -= 1
        (work / "unit-1.json").write_text(json.dumps(payload))
    else:
        state["attrs"]["critic_updates"] -= 1
        point = work / "checkpoint-1"
        torch.save(state, point / "state.pt")
        sha = hashlib.sha256((point / "state.pt").read_bytes()).hexdigest()
        manifest = json.loads((point / "manifest.json").read_text())
        manifest["state_sha256"] = sha
        (point / "manifest.json").write_text(json.dumps(manifest))
        payload["checkpoint_sha256"] = sha
        (work / "unit-1.json").write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="optimizer counters"):
        _verify_completion(work, 1, settings, condition, run_id,
                           {"status": "passed"}, provenance, diagnostic_n)


@pytest.mark.parametrize("field", ["purpose", "marker_missing", "optimizer_step"])
def test_supervisor_rejects_report_profile_or_optimizer_state(tmp_path, field):
    args = fixture_completion(tmp_path, training=True, unit=1, marker=True)
    work, settings, condition, run_id, provenance, diagnostic_n, payload, state = args
    if field == "purpose":
        payload["report"]["purpose"] = "p2_synthetic_tests_only"
    elif field == "marker_missing":
        payload["report"].pop("market_training_executed")
    else:
        point = work / "checkpoint-1"
        state["actor_optimizer"]["state"][0]["step"] = torch.tensor(7.0)
        torch.save(state, point / "state.pt")
        sha = hashlib.sha256((point / "state.pt").read_bytes()).hexdigest()
        manifest = json.loads((point / "manifest.json").read_text())
        manifest["state_sha256"] = sha
        (point / "manifest.json").write_text(json.dumps(manifest))
        payload["checkpoint_sha256"] = sha
    (work / "unit-1.json").write_text(json.dumps(payload))
    message = "profile" if field == "purpose" else (
        "market training marker" if field == "marker_missing" else "optimizer counters"
    )
    with pytest.raises(ValueError, match=message):
        _verify_completion(work, 1, settings, condition, run_id,
                           {"status": "passed"}, provenance, diagnostic_n)


def test_synthetic_learning_reports_false_even_after_both_optimizers(config, tmp_path):
    from btc_risk_rl.agents.synthetic import SyntheticMarket
    from btc_risk_rl.pilots.p2_runner import complete_unit

    settings = P2SyntheticSettings(seed=610031, iterations=1, hidden=4,
                                   n_a=1, n_q=2, n_b=2, actor_epochs=1,
                                   critic_epochs=4)
    root = tmp_path / "synthetic-learning"
    source = SyntheticMarket(config)
    q0 = complete_unit(source, settings, root=root, condition="C5",
                       run_id="run-00-C5", unit=0, atomic_checkpoint=True)
    iteration = complete_unit(source, settings, root=root, condition="C5",
                              run_id="run-00-C5", unit=1,
                              previous=q0["checkpoint"], atomic_checkpoint=True)
    assert q0["report"]["market_training_executed"] is False
    assert iteration["report"]["market_training_executed"] is False
    assert iteration["report"]["actor_updates"] == 1
    assert iteration["report"]["critic_updates"] == 4


def test_supervisor_fails_ledger_on_false_market_marker_and_preserves_q0(
    tmp_path, monkeypatch,
):
    """All training-profile envelopes are fabricated; no market worker runs."""
    from btc_risk_rl.config import load_config
    from btc_risk_rl.pilots import p2r_units

    class MetadataOnlyTrainingFixture:
        config = load_config(Path("configs/initial.toml"))

        def identity(self):
            return {"profile": "accepted_train_collection_only", "fixture": "synthetic_only"}

    source = MetadataOnlyTrainingFixture()
    settings = P2RMarketSettings(seed=610031)
    root = tmp_path / "artifacts" / "p2r-synthetic-marker-gate"
    power = tmp_path / "power"
    for name, kind, field, value in (("ADP1", "Mains", "online", "1"),
                                     ("BAT1", "Battery", "capacity", "80")):
        item = power / name
        item.mkdir(parents=True)
        (item / "type").write_text(kind)
        (item / field).write_text(value)
        if kind == "Battery":
            (item / "scope").write_text("System")
    q0_hash = None

    def fabricated_supervise(_command, **kwargs):
        nonlocal q0_hash
        marker_path = Path(kwargs["closing_marker"])
        work = marker_path.parent
        unit = int(marker_path.stem.split("-")[-1])
        if unit == 1:
            q0 = work / "checkpoint-0" / "state.pt"
            q0_hash = hashlib.sha256(q0.read_bytes()).hexdigest()
        fixture_root = tmp_path / f"envelope-{unit}"
        fake_work, _, _, _, _, _, payload, _ = fixture_completion(
            fixture_root, training=True, unit=unit, marker=False,
        )
        point = work / f"checkpoint-{unit}"
        shutil.copytree(fake_work / f"checkpoint-{unit}", point)
        manifest = json.loads((point / "manifest.json").read_text())
        manifest["provenance"] = p2r_units.provenance(source) | {
            "threads": 1, "deterministic": True,
        }
        (point / "manifest.json").write_text(json.dumps(manifest))
        payload["checkpoint"] = str(point)
        (work / f"unit-{unit}.json").write_text(json.dumps(payload))
        return {"status": "passed", "work_seconds": 0.01,
                "work_ended": time.time()}

    monkeypatch.setattr(p2r_units, "supervise", fabricated_supervise)
    args = dict(roster=[(610031, "C5")], source=source,
                settings_for=lambda _seed: settings,
                command_for=lambda _request: ["synthetic-fixture-no-execution"],
                profile="p2r_synthetic_units", diagnostic_n=64,
                power_root=power, memory_available=4 * 1024**3,
                disk_free=10 * 1024**3, fixture_window=True)
    with pytest.raises(ValueError, match="market training marker"):
        p2r_units._run_units(root, "configs/initial.toml", settings, **args)
    ledger = json.loads((root / "ledger.jsonl").read_text().splitlines()[-1])
    assert ledger["status"] == "failed"
    assert [(unit["unit"], unit["checkpoint_sha256"]) for unit in ledger["units"]] == [
        (0, q0_hash),
    ]
    assert ledger["pending"]["unit"] == 1
    assert hashlib.sha256((root / "run-00-C5/checkpoint-0/state.pt").read_bytes()).hexdigest() == q0_hash
    assert all(unit["unit"] != 1 for unit in ledger["units"])
    with pytest.raises(ValueError, match="failed/incomplete"):
        p2r_units._run_units(root, "configs/initial.toml", settings, **args)
