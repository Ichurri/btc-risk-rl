"""Synthetic checks for a metered, unapproved 2022-only WF cost campaign."""

import json
import subprocess
import sys
from datetime import datetime

import pytest

from btc_risk_rl.pilots import wf_cost_2022_orchestrator as wf22
from btc_risk_rl.pilots.budget import LA_PAZ
from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal


class Clock:
    def __init__(self, epoch):
        self.epoch = epoch
        self.mono = 100.0

    def now(self):
        return self.epoch

    def monotonic(self):
        return self.mono

    def advance(self, seconds):
        self.epoch += seconds
        self.mono += seconds


def epoch(day, hour, minute):
    return datetime(2026, 11, day, hour, minute, tzinfo=LA_PAZ).timestamp()


def test_first_check_is_inside_durable_attempt_and_charged_before_ledger(tmp_path):
    clock = Clock(epoch(4, 10, 0))
    with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                            authorize=lambda: True,
                            external_spent=lambda _now: 0) as attempt:
        def suite():
            assert attempt.journal_path.is_file()
            start = json.loads(attempt.journal_path.read_text().splitlines()[0])
            assert start["event"] == "start"
            assert not (tmp_path / wf22.CAMPAIGN_NAME).exists()
            clock.advance(390)

        attempt.run_check("suite", suite)
        snapshot = attempt.snapshot({})
        assert snapshot.own_by_day == {"2026-11-04": pytest.approx(390)}
        assert attempt.admit({}, unit=0) == "start"
    with WFCostSessionJournal(attempt.journal_path, campaign=wf22.CAMPAIGN_NAME,
                              read_only=True) as journal:
        assert journal.sessions[0]["end"]["status"] == "ready"
    checks = [json.loads(row) for row in attempt.checks_path.read_text().splitlines()]
    assert [row["event"] for row in checks] == ["check_start", "check_end"]
    assert [row["name"] for row in checks] == ["suite", "suite"]
    assert checks[-1]["elapsed_seconds"] == pytest.approx(390)


def test_full_approval_check_is_metered_after_lightweight_code_gate(tmp_path):
    clock = Clock(epoch(4, 10, 0))

    def check_approval():
        path = tmp_path / "shared-pilot-budget" / wf22.JOURNAL_NAME
        assert json.loads(path.read_text().splitlines()[0])["event"] == "start"
        clock.advance(25)

    with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                            authorize=check_approval,
                            external_spent=lambda _now: 0) as attempt:
        assert attempt.snapshot({}).own_by_day["2026-11-04"] == pytest.approx(25)


def test_attempt_session_ledger_union_does_not_duplicate_overlap(tmp_path):
    clock = Clock(epoch(4, 10, 0))
    with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                            authorize=lambda: True,
                            external_spent=lambda _now: 0) as attempt:
        clock.advance(300)
        sessions_path = tmp_path / wf22.CAMPAIGN_NAME / "sessions.jsonl"
        with WFCostSessionJournal(sessions_path, campaign=wf22.CAMPAIGN_NAME) as sessions:
            token = sessions.start(now=clock.now(), monotonic=clock.monotonic(),
                                   invocation_id="synthetic-service")
            clock.advance(100)
            ledger = {"days": {"2026-11-04": {
                "started_utc_epoch": clock.now(), "charged_wall_seconds": 150,
            }}, "status": "ready", "pending": None}
            clock.advance(100)
            sessions.end(token, now=clock.now(), monotonic=clock.monotonic(), status="ready")
            clock.advance(100)
            assert attempt.snapshot(ledger, sessions=sessions).own_by_day == {
                "2026-11-04": pytest.approx(600)
            }


def test_midnight_counts_both_days_and_third_day_is_incomplete(tmp_path):
    clock = Clock(epoch(4, 23, 59))
    with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                            authorize=lambda: True,
                            external_spent=lambda _now: 0) as attempt:
        clock.advance(120)
        snap = attempt.snapshot({})
        assert snap.own_by_day == {"2026-11-04": pytest.approx(60),
                                   "2026-11-05": pytest.approx(60)}
        assert attempt.admit({}, unit=0) == "start"
    clock.advance(86400)
    with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                            authorize=lambda: True,
                            external_spent=lambda _now: 0) as attempt:
        assert attempt.admit({}, unit=0) == "incomplete"


