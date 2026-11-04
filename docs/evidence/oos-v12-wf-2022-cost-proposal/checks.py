"""Read-only arithmetic checks for the proposed 2022-only WF cost study."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / "docs/evidence/oos-v1-2-wf-cost-05-session-02-20261101/audit.json"
CLOSURE = ROOT / "docs/evidence/oos-v1-2-wf-cost-05-closure-20261103/results.json"
PROPOSAL = ROOT / "docs/proposals/OOS-v1-2-costo-2022-exclusivo-v1.md"
NEW_ROOT = ROOT / "artifacts/oos-v12-wf-cost-only-2022-01"
OLD_ROOT = ROOT / "artifacts/oos-v12-wf-cost-only-05"
APPROVAL = ROOT / "docs/protocols/OOS-v1-2-wf-cost-2022-only-approval.json"
NEW_JOURNAL = ROOT / "artifacts/shared-pilot-budget/wf-2022-only-01-attempts.jsonl"
LA_PAZ = ZoneInfo("America/La_Paz")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def union_seconds(intervals: list[tuple[float, float]]) -> float:
    """Charge overlapping half-open time intervals once."""
    result = 0.0
    end = None
    for start, stop in sorted(intervals):
        assert stop >= start
        if end is None or start > end:
            result += stop - start
            end = stop
        elif stop > end:
            result += stop - end
            end = stop
    return result


def split_local_days(start: datetime, end: datetime) -> dict[str, float]:
    """Synthetic UTC interval separated by La Paz calendar dates."""
    assert start.tzinfo is not None and end.tzinfo is not None and start <= end
    result: dict[str, float] = {}
    current = start
    while current < end:
        local = current.astimezone(LA_PAZ)
        next_midnight = datetime.fromordinal(local.date().toordinal() + 1).replace(
            tzinfo=LA_PAZ
        ).astimezone(timezone.utc)
        stop = min(end, next_midnight)
        result[local.date().isoformat()] = result.get(local.date().isoformat(), 0) + (
            stop - current
        ).total_seconds()
        current = stop
    return result


def main() -> None:
    audit = json.loads(AUDIT.read_text())
    closure = json.loads(CLOSURE.read_text())
    assert audit["status"] == "ready" and audit["accepted_units"] == 11
    assert closure["methodological_status"] == "incomplete_two_active_days_exhausted"
    assert closure["accepted_units"] == 11
    assert not NEW_ROOT.exists() and not APPROVAL.exists() and not NEW_JOURNAL.exists()
    assert PROPOSAL.is_file()
    original_files = {
        str(path.relative_to(OLD_ROOT)): sha256(path)
        for path in sorted(OLD_ROOT.rglob("*")) if path.is_file()
    }
    original_mapping = hashlib.sha256(
        json.dumps(original_files, sort_keys=True).encode()
    ).hexdigest()
    assert len(original_files) == closure["historical_root_file_count"]
    assert original_mapping == closure["historical_root_mapping_sha256"]
    assert sha256(OLD_ROOT / "ledger.jsonl") == closure["ledger_sha256"]

    accepted = audit["accepted"]
    assert [row["unit"] for row in accepted] == list(range(11))
    q0 = accepted[0]["ledger_wall_seconds"]
    iterations = sum(row["ledger_wall_seconds"] for row in accepted[1:])
    d = sum(row["diagnostic_D_seconds"] for row in accepted[1:])
    assert abs(q0 - 28.650246381759644) < 1e-9
    assert abs(iterations - 714.7581367492676) < 1e-9
    assert abs(d - 47.817987100998835) < 1e-9
    assert abs(closure["days"]["2026-11-02"]["suite_seconds"] - 390.45) < 1e-9
    service = audit["session_01_wall_seconds"] + audit["session_02_wall_seconds"]
    assert abs(service - 749.20548057556) < 1e-5
    unit_caps = 120 + 10 * 180
    assert unit_caps == 1920

    # Suite lies inside the first attempt; ledger lies inside the service.
    # Adding their itemized durations would double count 390 + 100 seconds.
    synthetic = [(0, 390), (380, 600), (500, 700)]
    assert union_seconds(synthetic) == 700
    assert sum(b - a for a, b in synthetic) == 810
    midnight = split_local_days(
        datetime(2026, 11, 4, 3, 59, 30, tzinfo=timezone.utc),
        datetime(2026, 11, 4, 4, 0, 30, tzinfo=timezone.utc),
    )
    assert midnight == {"2026-11-03": 30.0, "2026-11-04": 30.0}

    suite_proxy = 390.45
    other_assumption = 300.0
    close_reserve = 600.0
    scenarios = {}
    for factor in (1, 1.5, 2):
        projected_service = service * factor
        total = suite_proxy + other_assumption + projected_service + close_reserve
        scenarios[str(factor)] = dict(service_seconds=projected_service,
                                      total_seconds=total,
                                      margin_daily_seconds=3600 - total)
    cap_total = suite_proxy + other_assumption + unit_caps + close_reserve
    assert cap_total == 3210.45
    assert 2 * (suite_proxy + other_assumption + close_reserve) + unit_caps == 4500.9
    assert math.isclose(4800 - 4500.9, 299.1, abs_tol=1e-9)
    assert all(row["margin_daily_seconds"] > 0 for row in scenarios.values())

    print(json.dumps({
        "status": "algebraic_and_synthetic_checks_only",
        "source_sha256": {str(path.relative_to(ROOT)): sha256(path)
                          for path in (AUDIT, CLOSURE, PROPOSAL)},
        "new_root_absent": True,
        "approval_absent": True,
        "budget_journal_absent": True,
        "measured_2021": dict(q0_ledger_seconds=q0, iteration_ledger_seconds=iterations,
                              d_seconds_included=d, sessions_wall_seconds=service),
        "measured_other_day_suite_proxy_seconds": suite_proxy,
        "assumed_other_seconds": other_assumption,
        "proposed_own_close_reserve_seconds": close_reserve,
        "proposed_unit_caps_sum_seconds": unit_caps,
        "projected_2022_scenarios": scenarios,
        "all_units_at_cap_planning_total_seconds": cap_total,
        "two_days_at_cap_planning_total_seconds": 4500.9,
        "two_days_cumulative_margin_seconds": 299.1,
        "synthetic_union_seconds": union_seconds(synthetic),
        "synthetic_naive_sum_seconds": 810,
        "synthetic_local_midnight_split": midnight,
        "historical_wf05_unchanged_sha256": {
            "ledger": closure["ledger_sha256"],
            "last_checkpoint": closure["checkpoint_sha256"]
            if "checkpoint_sha256" in closure else audit["checkpoint_10_sha256"],
            "root_mapping": original_mapping,
        },
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
