"""Only accepted complete OOS units enter progress figures."""

import pytest


def test_progress_counts_complete_runs_and_keeps_profiles_separate():
    from btc_risk_rl.reporting.oos_progress import summarize_state

    units = [dict(run_id="run-00-C0-b0", unit=i, seconds=60.0)
             for i in range(11)]
    units += [dict(run_id="run-01-C5-b0", unit=i, seconds=70.0)
              for i in range(4)]
    state = dict(status="running", cursor=1, units=units,
                 pending=dict(run_id="run-01-C5-b0", unit=4))
    summary = summarize_state("wf-2022", state, expected_runs=9)
    assert summary["completed_runs"] == 1
    assert summary["accepted_units"] == 15
    assert summary["completed_by_condition"] == {"C0": 1, "C5": 0, "C10": 0}
    assert summary["measured_unit_seconds"] == pytest.approx(11 * 60 + 4 * 70)
    assert summary["pending"] == "run-01-C5-b0/4"


def test_progress_rejects_missing_or_duplicate_unit_without_drawing_it():
    from btc_risk_rl.reporting.oos_progress import summarize_state

    state = dict(status="ready", cursor=0,
                 units=[dict(run_id="run-00-C0-b0", unit=0, seconds=1.0),
                        dict(run_id="run-00-C0-b0", unit=2, seconds=1.0)],
                 pending=None)
    with pytest.raises(ValueError, match="contiguous"):
        summarize_state("wf-2022", state, expected_runs=9)


def test_pending_q0_is_not_counted_as_accepted():
    from btc_risk_rl.reporting.oos_progress import summarize_state

    state = dict(status="running", cursor=0, units=[],
                 pending=dict(run_id="run-00-C0-b0", unit=0))
    summary = summarize_state("wf-2022", state, expected_runs=9)
    assert summary["accepted_units"] == 0
    assert summary["completed_runs"] == 0
    assert summary["pending"] == "run-00-C0-b0/0"


def test_read_verified_ledger_rejects_bad_chain_and_keeps_pending_separate(tmp_path):
    import json

    from btc_risk_rl.pilots.p2_budget import state_hash
    from btc_risk_rl.reporting.oos_progress import read_verified_ledger

    path = tmp_path / "ledger.jsonl"
    state = dict(status="running", cursor=0, units=[],
                 pending=dict(run_id="run-00-C0-b0", unit=0), previous_hash=None)
    state["state_hash"] = state_hash(state)
    path.write_text(json.dumps(state) + "\n")
    assert read_verified_ledger(path)["pending"]["unit"] == 0
    bad = dict(state, cursor=1)
    path.write_text(json.dumps(bad) + "\n")
    with pytest.raises(ValueError, match="chain"):
        read_verified_ledger(path)
