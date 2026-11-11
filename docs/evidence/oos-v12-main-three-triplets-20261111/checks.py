"""Read-only audit of the first three complete OOS main seed blocks."""

import hashlib
import json
from pathlib import Path

from btc_risk_rl.pilots.oos_v12_training import roster, run_id_for
from btc_risk_rl.pilots.p2_budget import state_hash

ROOT = Path(__file__).resolve().parents[3]
CAMPAIGN = ROOT / "artifacts/oos-v12-training-main-01"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    raw = (CAMPAIGN / "ledger.jsonl").read_bytes()
    previous = None
    for count, line in enumerate(raw.splitlines(), 1):
        state = json.loads(line)
        if state["previous_hash"] != previous or state["state_hash"] != state_hash(state):
            raise ValueError(f"Ledger chain failed at state {count}")
        previous = state["state_hash"]
    expected = roster("main-2018-2022")
    if (state["identity"]["roster"] != [list(row) for row in expected]
            or state["status"] not in ("running", "ready", "completed")
            or state["cursor"] < 9):
        raise ValueError("First three triplets are not accepted")
    runs = []
    for index, row in enumerate(expected[:9]):
        run_id = run_id_for("main-2018-2022", index, row)
        units = [unit for unit in state["units"] if unit["run_id"] == run_id]
        if [unit["unit"] for unit in units] != list(range(11)):
            raise ValueError(f"Incomplete run: {run_id}")
        for unit in units:
            number = unit["unit"]
            paths = {
                "checkpoint": Path(unit["checkpoint"]) / "state.pt",
                "report": CAMPAIGN / run_id / f"unit-{number}.json",
                "request": CAMPAIGN / run_id / f"request-{number}.json",
            }
            for label, path in paths.items():
                if (not path.resolve().is_relative_to(CAMPAIGN.resolve())
                        or digest(path) != unit[f"{label}_sha256"]):
                    raise ValueError(f"{label} hash differs: {run_id}/{number}")
        final = json.loads((Path(units[-1]["checkpoint"]) / "manifest.json").read_text())
        if (final["run_id"] != run_id or final["condition"] != row[1]
                or final["settings"]["seed"] != row[0]
                or final["boundary"] != "after_dual_and_D"
                or final["state_sha256"] != units[-1]["checkpoint_sha256"]):
            raise ValueError(f"K10 identity mismatch: {run_id}")
        runs.append({
            "run_id": run_id, "seed": row[0], "condition": row[1],
            "unit_seconds": round(sum(unit["seconds"] for unit in units), 6),
            "k10_sha256": units[-1]["checkpoint_sha256"],
            "peak_rss_bytes": max(unit["supervisor"]["rss_peak_bytes"] for unit in units),
        })
    blocks = [
        {"block": block, "seed": runs[3 * block]["seed"],
         "unit_seconds": round(sum(row["unit_seconds"]
                                   for row in runs[3 * block:3 * block + 3]), 6)}
        for block in range(3)
    ]
    print(json.dumps({
        "ledger_snapshot_sha256": hashlib.sha256(raw).hexdigest(),
        "state_count": count, "ledger_status": state["status"],
        "accepted_runs_at_snapshot": state["cursor"],
        "accepted_units_at_snapshot": len(state["units"]),
        "first_three_blocks": blocks, "runs": runs,
        "measured_mean_block_unit_seconds": round(
            sum(block["unit_seconds"] for block in blocks) / 3, 6),
        "files_hashed": {"checkpoint": 99, "report": 99, "request": 99},
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
