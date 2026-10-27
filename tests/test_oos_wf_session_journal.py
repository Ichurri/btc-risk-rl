"""Synthetic, deterministic accounting of WF supervisor sessions."""

import hashlib
import json
import time
from datetime import datetime

import pytest

from btc_risk_rl.pilots.budget import LA_PAZ
from btc_risk_rl.pilots.wf_cost import WFCostLedger
from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal


def _epoch(day, hour, minute):
    return datetime(2026, 10, day, hour, minute, tzinfo=LA_PAZ).timestamp()


def test_preledger_identity_failure_is_durable_and_reentry_is_rejected(tmp_path):
    path = tmp_path / "sessions.jsonl"
    with WFCostSessionJournal(path, campaign="synthetic") as journal:
        token = journal.start(now=1000, monotonic=500, invocation_id="first")
        with pytest.raises(ValueError, match="identity mismatch"):
            try:
                raise ValueError("identity mismatch before ledger")
            except ValueError:
                journal.end(token, now=1003, monotonic=503, status="failed",
                            reason="identity mismatch before ledger")
                raise
    with WFCostSessionJournal(path, campaign="synthetic") as reopened:
        assert reopened.charges({}, now=1004).extra_by_day == {
            "1969-12-31": pytest.approx(3)
        }
        with pytest.raises(ValueError, match="failed session"):
            reopened.start(now=1004, monotonic=510, invocation_id="second")


def test_admission_subtracts_ledger_overlap_without_double_charge(tmp_path):
    root = tmp_path / "synthetic"
    path = root / "sessions.jsonl"
    with WFCostSessionJournal(path, campaign="synthetic") as journal:
        token = journal.start(now=1000, monotonic=500, invocation_id="first")
        with WFCostLedger(root, identity={"fixture": True}, now=1010,
                          session_journal=journal, session_token=token) as ledger:
            ledger.preflight_done(1011)
            # 10 s before ledger + 10 s covered by its live interval = 20 s total.
            snapshot = journal.charges(ledger.state, now=1020, active_token=token)
            assert snapshot.extra_by_day == {ledger.day_key: pytest.approx(10)}
            assert ledger._seconds(1020) == pytest.approx((20, 20))
            assert ledger.admit_unit("2021", 0, 1020) == "start"
        journal.end(token, now=1021, monotonic=521, status="ready")
    with WFCostSessionJournal(path, campaign="synthetic") as journal:
        token = journal.start(now=1030, monotonic=530, invocation_id="second")
        with WFCostLedger(root, identity={"fixture": True}, now=1032,
                          session_journal=journal, session_token=token) as ledger:
            ledger.preflight_done(1033)
            # Ledger day began at 1010: the second session lies within its span.
            assert journal.charges(ledger.state, now=1040, active_token=token).extra_by_day == {
                ledger.day_key: pytest.approx(10)
            }
            assert ledger._seconds(1040) == pytest.approx((40, 40))
        journal.end(token, now=1041, monotonic=541, status="ready")


def test_unclosed_session_charges_full_days_and_blocks_new_session(tmp_path):
    path = tmp_path / "sessions.jsonl"
    start = _epoch(26, 23, 50)
    next_day = _epoch(27, 0, 10)
    with WFCostSessionJournal(path, campaign="synthetic") as journal:
        journal.start(now=start, monotonic=100, invocation_id="lost")
    with WFCostSessionJournal(path, campaign="synthetic") as journal:
        snapshot = journal.charges({}, now=next_day)
        assert snapshot.blocked
        assert snapshot.extra_by_day == {"2026-10-26": 10800, "2026-10-27": 10800}
        with pytest.raises(ValueError, match="unclosed session"):
            journal.start(now=next_day, monotonic=1300, invocation_id="new")


def test_midnight_split_and_overlap_uses_lapaz_days(tmp_path):
    path = tmp_path / "sessions.jsonl"
    start = _epoch(26, 23, 50)
    end = _epoch(27, 0, 10)
    with WFCostSessionJournal(path, campaign="synthetic") as journal:
        token = journal.start(now=start, monotonic=100, invocation_id="cross")
        journal.end(token, now=end, monotonic=1300, status="ready")
        state = {"days": {
            "2026-10-26": {"started_utc_epoch": start + 300, "charged_wall_seconds": 300},
            "2026-10-27": {"started_utc_epoch": end - 600, "charged_wall_seconds": 300},
        }}
        assert journal.charges(state, now=end).extra_by_day == {
            "2026-10-26": pytest.approx(300), "2026-10-27": pytest.approx(300)
        }
        assert journal.charges({}, now=end).extra_by_day == {
            "2026-10-26": pytest.approx(600), "2026-10-27": pytest.approx(600)
        }


