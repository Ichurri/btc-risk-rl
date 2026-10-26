"""Supervised, synthetic-only end-to-end evaluation cost measurement."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from btc_risk_rl.agents.models import fingerprint
from btc_risk_rl.config import load_config
from btc_risk_rl.evaluation.synthetic import (
    audit_trace,
    evaluate_continuous,
    load_verified_actor,
    load_verified_scaler,
    make_synthetic_path,
    sha256,
)
from btc_risk_rl.pilots.supervisor import supervise

ROOT = Path(__file__).resolve().parents[3]
CHECKPOINT = ROOT / "artifacts/p3-approved-v1/run-00-C0-b0/checkpoint-10/state.pt"
CHECKPOINT_SHA = "0ca4fe4ea0943d05da1eb6d9e3b12ae8639c41466c6a98273b5505674e2b931c"
SHARD = ROOT / "data/processed/p2r-training-h1"
SHARD_SHA = "62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9"
SCALER_SHA = "a598a99c368f1d50bba9f78fca2f803e46d77702d05547ccc12d076771e57479"
LENGTHS = (1979, 2190, 4386)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: dict) -> None:
    if path.exists() or path.with_suffix(path.suffix + ".tmp").exists():
        raise FileExistsError(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def event(root: Path, kind: str, **details) -> None:
    with (root / "events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"utc": utc_now(), "event": kind, **details}, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def guard_public_output(path: Path, *, repo: Path = ROOT) -> None:
    try:
        relative = path.resolve().relative_to((repo / "artifacts").resolve())
    except ValueError as exc:
        raise ValueError("Synthetic output must be under artifacts") from exc
    if len(relative.parts) < 2 or not relative.parts[0].startswith("oos-synthetic-evaluation-"):
        raise ValueError("Synthetic output requires an isolated root")


def guard_worker_output(path: Path) -> None:
    try:
        path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return  # Pytest's temporary directory is outside the repository.
    guard_public_output(path)


def worker(root: Path) -> None:
    guard_worker_output(root)
    request = json.loads((root / "request.json").read_text(encoding="utf-8"))
    if (request.get("profile") != "synthetic_only"
            or request.get("checkpoint") != str(CHECKPOINT)
            or request.get("checkpoint_sha256") != CHECKPOINT_SHA
            or request.get("shard_manifest_sha256") != SHARD_SHA):
        raise ValueError("Synthetic worker request provenance mismatch")
    steps, seed = request["steps"], request["seed"]
    if type(steps) is not int or not 1 <= steps <= 4386 or type(seed) is not int:
        raise ValueError("Invalid synthetic request")
    timings = {}
    t0 = time.perf_counter()
    actor, actor_hash = load_verified_actor(CHECKPOINT, expected_sha256=CHECKPOINT_SHA)
    scaler, scaler_sha = load_verified_scaler(
        SHARD / "manifest.json", SHARD / "scaler.json", manifest_sha256=SHARD_SHA
    )
    config = load_config(ROOT / "configs/initial.toml")
    timings["checkpoint_scaler_config_load_seconds"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    path = make_synthetic_path(steps, seed=seed, scaler=scaler)
    timings["synthetic_feature_generation_seconds"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    trace = evaluate_continuous(path, actor, config)
    if fingerprint(actor) != actor_hash:
        raise ValueError("Frozen actor changed during synthetic evaluation")
    timings["continuous_accounting_seconds"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    summary = audit_trace(trace, expected_steps=steps)
    timings["worker_metrics_audit_seconds"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    temp = root / "trace.csv.tmp"
    with temp.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(trace[0]))
        writer.writeheader()
        writer.writerows(trace)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, root / "trace.csv")
    write_json(root / "worker-result.json", {
        "profile": "synthetic_only", "steps": steps, "seed": seed,
        "metrics": summary["metrics"],
        "commission_total": summary["commission_total"],
        "slippage_total": summary["slippage_total"],
        "final_equity": summary["final_equity"],
        "actor_fingerprint": actor_hash,
        "checkpoint_sha256": CHECKPOINT_SHA,
        "scaler_sha256": scaler_sha,
        "config_sha256": sha256(ROOT / "configs/initial.toml"),
        "trace_sha256": sha256(root / "trace.csv"),
        "opened_data_files": [str(CHECKPOINT), str(SHARD / "manifest.json"),
                              str(SHARD / "scaler.json"), str(ROOT / "configs/initial.toml")],
        "timings": timings,
        "worker_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    })
    print(json.dumps({"synthetic_worker": "complete", "steps": steps}), flush=True)


def read_trace(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or "step" not in reader.fieldnames:
            raise ValueError("Trace schema missing")
        return [
            {key: int(value) if key == "step" else float(value) for key, value in row.items()}
            for row in reader
        ]


def run(output: Path, *, steps: int, seed: int, checkpoint_sha: str = CHECKPOINT_SHA) -> dict:
    start = time.perf_counter()
    started_utc = utc_now()
    guard_worker_output(output)
    if type(steps) is not int or not 1 <= steps <= 4386 or type(seed) is not int:
        raise ValueError("Bounded synthetic request required")
    output.mkdir(parents=True, exist_ok=False)
    event(output, "started", steps=steps, seed=seed)
    write_json(output / "request.json", {
        "profile": "synthetic_only", "steps": steps, "seed": seed,
        "checkpoint": str(CHECKPOINT), "checkpoint_sha256": checkpoint_sha,
        "shard_manifest_sha256": SHARD_SHA,
    })
    result = supervise(
        [sys.executable, "-m", "btc_risk_rl.evaluation.synthetic_runner", "--worker", str(output)],
        output=output / "worker.log", seconds=120, rss_limit=2 * 1024**3, poll=0.1,
    )
    event(output, "supervised", status=result["status"], reason=result["reason"])
    closure = {
        "status": "failed", "profile": "synthetic_only", "steps": steps, "seed": seed,
        "supervisor": result, "started_wall_utc": started_utc,
    }
    try:
        if result["status"] != "passed":
            raise ValueError(f"Worker failed: {result['reason']}")
        worker_result = json.loads((output / "worker-result.json").read_text(encoding="utf-8"))
        if (worker_result["profile"] != "synthetic_only"
                or worker_result["steps"] != steps or worker_result["seed"] != seed
                or worker_result["checkpoint_sha256"] != CHECKPOINT_SHA
                or worker_result["scaler_sha256"] != SCALER_SHA
                or worker_result["config_sha256"] != sha256(ROOT / "configs/initial.toml")
                or worker_result["trace_sha256"] != sha256(output / "trace.csv")):
            raise ValueError("Worker report provenance or trace hash mismatch")
        audit_start = time.perf_counter()
        trace = read_trace(output / "trace.csv")
        audit = audit_trace(trace, expected_steps=steps)
        if audit["metrics"] != worker_result["metrics"]:
            raise ValueError("Parent trace recomputation differs from worker")
        if any(
            not math.isclose(audit[key], worker_result[key], rel_tol=1e-12, abs_tol=1e-9)
            for key in ("commission_total", "slippage_total", "final_equity")
        ):
            raise ValueError("Worker cost or equity report differs from parent audit")
        audit["trace_sha256"] = worker_result["trace_sha256"]
        audit["parent_audit_seconds"] = time.perf_counter() - audit_start
        write_json(output / "audit.json", audit)
        event(output, "audited", trace_sha256=audit["trace_sha256"])
        closure.update({
            "status": "completed_synthetic", "trace_sha256": audit["trace_sha256"],
            "metrics": audit["metrics"], "actor_fingerprint": worker_result["actor_fingerprint"],
            "checkpoint_sha256": CHECKPOINT_SHA,
            "scaler_sha256": worker_result["scaler_sha256"],
            "config_sha256": worker_result["config_sha256"],
            "opened_data_files": worker_result["opened_data_files"],
            "worker_timings": worker_result["timings"],
            "parent_audit_seconds": audit["parent_audit_seconds"],
        })
    except (OSError, ValueError, KeyError, TypeError) as exc:
        closure["failure"] = str(exc)
    closure["wall_seconds_before_closure"] = time.perf_counter() - start
    closure["worker_rss_peak_bytes"] = result["rss_peak_bytes"]
    closure["parent_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    closure["disk_bytes_before_closure"] = sum(p.stat().st_size for p in output.iterdir() if p.is_file())
    closure["closed_utc"] = utc_now()
    write_json(output / "closure.json", closure)
    event(output, "closed", status=closure["status"])
    return closure


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--steps", type=int, choices=LENGTHS)
    parser.add_argument("--seed", type=int, default=910031)
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker is not None:
        worker(args.worker)
        return
    if args.output is None or args.steps is None:
        parser.error("--output and --steps required")
    guard_public_output(args.output)
    closure = run(args.output, steps=args.steps, seed=args.seed)
    print(json.dumps({"root": str(args.output), "status": closure["status"],
                      "wall_seconds_before_closure": closure["wall_seconds_before_closure"]}))
    if closure["status"] != "completed_synthetic":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
