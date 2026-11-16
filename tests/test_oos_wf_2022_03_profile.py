"""Independent third 2022-only cost profile and admission checks."""

import importlib.util
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest


def test_2022_03_is_distinct_and_closed_gate_can_be_forced(monkeypatch):
    from btc_risk_rl.pilots import wf_cost_2022_03_exec as profile
    from btc_risk_rl.pilots import wf_cost_2022_03_orchestrator as budget
    from btc_risk_rl.pilots.wf_permits import authorized_wf_permits

    assert profile.CAMPAIGN.name == "oos-v12-wf-cost-only-2022-03"
    assert budget.APPROVAL.name == "OOS-v1-2-wf-cost-2022-only-03-approval.json"
    assert budget.JOURNAL_NAME == "wf-2022-only-03-attempts.jsonl"
    assert profile.ROSTER == (("2022", 498614892, "C10"),)
    assert profile.UNITS == tuple(range(11))
    assert authorized_wf_permits()[profile.WF2022Permit] == profile.CAMPAIGN
    monkeypatch.setattr(profile, "MARKET_EXECUTION_ENABLED", False)
    monkeypatch.setattr(budget, "MARKET_EXECUTION_ENABLED", False)
    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        profile.require_campaign()


def test_2022_03_public_entry_rejects_closed_gate_before_root(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_2022_03_exec as profile
    from btc_risk_rl.pilots import wf_cost_2022_03_worker as worker

    monkeypatch.setattr(profile, "CAMPAIGN", tmp_path / "missing-root")
    monkeypatch.setattr(profile, "MARKET_EXECUTION_ENABLED", False)
    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        worker.run_request(tmp_path / "missing-request.json")
    assert not (tmp_path / "missing-root").exists()


def test_2022_03_debits_failed_02_without_changing_07_november(tmp_path):
    from btc_risk_rl.pilots import wf_cost_2022_03_orchestrator as budget

    assert budget.ATTEMPT_PROFILES[-1] == (
        "oos-v12-wf-cost-only-2022-03", "wf-2022-only-03-attempts.jsonl")
    assert budget.ATTEMPT_PROFILES[:2] == (
        ("oos-v12-wf-cost-only-2022-01", "wf-2022-only-01-attempts.jsonl"),
        ("oos-v12-wf-cost-only-2022-02", "wf-2022-only-02-attempts.jsonl"),
    )


def test_2022_03_shared_budget_charges_failed_02_once(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost
    from btc_risk_rl.pilots.p2_budget import state_hash
    from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal

    now = datetime(2026, 11, 9, 1, 45, tzinfo=ZoneInfo("America/La_Paz")).timestamp()
    artifacts = tmp_path / "artifacts"
    old = artifacts / "oos-v12-wf-cost-only-2022-02"
    old.mkdir(parents=True)
    state = {"status": "failed", "pending": {"unit": 8},
             "days": {"2026-11-09": {"started_utc_epoch": now - 611,
                                     "charged_wall_seconds": 611.0}}}
    state["state_hash"] = state_hash(state)
    (old / "ledger.jsonl").write_text(json.dumps(state) + "\n")
    with WFCostSessionJournal(old / "sessions.jsonl", campaign=old.name) as sessions:
        token = sessions.start(now=now - 611, monotonic=100,
                               invocation_id="historical-failed-fixture")
        sessions.end(token, now=now, monotonic=711, status="failed",
                     reason="memory guard")
    monkeypatch.setattr(wf_cost, "ROOT", tmp_path)
    result = wf_cost.inspect_budget(now=now,
                                    campaign=artifacts / "oos-v12-wf-cost-only-2022-03")
    assert result["global_spent"] == 10800
    assert sum(x["charged_today_seconds"] for x in result["sources"]
               if "2022-02" in x["path"]) == 10800


def test_2022_03_cannot_start_before_10_november():
    from btc_risk_rl.pilots.wf_cost_2022_03_exec import (
        date_admissible,
        window_admissible,
    )

    zone = ZoneInfo("America/La_Paz")
    before = datetime(2026, 11, 9, 23, 59, 59, tzinfo=zone).timestamp()
    first = datetime(2026, 11, 10, 0, 0, 0, tzinfo=zone).timestamp()
    assert not date_admissible(before)
    assert date_admissible(first)
    assert not window_admissible(first)
    assert not window_admissible(datetime(2026, 11, 10, 0, 59, tzinfo=zone).timestamp())
    assert window_admissible(datetime(2026, 11, 10, 1, tzinfo=zone).timestamp())
    assert window_admissible(datetime(2026, 11, 10, 8, 59, tzinfo=zone).timestamp())
    assert not window_admissible(datetime(2026, 11, 10, 9, tzinfo=zone).timestamp())


def test_public_prepare_uses_night_window_before_suite(monkeypatch):
    from btc_risk_rl.pilots.protocol import ROOT

    spec = importlib.util.spec_from_file_location(
        "wf03_entry_test", ROOT / "scripts/run_oos_wf_cost_2022_03.py")
    assert spec is not None and spec.loader is not None
    entry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry)

    class ReachedBudget(Exception):
        pass

    def budget_attempt(*_args, **kwargs):
        assert kwargs["night_window"] is True
        raise ReachedBudget

    monkeypatch.setattr(entry, "require_campaign", lambda: {"authorized": True})
    monkeypatch.setattr(entry, "BudgetAttempt", budget_attempt)
    with pytest.raises(ReachedBudget):
        entry.prepare()


def test_2022_03_launch_headroom_preserves_four_gib_operational_guard(monkeypatch):
    from btc_risk_rl.pilots import wf_cost_2022_03_units as units
    from btc_risk_rl.pilots.wf_cost_2022_03_exec import (
        LAUNCH_MEMORY_MIN_BYTES,
        launch_memory_ready,
    )
    from btc_risk_rl.pilots.wf_cost_2022_03_orchestrator import PreflightBlocked

    assert LAUNCH_MEMORY_MIN_BYTES == 4 * 1024**3 + 512 * 1024**2 + 1_195_008_000
    assert not launch_memory_ready(LAUNCH_MEMORY_MIN_BYTES - 1)
    assert launch_memory_ready(LAUNCH_MEMORY_MIN_BYTES)
    monkeypatch.setattr(units, "check_service_context", lambda **_kw: None)
    monkeypatch.setattr(units, "inspect_host", lambda: {
        "power": {"ac": True, "battery_percent": 100},
        "memory_available_bytes": LAUNCH_MEMORY_MIN_BYTES - 1,
        "disk_free_bytes": 100 * 1024**3,
        "linger": "yes", "user_manager": "running",
    })
    with pytest.raises(PreflightBlocked, match="headroom"):
        units._preflight()
