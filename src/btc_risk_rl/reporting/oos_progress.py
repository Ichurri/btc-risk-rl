"""Read-only progress metrics from accepted OOS training ledger states."""

from __future__ import annotations

import math


def summarize_state(profile: str, state: dict, *, expected_runs: int) -> dict:
    if profile not in {"wf-2021", "wf-2022", "main-2018-2022"}:
        raise ValueError("Unknown OOS profile")
    if state.get("status") not in {"ready", "running", "completed", "failed", "incomplete"}:
        raise ValueError("Unknown OOS ledger status")
    runs = {}
    measured = 0.0
    for row in state.get("units", []):
        run_id, unit, seconds = row.get("run_id"), row.get("unit"), row.get("seconds")
        if (not isinstance(run_id, str) or type(unit) is not int
                or type(seconds) not in (int, float) or not math.isfinite(seconds)
                or seconds <= 0):
            raise ValueError("Invalid accepted OOS unit")
        run_units = runs.setdefault(run_id, [])
        if unit != len(run_units) or unit > 10:
            raise ValueError("OOS accepted units must be contiguous from Q0")
        run_units.append(unit)
        measured += seconds
    completed_by_condition = {condition: 0 for condition in ("C0", "C5", "C10")}
    for run_id, units in runs.items():
        pieces = run_id.split("-")
        if (len(pieces) != 4 or pieces[0] != "run" or pieces[2] not in completed_by_condition
                or pieces[3] != "b0" or not pieces[1].isdigit()
                or int(pieces[1]) >= expected_runs):
            raise ValueError("Unexpected OOS run identifier")
        if len(units) == 11:
            completed_by_condition[pieces[2]] += 1
    complete = sum(completed_by_condition.values())
    if complete != state.get("cursor") or complete > expected_runs:
        raise ValueError("OOS cursor disagrees with completed units")
    pending = state.get("pending")
    if pending is not None:
        prefix = runs.get(pending.get("run_id"), [])
        if (state["status"] != "running"
                or pending.get("unit") != len(prefix)
                or (not prefix and pending.get("unit") != 0)):
            raise ValueError("OOS pending unit does not follow accepted prefix")
        pending_label = f"{pending['run_id']}/{pending['unit']}"
    else:
        pending_label = None
    return dict(profile=profile, status=state["status"],
                expected_runs=expected_runs, completed_runs=complete,
                accepted_units=len(state.get("units", [])),
                completed_by_condition=completed_by_condition,
                measured_unit_seconds=measured, pending=pending_label)