def test_unclosed_attempt_blocks_restart_and_charges_full_days(tmp_path):
    clock = Clock(epoch(4, 23, 59))
    path = tmp_path / "shared-pilot-budget" / wf22.JOURNAL_NAME
    with WFCostSessionJournal(path, campaign=wf22.CAMPAIGN_NAME) as journal:
        journal.start(now=clock.now(), monotonic=clock.monotonic(),
                      invocation_id="interrupted")
    clock.advance(120)
    with WFCostSessionJournal(path, campaign=wf22.CAMPAIGN_NAME,
                              read_only=True) as journal:
        snap = wf22.reconcile(journal, None, {}, now=clock.now())
        assert snap.blocked
        assert snap.own_by_day == {"2026-11-04": 10800, "2026-11-05": 10800}
    with pytest.raises(ValueError, match="unclosed"):
        with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                                authorize=lambda: True,
                                external_spent=lambda _now: 0):
            pass


def test_preledger_failure_is_durable_and_not_restarted(tmp_path):
    clock = Clock(epoch(4, 10, 0))
    with pytest.raises(ValueError, match="synthetic integrity failure"):
        with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                                authorize=lambda: True,
                                external_spent=lambda _now: 0) as attempt:
            attempt.run_check("preflight", lambda: (_ for _ in ()).throw(
                ValueError("synthetic integrity failure")))
    with WFCostSessionJournal(attempt.journal_path, campaign=wf22.CAMPAIGN_NAME,
                              read_only=True) as journal:
        assert journal.sessions[0]["end"]["status"] == "failed"
    with pytest.raises(ValueError, match="failed"):
        with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                                authorize=lambda: True,
                                external_spent=lambda _now: 0):
            pass


def test_blocked_preflight_consumes_day_but_allows_new_attempt(tmp_path):
    clock = Clock(epoch(4, 10, 0))
    with pytest.raises(wf22.PreflightBlocked, match="memory"):
        with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                                authorize=lambda: True,
                                external_spent=lambda _now: 0) as attempt:
            def blocked():
                clock.advance(390)
                raise wf22.PreflightBlocked("memory below 4 GiB")

            attempt.run_check("preflight", blocked)
    with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                            authorize=lambda: True,
                            external_spent=lambda _now: 0) as resumed:
        assert resumed.snapshot({}).own_by_day["2026-11-04"] == pytest.approx(390)


def test_checks_and_reserves_can_pause_before_unit(tmp_path):
    clock = Clock(epoch(4, 10, 0))
    called = []
    with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                            authorize=lambda: True,
                            external_spent=lambda _now: 0) as attempt:
        attempt.run_check("suite", lambda: clock.advance(2890))
        assert attempt.admit({}, unit=0) == "pause"  # 2890 + 120 + 600 > 3600
        assert attempt.run_unit({}, unit=0, operation=lambda: called.append(0)) == "pause"
        assert called == []
    clock.advance(10)
    with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                            authorize=lambda: True,
                            external_spent=lambda _now: 7000) as attempt:
        assert attempt.admit({}, unit=0) == "pause"  # global reserve


def test_night_window_never_starts_a_unit_that_cannot_close_by_nine(tmp_path):
    clock = Clock(epoch(4, 0, 59))
    with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                            authorize=lambda: True, external_spent=lambda _now: 0,
                            night_window=True) as attempt:
        assert attempt.admit({}, unit=0) == "pause"
        clock.advance(60)
        assert attempt.admit({}, unit=0) == "start"
    late = Clock(epoch(5, 8, 47))
    with wf22.BudgetAttempt(tmp_path / "late", clock=late, gate=lambda: True,
                            authorize=lambda: True, external_spent=lambda _now: 0,
                            night_window=True) as attempt:
        assert attempt.admit({}, unit=0) == "start"  # 13 minutes cover Q0 and closure.
        late.advance(120)
        assert attempt.admit({}, unit=0) == "pause"
    outside = Clock(epoch(5, 23, 0))
    with wf22.BudgetAttempt(tmp_path / "outside", clock=outside, gate=lambda: True,
                            authorize=lambda: True, external_spent=lambda _now: 0,
                            night_window=True) as attempt:
        assert attempt.admit({}, unit=0) == "pause"


