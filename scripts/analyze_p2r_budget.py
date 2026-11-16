"""Read-only timing analysis of completed P0/P1/P2 units; no market loading."""

import hashlib
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGNS = {
    "P0": ("p0-approved-v1", "1d1ee72ca0ac49529f205b30942a68f381d86037e336091c490c624098339b8c", 27, "completed"),
    "P1": ("p1-approved-v1", "926eab40bc764e1cae88a74e6718ba70b50e2df0626e8e34964078cc4ba55755", 54, "completed"),
    "P2": ("p2-approved-v1", "e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8", 57, "failed"),
}


def describe(values):
    if not values:
        return None
    return dict(n=len(values), total=math.fsum(values), minimum=min(values),
                median=statistics.median(values), maximum=max(values),
                mean=statistics.fmean(values))


def analyze(label, name, expected_sha, expected_units, expected_status):
    root = ROOT / "artifacts" / name
    ledger_path = root / "ledger.jsonl"
    raw = ledger_path.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != expected_sha:
        raise ValueError(f"{label} ledger SHA-256 changed")
    state = json.loads(raw.splitlines()[-1])
    units = state["units"]
    if len(units) != expected_units or state["status"] != expected_status:
        raise ValueError(f"{label} completion/status changed")
    grouped = defaultdict(lambda: defaultdict(list))
    arms = defaultdict(lambda: defaultdict(list))
    conditions = defaultdict(lambda: defaultdict(list))
    phase_times = defaultdict(list)
    previous_telemetry = {}
    by_run = defaultdict(list)
    for unit in units:
        run_id, number = unit["run_id"], unit["unit"]
        payload = json.loads((root / run_id / f"unit-{number}.json").read_text())
        if (payload["status"] != "passed" or payload["unit"] != number
                or payload["checkpoint_sha256"] != unit["checkpoint_sha256"]
                or payload["resources"] != unit["resources"]):
            raise ValueError(f"{label} accepted unit/payload mismatch: {run_id}/{number}")
        telemetry = payload["report"]["telemetry"]
        old = previous_telemetry.get(run_id, [])
        if number != len(by_run[run_id]) or telemetry[:len(old)] != old:
            raise ValueError(f"{label} cumulative telemetry mismatch: {run_id}/{number}")
        for entry in telemetry[len(old):]:
            if entry["status"] != "complete":
                raise ValueError(f"{label} incomplete phase in accepted unit")
            phase_times[entry["phase"]].append(float(entry["wall_seconds"]))
        previous_telemetry[run_id] = telemetry
        by_run[run_id].append(unit)
        kind = unit["kind"]
        group = grouped[kind]
        ledger_seconds = float(unit["seconds"])
        supervisor_seconds = float(unit["supervisor"]["wall_seconds"])
        work_seconds = float(unit["work_seconds"])
        algorithm_seconds = float(payload["algorithm_seconds"])
        save_seconds = float(payload["save_seconds"])
        if (not 0 < algorithm_seconds <= work_seconds <= supervisor_seconds <= ledger_seconds
                or not 0 <= save_seconds <= supervisor_seconds - work_seconds):
            raise ValueError(f"{label} inconsistent duration decomposition")
        group["ledger_seconds"].append(ledger_seconds)
        group["supervisor_seconds"].append(supervisor_seconds)
        group["work_seconds"].append(work_seconds)
        group["algorithm_seconds"].append(algorithm_seconds)
        group["save_seconds"].append(save_seconds)
        group["worker_setup_gap"].append(work_seconds - algorithm_seconds)
        group["supervisor_tail_gap"].append(supervisor_seconds - work_seconds)
        group["ledger_gap"].append(ledger_seconds - supervisor_seconds)
        group["total_non_algorithm_gap"].append(ledger_seconds - algorithm_seconds)
        condition = run_id.split("-")[2]
        conditions[condition][kind].append(ledger_seconds)
        if label == "P1":
            arms[run_id.rsplit("-", 1)[-1]][kind].append(ledger_seconds)
    if label == "P2" and (len(by_run) != 6 or len(phase_times["D"]) != 51):
        raise ValueError("P2 complete-unit D count changed")
    days = {}
    for day, value in state["days"].items():
        charged = value.get("charged_wall_seconds")
        days[day] = dict(charged_wall_seconds=charged,
                         external_seconds=value.get("external_seconds"),
                         active_seconds=value.get("active_seconds"))
    total_units = math.fsum(unit["seconds"] for unit in units)
    if label == "P2" and (abs(total_units - 3695.943) > 0.001
                          or abs(math.fsum(phase_times["D"]) - 248.335) > 0.001):
        raise ValueError("P2 published unit/D totals do not reconcile")
    full_campaign_wall = (sum(d["charged_wall_seconds"] for d in days.values())
                          if all(d["charged_wall_seconds"] is not None for d in days.values())
                          else None)
    return dict(status=state["status"], ledger_sha256=actual_sha,
                accepted_units=len(units), accepted_runs=len(by_run),
                by_kind={kind: {key: describe(values) for key, values in measures.items()}
                         for kind, measures in grouped.items()},
                new_phase_times={phase: describe(values)
                                 for phase, values in phase_times.items()},
                p1_by_critic_arm={arm: {kind: describe(values)
                                        for kind, values in groups.items()}
                                  for arm, groups in arms.items()},
                by_condition={condition: {kind: describe(values)
                                          for kind, values in groups.items()}
                              for condition, groups in conditions.items()},
                accepted_unit_wall_seconds=total_units,
                campaign_charged_wall_seconds=full_campaign_wall,
                campaign_minus_accepted_units=(full_campaign_wall - total_units
                                               if full_campaign_wall is not None else None),
                days=days)


def main():
    campaigns = {label: analyze(label, *arguments)
                 for label, arguments in CAMPAIGNS.items()}
    p2 = campaigns["P2"]["by_kind"]
    q = p2["q0"]["ledger_seconds"]
    iteration = p2["iteration"]["ledger_seconds"]
    scenarios = {}
    for label, q_seconds, iteration_seconds in (
        ("observed_P2_medians", q["median"], iteration["median"]),
        ("observed_P2_maxima", q["maximum"], iteration["maximum"]),
    ):
        base = 9 * q_seconds + 90 * iteration_seconds
        scenarios[label] = dict(
            basis_q0_seconds=q_seconds, basis_iteration_seconds=iteration_seconds,
            base_99_units_seconds=base,
            hypothetical_extra_seconds_per_unit={
                str(extra): dict(total_seconds=base + 99 * extra,
                                 remaining_from_24300=24300 - base - 99 * extra)
                for extra in (0, 30, 120, 180)
            },
            break_even_extra_seconds_per_unit=(24300 - base) / 99,
        )
    report = dict(status="read_only_analysis", checked_utc=datetime.now(timezone.utc).isoformat(),
                  source="accepted_units_only_no_optimizer_or_market_data_access",
                  budget_work_seconds_three_days=24300,
                  roster_units=dict(q0=9, iteration=90, total=99),
                  campaigns=campaigns, scenarios=scenarios)
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
