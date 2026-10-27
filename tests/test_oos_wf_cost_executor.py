"""The unapproved two-fold cost executor must fail closed."""

import json

import pytest

from btc_risk_rl.pilots import wf_cost


def test_fixed_roster_and_caps():
    rows = wf_cost.roster()
    assert rows == (("2021", 276696733, "C10"), ("2022", 498614892, "C10"))
    assert [u for _, u in wf_cost.units()] == list(range(11)) * 2
    assert sum(wf_cost.unit_cap(u) for _, u in wf_cost.units()) == 3840


def test_public_gate_rejects_before_any_root_or_source_access(tmp_path, monkeypatch):
    root = tmp_path / "cost-root"
    monkeypatch.setattr(wf_cost, "CAMPAIGN", root)
    monkeypatch.setattr(wf_cost, "TRAIN_SHARD", tmp_path / "missing-shard")
    monkeypatch.setattr(wf_cost, "MARKET_EXECUTION_ENABLED", False)
    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        wf_cost.run_historical_units()
    assert not root.exists()


def test_admission_accounts_global_and_own_limits_without_mutation():
    state = wf_cost.BudgetState(active_days=("2026-10-26",), daily_own=3490,
                                cumulative=4800, global_spent=6600)
    assert wf_cost.admit(state, "2026-10-26", 0) == "pause"
    state = wf_cost.BudgetState(active_days=("2026-10-26",), daily_own=3300,
                                cumulative=4800, global_spent=6600)
    assert wf_cost.admit(state, "2026-10-26", 1) == "start"
    assert wf_cost.admit(state, "2026-10-27", 1) == "start"
    state = wf_cost.BudgetState(active_days=("2026-10-26", "2026-10-27"),
                                daily_own=0, cumulative=4800, global_spent=0)
    assert wf_cost.admit(state, "2026-10-28", 1) == "incomplete"
    assert wf_cost.admit(wf_cost.BudgetState((), 0, 0, 8101), "2026-10-26", 1) == "pause"


def test_preflight_summary_is_read_only_and_reports_blockers(tmp_path, monkeypatch):
    root = tmp_path / "root"
    monkeypatch.setattr(wf_cost, "CAMPAIGN", root)
    monkeypatch.setattr(wf_cost, "inspect_host", lambda: {
        "power": {"ac": False, "battery_percent": 80},
        "memory_available_bytes": 5 * 1024**3,
        "disk_free_bytes": 25 * 1024**3,
        "linger": "yes", "user_manager": "running",
    })
    monkeypatch.setattr(wf_cost, "inspect_inputs", lambda: {"ok": True, "opened": []})
    monkeypatch.setattr(wf_cost, "inspect_budget", lambda: {"ok": True, "global_spent": 0})
    result = wf_cost.inspect_preflight()
    assert result["status"] == "blocked"
    assert "AC not connected" in result["blockers"]
    assert not root.exists()
    assert not (tmp_path / "root" / "ledger.jsonl").exists()
    assert json.loads(json.dumps(result))["market_execution_enabled"] is False
    assert "Cost-study campaign has no active approval" in result["blockers"]


def test_protected_input_names_rejected(tmp_path):
    for bad in ("validation.csv", "final.csv", "segmented-B-h1"):
        with pytest.raises(ValueError):
            wf_cost.guard_fold_path(tmp_path / bad)


def test_fold_source_refits_only_cutoff_training_and_has_expected_starts():
    from btc_risk_rl.pilots.wf_cost_source import inspect_fold

    for year, starts, fit_rows in (("2021", 3639, 5764), ("2022", 4678, 7703)):
        result = inspect_fold(year)
        assert result["episodes"] == starts
        assert result["fit_rows"] == fit_rows
        assert result["latest_target_ms"] < result["cutoff_ms"]
        assert result["source_profile"] == "accepted_train_collection_only"
        assert result["validation_observations_loaded"] is False
        assert result["trajectories_generated"] == 0


def test_settings_match_fixed_cost_study_and_reject_other_seeds():
    from btc_risk_rl.pilots.wf_cost import WFCostSettings

    for _, seed, _ in wf_cost.roster():
        settings = WFCostSettings(seed=seed)
        assert settings.iterations == 10
        assert settings.critic_beta == 0
        assert settings.critic_epochs == 4
        assert settings.n_q == settings.n_b == 400
        assert settings.n_a == 64
    with pytest.raises(ValueError):
        WFCostSettings(seed=610031)


def test_completed_q0_study_stays_closed_after_preunit_identity_failure():
    assert wf_cost.MARKET_EXECUTION_ENABLED is False
    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        wf_cost.require_campaign()
    entry = json.loads(wf_cost.REGISTRATION.read_text())
    assert entry["campaign"] == "oos-v12-wf-cost-only-01"
    assert entry["active"] is True  # Historical approval remains immutable.
    assert wf_cost.digest(wf_cost.REGISTRATION) == wf_cost.REGISTRATION_SHA256
    assert entry["scope"] == "cost_measurement_training_folds_only"
    assert entry["protocol_sha256"] == wf_cost.digest(wf_cost.PROTOCOL)
    assert entry["design_sha256"] == wf_cost.digest(wf_cost.DESIGN)
    assert entry["training_shard_manifest_sha256"] == wf_cost.SHARD_MANIFEST_SHA256


