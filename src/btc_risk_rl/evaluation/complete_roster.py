"""Require 36 complete paired training blocks before historical evaluation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from btc_risk_rl.reporting.oos_progress import read_verified_snapshot
from btc_risk_rl.reporting.oos_tables import completed_run_rows

FREEZE_SHA256 = "0651f396f3157eaa5abd6bb7faf7ec1c6463210d255fa2fbd8a932e2999870a0"
FREEZE_RELATIVE = Path("docs/protocols/OOS-v1-2-training-freeze-20261110.json")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_complete_main_roster(repo_root: Path, *, freeze_path: Path | None = None,
                                freeze_sha256: str = FREEZE_SHA256) -> dict:
    """Verify a fixed full roster and every accepted training artifact hash.

    The default freeze pin is production. Alternate pins are for invented
    fixture roots; a future public entry point must use the default.
    """
    repo_root = Path(repo_root).resolve()
    freeze_path = repo_root / FREEZE_RELATIVE if freeze_path is None else Path(freeze_path)
    if freeze_path.is_symlink() or _sha(freeze_path) != freeze_sha256:
        raise ValueError("OOS training freeze hash mismatch")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    entries = [row for row in freeze["roster"] if row["source"] == "main-2018-2022"]
    if len(entries) != 108:
        raise ValueError("OOS main requires 108 frozen runs")
    roster = []
    for block in range(36):
        three = entries[3 * block:3 * block + 3]
        if (len(three) != 3 or {row["condition"] for row in three} != {"C0", "C5", "C10"}
                or len({row["seed"] for row in three}) != 1
                or any(row["block"] != block or row["beta"] != 0 for row in three)):
            raise ValueError("OOS main paired roster identity mismatch")
        roster.extend((row["seed"], row["condition"], row["beta"]) for row in three)
    if len({entries[3 * block]["seed"] for block in range(36)}) != 36:
        raise ValueError("OOS main seed blocks not distinct")
    root = (repo_root / freeze["campaign_roots"]["main-2018-2022"]).resolve()
    if not root.is_relative_to((repo_root / "artifacts").resolve()):
        raise ValueError("OOS main campaign root outside artifacts")
    ledger = root / "ledger.jsonl"
    if ledger.is_symlink():
        raise ValueError("OOS main ledger symlink invalid")
    raw = ledger.read_bytes()
    state = read_verified_snapshot(raw)
    if (state.get("status") != "completed" or state.get("cursor") != 108
            or state.get("pending") is not None or len(state.get("units", [])) != 1188):
        raise ValueError("OOS main training is not completed")
    rows = completed_run_rows("main-2018-2022", state, roster, root=root)
    for unit in state["units"]:
        run_id, number = unit["run_id"], unit["unit"]
        for label, path in (
            ("report", root / run_id / f"unit-{number}.json"),
            ("request", root / run_id / f"request-{number}.json"),
        ):
            if (path.is_symlink() or not path.resolve().is_relative_to(root)
                    or _sha(path) != unit[f"{label}_sha256"]):
                raise ValueError(f"OOS accepted {label} hash mismatch: {run_id}/{number}")
    return {
        "status": "complete_verified", "profile": "main-2018-2022",
        "complete_runs": len(rows), "accepted_units": len(state["units"]),
        "ledger_sha256": hashlib.sha256(raw).hexdigest(),
        "freeze_sha256": freeze_sha256, "runs": rows,
    }
