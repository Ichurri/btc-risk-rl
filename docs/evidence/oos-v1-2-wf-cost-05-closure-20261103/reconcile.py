"""Read-only integrity and budget reconciliation for the closed WF05 study."""

import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

from btc_risk_rl.pilots.p2_budget import state_hash
from btc_risk_rl.pilots.wf_cost_replacement_05_exec import (
    CAMPAIGN,
    MARKET_EXECUTION_ENABLED,
    REGISTRATION,
    REGISTRATION_SHA256,
)
from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "docs/evidence"
PREVIOUS = EVIDENCE / "oos-v1-2-wf-cost-05-session-02-20261101/audit.json"
Q0 = EVIDENCE / "oos-v1-2-wf-cost-05-q0-20261101"
BLOCKED_01 = EVIDENCE / "oos-v1-2-wf-cost-05-reentry-blocked-20261101"
SESSION_02 = EVIDENCE / "oos-v1-2-wf-cost-05-session-02-20261101"
BLOCKED_02 = EVIDENCE / "oos-v1-2-wf-cost-05-reentry-blocked-20261102"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pytest_seconds(path):
    matches = re.findall(r"463 passed in ([0-9.]+)s", Path(path).read_text())
    assert len(matches) == 1
    return float(matches[0])


def git_time(commit):
    return datetime.fromisoformat(subprocess.check_output(
        ["git", "show", "-s", "--format=%aI", commit], cwd=ROOT, text=True,
    ).strip())


