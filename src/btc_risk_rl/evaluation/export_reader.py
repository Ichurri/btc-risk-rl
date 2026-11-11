"""Read a separately pinned evaluation export after an external access gate.

This is a core parser, not a public entry point or authorization to open
historical partitions. No approved export or evaluation permit exists yet.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from btc_risk_rl.config import STEP_MS
from btc_risk_rl.evaluation.features import evaluation_features
from btc_risk_rl.evaluation.historical_path import PERIODS, HistoricalEvaluationPath

COLUMNS = ("open_time_ms", "close_time_ms", "open", "high", "low", "close", "volume")
MANIFEST_KEYS = {
    "schema", "status", "partition", "start_ms", "end_exclusive_ms",
    "warmup_bars", "rows", "bars_sha256", "training_scaler_sha256",
    "source_manifest_sha256",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _digest(value: object) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def load_evaluation_export(root: Path, *, partition: str,
                           expected_manifest_sha256: str, scaler,
                           expected_scaler_sha256: str
                           ) -> tuple[HistoricalEvaluationPath, dict]:
    """Verify exact temporal and file identity, then build an in-memory path.

    The caller must check a separate partition-specific permission and pin
    the manifest/scaler hashes before calling this function. The manifest's
    parent source hash still needs an independent source audit.
    """
    if partition not in PERIODS or not _digest(expected_manifest_sha256):
        raise ValueError("Evaluation partition or manifest pin invalid")
    root = Path(root)
    manifest_path, bars_path = root / "manifest.json", root / "bars.csv"
    if root.is_symlink() or manifest_path.is_symlink() or bars_path.is_symlink():
        raise ValueError("Evaluation export symlinks are forbidden")
    if _sha256(manifest_path) != expected_manifest_sha256:
        raise ValueError("Evaluation export manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if type(manifest) is not dict:
        raise ValueError("Evaluation export manifest must be an object")
    start, end, steps = PERIODS[partition]
    if (set(manifest) != MANIFEST_KEYS
            or manifest.get("schema") != "oos_v12_evaluation_export_v1"
            or manifest.get("status") != "accepted"
            or manifest.get("partition") != partition
            or manifest.get("start_ms") != start
            or manifest.get("end_exclusive_ms") != end
            or manifest.get("warmup_bars") != 42
            or manifest.get("rows") != steps + 43
            or manifest.get("training_scaler_sha256") != expected_scaler_sha256
            or not _digest(expected_scaler_sha256)
            or not _digest(manifest.get("bars_sha256"))
            or not _digest(manifest.get("source_manifest_sha256"))):
        raise ValueError("Evaluation export partition or provenance mismatch")
    if _sha256(bars_path) != manifest["bars_sha256"]:
        raise ValueError("Evaluation export bars hash mismatch")
    bars = pd.read_csv(bars_path, float_precision="round_trip")
    if tuple(bars.columns) != COLUMNS or len(bars) != steps + 43:
        raise ValueError("Evaluation export bars schema or count mismatch")
    times = bars["open_time_ms"].to_numpy()
    close_times = bars["close_time_ms"].to_numpy()
    if (not np.issubdtype(times.dtype, np.integer)
            or not np.issubdtype(close_times.dtype, np.integer)
            or int(times[0]) != start - 43 * STEP_MS
            or int(times[-1]) != end - STEP_MS
            or not (np.diff(times) == STEP_MS).all()
            or not (close_times == times + STEP_MS - 1).all()):
        raise ValueError("Evaluation export requires complete candles and warmup")
    prices = bars[["open", "high", "low", "close", "volume"]].to_numpy(dtype=np.float64)
    if (not np.isfinite(prices).all() or (prices[:, :4] <= 0).any()
            or (prices[:, 4] < 0).any()
            or (prices[:, 1] < np.maximum(prices[:, 0], prices[:, 3])).any()
            or (prices[:, 2] > np.minimum(prices[:, 0], prices[:, 3])).any()):
        raise ValueError("Evaluation export invalid OHLCV")
    frame = pd.DataFrame(prices, columns=["open", "high", "low", "close", "volume"],
                         index=pd.to_datetime(times, unit="ms", utc=True))
    features = evaluation_features(frame, scaler)
    path = HistoricalEvaluationPath(
        partition, times[42:], prices[42:, 0], prices[42:, 3],
        features.to_numpy(dtype=np.float64),
    )
    provenance = {
        "manifest_sha256": expected_manifest_sha256,
        "bars_sha256": manifest["bars_sha256"],
        "training_scaler_sha256": expected_scaler_sha256,
        "source_manifest_sha256": manifest["source_manifest_sha256"],
        "partition": partition,
    }
    return path, provenance
