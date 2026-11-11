"""One verified continuous evaluation unit, with no public access entry point.

The caller must first authorize the partition, audit the source manifest,
verify the training ledger, and load the frozen training scaler. This unit
does not acquire data or take optimizer steps.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

from btc_risk_rl.agents.models import fingerprint
from btc_risk_rl.evaluation.checkpoint_read import load_oos_final_actor
from btc_risk_rl.evaluation.export_reader import load_evaluation_export
from btc_risk_rl.evaluation.historical_path import PERIODS, evaluate_in_memory
from btc_risk_rl.evaluation.synthetic import audit_trace


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def evaluate_verified_unit(export_root: Path, checkpoint: Path, output_root: Path, *,
                           partition: str, export_manifest_sha256: str,
                           source_manifest_sha256: str, scaler, scaler_sha256: str,
                           run_id: str, seed: int, condition: str,
                           checkpoint_state_sha256: str, settings: dict,
                           source_identity: dict, actor_updates: int,
                           critic_updates: int, config: object) -> dict:
    """Evaluate an explicitly pinned unit; reject existing output evidence.

    No historical caller is enabled. Tests provide only invented exports and
    checkpoints. A future gated caller must pin all expected values itself.
    """
    output_root = Path(output_root)
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError(output_root)
    export_root = Path(export_root)
    manifest_path = export_root / "manifest.json"
    if export_root.is_symlink() or manifest_path.is_symlink():
        raise ValueError("Evaluation export symlinks are forbidden")
    raw_manifest = manifest_path.read_bytes()
    if _sha(raw_manifest) != export_manifest_sha256:
        raise ValueError("Evaluation export manifest hash mismatch")
    manifest = json.loads(raw_manifest)
    if (type(manifest) is not dict
            or manifest.get("source_manifest_sha256") != source_manifest_sha256):
        raise ValueError("Evaluation source manifest identity mismatch")

    actor, actor_meta = load_oos_final_actor(
        checkpoint, expected_state_sha256=checkpoint_state_sha256,
        expected_run_id=run_id, expected_seed=seed,
        expected_condition=condition, expected_settings=settings,
        expected_source_identity=source_identity,
        expected_actor_updates=actor_updates,
        expected_critic_updates=critic_updates,
    )
    path, export_meta = load_evaluation_export(
        export_root, partition=partition,
        expected_manifest_sha256=export_manifest_sha256, scaler=scaler,
        expected_scaler_sha256=scaler_sha256,
    )
    result = evaluate_in_memory(path, actor, config)
    if fingerprint(actor) != actor_meta["actor_fingerprint"]:
        raise ValueError("Evaluation changed the frozen actor")
    metrics = result["metrics"]
    if (metrics["sortino_annualized"] is None
            or not math.isfinite(metrics["sortino_annualized"])):
        raise ValueError("Evaluation primary Sortino undefined")

    output_root.mkdir(parents=True, exist_ok=False)
    trace_path = output_root / "trace.jsonl"
    with trace_path.open("x", encoding="utf-8") as stream:
        for row in result["trace"]:
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    trace_raw = trace_path.read_bytes()
    persisted = [json.loads(line) for line in trace_raw.splitlines()]
    audited = audit_trace(
        persisted, expected_steps=result["steps"],
        fee=config.environment.commission,
        slip=config.environment.slippage,
    )
    if audited["metrics"] != metrics:
        raise ValueError("Persisted evaluation metrics disagree")
    report = {
        "status": "completed", "audit_accepted": True,
        "profile": "main-2018-2022", "partition": partition,
        "run_id": run_id, "seed": seed, "condition": condition,
        "steps": result["steps"], "boundary": actor_meta["boundary"],
        "sortino_annualized": metrics["sortino_annualized"],
        "metrics": metrics,
        "commission_total": result["commission_total"],
        "slippage_total": result["slippage_total"],
        "trace_sha256": _sha(trace_raw),
        "checkpoint_state_sha256": checkpoint_state_sha256,
        "checkpoint_manifest_sha256": actor_meta["manifest_sha256"],
        "actor_fingerprint": actor_meta["actor_fingerprint"],
        "export_manifest_sha256": export_manifest_sha256,
        "source_manifest_sha256": export_meta["source_manifest_sha256"],
        "training_scaler_sha256": scaler_sha256,
    }
    temporary = output_root / "report.json.tmp"
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, output_root / "report.json")
    return report


def read_verified_unit_report(output_root: Path, *, expected_run_id: str,
                              expected_seed: int, expected_condition: str,
                              expected_partition: str,
                              expected_checkpoint_sha256: str,
                              expected_export_manifest_sha256: str,
                              config: object) -> dict:
    """Recompute the persisted trace before using a report in comparisons."""
    output_root = Path(output_root)
    if (output_root.is_symlink() or (output_root / "report.json").is_symlink()
            or (output_root / "trace.jsonl").is_symlink()):
        raise ValueError("Evaluation report symlink invalid")
    if expected_partition not in PERIODS:
        raise ValueError("Evaluation report partition invalid")
    report = json.loads((output_root / "report.json").read_text(encoding="utf-8"))
    if (type(report) is not dict
            or report.get("status") != "completed"
            or report.get("audit_accepted") is not True
            or report.get("profile") != "main-2018-2022"
            or report.get("run_id") != expected_run_id
            or report.get("seed") != expected_seed
            or report.get("condition") != expected_condition
            or report.get("partition") != expected_partition
            or report.get("steps") != PERIODS[expected_partition][2]
            or report.get("boundary") != "after_dual_and_D"
            or report.get("checkpoint_state_sha256") != expected_checkpoint_sha256
            or report.get("export_manifest_sha256") != expected_export_manifest_sha256):
        raise ValueError("Evaluation report identity mismatch")
    raw_trace = (output_root / "trace.jsonl").read_bytes()
    if _sha(raw_trace) != report.get("trace_sha256"):
        raise ValueError("Evaluation trace hash mismatch")
    trace = [json.loads(line) for line in raw_trace.splitlines()]
    audit = audit_trace(trace, expected_steps=report["steps"],
                        fee=config.environment.commission,
                        slip=config.environment.slippage)
    metrics = audit["metrics"]
    if (metrics != report.get("metrics")
            or metrics["sortino_annualized"] != report.get("sortino_annualized")
            or not math.isclose(audit["commission_total"], report["commission_total"],
                                rel_tol=1e-12, abs_tol=1e-9)
            or not math.isclose(audit["slippage_total"], report["slippage_total"],
                                rel_tol=1e-12, abs_tol=1e-9)):
        raise ValueError("Evaluation report metrics disagree with trace")
    return report