def test_preledger_midnight_counts_as_two_active_days_for_admission(tmp_path):
    root = tmp_path / "synthetic"
    start = _epoch(26, 23, 50)
    after_midnight = _epoch(27, 0, 10)
    with WFCostSessionJournal(root / "sessions.jsonl", campaign="synthetic") as journal:
        token = journal.start(now=start, monotonic=100, invocation_id="first")
        with WFCostLedger(root, identity={"fixture": True}, now=after_midnight - 10,
                          session_journal=journal, session_token=token) as ledger:
            ledger.preflight_done(after_midnight - 9)
            assert ledger._seconds(after_midnight) == pytest.approx((600, 1200))
            assert ledger.admit_unit("2021", 0, after_midnight) == "start"
        journal.end(token, now=after_midnight + 1, monotonic=1301, status="ready")
    third_day = _epoch(28, 0, 10)
    with WFCostSessionJournal(root / "sessions.jsonl", campaign="synthetic") as journal:
        token = journal.start(now=third_day, monotonic=2000, invocation_id="second")
        with WFCostLedger(root, identity={"fixture": True}, now=third_day,
                          session_journal=journal, session_token=token) as ledger:
            ledger.preflight_done(third_day + 1)
            assert ledger.admit_unit("2021", 0, third_day + 2) == "incomplete"
        journal.end(token, now=third_day + 3, monotonic=2003, status="ready")


def test_preledger_time_can_block_admission_and_active_day_limit(tmp_path):
    root = tmp_path / "synthetic"
    now = _epoch(27, 1, 10)
    with WFCostSessionJournal(root / "sessions.jsonl", campaign="synthetic") as journal:
        token = journal.start(now=now - 3500, monotonic=100, invocation_id="slow-load")
        with WFCostLedger(root, identity={"fixture": True}, now=now - 20,
                          session_journal=journal, session_token=token) as ledger:
            ledger.preflight_done(now - 19)
            assert ledger.admit_unit("2021", 0, now) == "pause"
        journal.end(token, now=now + 1, monotonic=3601, status="ready")


def test_preledger_time_consumes_global_reserve_at_admission(tmp_path):
    root = tmp_path / "synthetic"
    with WFCostSessionJournal(root / "sessions.jsonl", campaign="synthetic") as journal:
        token = journal.start(now=1000, monotonic=100, invocation_id="load")
        with WFCostLedger(root, identity={"fixture": True}, now=2000,
                          external_seconds=7000, session_journal=journal,
                          session_token=token) as ledger:
            ledger.preflight_done(2001)
            assert ledger._seconds(2010) == pytest.approx((1010, 1010))
            assert ledger.admit_unit("2021", 0, 2010) == "pause"
        journal.end(token, now=2011, monotonic=1111, status="ready")


