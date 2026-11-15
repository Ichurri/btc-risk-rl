"""Synthetic gate and admission tests; no protected partition is opened."""

import hashlib
import json
from dataclasses import asdict

import pytest


def _host(**changes):
    value = {
        "power": {"ac": True, "battery_percent": 60},
        "memory_available_bytes": 8 * 1024**3,
        "disk_free_bytes": 40 * 1024**3,
        "linger": "yes", "user_manager": "running",
    }
    value.update(changes)
    return value


@pytest.mark.parametrize("change,expected", [
    ({"power": {"ac": False, "battery_percent": 60}}, "AC"),
    ({"power": {"ac": True, "battery_percent": 49}}, "Battery"),
    ({"memory_available_bytes": 4 * 1024**3 - 1}, "MemAvailable"),
    ({"disk_free_bytes": 20 * 1024**3 - 1}, "Disk"),
    ({"linger": "no"}, "systemd"),
    ({"user_manager": "degraded"}, "systemd"),
])
def test_host_resource_guard_preserves_thresholds(change, expected):
    from btc_risk_rl.evaluation.historical_supervisor import host_blockers

    assert any(expected in row for row in host_blockers(_host(**change)))
    assert host_blockers(_host()) == []


def test_source_preflight_rejects_before_training_or_h1_open(monkeypatch, tmp_path):
    from btc_risk_rl.evaluation import access
    from btc_risk_rl.evaluation import historical_supervisor as target

    monkeypatch.setitem(access.ENABLED, "technical_2023_source", False)
    monkeypatch.setattr(target, "ROOT", tmp_path)
    monkeypatch.setattr(target, "verify_complete_main_roster",
                        lambda _root: pytest.fail("training roster opened"))
    with pytest.raises(PermissionError, match="disabled"):
        target.source_preflight()
    assert list(tmp_path.iterdir()) == []


def test_worker_rejects_closed_gate_before_ledger_or_export(monkeypatch, tmp_path):
    from btc_risk_rl.evaluation import access
    from btc_risk_rl.evaluation import historical_supervisor as target

    monkeypatch.setitem(access.ENABLED, "technical_2023", False)
    monkeypatch.setattr(target, "ROOT", tmp_path)
    monkeypatch.setattr(target, "_read_ledger_identity",
                        lambda: pytest.fail("ledger opened"))
    with pytest.raises(PermissionError, match="disabled"):
        target.worker("run-00-C0-b0", session_token="x" * 32,
                      parent_pid=12345)


