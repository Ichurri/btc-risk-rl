"""Read-only progress metrics from accepted OOS training ledger states."""

from __future__ import annotations

import json
import math
from html import escape
from pathlib import Path

from btc_risk_rl.pilots.p2_budget import state_hash


def read_verified_snapshot(raw: bytes) -> dict:
    """Verify one immutable byte snapshot of a newline-terminated ledger."""
    if not raw.endswith(b"\n"):
        raise ValueError("OOS ledger snapshot ends with an incomplete line")
    previous = None
    state = None
    for line in raw.decode("utf-8").splitlines():
        state = json.loads(line)
        if state.get("previous_hash") != previous or state.get("state_hash") != state_hash(state):
            raise ValueError("OOS ledger chain corrupt")
        previous = state["state_hash"]
    if state is None:
        raise ValueError("OOS ledger empty")
    return state


def read_verified_ledger(path: Path) -> dict:
    """Read an append-only snapshot and verify every complete chain entry."""
    return read_verified_snapshot(Path(path).read_bytes())


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


def render_progress_svg(summary: dict, *, source: str) -> str:
    """Compact offline figure of complete runs; pending work is text only."""
    profile = escape(summary["profile"])
    source_label = escape(source)
    target = summary["expected_runs"] // 3
    rows = []
    for index, condition in enumerate(("C0", "C5", "C10")):
        count = summary["completed_by_condition"][condition]
        y = 105 + 80 * index
        width = 600 * count / max(1, target)
        rows += [f'<text x="20" y="{y}" font-size="22">{condition}: {count}/{target}</text>',
                 f'<rect x="190" y="{y - 22}" width="600" height="28" fill="#e4e7eb"/>',
                 f'<rect x="190" y="{y - 22}" width="{width:.2f}" height="28" '
                 'fill="#246b77"/>']
    footer = (f'Unidades aceptadas: {summary["accepted_units"]}; '
              f'corridas completas: {summary["completed_runs"]}/{summary["expected_runs"]}; '
              f'pendiente: {summary["pending"] or "ninguna"}')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="850" height="390" '
            'viewBox="0 0 850 390" role="img">'
            f'<title>Avance {profile}, corridas completas</title>'
            '<rect width="850" height="390" fill="white"/>'
            f'<text x="20" y="35" font-size="25" font-weight="bold">{profile}: '
            'corridas completas por condición</text>'
            + "".join(rows)
            + f'<text x="20" y="350" font-size="15">{escape(footer)}</text>'
            + f'<text x="20" y="374" font-size="13">Fuente: {source_label}. '
              'Unidad: corridas y unidades; entrenamiento.</text></svg>')
