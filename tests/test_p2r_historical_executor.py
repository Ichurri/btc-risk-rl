"""P2R historical executor contract; no historical learning is run here."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from test_simulator import accepted_synthetic as accepted_fixture

accepted_synthetic = accepted_fixture


def test_market_settings_match_adopted_design():
    from btc_risk_rl.pilots.p2r_market import P2RMarketSettings, roster

    settings = P2RMarketSettings(seed=610031)
    assert (settings.iterations, settings.n_q, settings.n_a, settings.n_b) == (
        10, 400, 64, 400
    )
    assert (settings.critic_epochs, settings.actor_epochs, settings.bound) == (
        4, 2, 0.10536051565782628
    )
    assert settings.purpose == "authorized_p2r_only"
    assert roster() == [
        (610031, "C0"), (610031, "C5"), (610031, "C10"),
        (610047, "C5"), (610047, "C10"), (610047, "C0"),
        (610081, "C10"), (610081, "C0"), (610081, "C5"),
    ]
    with pytest.raises(ValueError):
        P2RMarketSettings(seed=610031, n_q=399)


def test_market_entry_rejected_before_loading_data_or_creating_root(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import p2r_market

    monkeypatch.setattr(p2r_market, "MARKET_EXECUTION_ENABLED", False)
    monkeypatch.setattr(p2r_market, "TrainingMarket", lambda *_a, **_k: pytest.fail("loaded"))
    monkeypatch.setattr(p2r_market, "ROOT", tmp_path)
    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        p2r_market.run_market_units()
    assert not list(tmp_path.iterdir())


def test_market_worker_rejects_even_forged_request_before_reading_it(tmp_path):
    forged = tmp_path / "forged.json"
    forged.write_text(json.dumps({"authorized": True, "market_execution_authorized": True}))
    result = subprocess.run(
        [sys.executable, "-m", "btc_risk_rl.pilots.p2r_worker", str(forged)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert ("ledger.jsonl" in result.stderr
            or "P2R worker request does not match pending unit" in result.stderr)
    assert not (tmp_path / "checkpoint-0").exists()


def test_public_market_command_rejects_before_output(tmp_path):
    root = tmp_path / "p2r-market"
    result = subprocess.run(
        [sys.executable, "scripts/run_p2r.py", "--profile", "market", "--mode",
         "algorithm", "--output", str(root)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 2
    assert "NOT AUTHORIZED" in result.stderr
    assert not root.exists()


def test_separate_historical_command_requires_user_service_before_data_access():
    result = subprocess.run(
        [sys.executable, "scripts/run_p2r_market.py"], capture_output=True,
        text=True, check=False,
    )
    assert result.returncode != 0
    assert "requires a systemd user service" in result.stderr


def test_edited_approval_json_cannot_activate_market(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import p2r_market

    forged = tmp_path / "approval.json"
    forged.write_text(json.dumps(dict(active=True, scope="accepted_training_2018_2022_only")))
    monkeypatch.setattr(p2r_market, "REGISTRATION", forged)
    with pytest.raises(PermissionError, match="approval hash mismatch"):
        p2r_market.P2RMarketPermit.require_campaign()
    assert not (tmp_path / "p2r-approved-v2").exists()


def test_pinned_approval_matches_adopted_protocol_and_training_scope():
    from btc_risk_rl.pilots import p2r_market

    approval = p2r_market.P2RMarketPermit.require_campaign()
    assert p2r_market.digest(p2r_market.REGISTRATION) == p2r_market.REGISTRATION_SHA256
    assert approval["campaign"] == p2r_market.CAMPAIGN.name
    assert approval["scope"] == "accepted_training_2018_2022_only"
    assert approval["training_shard_manifest_sha256"] == (
        p2r_market.TRAIN_SHARD_MANIFEST_SHA256
    )


def test_market_unit_and_diagnostic_require_p2r_lease(accepted_synthetic, tmp_path):
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.pilots.p2 import Diagnostic
    from btc_risk_rl.pilots.p2_runner import complete_unit
    from btc_risk_rl.pilots.p2r_market import P2RMarketSettings

    config, _, prepared, _ = accepted_synthetic
    manifest_sha = __import__("hashlib").sha256((prepared / "manifest.json").read_bytes()).hexdigest()
    source = TrainingMarket(config, prepared, expected_manifest=manifest_sha)
    settings = P2RMarketSettings(seed=610031)
    output = tmp_path / "blocked"
    with pytest.raises(PermissionError):
        complete_unit(source, settings, root=output, condition="C0",
                      run_id="run-00-C0", unit=0)
    assert not output.exists()
    with pytest.raises(PermissionError):
        Diagnostic(output / "D", n=64).bind(source, settings.seed, "run-00-C0")
    assert not output.exists()


def test_preflight_rejects_changed_protocol_before_training_source(monkeypatch):
    from btc_risk_rl.pilots import p2r_market

    monkeypatch.setitem(p2r_market.ANCHORS, p2r_market.PROTOCOL, "0" * 64)
    monkeypatch.setattr(p2r_market, "TrainingMarket", lambda *_a, **_k: pytest.fail("loaded"))
    with pytest.raises(ValueError, match="frozen input changed"):
        p2r_market.inspect_preflight()


def test_worker_request_must_match_canonical_run_and_pending_hash(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import p2r_market
    from btc_risk_rl.pilots.p2_budget import state_hash

    campaign = tmp_path / "p2r-approved-v2"
    run_root = campaign / "run-00-C0"
    run_root.mkdir(parents=True)
    monkeypatch.setattr(p2r_market, "CAMPAIGN", campaign)
    monkeypatch.setattr(p2r_market.P2RMarketPermit, "require_campaign", lambda *_: {})
    permit = p2r_market.P2RMarketPermit("token")
    request = run_root / "request-0.json"
    payload = dict(root=str(run_root), run_id="run-00-C0", unit=0, previous=None,
                   atomic_checkpoint=True, config=str(p2r_market.CONFIG), token="token")
    request.write_text(json.dumps(payload))
    state = dict(status="running", cursor=0, pending=dict(unit=0, run_id="run-00-C0",
                 token="token", supervisor_pid=__import__("os").getppid(),
                 request_sha256=p2r_market.digest(request)), runs={})
    state["state_hash"] = state_hash(state)
    (campaign / "ledger.jsonl").write_text(json.dumps(state) + "\n")
    permit.validate_request(request, payload)
    payload["root"] = str(tmp_path / "wrong-root")
    request.write_text(json.dumps(payload))
    state["pending"]["request_sha256"] = p2r_market.digest(request)
    state["state_hash"] = state_hash(state)
    (campaign / "ledger.jsonl").write_text(json.dumps(state) + "\n")
    with pytest.raises(PermissionError, match="request"):
        permit.validate_request(request, payload)


def test_readonly_budget_charges_failed_pending_day_conservatively(tmp_path):
    from datetime import datetime, timezone

    from btc_risk_rl.pilots.p2r_market import inspect_shared_budget

    day = "2026-10-07"
    ledger = tmp_path / "p2-approved-v1" / "ledger.jsonl"
    ledger.parent.mkdir()
    ledger.write_text(json.dumps(dict(status="failed", pending={"unit": 1},
                    days={day: {"charged_wall_seconds": 80.0}})) + "\n")
    now = datetime(2026, 10, 7, 12, tzinfo=timezone.utc).timestamp()
    snapshot = inspect_shared_budget(tmp_path, now=now)
    assert snapshot["remaining_seconds"] == 0
    assert snapshot["external_seconds"] == 10800
    assert snapshot["sources"][0]["reason"] == "incomplete_debit"
    assert not (tmp_path / "shared-pilot-budget").exists()


def test_shared_supervisor_advances_two_synthetic_runs(tmp_path):
    from test_p2r_units import fixture_power

    from btc_risk_rl.agents.synthetic import SyntheticMarket
    from btc_risk_rl.config import load_config
    from btc_risk_rl.pilots.p2 import P2SyntheticSettings
    from btc_risk_rl.pilots.p2r_units import _run_units, synthetic_worker_command

    rows = [(610031, "C0"), (610047, "C5")]

    def settings(seed):
        return P2SyntheticSettings(seed=seed, iterations=1, hidden=4, n_a=1,
                                   n_q=2, n_b=2, actor_epochs=1, critic_epochs=4)

    root = tmp_path / "artifacts" / "p2r-synthetic-two-runs"
    kwargs = dict(
        roster=rows, source=SyntheticMarket(load_config(Path("configs/initial.toml"))),
        settings_for=settings, command_for=synthetic_worker_command,
        profile="p2r_synthetic_units", diagnostic_n=2, max_units=3,
        power_root=fixture_power(tmp_path), memory_available=4 * 1024**3,
        disk_free=10 * 1024**3, fixture_window=True, heartbeat_seconds=.05,
    )
    state = _run_units(root, "configs/initial.toml", settings(rows[0][0]), **kwargs)
    assert state["status"] == "ready" and state["cursor"] == 1
    assert [(unit["run_id"], unit["unit"]) for unit in state["units"]] == [
        ("run-00-C0", 0), ("run-00-C0", 1), ("run-01-C5", 0)
    ]
    assert (root / "run-00-C0/checkpoint-1").is_dir()
    assert (root / "run-01-C5/checkpoint-0").is_dir()
    assert not list(root.rglob("checkpoint-*.partial-*"))
    kwargs["max_units"] = None
    resumed = _run_units(root, "configs/initial.toml", settings(rows[0][0]), **kwargs)
    assert resumed["status"] == "completed" and resumed["cursor"] == 2


def test_p2r_checkpoint_is_not_published_if_write_interrupts(config, tmp_path, monkeypatch):
    from btc_risk_rl.agents import checkpoint
    from btc_risk_rl.agents.synthetic import SyntheticMarket
    from btc_risk_rl.pilots.p2 import P2SyntheticSettings
    from btc_risk_rl.pilots.p2_runner import complete_unit

    def interrupted(*_args, **_kwargs):
        raise RuntimeError("synthetic interrupted checkpoint write")

    monkeypatch.setattr(checkpoint.torch, "save", interrupted)
    root = tmp_path / "synthetic-checkpoint"
    settings = P2SyntheticSettings(iterations=1, hidden=4, n_a=1, n_q=2, n_b=2,
                                   actor_epochs=1, critic_epochs=4, seed=610031)
    with pytest.raises(RuntimeError, match="synthetic interrupted"):
        complete_unit(SyntheticMarket(config), settings, root=root, condition="C5",
                      run_id="run-00-C5", unit=0, atomic_checkpoint=True)
    assert not (root / "checkpoint-0").exists()
    assert len(list(root.glob("checkpoint-0.partial-*"))) == 1
