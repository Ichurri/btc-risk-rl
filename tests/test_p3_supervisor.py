"""P3 supervised unit lifecycle on fabricated routes and metadata envelopes."""

import hashlib
import json
import math
import os
import signal
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, time, timedelta
from pathlib import Path

import pytest
import torch

from btc_risk_rl.pilots.budget import LA_PAZ
from btc_risk_rl.pilots.p2 import tree_hash
from btc_risk_rl.pilots.p2r_units import _expected, _verify_completion
from btc_risk_rl.pilots.p3_budget import P3Ledger
from btc_risk_rl.pilots.p3_critic import P3SyntheticSettings
from btc_risk_rl.pilots.p3_market import P3MarketSettings
from btc_risk_rl.pilots.p3_units import run_synthetic_units


def power_fixture(tmp_path):
    root = tmp_path / "power"
    for name, kind, field, value in (("ADP1", "Mains", "online", "1"),
                                     ("BAT1", "Battery", "capacity", "80")):
        item = root / name
        item.mkdir(parents=True, exist_ok=True)
        (item / "type").write_text(kind)
        (item / field).write_text(value)
        if kind == "Battery":
            (item / "scope").write_text("System")
    return root


ROWS = [(710031, "C5", 0), (710031, "C5", 1)]


def synthetic_settings(row):
    return P3SyntheticSettings(
        seed=row[0], critic_beta=row[2], iterations=1, hidden=4,
        n_a=2, n_q=2, n_b=2, actor_epochs=1, critic_epochs=4, minibatch=1,
    )


def run(root, power, *, max_units=None, fixture_window=True):
    return run_synthetic_units(
        root, "configs/initial.toml", ROWS, synthetic_settings,
        max_units=max_units, power_root=power, memory_available=4 * 1024**3,
        disk_free=10 * 1024**3, fixture_window=fixture_window,
        heartbeat_seconds=0.05,
    )


def test_two_arms_have_separate_complete_units_reports_and_checkpoints(tmp_path):
    power = power_fixture(tmp_path)
    root = tmp_path / "artifacts" / "p3-synthetic-paired"
    partial = run(root, power, max_units=3)
    assert partial["status"] == "ready" and partial["cursor"] == 1
    assert [(u["run_id"], u["unit"]) for u in partial["units"]] == [
        ("run-00-C5-b0", 0), ("run-00-C5-b0", 1), ("run-01-C5-b1", 0)
    ]
    finished = run(root, power)
    assert finished["status"] == "completed" and finished["cursor"] == 2
    assert len(finished["units"]) == 4
    for index, beta in enumerate((0, 1)):
        work = root / f"run-{index:02d}-C5-b{beta}"
        assert [json.loads((work / f"checkpoint-{u}/manifest.json").read_text())["boundary"]
                for u in (0, 1)] == ["after_q0", "after_dual_and_D"]
        report = json.loads((work / "unit-1.json").read_text())
        assert report["beta"] == beta
        assert report["report"]["settings"]["critic_beta"] == beta
        assert report["report"]["market_training_executed"] is False
        assert report["report"]["diagnostic"]["records"][0]["policy_version"].startswith("policy-0:")
    assert not list(root.rglob("checkpoint-*.partial-*"))


def test_p3_paired_pause_matches_continuous_learning_state(tmp_path):
    power = power_fixture(tmp_path)
    artifacts = tmp_path / "artifacts"
    continuous = artifacts / "p3-synthetic-continuous"
    paused = artifacts / "p3-synthetic-paused"
    assert run(continuous, power)["status"] == "completed"
    assert run(paused, power, max_units=3)["status"] == "ready"
    assert run(paused, power)["status"] == "completed"
    for index, beta in enumerate((0, 1)):
        relative = f"run-{index:02d}-C5-b{beta}/checkpoint-1/state.pt"
        left = torch.load(continuous / relative, map_location="cpu", weights_only=True)
        right = torch.load(paused / relative, map_location="cpu", weights_only=True)
        for field in ("actor", "critic", "actor_optimizer", "critic_optimizer", "attrs",
                      "collector", "diagnostic"):
            if field == "diagnostic":
                # Archive paths are rooted per run; policies, metrics and targets match.
                records_left = deepcopy(left[field]["records"])
                records_right = deepcopy(right[field]["records"])
                for records in (records_left, records_right):
                    for row in records:
                        for archive in row["archives"]:
                            archive["path"] = Path(archive["path"]).name
                assert tree_hash(records_left) == tree_hash(records_right)
                for key in ("trajectories", "transitions", "used"):
                    assert tree_hash(left[field][key]) == tree_hash(right[field][key])
            else:
                assert tree_hash(left[field]) == tree_hash(right[field]), (beta, field)


