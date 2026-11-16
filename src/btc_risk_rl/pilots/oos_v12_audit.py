"""Read-only counterfactual budget audit for the completed 2021 OOS fold."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, time
from pathlib import Path

from btc_risk_rl.pilots.budget import CAPS, LA_PAZ
from btc_risk_rl.pilots.oos_v12_budget import PREP_CAMPAIGN, PREP_NAME
from btc_risk_rl.pilots.oos_v12_training import (
    LEGACY_COMPLETED_ROOTS,
    ROOT,
    verified_legacy_completed_root,
)
from btc_risk_rl.pilots.wf_cost_session import DAY_LIMIT, WFCostSessionJournal

CLOSING_RESERVE = 2700


def reconstruct_admissions(
    units,
    *,
    preparation_start: float,
    nine_epoch: float,
    other_registered_seconds: float = 0.0,
) -> dict:
    """Replay the adopted estimates using unit begin as a later time bound."""
    if (not all(math.isfinite(x) for x in
                (preparation_start, nine_epoch, other_registered_seconds))
            or other_registered_seconds < 0):
        raise ValueError("Invalid OOS reconstruction clock or external debit")
    hard = min(preparation_start + DAY_LIMIT - other_registered_seconds, nine_epoch)
    work = hard - CLOSING_RESERVE
    measurements: dict[tuple[str, str], list[float]] = {}
    rows = []
    for item in units:
        kind = item["kind"]
        parts = item["run_id"].split("-")
        if kind not in CAPS or len(parts) != 4 or parts[2] not in {"C0", "C5", "C10"}:
            raise ValueError("Invalid OOS unit kind or condition")
        condition = parts[2]
        prior = measurements.get((condition, kind), [])
        required = 1.5 * max(prior) if prior else CAPS[kind]
        if required > CAPS[kind]:
            raise ValueError("OOS conservative estimate exceeds adopted cap")
        start, work_ended, end = item["start"], item["work_ended"], item["end"]
        work_seconds = item["work_seconds"]
        if (not all(math.isfinite(x) for x in (start, work_ended, end, work_seconds))
                or not 0 < work_seconds <= CAPS[kind]
                or not start <= work_ended <= end):
            raise ValueError("Invalid OOS accepted unit clocks")
        admission_margin = work - start - required
        rows.append({
            "run_id": item["run_id"], "unit": item["unit"], "condition": condition,
            "kind": kind, "recorded_begin_epoch": start,
            "required_seconds": required,
            "admission_margin_seconds": admission_margin,
            "work_completion_margin_seconds": work - work_ended,
            "closing_margin_seconds": hard - end,
            "would_fit_at_recorded_begin": admission_margin >= 0
            and work_ended <= work and end <= hard,
        })
        measurements.setdefault((condition, kind), []).append(work_seconds)
    return {
        "counterfactual_hard_deadline": hard,
        "counterfactual_work_deadline": work,
        "other_registered_seconds": other_registered_seconds,
        "all_fit_at_recorded_begin": all(row["would_fit_at_recorded_begin"] for row in rows),
        "minimum_admission_margin_seconds": min(
            (row["admission_margin_seconds"] for row in rows), default=None
        ),
        "units": rows,
    }


def audit_legacy_2021() -> dict:
    """Verify original evidence and reconstruct the shared admission boundary."""
    root = verified_legacy_completed_root("wf-2021")
    if root is None:
        raise ValueError("Pinned 2021 historical root absent")
    ledger = root / "ledger.jsonl"
    state = json.loads(ledger.read_text().splitlines()[-1])
    units = state["units"]
    if len(units) != 99:
        raise ValueError("Expected 99 accepted 2021 units")
    for unit in units:
        work = root / unit["run_id"]
        checkpoint = Path(unit["checkpoint"]) / "state.pt"
        paths = (
            (checkpoint, "checkpoint_sha256"),
            (work / f"unit-{unit['unit']}.json", "report_sha256"),
            (work / f"request-{unit['unit']}.json", "request_sha256"),
        )
        for path, field in paths:
            if (not path.resolve().is_relative_to(root.resolve())
                    or not path.is_file()
                    or hashlib.sha256(path.read_bytes()).hexdigest() != unit[field]):
                raise ValueError(f"OOS 2021 evidence hash mismatch: {field}")
    journal_path = ROOT / "artifacts/shared-pilot-budget" / PREP_NAME
    with WFCostSessionJournal(journal_path, campaign=PREP_CAMPAIGN,
                              read_only=True) as journal:
        if len(journal.sessions) != 2:
            raise ValueError("Unexpected OOS preparation session count")
        first = journal.sessions[0]
        if (first["end"] is None or first["end"]["status"] != "ready"
                or not first["start"]["epoch"] <= units[0]["start"]
                or not units[-1]["end"] <= first["end"]["epoch"]):
            raise ValueError("OOS preparation did not cover all accepted units")
        preparation_start = first["start"]["epoch"]
    local_day = datetime.fromtimestamp(preparation_start, LA_PAZ).date()
    nine = datetime.combine(local_day, time(9), LA_PAZ).timestamp()
    reconstruction = reconstruct_admissions(
        units, preparation_start=preparation_start, nine_epoch=nine
    )
    return {
        "scope": "counterfactual_registered_budget_only; not a retroactive supervisor pass",
        "legacy_root": str(root),
        "frozen_root": str(ROOT / "artifacts/oos-v12-training-wf-2021-01"),
        "ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
        "pinned_ledger_sha256": LEGACY_COMPLETED_ROOTS["wf-2021"]["ledger_sha256"],
        "preparation_journal_sha256": hashlib.sha256(journal_path.read_bytes()).hexdigest(),
        "integrity": {"ledger_chain": "verified", "checkpoints": 99,
                      "reports": 99, "requests": 99},
        "preparation_start_epoch": preparation_start,
        "reconstruction": reconstruction,
        "uncertainty": [
            "The exact admit() timestamps were not logged; recorded unit begin is later.",
            "The missing shared lock cannot prove that no unregistered contender attempted entry.",
            "Other registered debit is set to zero based on the available preflight and ledgers.",
        ],
    }