def test_public_gate_rejects_when_permit_is_disabled_without_creating_root(
    tmp_path, monkeypatch
):
    root = tmp_path / "new-campaign"
    monkeypatch.setattr(wf_cost, "CAMPAIGN", root)
    assert not root.exists()
    monkeypatch.setattr(wf_cost, "MARKET_EXECUTION_ENABLED", False)
    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        wf_cost.run_historical_units()
    assert not root.exists()


def test_forged_registration_does_not_unlock(monkeypatch, tmp_path):
    fake = tmp_path / "approval.json"
    fake.write_text(json.dumps({"active": True, "scope": "cost_measurement_training_folds_only"}))
    monkeypatch.setattr(wf_cost, "MARKET_EXECUTION_ENABLED", True)
    monkeypatch.setattr(wf_cost, "REGISTRATION", fake)
    monkeypatch.setattr(wf_cost, "REGISTRATION_SHA256", "0" * 64)
    with pytest.raises(PermissionError, match="hash mismatch"):
        wf_cost.require_campaign()


def test_unit_acceptance_rejects_forged_marker_and_preserves_prior_checkpoint(tmp_path):
    from btc_risk_rl.pilots.wf_cost import WFCostLedger

    root = tmp_path / "cost"
    ledger = WFCostLedger(root, identity={"fixture": True}, now=1000)
    with ledger:
        ledger.preflight_done(1001)
        ledger.begin_unit("2021", 0, 1002)
        q0 = root / "wf-2021" / "checkpoint-0"
        q0.mkdir(parents=True)
        (q0 / "state.pt").write_bytes(b"complete Q0")
        (q0 / "manifest.json").write_text(json.dumps({
            "schema_version": "p2_complete_boundary_v1", "boundary": "after_q0",
            "state_sha256": wf_cost.digest(q0 / "state.pt"),
            "profile": "wf_cost_only",
            "run_id": "wf-2021", "condition": "C10",
        }))
        ledger.accept_unit("2021", 0, 1010, q0, report={
            "market_training_executed": False, "actor_updates": 0,
            "critic_updates": 0, "boundary": "after_q0",
        })
        original = wf_cost.digest(q0 / "state.pt")
        ledger.begin_unit("2021", 1, 1011)
        later = root / "wf-2021" / "checkpoint-1"
        later.mkdir()
        (later / "state.pt").write_bytes(b"partial")
        with pytest.raises(ValueError, match="marker"):
            ledger.accept_unit("2021", 1, 1018, later, report={
                "market_training_executed": False, "actor_updates": 8,
                "critic_updates": 16, "boundary": "after_dual_and_D",
            })
        assert ledger.state["status"] == "failed"
        assert len(ledger.state["units"]) == 1
        assert wf_cost.digest(q0 / "state.pt") == original
    with pytest.raises(ValueError, match="failed"):
        WFCostLedger(root, identity={"fixture": True}, now=1100)


def test_first_q0_complete_boundary_requires_audit_pause(tmp_path):
    from btc_risk_rl.pilots.wf_cost import WFCostLedger
    from btc_risk_rl.pilots.wf_cost_units import first_q0_audit_pause

    root = tmp_path / "cost"
    with WFCostLedger(root, identity={"fixture": True}, now=1000) as ledger:
        ledger.preflight_done(1001)
        assert not first_q0_audit_pause(ledger.state)
        ledger.begin_unit("2021", 0, 1002)
        checkpoint = root / "wf-2021/checkpoint-0"
        checkpoint.mkdir(parents=True)
        (checkpoint / "state.pt").write_bytes(b"complete Q0")
        (checkpoint / "manifest.json").write_text(json.dumps({
            "schema_version": "p2_complete_boundary_v1", "boundary": "after_q0",
            "state_sha256": wf_cost.digest(checkpoint / "state.pt"),
            "profile": "wf_cost_only", "run_id": "wf-2021", "condition": "C10",
        }))
        ledger.accept_unit("2021", 0, 1010, checkpoint, report={
            "market_training_executed": False, "actor_updates": 0,
            "critic_updates": 0, "boundary": "after_q0",
        })
        assert first_q0_audit_pause(ledger.state)
        assert ledger.state["status"] == "ready"
        assert len(ledger.state["units"]) == 1
        assert ledger.state["pending"] is None