def test_unit_inputs_require_frozen_beta_zero_and_training_provenance(monkeypatch, tmp_path):
    from btc_risk_rl.evaluation import historical_supervisor as target
    from btc_risk_rl.pilots.oos_v12_training import OOSSettings

    seed, run_id = 1869792951, "run-00-C0-b0"
    checkpoint = tmp_path / run_id / "checkpoint-10"
    checkpoint.mkdir(parents=True)
    manifest = {
        "settings": asdict(OOSSettings(seed=seed)),
        "provenance": {"data": {"manifest_sha256": target.H1_SHA,
                                "scaler_sha256": target.SCALER_SHA}},
    }
    identity = manifest["provenance"]["data"]
    monkeypatch.setattr(target, "TRAINING_IDENTITY_SHA", hashlib.sha256(json.dumps(
        identity, sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest())
    (checkpoint / "manifest.json").write_text(json.dumps(manifest))
    monkeypatch.setattr(target, "TRAINING_ROOT", tmp_path)
    monkeypatch.setattr(target, "EXPORT", tmp_path)
    (tmp_path / "manifest.json").write_text("synthetic export identity")
    run = {"run_id": run_id, "seed": seed, "condition": "C0",
           "checkpoint_sha256": "a" * 64}
    found, kwargs = target._unit_inputs(run, scaler=object(), config=object())
    assert found == checkpoint
    assert kwargs["settings"]["critic_beta"] == 0
    assert kwargs["actor_updates"] == 80
    assert kwargs["critic_updates"] == 160
    manifest["settings"]["critic_beta"] = 1
    (checkpoint / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="settings"):
        target._unit_inputs(run, scaler=object(), config=object())


def test_budget_block_prevents_ledger_creation_and_worker(monkeypatch):
    from btc_risk_rl.evaluation import historical_supervisor as target

    monkeypatch.setattr(target, "technical_preflight",
                        lambda: ({"runs": []}, {}, {}))
    monkeypatch.setattr(target, "inspect_host", lambda: _host())
    monkeypatch.setattr(target, "budget_snapshot", lambda **_kw: {
        "ok": True, "remaining_before_reserve": 299.9,
        "oos_active_days": [],
    })
    monkeypatch.setattr(target, "_expected_roster",
                        lambda _verified: pytest.fail("ledger creation reached"))

    class Journal:
        def end(self, _token, **kwargs):
            assert kwargs["status"] == "ready"

    result = target._run_technical_session(Journal(), "t", 0.0)
    assert result["status"] == "blocked"


def test_parent_supervisor_pauses_and_reenters_only_after_complete_unit(
    monkeypatch, tmp_path,
):
    """Exercise the parent and real append-only ledger with invented units."""
    from btc_risk_rl.evaluation import historical_supervisor as target
    from btc_risk_rl.evaluation.ledger import EvaluationLedger

    runs = [
        {"run_id": f"run-{i:02d}-{condition}-b0", "seed": 101,
         "condition": condition, "checkpoint_sha256": str(i + 1) * 64}
        for i, condition in enumerate(("C0", "C5"))
    ]
    verified = {"runs": runs, "ledger_sha256": "a" * 64}
    campaign = tmp_path / "technical"
    export = tmp_path / "export"
    export.mkdir()
    monkeypatch.setattr(target, "CAMPAIGN", campaign)
    monkeypatch.setattr(target, "EXPORT", export)
    monkeypatch.setattr(target, "technical_preflight", lambda: (verified, {}, {"config": None}))
    monkeypatch.setattr(target, "budget_snapshot", lambda **_kw: {
        "ok": True, "remaining_before_reserve": 1200.0,
        "oos_active_days": ["2026-11-15"], "day_la_paz": "2026-11-15",
    })
    monkeypatch.setattr(target, "sha", lambda _path: "b" * 64)
    monkeypatch.setattr(target, "execution_code_sha256", lambda _root: "c" * 64)
    state = {"pause": False, "supervised": []}

    def host():
        return _host(memory_available_bytes=0) if state["pause"] else _host()

    monkeypatch.setattr(target, "inspect_host", host)

    def supervised(command, **_kwargs):
        run_id = command[command.index("--worker") + 1]
        identity = json.loads((campaign / "ledger.jsonl").read_text().splitlines()[0])["identity"]
        ledger = EvaluationLedger.open(campaign, identity)
        run = identity["roster"][ledger.state["cursor"]]
        assert run_id == run["run_id"]
        ledger.begin(run, token="invented")
        ledger.accept(run, token="invented", report_sha256="d" * 64,
                      trace_sha256="e" * 64, seconds=1.0)
        state["supervised"].append(run_id)
        if len(state["supervised"]) == 1:
            state["pause"] = True
        return {"status": "passed", "wall_seconds": 1.0}

    monkeypatch.setattr(target, "supervise", supervised)

    class Journal:
        def __init__(self):
            self.ends = []

        def end(self, _token, **kwargs):
            self.ends.append(kwargs["status"])

    first_journal = Journal()
    first = target._run_technical_session(first_journal, "synthetic", 0.0)
    assert first["status"] == "ready" and first["accepted"] == 1
    assert first_journal.ends == ["ready"]
    assert EvaluationLedger.open(campaign, json.loads(
        (campaign / "ledger.jsonl").read_text().splitlines()[0]
    )["identity"]).state["pending"] is None
    state["pause"] = False

    def closure(_ledger, destination, **_kwargs):
        destination.write_text("synthetic closure")
        return {"status": "passed"}

    monkeypatch.setattr(target, "write_technical_closure", closure)
    second_journal = Journal()
    second = target._run_technical_session(second_journal, "synthetic", 0.0)
    assert second["status"] == "passed" and second["accepted"] == 2
    assert second_journal.ends == ["ready"]
    assert state["supervised"] == [row["run_id"] for row in runs]
