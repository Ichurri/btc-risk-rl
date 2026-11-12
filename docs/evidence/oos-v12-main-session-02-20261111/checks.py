"""Reaudit the immutable second-session ledger prefix and accepted files."""

import hashlib
import json
import statistics
from pathlib import Path

from btc_risk_rl.pilots.oos_v12_training import roster, run_id_for
from btc_risk_rl.pilots.p2_budget import state_hash

ROOT = Path(__file__).resolve().parents[3]
CAMPAIGN = ROOT / "artifacts/oos-v12-training-main-01"
EXPECTED_LEDGER_SHA256 = "1245b4299103401bbc066f9044278ffeabd55606687ac3ddab0bfb5c712c5749"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    raw = (CAMPAIGN / "ledger.jsonl").read_bytes()
    prefix = bytearray()
    previous = None
    state = None
    for number, line in enumerate(raw.splitlines(keepends=True), 1):
        prefix.extend(line)
        state = json.loads(line)
        if state["previous_hash"] != previous or state["state_hash"] != state_hash(state):
            raise ValueError(f"Ledger chain invalid at state {number}")
        previous = state["state_hash"]
        if hashlib.sha256(prefix).hexdigest() == EXPECTED_LEDGER_SHA256:
            break
    else:
        raise ValueError("Frozen second-session ledger prefix absent")
    expected = roster("main-2018-2022")
    if (state["status"] != "ready" or state["cursor"] != 19
            or state["pending"] is not None or len(state["units"]) != 215
            or state["identity"]["roster"] != [list(row) for row in expected]):
        raise ValueError("Second-session boundary or roster invalid")
    for unit in state["units"]:
        run_id, index = unit["run_id"], unit["unit"]
        paths = {
            "checkpoint": Path(unit["checkpoint"]) / "state.pt",
            "report": CAMPAIGN / run_id / f"unit-{index}.json",
            "request": CAMPAIGN / run_id / f"request-{index}.json",
        }
        for label, path in paths.items():
            if (not path.resolve().is_relative_to(CAMPAIGN.resolve())
                    or digest(path) != unit[f"{label}_sha256"]):
                raise ValueError(f"Accepted {label} hash mismatch: {run_id}/{index}")
    blocks = []
    for block in range(6):
        seconds = 0.0
        for index in range(3 * block, 3 * block + 3):
            row = expected[index]
            run_id = run_id_for("main-2018-2022", index, row)
            units = [unit for unit in state["units"] if unit["run_id"] == run_id]
            if [unit["unit"] for unit in units] != list(range(11)):
                raise ValueError(f"Incomplete paired run: {run_id}")
            manifest = json.loads((Path(units[-1]["checkpoint"]) / "manifest.json").read_text())
            if (manifest["run_id"] != run_id
                    or manifest["condition"] != row[1]
                    or manifest["settings"]["seed"] != row[0]
                    or manifest["boundary"] != "after_dual_and_D"
                    or manifest["state_sha256"] != units[-1]["checkpoint_sha256"]):
                raise ValueError(f"K10 checkpoint identity mismatch: {run_id}")
            seconds += sum(unit["seconds"] for unit in units)
        blocks.append(round(seconds, 6))
    partial_id = run_id_for("main-2018-2022", 19, expected[19])
    partial = [unit for unit in state["units"] if unit["run_id"] == partial_id]
    if [unit["unit"] for unit in partial] != list(range(6)):
        raise ValueError("Accepted partial run prefix differs")
    mean = statistics.mean(blocks)
    print(json.dumps({
        "ledger_prefix_sha256": EXPECTED_LEDGER_SHA256,
        "chain_states": number, "ledger_status_at_pause": state["status"],
        "complete_runs": state["cursor"], "accepted_units": len(state["units"]),
        "verified_files": {"checkpoint": 215, "report": 215, "request": 215},
        "complete_paired_blocks": len(blocks),
        "block_unit_seconds": blocks,
        "mean_block_unit_seconds": round(mean, 6),
        "remaining_30_blocks_unit_seconds_extrapolated": round(30 * mean, 6),
        "partial_run": partial_id, "partial_run_accepted_units": len(partial),
        "last_checkpoint": state["units"][-1]["checkpoint"],
        "last_checkpoint_sha256": state["units"][-1]["checkpoint_sha256"],
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