def test_supervisor_records_source_identity_failure_before_ledger(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_units

    root = tmp_path / "future-study"
    monkeypatch.setattr(wf_cost_units, "CAMPAIGN", root)
    monkeypatch.setattr(wf_cost_units, "require_campaign", lambda: {"synthetic": True})
    monkeypatch.setattr(wf_cost_units, "_launch_readiness",
                        lambda: ({"sha256": {}}, {"global_spent": 0}))

    class SyntheticSharedBudget:
        external_seconds = 0

        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

    monkeypatch.setattr(wf_cost_units, "P2RSharedBudget", SyntheticSharedBudget)

    def fail_before_ledger(_fold):
        assert (root / "sessions.jsonl").exists()
        raise ValueError("synthetic source identity mismatch")

    monkeypatch.setattr(wf_cost_units, "build_fold_source", fail_before_ledger)
    with pytest.raises(ValueError, match="source identity mismatch"):
        wf_cost_units.run_units()
    assert not (root / "ledger.jsonl").exists()
    with WFCostSessionJournal(root / "sessions.jsonl", campaign=root.name) as journal:
        assert len(journal.sessions) == 1
        assert journal.sessions[0]["end"]["status"] == "failed"
        assert journal.sessions[0]["end"]["reason"] == "synthetic source identity mismatch"
        with pytest.raises(ValueError, match="failed session"):
            journal.start(now=journal.sessions[0]["end"]["epoch"] + 1,
                          monotonic=journal.sessions[0]["end"]["monotonic"] + 1,
                          invocation_id="not-a-retry")


def test_supervisor_records_preflight_failure_after_gate_before_ledger(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_units

    root = tmp_path / "future-study"

    class SyntheticSharedBudget:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

    monkeypatch.setattr(wf_cost_units, "CAMPAIGN", root)
    monkeypatch.setattr(wf_cost_units, "require_campaign", lambda: {"synthetic": True})
    monkeypatch.setattr(wf_cost_units, "P2RSharedBudget", SyntheticSharedBudget)
    monkeypatch.setattr(wf_cost_units, "_launch_readiness",
                        lambda: (_ for _ in ()).throw(ValueError("synthetic preflight failure")))
    with pytest.raises(ValueError, match="synthetic preflight failure"):
        wf_cost_units.run_units()
    assert not (root / "ledger.jsonl").exists()
    with WFCostSessionJournal(root / "sessions.jsonl", campaign=root.name) as journal:
        assert journal.sessions[0]["end"]["status"] == "failed"
        assert journal.sessions[0]["end"]["reason"] == "synthetic preflight failure"


def test_observed_ledger_identity_mismatch_is_charged_and_not_retryable(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_units

    root = tmp_path / "synthetic-identity"
    with WFCostLedger(root, identity={"old_fixture": True}, now=time.time() - 60):
        pass

    class SyntheticSource:
        def identity(self):
            return {"synthetic": True}

    class SyntheticSharedBudget:
        external_seconds = 0

        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

    monkeypatch.setattr(wf_cost_units, "CAMPAIGN", root)
    monkeypatch.setattr(wf_cost_units, "require_campaign", lambda: {"synthetic": True})
    monkeypatch.setattr(wf_cost_units, "_launch_readiness",
                        lambda: ({"sha256": {}}, {"global_spent": 0}))
    monkeypatch.setattr(wf_cost_units, "P2RSharedBudget", SyntheticSharedBudget)
    monkeypatch.setattr(wf_cost_units, "build_fold_source", lambda _fold: SyntheticSource())
    monkeypatch.setattr(wf_cost_units, "provenance", lambda _source: {"synthetic": True})
    monkeypatch.setattr(wf_cost_units, "digest", lambda _path: "synthetic-hash")
    monkeypatch.setattr(wf_cost_units, "_record_fold_manifests", lambda _sources: None)
    monkeypatch.setattr(wf_cost_units, "inspect_host", lambda: {"synthetic": True})
    ledger_path = root / "ledger.jsonl"
    before = ledger_path.read_bytes()
    with pytest.raises(ValueError, match="Campaign identity mismatch"):
        wf_cost_units.run_units()
    assert ledger_path.read_bytes() == before
    with WFCostSessionJournal(root / "sessions.jsonl", campaign=root.name) as journal:
        assert journal.sessions[0]["end"]["status"] == "failed"
        assert "Campaign identity mismatch" in journal.sessions[0]["end"]["reason"]
        assert journal.charges({}, now=time.time()).blocked


def test_shared_budget_charges_preledger_failed_wf_session_without_ledger(tmp_path):
    from btc_risk_rl.pilots.p2r import P2RSharedBudget

    root = tmp_path / "oos-v12-wf-cost-only-synthetic"
    now = _epoch(27, 10, 0)
    with WFCostSessionJournal(root / "sessions.jsonl", campaign=root.name) as journal:
        token = journal.start(now=now - 5, monotonic=100, invocation_id="failed")
        journal.end(token, now=now - 2, monotonic=103, status="failed",
                    reason="synthetic identity mismatch")
    assert not (root / "ledger.jsonl").exists()
    with P2RSharedBudget(tmp_path, "other-synthetic", now=now,
                         synthetic_fixture=True) as shared:
        assert shared.external_seconds == 10800
        assert any(row["path"] == str(root / "sessions.jsonl") for row in shared.sources)


def test_wf_read_only_budget_preflight_sees_failed_preledger_session(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost

    root = tmp_path / "artifacts/oos-v12-wf-cost-only-synthetic"
    now = _epoch(27, 10, 0)
    with WFCostSessionJournal(root / "sessions.jsonl", campaign=root.name) as journal:
        token = journal.start(now=now - 5, monotonic=100, invocation_id="failed")
        journal.end(token, now=now - 2, monotonic=103, status="failed",
                    reason="synthetic identity mismatch")
    monkeypatch.setattr(wf_cost, "ROOT", tmp_path)
    budget = wf_cost.inspect_budget(now=now)
    assert budget["global_spent"] == 10800
    assert budget["remaining_before_reserve"] == 0
    assert any(row["path"] == str(root / "sessions.jsonl") for row in budget["sources"])


def test_wf_budget_preflight_does_not_create_session_lock(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost

    root = tmp_path / "artifacts/oos-v12-wf-cost-only-synthetic"
    now = _epoch(27, 10, 0)
    with WFCostSessionJournal(root / "sessions.jsonl", campaign=root.name) as journal:
        token = journal.start(now=now - 5, monotonic=100, invocation_id="closed")
        journal.end(token, now=now - 2, monotonic=103, status="ready")
    lock = root / "sessions.lock"
    lock.unlink()
    before = (root / "sessions.jsonl").read_bytes()
    monkeypatch.setattr(wf_cost, "ROOT", tmp_path)
    wf_cost.inspect_budget(now=now)
    assert not lock.exists()
    assert (root / "sessions.jsonl").read_bytes() == before


def test_shared_budget_unions_closed_session_with_ledger_interval(tmp_path):
    from btc_risk_rl.pilots.p2r import P2RSharedBudget

    root = tmp_path / "oos-v12-wf-cost-only-synthetic"
    start = _epoch(27, 10, 0)
    with WFCostSessionJournal(root / "sessions.jsonl", campaign=root.name) as journal:
        token = journal.start(now=start, monotonic=100, invocation_id="closed")
        journal.end(token, now=start + 20, monotonic=120, status="ready")
    with WFCostLedger(root, identity={"fixture": True}, now=start + 5) as ledger:
        ledger.day["charged_wall_seconds"] = 10
        ledger.persist(start + 15)
    with P2RSharedBudget(tmp_path, "other-synthetic", now=start + 30,
                         synthetic_fixture=True) as shared:
        assert shared.external_seconds == pytest.approx(20)
        assert {row["reason"] for row in shared.sources} == {"measured", "session_gap"}


def test_shared_budget_debits_each_touched_day_of_unclosed_session(tmp_path):
    from btc_risk_rl.pilots.p2r import P2RSharedBudget

    root = tmp_path / "oos-v12-wf-cost-only-synthetic"
    with WFCostSessionJournal(root / "sessions.jsonl", campaign=root.name) as journal:
        journal.start(now=_epoch(26, 23, 50), monotonic=100,
                      invocation_id="synthetic-crash")
    for now in (_epoch(26, 23, 55), _epoch(27, 0, 10)):
        with P2RSharedBudget(tmp_path, "other-synthetic", now=now,
                             synthetic_fixture=True) as shared:
            assert shared.external_seconds == 10800
            assert shared.sources[0]["reason"] == "failed_or_unclosed_session"


def test_zero_duration_failed_session_still_consumes_its_day(tmp_path):
    from btc_risk_rl.pilots.p2r import P2RSharedBudget

    root = tmp_path / "oos-v12-wf-cost-only-synthetic"
    now = _epoch(27, 10, 0)
    with WFCostSessionJournal(root / "sessions.jsonl", campaign=root.name) as journal:
        token = journal.start(now=now, monotonic=100, invocation_id="instant-failure")
        journal.end(token, now=now, monotonic=100, status="failed",
                    reason="synthetic preledger failure")
    with P2RSharedBudget(tmp_path, "other-synthetic", now=now + 1,
                         synthetic_fixture=True) as shared:
        assert shared.external_seconds == 10800


def test_full_day_ledger_fallback_is_not_augmented_by_session_gap(tmp_path):
    from btc_risk_rl.pilots.p2r import P2RSharedBudget

    root = tmp_path / "oos-v12-wf-cost-only-synthetic"
    now = _epoch(27, 10, 0)
    with WFCostSessionJournal(root / "sessions.jsonl", campaign=root.name) as journal:
        token = journal.start(now=now, monotonic=100, invocation_id="closed")
        journal.end(token, now=now + 10, monotonic=110, status="ready")
    with WFCostLedger(root, identity={"fixture": True}, now=now + 5):
        pass  # No charged_wall_seconds: legacy conservative full-day debit.
    with P2RSharedBudget(tmp_path, "other-synthetic", now=now + 20,
                         synthetic_fixture=True) as shared:
        assert shared.external_seconds == 10800


def test_self_consistent_but_invalid_session_record_is_rejected(tmp_path):
    path = tmp_path / "sessions.jsonl"
    with WFCostSessionJournal(path, campaign="synthetic") as journal:
        journal.start(now=1000, monotonic=500, invocation_id="synthetic")
    row = json.loads(path.read_text())
    row["schema_version"] = "unknown"
    row.pop("sha256")
    row["sha256"] = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
    path.write_text(json.dumps(row) + "\n")
    with pytest.raises(ValueError, match="schema"):
        WFCostSessionJournal(path, campaign="synthetic")
