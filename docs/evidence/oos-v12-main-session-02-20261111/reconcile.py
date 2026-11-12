"""Explain the day-11 conservative debit from frozen session evidence."""

import hashlib
import json
import math
from pathlib import Path

from btc_risk_rl.pilots.oos_v12_budget import PREP_CAMPAIGN, amended_budget
from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).parent
JOURNAL_SHA256 = "c73253ca368652ca240a91956f38ae3b18c4b327fc7d334b3ab59c8e56d6ca6d"


def main():
    path = EVIDENCE / "preflight-journal-snapshot.jsonl"
    if hashlib.sha256(path.read_bytes()).hexdigest() != JOURNAL_SHA256:
        raise ValueError("Frozen session journal hash differs")
    with WFCostSessionJournal(path, campaign=PREP_CAMPAIGN, read_only=True) as journal:
        sessions = journal.sessions
    if len(sessions) != 5 or any(item["end"] is None for item in sessions):
        raise ValueError("Expected five closed day-11 sessions")
    intervals = [(row["start"]["epoch"], row["end"]["epoch"])
                 for row in sessions]
    if any(left[1] > right[0] for left, right in zip(intervals, intervals[1:])):
        raise ValueError("Session intervals overlap")
    measured = sum(end - start for start, end in intervals)
    extra = amended_budget()["prior_day"]["conservative_extra_debit_seconds"]
    budget = json.loads((EVIDENCE / "budget.json").read_text())
    if (budget["day_la_paz"] != "2026-11-11"
            or budget["ledger_sha256"]
            != "1245b4299103401bbc066f9044278ffeabd55606687ac3ddab0bfb5c712c5749"
            or not math.isclose(budget["global_spent_seconds"], 47008.73810338974,
                                abs_tol=1e-6)):
        raise ValueError("Frozen budget snapshot differs")
    gap = intervals[4][0] - intervals[3][1]
    overcharge = budget["global_spent_seconds"] - measured - extra
    if not math.isclose(overcharge, gap, abs_tol=1e-5):
        raise ValueError("Conservative debit cannot be explained by idle gap")
    print(json.dumps({
        "session_journal_sha256": JOURNAL_SHA256,
        "session_count": len(sessions),
        "session_wall_seconds": [round(end - start, 6) for start, end in intervals],
        "measured_session_union_seconds": round(measured, 6),
        "prior_conservative_extra_seconds": round(extra, 6),
        "no_idle_gap_reference_seconds": round(measured + extra, 6),
        "protocol_charged_seconds": round(budget["global_spent_seconds"], 6),
        "idle_gap_seconds": round(gap, 6),
        "additional_conservative_debit_seconds": round(overcharge, 6),
        "interpretation": "idle gap charged by cumulative same-day ledger span; not compute time",
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
