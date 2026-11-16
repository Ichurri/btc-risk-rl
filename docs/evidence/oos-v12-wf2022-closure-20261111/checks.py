"""Read-only reproducibility check for the accepted wf-2022 cut."""

import hashlib
import json
from pathlib import Path

from btc_risk_rl.pilots.oos_v12_training import roster, run_id_for
from btc_risk_rl.pilots.p2_budget import state_hash

ROOT = Path(__file__).resolve().parents[3]
CAMPAIGN = ROOT / "artifacts/oos-v12-training-wf-2022-01"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ledger = CAMPAIGN / "ledger.jsonl"
    raw = ledger.read_bytes()
    previous = None
    for count, line in enumerate(raw.splitlines(), 1):
        state = json.loads(line)
        if state["previous_hash"] != previous or state["state_hash"] != state_hash(state):
            raise ValueError(f"Ledger chain failed at state {count}")
        previous = state["state_hash"]
    if (state["status"] != "completed" or state["cursor"] != 9
            or state["pending"] is not None or len(state["units"]) != 99
            or state["identity"]["roster"] != [list(row) for row in roster("wf-2022")]):
        raise ValueError("wf-2022 completion or roster mismatch")
    checked = {"checkpoint": 0, "report": 0, "request": 0}
    runs = []
    for index, row in enumerate(roster("wf-2022")):
        run_id = run_id_for("wf-2022", index, row)
        units = [unit for unit in state["units"] if unit["run_id"] == run_id]
        if [unit["unit"] for unit in units] != list(range(11)):
            raise ValueError(f"Incomplete run: {run_id}")
        for unit in units:
            n = unit["unit"]
            files = {
                "checkpoint": Path(unit["checkpoint"]) / "state.pt",
                "report": CAMPAIGN / run_id / f"unit-{n}.json",
                "request": CAMPAIGN / run_id / f"request-{n}.json",
            }
            for label, path in files.items():
                if digest(path) != unit[f"{label}_sha256"]:
                    raise ValueError(f"{label} hash differs: {run_id}/{n}")
                checked[label] += 1
        runs.append({"run_id": run_id, "seed": row[0], "condition": row[1],
                     "unit_seconds": round(sum(unit["seconds"] for unit in units), 6),
                     "checkpoint_k10_sha256": units[-1]["checkpoint_sha256"]})
    print(json.dumps({
        "status": state["status"], "ledger_sha256": hashlib.sha256(raw).hexdigest(),
        "state_count": count, "accepted_units": len(state["units"]),
        "hashes_checked": checked,
        "measured_unit_seconds": round(sum(unit["seconds"] for unit in state["units"]), 6),
        "charged_wall_seconds": state["days"]["2026-11-11"]["charged_wall_seconds"],
        "runs": runs,
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