def main():
    prior = json.loads(PREVIOUS.read_text())
    rows = [json.loads(line) for line in (CAMPAIGN / "ledger.jsonl").read_text().splitlines()]
    previous_hash = None
    for row in rows:
        assert row["previous_hash"] == previous_hash
        assert row["state_hash"] == state_hash(row)
        previous_hash = row["state_hash"]
    state = rows[-1]
    assert state["status"] == "ready" and state["pending"] is None
    assert len(state["units"]) == prior["accepted_units"] == 11
    assert sha(CAMPAIGN / "ledger.jsonl") == prior["ledger_sha256"]
    assert MARKET_EXECUTION_ENABLED is False
    assert sha(REGISTRATION) == REGISTRATION_SHA256
    files = {str(path.relative_to(CAMPAIGN)): sha(path)
             for path in sorted(CAMPAIGN.rglob("*")) if path.is_file()}
    mapping_sha = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    assert mapping_sha == prior["root_mapping_sha256"]
    assert len(files) == prior["root_file_count"]
    for unit in prior["accepted"]:
        number = unit["unit"]
        assert sha(CAMPAIGN / f"wf-2021/unit-{number}.json") == unit["report_sha256"]
        assert sha(CAMPAIGN / f"wf-2021/checkpoint-{number}/state.pt") == unit[
            "checkpoint_sha256"
        ]
        assert sha(CAMPAIGN / f"wf-2021/checkpoint-{number}/manifest.json") == unit[
            "checkpoint_manifest_sha256"
        ]
    assert not (CAMPAIGN / "wf-2022/checkpoint-0").exists()
    with WFCostSessionJournal(CAMPAIGN / "sessions.jsonl", campaign=CAMPAIGN.name,
                              read_only=True) as journal:
        assert len(journal.sessions) == 2
        assert all(item["end"]["status"] == "ready" for item in journal.sessions)
        charges = journal.charges(state, now=journal.sessions[-1]["end"]["epoch"])
        assert not charges.blocked

    q0_preflight = json.loads((Q0 / "preflight-launch.json").read_text())
    blocked_01 = json.loads((BLOCKED_01 / "preflight.json").read_text())
    session_02 = json.loads((SESSION_02 / "preflight-launch.json").read_text())
    blocked_02 = json.loads((BLOCKED_02 / "preflight.json").read_text())
    assert blocked_02["preflight"]["status"] == "blocked"
    assert blocked_02["preflight"]["host"]["memory_available_bytes"] == 4259569664
    suite_q0 = pytest_seconds(Q0 / "pytest-before-launch.log")
    suite_blocked_01 = pytest_seconds(BLOCKED_01 / "pytest.log")
    suite_session_02 = pytest_seconds(SESSION_02 / "pytest-before-launch.log")
    suite_blocked_02 = pytest_seconds(BLOCKED_02 / "pytest.log")

    first_preflight_at = datetime.fromisoformat(q0_preflight["preflight"]["observed_utc"])
    blocked_01_at = datetime.fromisoformat(blocked_01["preflight"]["observed_utc"])
    session_02_at = datetime.fromisoformat(session_02["preflight"]["observed_utc"])
    blocked_02_at = datetime.fromisoformat(blocked_02["preflight"]["observed_utc"])
    ledger_start = datetime.fromisoformat(state["days"]["2026-11-01"]["started_utc"])
    session_02_end = datetime.fromisoformat(prior["session_02_end_utc"])
    assert (first_preflight_at < ledger_start < blocked_01_at < session_02_at
            < session_02_end < blocked_02_at)
    day1_ledger = state["days"]["2026-11-01"]["charged_wall_seconds"]
    day1_gap = charges.extra_by_day["2026-11-01"]
    day1_recorded = day1_ledger + day1_gap
    assert abs(day1_recorded - prior["budget_accounting"]["global_charged_seconds"]) < 1e-6
    day1_distinct_minimum = day1_recorded + suite_q0
    day1_envelope = (git_time("4e2ab6a") - git_time("cacf6a9")).total_seconds()
    # The 02/11 start was printed by the first read-only command in the
    # conversation; it has one-second resolution and was not logged by WF05.
    day2_first_observed = datetime.fromisoformat("2026-11-02T17:22:39-04:00")
    day2_close = git_time("2f25d6a")
    day2_envelope = (day2_close - day2_first_observed).total_seconds()
    day2_before_preflight = (blocked_02_at - day2_first_observed).total_seconds()
    day2_after_preflight = (day2_close - blocked_02_at).total_seconds()
    assert day1_envelope >= day1_distinct_minimum > 3600
    assert day2_envelope >= suite_blocked_02
    assert day2_envelope == day2_before_preflight + day2_after_preflight
    result = {
        "methodological_status": "incomplete_two_active_days_exhausted",
        "ledger_status_unchanged": state["status"],
        "accepted_units": 11,
        "pending": state["pending"],
        "unaccepted_next": "wf-2022/Q0",
        "historical_approval_sha256": sha(REGISTRATION),
        "historical_root_file_count": len(files),
        "historical_root_mapping_sha256": mapping_sha,
        "ledger_sha256": sha(CAMPAIGN / "ledger.jsonl"),
        "session_journal_sha256": sha(CAMPAIGN / "sessions.jsonl"),
        "supervisor_journal_sha256": sha(CAMPAIGN / "supervisor.jsonl"),
        "days": {
            "2026-11-01": {
                "ledger_span_seconds": day1_ledger,
                "session_gap_uncovered_seconds": day1_gap,
                "automated_charge_seconds": day1_recorded,
                "suite_before_ledger_seconds": suite_q0,
                "distinct_measured_minimum_seconds": day1_distinct_minimum,
                "wall_envelope_approval_to_report_seconds": day1_envelope,
                "suites_inside_ledger_span_seconds_not_added": [
                    suite_blocked_01, suite_session_02,
                ],
                "own_daily_limit_seconds": 3600,
                "minimum_own_daily_excess_seconds": day1_distinct_minimum - 3600,
                "global_productive_allowance_after_reserve_seconds": 8100,
            },
            "2026-11-02": {
                "suite_seconds": suite_blocked_02,
                "first_observed_local_one_second_resolution": day2_first_observed.isoformat(),
                "preflight_observed_utc": blocked_02_at.isoformat(),
                "closure_commit_local": day2_close.isoformat(),
                "wall_envelope_total_seconds": day2_envelope,
                "wall_envelope_before_preflight_seconds": day2_before_preflight,
                "within_before_preflight_not_suite_seconds": (
                    day2_before_preflight - suite_blocked_02
                ),
                "wall_envelope_after_preflight_seconds": day2_after_preflight,
                "own_daily_limit_seconds": 3600,
                "global_productive_allowance_after_reserve_seconds": 8100,
            },
        },
        "two_day_distinct_minimum_seconds": day1_distinct_minimum + suite_blocked_02,
        "two_day_conservative_envelope_seconds": day1_envelope + day2_envelope,
        "own_cumulative_limit_seconds": 5400,
        "cumulative_margin_after_envelopes_seconds": 5400 - day1_envelope - day2_envelope,
        "not_recoverable_exactly": [
            "individual duration of Q0 and reentry audits outside ledger",
            "individual duration of Ruff and watched preflight outside ledger",
            "individual duration of documentation and closure",
            "any unrecorded idle inside wall envelopes",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