def test_unit_over_cap_fails_attempt_without_accepting_a_partial(tmp_path):
    clock = Clock(epoch(4, 10, 0))
    with pytest.raises(ValueError, match="unit cap exceeded"):
        with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                                authorize=lambda: True,
                                external_spent=lambda _now: 0) as attempt:
            attempt.run_unit({}, unit=0, operation=lambda: clock.advance(121))
    with WFCostSessionJournal(attempt.journal_path, campaign=wf22.CAMPAIGN_NAME,
                              read_only=True) as journal:
        assert journal.sessions[0]["end"]["status"] == "failed"
    assert not (tmp_path / wf22.CAMPAIGN_NAME / "ledger.jsonl").exists()


def test_resource_guard_failure_inside_unit_is_permanent(tmp_path):
    clock = Clock(epoch(4, 10, 0))
    with pytest.raises(ValueError, match="during unit"):
        with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                                authorize=lambda: True,
                                external_spent=lambda _now: 0) as attempt:
            attempt.run_unit({}, unit=0, operation=lambda: (_ for _ in ()).throw(
                wf22.PreflightBlocked("lost memory")))
    with WFCostSessionJournal(attempt.journal_path, campaign=wf22.CAMPAIGN_NAME,
                              read_only=True) as journal:
        assert journal.sessions[0]["end"]["status"] == "failed"


def test_cumulative_reserve_blocks_unit_even_when_day_is_fresh(tmp_path):
    clock = Clock(epoch(4, 10, 0))
    with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                            authorize=lambda: True,
                            external_spent=lambda _now: 0) as attempt:
        clock.advance(2900)
    clock.advance(86400 - 2900)
    with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                            authorize=lambda: True,
                            external_spent=lambda _now: 0) as attempt:
        clock.advance(1210)
        assert attempt.admit({}, unit=0) == "incomplete"


def test_closed_public_entry_creates_no_journal_or_campaign(tmp_path, monkeypatch):
    clock = Clock(epoch(4, 10, 0))
    monkeypatch.setattr(wf22, "MARKET_EXECUTION_ENABLED", False)
    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        with wf22.BudgetAttempt(tmp_path, clock=clock,
                                authorize=wf22.require_campaign,
                                external_spent=lambda _now: 0):
            pass
    assert not (tmp_path / "shared-pilot-budget" / wf22.JOURNAL_NAME).exists()
    assert not (tmp_path / wf22.CAMPAIGN_NAME).exists()
    script = ("import runpy, sys; "
              "from btc_risk_rl.pilots import wf_cost_2022_exec as profile; "
              "profile.MARKET_EXECUTION_ENABLED=False; "
              "sys.argv=['scripts/run_oos_wf_cost_2022.py','--run']; "
              "runpy.run_path('scripts/run_oos_wf_cost_2022.py',run_name='__main__')")
    result = subprocess.run([sys.executable, "-c", script],
                            capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "NOT AUTHORIZED" in result.stderr
    assert not wf22.CAMPAIGN.exists()


def test_shared_budget_sees_precheck_journal_without_ledger(tmp_path):
    from btc_risk_rl.pilots import wf_cost
    from btc_risk_rl.pilots.p2r import P2RSharedBudget

    clock = Clock(epoch(4, 10, 0))
    with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                            authorize=lambda: True,
                            external_spent=lambda _now: 0):
        clock.advance(400)
    with P2RSharedBudget(tmp_path, "other-campaign", now=clock.now(),
                         synthetic_fixture=True) as shared:
        assert shared.external_seconds == pytest.approx(400)
    assert wf22.shared_attempt_debit(tmp_path, now=clock.now(), day="2026-11-04") == 400
    assert wf_cost.MARKET_EXECUTION_ENABLED is False


