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
