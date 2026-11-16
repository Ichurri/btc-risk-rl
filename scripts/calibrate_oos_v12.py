"""Cost probes for unadopted OOS v1.2; never opens validation or final data.

Each invocation is a separate process so peak RSS belongs to one phase. Outputs
must be new. The synthetic accounting loop is a timing proxy, not an evaluator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from btc_risk_rl.agents.models import Actor, fingerprint
from btc_risk_rl.config import load_config
from btc_risk_rl.data.segmentation import build_tables
from btc_risk_rl.env.accounting import rebalance
from btc_risk_rl.features.market import FEATURES, TrainScaler

ROOT = Path(__file__).resolve().parents[1]
SHARD = ROOT / "data/processed/p2r-training-h1"
CHECKPOINT = ROOT / "artifacts/p3-approved-v1/run-00-C0-b0/checkpoint-10/state.pt"
PINNED_SHARD = "62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9"
CUTOFFS = {"2021": "2020-12-02T00:00:00Z", "2022": "2021-12-02T00:00:00Z"}
LENGTHS = {
    "wf-2021-equivalent": 1979,
    "wf-2022-equivalent": 2190,
    "2023-equivalent": 2190,
    "final-equivalent": 4386,
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def guard_output(path: Path) -> None:
    relative = path.resolve().relative_to((ROOT / "artifacts").resolve())
    if len(relative.parts) < 2 or not relative.parts[0].startswith("oos-cost-v12-"):
        raise ValueError("Calibration output must be a new oos-cost-v12 artifact root")


def checked_shard() -> tuple[dict, list[str]]:
    manifest_path = SHARD / "manifest.json"
    if digest(manifest_path) != PINNED_SHARD:
        raise ValueError("Training-only shard manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["status"] != "accepted_for_p2r_training_only":
        raise ValueError("Training-only shard not accepted")
    bars = SHARD / "bars.csv"
    if digest(bars) != manifest["files"]["bars.csv"]:
        raise ValueError("Training-only bars hash mismatch")
    return manifest, [str(manifest_path), str(bars)]


def build_fold(year: str, output: Path) -> dict:
    _, opened = checked_shard()
    config = load_config(ROOT / "configs/initial.toml")
    opened.append(str(ROOT / "configs/initial.toml"))
    cutoff = pd.Timestamp(CUTOFFS[year]).timestamp() * 1000
    frame = pd.read_csv(SHARD / "bars.csv")
    if frame.partition.isin(["validation", "test"]).any():
        raise ValueError("Shard contains protected rows")
    frame = frame.loc[frame.open_time < cutoff].copy()
    if frame.empty or frame.open_time.max() >= cutoff or frame.open_time.min() < 0:
        raise ValueError("Invalid fold boundary")
    mask = frame[["open_time", "segment_id", "partition"]].copy()
    mask["reason"] = "retained"
    bars = frame.drop(columns=["segment_id", "partition"])
    t0 = time.perf_counter()
    tables = build_tables(bars, mask, config)
    rebuild_s = time.perf_counter() - t0
    feature_table = tables["features.csv"]
    features = feature_table.set_index(pd.to_datetime(feature_table.open_time, unit="ms", utc=True))[
        FEATURES
    ]
    t1 = time.perf_counter()
    scaler = TrainScaler.fit(features, pd.Timestamp(config.data.train_start), pd.Timestamp(cutoff, unit="ms", tz="UTC"))
    transformed = scaler.transform(features)
    if not np.isfinite(transformed.to_numpy()).all():
        raise ValueError("Nonfinite fold normalization")
    refit_s = time.perf_counter() - t1
    # Derived fold products live only in the new, ignored calibration root.
    t2 = time.perf_counter()
    products = {
        "normalized_features.csv": transformed.reset_index(drop=True),
        "episodes.csv": tables["episodes.csv"],
        "transitions.csv": tables["transitions.csv"],
    }
    for name, table in products.items():
        table.to_csv(output / name, index=False)
    (output / "scaler.json").write_text(
        json.dumps(scaler.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    save_s = time.perf_counter() - t2
    product_hashes = {name: digest(output / name) for name in (*products, "scaler.json")}
    product_bytes = sum((output / name).stat().st_size for name in product_hashes)
    payload = {
        "fold": year,
        "cutoff_exclusive": CUTOFFS[year],
        "input_rows_including_2017_warmup": len(frame),
        "features": len(features),
        "fit_rows": scaler.fit_count,
        "episodes": len(tables["episodes.csv"]),
        "transitions": len(tables["transitions.csv"]),
        "rebuild_seconds": rebuild_s,
        "refit_and_transform_seconds": refit_s,
        "save_fold_products_seconds": save_s,
        "fold_product_bytes": product_bytes,
        "fold_product_sha256": product_hashes,
        "scaler": scaler.to_dict(),
        "source_sha256": {str(SHARD / "manifest.json"): PINNED_SHARD, str(SHARD / "bars.csv"): digest(SHARD / "bars.csv")},
        "opened_files": opened,
    }
    return payload


def load_actor() -> tuple[Actor, dict]:
    if not CHECKPOINT.is_file():
        raise ValueError("Fixed P3 checkpoint absent")
    t0 = time.perf_counter()
    state = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
    deserialize_s = time.perf_counter() - t0
    weights = state["actor"]
    hidden = int(weights["net.0.weight"].shape[0])
    actor = Actor(hidden=hidden, seed=0).eval().requires_grad_(False)
    t1 = time.perf_counter()
    actor.load_state_dict(weights, strict=True)
    load_weights_s = time.perf_counter() - t1
    return actor, {
        "checkpoint_path": str(CHECKPOINT),
        "checkpoint_sha256": digest(CHECKPOINT),
        "checkpoint_bytes": CHECKPOINT.stat().st_size,
        "actor_fingerprint": fingerprint(actor),
        "deserialize_seconds": deserialize_s,
        "load_weights_seconds": load_weights_s,
        "opened_files": [str(CHECKPOINT)],
    }


def synthetic_walk(label: str, output: Path) -> dict:
    actor, checkpoint = load_actor()
    steps = LENGTHS[label]
    rng = np.random.default_rng(910031)
    # Fabricated features and prices; no market path or dates are read.
    features = rng.normal(0, 0.02, (steps + 1, 10)).astype(np.float64)
    opens = 10000 * np.exp(np.cumsum(rng.normal(0, 0.004, steps + 1)))
    closes = opens * np.exp(rng.normal(0, 0.002, steps + 1))
    cash, btc, initial = 10000.0, 0.0, 10000.0
    equity = cash
    simple_returns = np.empty(steps, dtype=np.float64)
    action_digest = hashlib.sha256()
    t0 = time.perf_counter()
    for i in range(steps):
        observation = np.r_[features[i], btc * closes[i] / equity, math.log(equity / initial), 1.0]
        action = actor.deterministic_action(observation)
        action_digest.update(np.float64(action).tobytes())
        trade = rebalance(cash, btc, opens[i + 1], action, 0.001, 0.0005)
        cash, btc = trade.cash, trade.btc
        next_equity = cash + btc * closes[i + 1]
        simple_returns[i] = next_equity / equity - 1
        equity = next_equity
        if not np.isfinite(equity) or equity <= 0:
            raise ValueError("Nonfinite synthetic equity")
    walk_s = time.perf_counter() - t0
    t1 = time.perf_counter()
    result_path = output / "simple_returns.npy"
    np.save(result_path, simple_returns, allow_pickle=False)
    save_s = time.perf_counter() - t1
    return {
        "label": label,
        "steps": steps,
        "synthetic_only": True,
        "one_continuous_portfolio": True,
        "clock": 1.0,
        "walk_seconds": walk_s,
        "save_returns_seconds": save_s,
        "return_file": str(result_path),
        "return_sha256": digest(result_path),
        "action_sha256": action_digest.hexdigest(),
        "final_synthetic_equity": equity,
        "checkpoint": checkpoint,
    }


def audit(path: Path) -> dict:
    guard_output(path)
    manifest = json.loads((path / "result.json").read_text(encoding="utf-8"))
    if not manifest.get("synthetic_only") or manifest.get("phase") not in {
        "synthetic-wf-2021-equivalent", "synthetic-wf-2022-equivalent",
        "synthetic-2023-equivalent", "synthetic-final-equivalent"
    }:
        raise ValueError("Only synthetic calibration returns may be audited")
    data_path = path / "simple_returns.npy"
    if not data_path.is_file():
        raise ValueError("No synthetic return file")
    t0 = time.perf_counter()
    values = np.load(data_path, allow_pickle=False)
    if (values.ndim != 1 or len(values) != manifest["steps"]
            or len(values) not in LENGTHS.values() or not np.isfinite(values).all()
            or digest(data_path) != manifest["return_sha256"]):
        raise ValueError("Invalid synthetic returns")
    downside = math.sqrt(float(np.mean(np.minimum(values, 0) ** 2)))
    sortino = math.sqrt(2190) * float(np.mean(values)) / downside if downside > 0 else None
    metrics_s = time.perf_counter() - t0
    t1 = time.perf_counter()
    file_hash = digest(data_path)
    disk_bytes = sum(p.stat().st_size for p in path.iterdir() if p.is_file())
    audit_s = time.perf_counter() - t1
    return {"synthetic_only": True, "periods": len(values), "mean_simple_return": float(np.mean(values)), "downside_deviation": downside, "sortino_annualized_synthetic": sortino, "metrics_seconds": metrics_s, "audit_seconds": audit_s, "return_sha256": file_hash, "disk_bytes_before_report": disk_bytes, "opened_files": [str(data_path)]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=[
        "fold-2021", "fold-2022", "checkpoint", "synthetic-wf-2021-equivalent",
        "synthetic-wf-2022-equivalent", "synthetic-2023-equivalent",
        "synthetic-final-equivalent", "audit"
    ], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--input", type=Path, help="Synthetic output directory for audit phase")
    args = parser.parse_args()
    guard_output(args.output)
    if args.output.exists():
        raise ValueError("Output must be a new directory")
    if args.phase == "audit" and (args.input is None or not args.input.is_dir()):
        raise ValueError("Audit requires an existing synthetic directory")
    args.output.mkdir(parents=True)
    started = datetime.now(timezone.utc).isoformat()
    total_start = time.perf_counter()
    if args.phase.startswith("fold-"):
        result = build_fold(args.phase.removeprefix("fold-"), args.output)
    elif args.phase == "checkpoint":
        _, result = load_actor()
    elif args.phase.startswith("synthetic-"):
        result = synthetic_walk(args.phase.removeprefix("synthetic-"), args.output)
    else:
        result = audit(args.input)
    result.update({"phase": args.phase, "started_utc": started, "total_seconds_before_report": time.perf_counter() - total_start, "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, "free_disk_bytes_before_report": shutil.disk_usage(args.output).free, "source_commit": os.environ.get("CALIBRATION_SOURCE_COMMIT", "uncommitted")})
    report = args.output / "result.json"
    report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"phase": args.phase, "result": str(report), "sha256": digest(report), "seconds": result["total_seconds_before_report"]}, sort_keys=True))


if __name__ == "__main__":
    main()