def test_failed_2022_01_attempt_remains_a_global_debit_for_2022_02(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost
    from btc_risk_rl.pilots.p2r import P2RSharedBudget

    artifacts = tmp_path / "artifacts"
    audit = artifacts / "shared-pilot-budget"
    audit.mkdir(parents=True)
    clock = Clock(epoch(7, 1, 0))
    old_campaign = "oos-v12-wf-cost-only-2022-01"
    old_journal = audit / "wf-2022-only-01-attempts.jsonl"
    with WFCostSessionJournal(old_journal, campaign=old_campaign) as journal:
        token = journal.start(now=clock.now(), monotonic=clock.monotonic(),
                              invocation_id="old-synthetic")
        clock.advance(441)
        journal.end(token, now=clock.now(), monotonic=clock.monotonic(),
                    status="failed", reason="suite failed")

    monkeypatch.setattr(wf_cost, "ROOT", tmp_path)
    result = wf_cost.inspect_budget(now=clock.now(),
                                    campaign=artifacts / wf22.CAMPAIGN_NAME)
    assert result["global_spent"] == 10800
    assert result["remaining_before_reserve"] == 0
    assert any(row["path"] == str(old_journal)
               and row["charged_today_seconds"] == 10800
               for row in result["sources"])
    with P2RSharedBudget(artifacts, wf22.CAMPAIGN_NAME, now=clock.now(),
                         synthetic_fixture=True) as shared:
        assert shared.external_seconds == 10800
    clock.advance(86400)
    assert wf_cost.inspect_budget(now=clock.now(),
                                  campaign=artifacts / wf22.CAMPAIGN_NAME)["global_spent"] == 0


def test_read_only_wf_budget_scanner_sees_precheck_without_ledger(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost

    artifacts = tmp_path / "artifacts"
    clock = Clock(epoch(4, 10, 0))
    with wf22.BudgetAttempt(artifacts, clock=clock, gate=lambda: True,
                            authorize=lambda: True,
                            external_spent=lambda _now: 0):
        clock.advance(250)
    monkeypatch.setattr(wf_cost, "ROOT", tmp_path)
    result = wf_cost.inspect_budget(now=clock.now(), campaign=artifacts / "another")
    assert result["global_spent"] == pytest.approx(250)
    assert any(source["reason"] == "precheck_attempt" for source in result["sources"])


def test_fake_registration_cannot_enable_campaign(tmp_path, monkeypatch):
    fake = tmp_path / "approval.json"
    fake.write_text(json.dumps({"active": True, "campaign": wf22.CAMPAIGN_NAME}))
    monkeypatch.setattr(wf22, "MARKET_EXECUTION_ENABLED", True)
    monkeypatch.setattr(wf22, "APPROVAL", fake)
    monkeypatch.setattr(wf22, "REGISTRATION_SHA256", "0" * 64)
    with pytest.raises(PermissionError, match="hash mismatch"):
        wf22.require_campaign()


def test_attempt_cannot_run_check_after_context_closed(tmp_path):
    clock = Clock(epoch(4, 10, 0))
    with wf22.BudgetAttempt(tmp_path, clock=clock, gate=lambda: True,
                            authorize=lambda: True,
                            external_spent=lambda _now: 0) as attempt:
        pass
    with pytest.raises(ValueError, match="active metered attempt"):
        attempt.run_check("late-suite", lambda: clock.advance(20))


def test_shared_budget_counts_attempt_service_and_ledger_once(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost
    from btc_risk_rl.pilots.p2r import P2RSharedBudget

    artifacts = tmp_path / "artifacts"
    clock = Clock(epoch(4, 10, 0))
    with wf22.BudgetAttempt(artifacts, clock=clock, gate=lambda: True,
                            authorize=lambda: True,
                            external_spent=lambda _now: 0):
        clock.advance(300)
        root = artifacts / wf22.CAMPAIGN_NAME
        with WFCostSessionJournal(root / "sessions.jsonl", campaign=root.name) as session:
            token = session.start(now=clock.now(), monotonic=clock.monotonic(),
                                  invocation_id="synthetic")
            clock.advance(100)
            ledger = {"status": "ready", "pending": None,
                      "days": {"2026-11-04": {
                          "started_utc_epoch": clock.now(),
                          "charged_wall_seconds": 100,
                      }}}
            (root / "ledger.jsonl").write_text(json.dumps(ledger) + "\n")
            clock.advance(100)
            session.end(token, now=clock.now(), monotonic=clock.monotonic(),
                        status="ready")
        clock.advance(100)
    with P2RSharedBudget(artifacts, "other-campaign", now=clock.now(),
                         synthetic_fixture=True) as shared:
        assert shared.external_seconds == pytest.approx(600)
        assert [source["seconds"] for source in shared.sources] == pytest.approx(
            [100, 100, 400]
        )
    monkeypatch.setattr(wf_cost, "ROOT", tmp_path)
    assert wf_cost.inspect_budget(now=clock.now(),
                                  campaign=artifacts / "other")["global_spent"] == 600
