"""Internal evaluation worker for one complete, already authorized policy.

The future public supervisor must check partition access, source identity,
the full 108-run roster, resources, and budget before calling this worker.
"""

from __future__ import annotations

import hashlib
import secrets
import time
from pathlib import Path

from btc_risk_rl.evaluation.historical_unit import (
    evaluate_verified_unit,
    read_verified_unit_report,
)
from btc_risk_rl.evaluation.ledger import EvaluationLedger


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_accepted_outputs(ledger: EvaluationLedger, *, config: object) -> int:
    """Check every accepted output hash and recalculate its trace metrics."""
    state = ledger.state
    for accepted in state["accepted"]:
        run = accepted["run"]
        output = ledger.root / run["run_id"]
        if _sha(output / "report.json") != accepted["report_sha256"]:
            raise ValueError("Evaluation accepted report hash mismatch")
        if _sha(output / "trace.jsonl") != accepted["trace_sha256"]:
            raise ValueError("Evaluation accepted trace hash mismatch")
        read_verified_unit_report(
            output, expected_run_id=run["run_id"], expected_seed=run["seed"],
            expected_condition=run["condition"],
            expected_partition=ledger.identity["partition"],
            expected_checkpoint_sha256=run["checkpoint_sha256"],
            expected_export_manifest_sha256=ledger.identity["export_manifest_sha256"],
            config=config,
        )
    return len(state["accepted"])


def run_one_verified_unit(ledger: EvaluationLedger, export_root: Path,
                          checkpoint: Path, *, config: object,
                          evaluation_kwargs: dict) -> dict:
    """Persist one K10 evaluation; never restart an orphaned partial unit."""
    if type(ledger) is not EvaluationLedger or type(evaluation_kwargs) is not dict:
        raise ValueError("Evaluation worker identity invalid")
    state = ledger.state
    if state["status"] == "running":
        ledger.mark_interrupted("orphaned_partial_evaluation_unit")
        raise ValueError("Evaluation unit interrupted; ledger failed")
    if state["status"] == "failed":
        raise ValueError("Evaluation ledger failed; no restart")
    if state["status"] == "completed":
        raise ValueError("Evaluation roster complete; no extra policy")
    verify_accepted_outputs(ledger, config=config)
    run = ledger.identity["roster"][state["cursor"]]
    if (evaluation_kwargs.get("partition") != ledger.identity["partition"]
            or evaluation_kwargs.get("export_manifest_sha256")
            != ledger.identity["export_manifest_sha256"]
            or evaluation_kwargs.get("run_id") != run["run_id"]
            or evaluation_kwargs.get("seed") != run["seed"]
            or evaluation_kwargs.get("condition") != run["condition"]
            or evaluation_kwargs.get("checkpoint_state_sha256")
            != run["checkpoint_sha256"]):
        raise ValueError("Evaluation worker roster or export identity mismatch")
    token = secrets.token_hex(16)
    output = ledger.root / run["run_id"]
    ledger.begin(run, token=token)
    started = time.perf_counter()
    try:
        report = evaluate_verified_unit(export_root, checkpoint, output,
                                        config=config, **evaluation_kwargs)
        checked = read_verified_unit_report(
            output, expected_run_id=run["run_id"], expected_seed=run["seed"],
            expected_condition=run["condition"],
            expected_partition=ledger.identity["partition"],
            expected_checkpoint_sha256=run["checkpoint_sha256"],
            expected_export_manifest_sha256=ledger.identity["export_manifest_sha256"],
            config=config,
        )
        if checked != report:
            raise ValueError("Evaluation report changed before acceptance")
        ledger.accept(run, token=token, report_sha256=_sha(output / "report.json"),
                      trace_sha256=_sha(output / "trace.jsonl"),
                      seconds=time.perf_counter() - started)
    except Exception as exc:
        if ledger.state["status"] == "running":
            ledger.mark_interrupted(f"unit_failed:{type(exc).__name__}:{exc}")
        raise
    return report
