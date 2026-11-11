"""Internal all-policy technical gate; no performance-based selection.

The future supervisor must first enforce the separate 2023 permit and pass
the roster from ``verify_complete_main_roster``. This module cannot open a
protected source by itself.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

from btc_risk_rl.evaluation.ledger import EvaluationLedger
from btc_risk_rl.evaluation.runner import verify_accepted_outputs


def _digest(value: object) -> bool:
    return (type(value) is str and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def check_technical_decision(roster: list[dict], reports: list[dict], *,
                             expected_blocks: int) -> int:
    """Require every paired policy and a defined metric, ignoring its sign."""
    if (type(expected_blocks) is not int or expected_blocks < 1
            or type(roster) is not list or type(reports) is not list
            or len(roster) != 3 * expected_blocks
            or len(reports) != len(roster)):
        raise ValueError("Technical evaluation is not complete")
    seen_seeds, seen_runs = set(), set()
    for block in range(expected_blocks):
        three = roster[3 * block:3 * block + 3]
        if (any(type(row) is not dict for row in three)
                or {row.get("condition") for row in three} != {"C0", "C5", "C10"}
                or len({row.get("seed") for row in three}) != 1
                or type(three[0].get("seed")) is not int):
            raise ValueError("Technical evaluation paired block invalid")
        seed = three[0]["seed"]
        if seed in seen_seeds:
            raise ValueError("Technical evaluation paired seeds duplicate")
        seen_seeds.add(seed)
        for row in three:
            run_id = row.get("run_id")
            if (type(run_id) is not str or not run_id
                    or run_id in seen_runs or not _digest(row.get("checkpoint_sha256"))):
                raise ValueError("Technical evaluation paired run invalid")
            seen_runs.add(run_id)
    for report in reports:
        value = report.get("sortino_annualized") if type(report) is dict else None
        if type(value) not in {int, float} or not math.isfinite(value):
            raise ValueError("Technical evaluation Sortino undefined")
    return len(roster)


def write_technical_closure(ledger: EvaluationLedger, destination: Path, *,
                            expected_roster: list[dict], config: object,
                            code_sha256: str) -> dict:
    """Audit all 108 traces, then write an immutable technical-only pass.

    No Sortino value or comparison is exposed in the closure. A final permit
    may later pin this file's hash, but this function cannot enable it.
    """
    if type(ledger) is not EvaluationLedger or not _digest(code_sha256):
        raise ValueError("Technical closure identity invalid")
    state = ledger.state
    roster = ledger.identity["roster"]
    if (ledger.identity["partition"] != "technical_2023"
            or state["status"] != "completed" or state["cursor"] != 108
            or state["pending"] is not None or roster != expected_roster):
        raise ValueError("Technical evaluation is not complete or roster differs")
    destination = Path(destination)
    if (destination.exists() or destination.is_symlink()
            or not destination.parent.is_dir()):
        raise FileExistsError("Technical closure destination exists or parent absent")
    if verify_accepted_outputs(ledger, config=config) != 108:
        raise ValueError("Technical evaluation outputs incomplete")
    reports = [json.loads((ledger.root / run["run_id"] / "report.json").read_text())
               for run in roster]
    count = check_technical_decision(roster, reports, expected_blocks=36)
    raw_ledger = ledger.path.read_bytes()
    if ledger.state["state_hash"] != state["state_hash"]:
        raise ValueError("Technical evaluation ledger changed during closure")
    closure = {
        "schema": "oos_v12_technical_closure_v1", "status": "passed",
        "partition": "technical_2023", "complete_policies": count,
        "interpretation": "technical_integrity_only_no_performance_selection",
        "approval_sha256": ledger.identity["approval_sha256"],
        "training_ledger_sha256": ledger.identity["training_ledger_sha256"],
        "export_manifest_sha256": ledger.identity["export_manifest_sha256"],
        "evaluation_ledger_sha256": hashlib.sha256(raw_ledger).hexdigest(),
        "code_sha256": code_sha256,
        "closed_utc": datetime.now(timezone.utc).isoformat(),
    }
    temporary = destination.with_name(destination.name + ".tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(closure, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, destination)
    return closure
