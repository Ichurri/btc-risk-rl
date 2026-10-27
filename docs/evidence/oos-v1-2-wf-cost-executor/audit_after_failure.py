"""Audit the frozen Q0 evidence and pre-unit failure without mutating artifacts."""

import json

from btc_risk_rl.pilots.p2_budget import state_hash
from btc_risk_rl.pilots.p2r import P2RJournal
from btc_risk_rl.pilots.p2r_units import _verify_completion
from btc_risk_rl.pilots.wf_cost import CAMPAIGN, WFCostSettings, digest


def check() -> dict:
    ledger_path = CAMPAIGN / "ledger.jsonl"
    lines = [json.loads(line) for line in ledger_path.read_text().splitlines()]
    previous = None
    for row in lines:
        assert row["previous_hash"] == previous
        assert row["state_hash"] == state_hash(row)
        previous = row["state_hash"]
    state = lines[-1]
    assert state["status"] == "ready"
    assert len(state["units"]) == 1 and state["pending"] is None
    unit = state["units"][0]
    assert (unit["run_id"], unit["kind"]) == ("wf-2021", "q0")
    work = CAMPAIGN / "wf-2021"
    payload, boundary = _verify_completion(
        work, 0, WFCostSettings(seed=276696733), "C10", "wf-2021",
        unit["supervisor"], state["identity"]["code"]["2021"], diagnostic_n=64,
    )
    assert boundary == "after_q0"
    assert payload["checkpoint_sha256"] == unit["checkpoint_sha256"]
    assert digest(work / "checkpoint-0/state.pt") == unit["checkpoint_sha256"]
    assert digest(work / "unit-0.json") == unit["report_sha256"]
    assert not (work / "checkpoint-1").exists()
    assert not (work / "unit-1.json").exists()
    journal_path = CAMPAIGN / "supervisor.jsonl"
    P2RJournal(journal_path, campaign=CAMPAIGN.name)
    events = [json.loads(line) for line in journal_path.read_text().splitlines()]
    assert sum(row["event"] == "unit_completed" for row in events) == 1
    assert any(row["event"] == "paused" and row.get("reason") == "first_q0_audit"
               for row in events)
    assert events[-1]["event"] == "supervisor_started"
    return {
        "status": "q0_complete_second_service_failed_before_unit_1",
        "accepted_units": 1,
        "ledger_status": state["status"],
        "ledger_sha256": digest(ledger_path),
        "journal_sha256": digest(journal_path),
        "checkpoint_sha256": unit["checkpoint_sha256"],
        "report_sha256": unit["report_sha256"],
        "q0_wall_seconds": unit["seconds"],
        "q0_worker_rss_peak_bytes": unit["supervisor"]["rss_peak_bytes"],
        "invocation_ids": sorted({row["invocation_id"] for row in events}),
    }


if __name__ == "__main__":
    print(json.dumps(check(), indent=2, sort_keys=True))