def test_shared_budget_charges_other_campaign_before_p3_unit(tmp_path):
    power = power_fixture(tmp_path)
    artifacts = tmp_path / "artifacts"
    day = datetime.now(LA_PAZ).date().isoformat()
    external = artifacts / "p0-approved-v1" / "ledger.jsonl"
    external.parent.mkdir(parents=True)
    external.write_text(json.dumps(dict(status="completed", days={day: {
        "charged_wall_seconds": 10800.0,
    }})) + "\n")
    root = artifacts / "p3-synthetic-budget"
    state = run(root, power, fixture_window=False)
    assert state["status"] == "ready" and state["units"] == []
    assert state["days"][day]["external_seconds"] == 10800.0
    assert not list(root.rglob("checkpoint-*"))


def test_p3_budget_pauses_before_midnight_and_caps_run_sessions(tmp_path):
    day = datetime.now(LA_PAZ).date()
    near_midnight = datetime.combine(day, time(23, 59), LA_PAZ).timestamp()
    with P3Ledger(tmp_path / "midnight", now=near_midnight,
                  identity={"profile": "p3_synthetic_units"}) as ledger:
        ledger.preflight_done(near_midnight + 1)
        assert ledger.admit("C0", "q0", near_midnight + 2) == "pause"
        assert ledger.day["hard_deadline"] <= datetime.combine(
            day + timedelta(days=1), time(), LA_PAZ,
        ).timestamp()

    start = datetime.combine(day, time(9), LA_PAZ).timestamp()
    identity = {"profile": "p3_synthetic_units", "fixture": "sessions"}
    for session in range(3):
        with P3Ledger(tmp_path / "sessions", now=start + session * 40,
                      identity=identity) as ledger:
            ledger.preflight_done(start + session * 40 + 1)
            for index in range(18):
                now = start + session * 40 + 2 * index + 2
                ledger.begin(f"run-{index:02d}", "q0", now)
                ledger.finish(now + 1, resources={}, condition="C0", work_seconds=1,
                              work_ended=now + 1)
    with P3Ledger(tmp_path / "sessions", now=start + 121, identity=identity) as ledger:
        with pytest.raises(ValueError, match="session limit"):
            ledger.begin("run-00", "q0", start + 122)
        assert ledger.state["status"] == "incomplete"


def test_signal_inside_second_unit_fails_without_accepting_partial(tmp_path, monkeypatch):
    import btc_risk_rl.pilots.p2r_units as engine

    power = power_fixture(tmp_path)
    root = tmp_path / "artifacts" / "p3-synthetic-signal"
    first = run(root, power, max_units=1)
    assert len(first["units"]) == 1
    previous = root / "run-00-C5-b0/checkpoint-0/state.pt"
    previous_sha = hashlib.sha256(previous.read_bytes()).hexdigest()
    actual = engine.supervise

    def interrupt(_command, **kwargs):
        on_poll = kwargs["on_poll"]
        sent = False

        def tick(pid, elapsed, peak):
            nonlocal sent
            on_poll(pid, elapsed, peak)
            if not sent:
                sent = True
                os.kill(os.getpid(), signal.SIGTERM)

        kwargs["on_poll"] = tick
        return actual(_command, **kwargs)

    monkeypatch.setattr(engine, "supervise", interrupt)
    failed = run(root, power)
    assert failed["status"] == "failed" and len(failed["units"]) == 1
    assert failed["pending"]["unit"] == 1
    assert hashlib.sha256(previous.read_bytes()).hexdigest() == previous_sha
    assert not (root / "run-00-C5-b0/checkpoint-1").exists()
    with pytest.raises(ValueError, match="failed/incomplete"):
        run(root, power)


