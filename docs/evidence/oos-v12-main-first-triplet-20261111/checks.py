"""Audit the first complete main OOS seed block without changing artifacts."""

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
    if state["identity"]["roster"] != [list(row) for row in expected]:
        raise ValueError("Main roster mismatch")
    if state["status"] not in ("running", "ready", "completed") or state["cursor"] < 3:
        raise ValueError("First triplet not accepted")

    runs = []
    for index, row in enumerate(expected[:3]):
        run_id = run_id_for("main-2018-2022", index, row)
        units = [unit for unit in state["units"] if unit["run_id"] == run_id]
        if [unit["unit"] for unit in units] != list(range(11)):
            raise ValueError(f"Incomplete run: {run_id}")
        for unit in units:
            n = unit["unit"]
            for label, path in {
                "checkpoint": Path(unit["checkpoint"]) / "state.pt",
                "report": CAMPAIGN / run_id / f"unit-{n}.json",
                "request": CAMPAIGN / run_id / f"request-{n}.json",
            }.items():
                if digest(path) != unit[f"{label}_sha256"]:
                    raise ValueError(f"{label} hash differs: {run_id}/{n}")
        manifest = json.loads((Path(units[-1]["checkpoint"]) / "manifest.json").read_text())
        if (manifest["run_id"] != run_id or manifest["condition"] != row[1]
                or manifest["settings"]["seed"] != row[0]
                or manifest["boundary"] != "after_dual_and_D"
                or manifest["state_sha256"] != units[-1]["checkpoint_sha256"]):
            raise ValueError(f"Final checkpoint identity mismatch: {run_id}")
        runs.append({
            "run_id": run_id, "seed": row[0], "condition": row[1],
            "unit_seconds": round(sum(unit["seconds"] for unit in units), 6),
            "k10_state_sha256": units[-1]["checkpoint_sha256"],
            "peak_worker_rss_bytes": max(unit["supervisor"]["rss_peak_bytes"] for unit in units),
        })
    print(json.dumps({
        "ledger_snapshot_sha256": hashlib.sha256(raw).hexdigest(),
        "state_count": count, "ledger_status": state["status"],
        "accepted_runs_at_snapshot": state["cursor"],
        "accepted_units_at_snapshot": len(state["units"]),
        "first_triplet": runs,
        "first_triplet_unit_seconds": round(sum(run["unit_seconds"] for run in runs), 6),
        "files_hashed": {"checkpoint": 33, "report": 33, "request": 33},
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