def test_synthetic_ledger_accepts_exactly_twenty_two_complete_units(tmp_path):
    from btc_risk_rl.pilots.wf_cost import WFCostLedger

    root = tmp_path / "cost"
    ledger = WFCostLedger(root, identity={"synthetic_fixture": True}, now=1000)
    with ledger:
        ledger.preflight_done(1001)
        now = 1002
        for fold, unit in wf_cost.units():
            assert ledger.admit_unit(fold, unit, now) == "start"
            ledger.begin_unit(fold, unit, now)
            point = root / f"wf-{fold}" / f"checkpoint-{unit}"
            point.mkdir(parents=True)
            (point / "state.pt").write_bytes(f"synthetic:{fold}:{unit}".encode())
            boundary = "after_q0" if unit == 0 else "after_dual_and_D"
            (point / "manifest.json").write_text(json.dumps({
                "schema_version": "p2_complete_boundary_v1", "boundary": boundary,
                "state_sha256": wf_cost.digest(point / "state.pt"),
                "profile": "wf_cost_only",
                "run_id": f"wf-{fold}", "condition": "C10",
            }))
            now += 10
            ledger.accept_unit(fold, unit, now, point, report={
                "market_training_executed": unit > 0,
                "actor_updates": 8 * unit, "critic_updates": 16 * unit,
                "boundary": boundary,
            })
            now += 1
        assert ledger.state["status"] == "completed"
        assert ledger.state["cursor"] == 2
        assert len(ledger.state["units"]) == 22
    reopened = WFCostLedger(root, identity={"synthetic_fixture": True}, now=now + 1)
    with reopened:
        assert reopened.state["status"] == "completed"


def test_corrupt_ledger_chain_is_rejected(tmp_path):
    from btc_risk_rl.pilots.wf_cost import WFCostLedger

    root = tmp_path / "cost"
    with WFCostLedger(root, identity={"synthetic_fixture": True}, now=1000):
        pass
    path = root / "ledger.jsonl"
    lines = path.read_text().splitlines()
    lines[-1] = lines[-1].replace('"status": "ready"', '"status": "completed"')
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="hash chain corrupt"):
        WFCostLedger(root, identity={"synthetic_fixture": True}, now=1001)


def test_read_only_budget_debits_failed_pending_campaign_conservatively(tmp_path,
                                                                         monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    monkeypatch.setattr(wf_cost, "ROOT", tmp_path)
    day = "2026-10-26"
    now = datetime(2026, 10, 26, 12, tzinfo=ZoneInfo("America/La_Paz")).timestamp()
    path = tmp_path / "artifacts/p2-approved-v1/ledger.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"status": "failed", "pending": {"unit": 1},
                                "days": {day: {"charged_wall_seconds": 100}}}) + "\n")
    result = wf_cost.inspect_budget(now=now)
    assert result["global_spent"] == 10800
    assert result["remaining_before_reserve"] == 0


def test_existing_shared_budget_counts_cost_study_ledger(tmp_path):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from btc_risk_rl.pilots.p2r import P2RSharedBudget
    from btc_risk_rl.pilots.p2r_market import inspect_shared_budget

    day = "2026-10-26"
    now = datetime(2026, 10, 26, 12, tzinfo=ZoneInfo("America/La_Paz")).timestamp()
    root = tmp_path / "artifacts"
    path = root / "oos-v12-wf-cost-only-01/ledger.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"status": "ready", "days": {
        day: {"charged_wall_seconds": 300}}}) + "\n")
    mirror = inspect_shared_budget(root, now=now)
    assert mirror["external_seconds"] == 300
    with P2RSharedBudget(root, "another-campaign", now=now, synthetic_fixture=True) as shared:
        assert shared.external_seconds == 300


def test_fold_manifest_is_immutable_after_creation(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_units

    class Source:
        route_ids = tuple(range(3))
        audit = {"fit_count": 5}

        def identity(self):
            return {"fold": "2021", "scaler_sha256": "abc"}

    monkeypatch.setattr(wf_cost_units, "CAMPAIGN", tmp_path / "isolated")
    sources = {"2021": Source()}
    wf_cost_units._record_fold_manifests(sources)
    manifest = tmp_path / "isolated/folds/wf-2021/manifest.json"
    original = wf_cost.digest(manifest)
    wf_cost_units._record_fold_manifests(sources)
    assert wf_cost.digest(manifest) == original
    manifest.write_text("{}")
    with pytest.raises(ValueError, match="changed on resume"):
        wf_cost_units._record_fold_manifests(sources)


def test_resource_guard_rejects_loss_during_supervised_unit():
    from btc_risk_rl.pilots.wf_cost_units import resource_ready

    good = {"power": {"ac": True, "battery_percent": 75},
            "memory_available_bytes": 5 * 1024**3,
            "disk_free_bytes": 25 * 1024**3}
    assert resource_ready(good)
    for change in ({"power": {"ac": False, "battery_percent": 75}},
                   {"power": {"ac": True, "battery_percent": 49}},
                   {"memory_available_bytes": 4 * 1024**3 - 1},
                   {"disk_free_bytes": 20 * 1024**3 - 1}):
        assert not resource_ready(good | change)