def test_incoherent_p3_report_fails_ledger_and_retains_prior_checkpoint(tmp_path, monkeypatch):
    import btc_risk_rl.pilots.p2r_units as engine

    power = power_fixture(tmp_path)
    root = tmp_path / "artifacts" / "p3-synthetic-forged-report"
    assert len(run(root, power, max_units=1)["units"]) == 1
    point = root / "run-00-C5-b0/checkpoint-0/state.pt"
    prior_sha = hashlib.sha256(point.read_bytes()).hexdigest()
    actual = engine.supervise

    def forge_after_worker(*args, **kwargs):
        result = actual(*args, **kwargs)
        work = Path(kwargs["output"]).parent
        path = work / "unit-1.json"
        payload = json.loads(path.read_text())
        payload["report"]["market_training_executed"] = True
        path.write_text(json.dumps(payload))
        return result

    monkeypatch.setattr(engine, "supervise", forge_after_worker)
    with pytest.raises(ValueError, match="market training marker"):
        run(root, power)
    ledger = json.loads((root / "ledger.jsonl").read_text().splitlines()[-1])
    assert ledger["status"] == "failed" and len(ledger["units"]) == 1
    assert ledger["pending"]["unit"] == 1
    assert hashlib.sha256(point.read_bytes()).hexdigest() == prior_sha
    with pytest.raises(ValueError, match="failed/incomplete"):
        run(root, power)


def fabricated_market_envelope(tmp_path, unit, marker):
    """Only JSON and tensors: no TrainingMarket construction or market steps."""
    settings = P3MarketSettings(seed=710031, critic_beta=1)
    work = tmp_path / "run-01-C0-b1"
    work.mkdir()
    point = work / f"checkpoint-{unit}"
    point.mkdir()
    boundary = "after_q0" if unit == 0 else "after_dual_and_D"
    batches = math.ceil(settings.n_a / settings.minibatch)
    actor, critic = unit * settings.actor_epochs * batches, unit * settings.critic_epochs * batches
    learning = settings.n_q + unit * (settings.n_a + settings.n_q + settings.n_b)
    state = dict(
        attrs=dict(actor_updates=actor, critic_updates=critic,
                   next_iteration=unit, boundary=boundary),
        collector=dict(trajectories=learning, transitions=180 * learning),
        diagnostic=dict(trajectories=unit * 64, transitions=unit * 64 * 180),
        actor_optimizer={"state": {} if unit == 0 else {0: {"step": torch.tensor(float(actor))}}},
        critic_optimizer={"state": {} if unit == 0 else {0: {"step": torch.tensor(float(critic))}}},
    )
    torch.save(state, point / "state.pt")
    sha = hashlib.sha256((point / "state.pt").read_bytes()).hexdigest()
    provenance = dict(data=dict(profile="accepted_train_collection_only"),
                      threads=1, deterministic=True)
    manifest = dict(state_sha256=sha, boundary=boundary,
                    schema_version="p2_complete_boundary_v1", profile=settings.purpose,
                    provenance=provenance, settings=asdict(settings),
                    condition="C0", run_id=work.name)
    (point / "manifest.json").write_text(json.dumps(manifest))
    report = dict(status="passed", purpose=settings.purpose, condition="C0",
                  settings=asdict(settings), market_training_executed=marker,
                  actor_updates=actor, critic_updates=critic,
                  next_iteration=unit, boundary=boundary,
                  trajectories=learning, transitions=180 * learning)
    payload = dict(status="passed", unit=unit, beta=1,
                   resources=_expected(settings, unit, 64), checkpoint=str(point),
                   checkpoint_sha256=sha, report=report)
    (work / f"unit-{unit}.json").write_text(json.dumps(payload))
    return work, settings, provenance, payload


@pytest.mark.parametrize("unit", [0, 1])
def test_p3_supervisor_checks_market_marker_before_accepting_unit(tmp_path, unit):
    work, settings, provenance, payload = fabricated_market_envelope(
        tmp_path, unit, marker=unit == 1,
    )
    _verify_completion(work, unit, settings, "C0", work.name,
                       {"status": "passed"}, provenance, 64)
    payload["report"]["market_training_executed"] = unit == 0
    (work / f"unit-{unit}.json").write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="market training marker"):
        _verify_completion(work, unit, settings, "C0", work.name,
                           {"status": "passed"}, provenance, 64)


def test_p3_supervisor_rejects_boolean_arm_identity(tmp_path):
    work, settings, provenance, payload = fabricated_market_envelope(tmp_path, 1, marker=True)
    payload["beta"] = True
    (work / "unit-1.json").write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="worker result"):
        _verify_completion(work, 1, settings, "C0", work.name,
                           {"status": "passed"}, provenance, 64)
