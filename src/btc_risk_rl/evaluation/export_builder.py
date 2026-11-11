"""Build a partition export from caller-supplied bars after an access gate.

This module has no data loader or public command. Tests supply invented bars.
The future caller must independently audit and pin the source manifest before
passing rows; the output's source hash records that provenance.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from btc_risk_rl.config import STEP_MS
from btc_risk_rl.evaluation.export_reader import COLUMNS
from btc_risk_rl.evaluation.historical_path import PERIODS


def _digest(value: str) -> bool:
    return (type(value) is str and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def write_evaluation_export(bars: pd.DataFrame, output: Path, *, partition: str,
                            source_manifest_sha256: str,
                            training_scaler_sha256: str) -> dict:
    """Accept exact four-hour coverage without filling or editing market rows."""
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    if (partition not in PERIODS or not _digest(source_manifest_sha256)
            or not _digest(training_scaler_sha256)):
        raise ValueError("Evaluation export identity invalid")
    start, end, steps = PERIODS[partition]
    if type(bars) is not pd.DataFrame or tuple(bars.columns) != COLUMNS:
        raise ValueError("Evaluation bars schema invalid")
    if len(bars) != steps + 43:
        raise ValueError("Evaluation bars count incomplete")
    times = bars["open_time_ms"].to_numpy()
    closes = bars["close_time_ms"].to_numpy()
    if (not np.issubdtype(times.dtype, np.integer)
            or not np.issubdtype(closes.dtype, np.integer)
            or int(times[0]) != start - 43 * STEP_MS
            or int(times[-1]) != end - STEP_MS
            or not (np.diff(times) == STEP_MS).all()
            or not (closes == times + STEP_MS - 1).all()):
        raise ValueError("Evaluation bars must be contiguous complete candles")
    prices = bars[["open", "high", "low", "close", "volume"]].to_numpy(dtype=np.float64)
    if (not np.isfinite(prices).all() or (prices[:, :4] <= 0).any()
            or (prices[:, 4] < 0).any()
            or (prices[:, 1] < np.maximum(prices[:, 0], prices[:, 3])).any()
            or (prices[:, 2] > np.minimum(prices[:, 0], prices[:, 3])).any()):
        raise ValueError("Evaluation bars OHLCV invalid")

    output.mkdir(parents=True, exist_ok=False)
    csv_path = output / "bars.csv"
    with csv_path.open("x", encoding="utf-8", newline="") as stream:
        bars.to_csv(stream, index=False, float_format="%.17g")
        stream.flush()
        os.fsync(stream.fileno())
    manifest = {
        "schema": "oos_v12_evaluation_export_v1", "status": "accepted",
        "partition": partition, "start_ms": start, "end_exclusive_ms": end,
        "warmup_bars": 42, "rows": len(bars),
        "bars_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "training_scaler_sha256": training_scaler_sha256,
        "source_manifest_sha256": source_manifest_sha256,
    }
    with (output / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return manifest
