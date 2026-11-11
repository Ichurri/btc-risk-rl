"""Internal H1 adapter for a separately authorized 2023 technical gate.

This module has no public entry point. Its caller must validate a distinct
2023 permit before it is invoked. Tests use invented H1-shaped tables only.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from btc_risk_rl.config import STEP_MS
from btc_risk_rl.evaluation.historical_path import PERIODS

H1_COLUMNS = ("open_time", "open", "high", "low", "close", "volume",
              "close_time", "segment_id", "partition")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_h1_technical_bars(source: Path, *, expected_h1_manifest_sha256: str,
                           expected_raw_manifest_sha256: str) -> tuple[pd.DataFrame, dict]:
    """Verify accepted H1 bytes, then extract the exact 2023 plus context rows."""
    source = Path(source)
    manifest_path, bars_path = source / "manifest.json", source / "bars.csv"
    coverage_path = source / "coverage.json"
    if (source.is_symlink() or manifest_path.is_symlink() or bars_path.is_symlink()
            or coverage_path.is_symlink()):
        raise ValueError("H1 source symlink invalid")
    if _sha(manifest_path) != expected_h1_manifest_sha256:
        raise ValueError("H1 manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (type(manifest) is not dict
            or manifest.get("status") != "accepted"
            or manifest.get("policy") != "B_ADR_004"
            or manifest.get("acceptance_scope")
            != "development_data_under_policy_B_not_training_authorization"
            or manifest.get("final_test_accessed") is not False
            or manifest.get("sources", {}).get("raw_manifest_sha256")
            != expected_raw_manifest_sha256):
        raise ValueError("H1 manifest provenance mismatch")
    expected_bars_sha = manifest.get("files", {}).get("bars.csv")
    expected_coverage_sha = manifest.get("files", {}).get("coverage.json")
    if (not isinstance(expected_coverage_sha, str)
            or _sha(coverage_path) != expected_coverage_sha):
        raise ValueError("H1 coverage hash mismatch")
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    validation = coverage.get("validation", {}) if type(coverage) is dict else {}
    if (type(validation) is not dict
            or validation.get("expected_bars") != 2190
            or validation.get("received_bars") != 2190
            or validation.get("retained_partition_bars") != 2190
            or validation.get("segments") != 1
            or validation.get("usable_transitions") != 2190
            or validation.get("exclusions") != {
                "missing": 0, "early_close": 0, "reopening": 0
            }):
        raise ValueError("H1 validation coverage mismatch")
    if not isinstance(expected_bars_sha, str) or _sha(bars_path) != expected_bars_sha:
        raise ValueError("H1 bars hash mismatch")
    frame = pd.read_csv(bars_path, float_precision="round_trip")
    if tuple(frame.columns) != H1_COLUMNS:
        raise ValueError("H1 bars schema mismatch")
    start, end, steps = PERIODS["technical_2023"]
    lo = start - 43 * STEP_MS
    chosen = frame.loc[(frame.open_time >= lo) & (frame.open_time < end)].copy()
    if len(chosen) != steps + 43:
        raise ValueError("H1 2023 bars count incomplete")
    times = chosen.open_time.to_numpy()
    closes = chosen.close_time.to_numpy()
    if (not np.issubdtype(times.dtype, np.integer)
            or not np.issubdtype(closes.dtype, np.integer)
            or int(times[0]) != lo or int(times[-1]) != end - STEP_MS
            or not (np.diff(times) == STEP_MS).all()
            or not (closes == times + STEP_MS - 1).all()):
        raise ValueError("H1 2023 bars not contiguous complete candles")
    if (chosen.partition.iloc[:43].tolist() != ["train"] * 43
            or chosen.partition.iloc[43:].tolist() != ["validation"] * steps):
        raise ValueError("H1 2023 partition or context mismatch")
    result = chosen.rename(columns={"open_time": "open_time_ms",
                                    "close_time": "close_time_ms"})
    result = result[["open_time_ms", "close_time_ms", "open", "high", "low",
                     "close", "volume"]].reset_index(drop=True)
    return result, {
        "source_manifest_sha256": expected_h1_manifest_sha256,
        "raw_manifest_sha256": expected_raw_manifest_sha256,
        "h1_bars_sha256": expected_bars_sha,
        "partition": "technical_2023",
    }
