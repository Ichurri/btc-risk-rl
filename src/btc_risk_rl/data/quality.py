"""Structural validation; never impute missing market prices."""

import numpy as np
import pandas as pd

from btc_risk_rl.config import STEP_MS, guard_development

COLUMNS = ["open_time", "open", "high", "low", "close", "volume", "close_time"]


def validate_rows(rows: list, start_ms: int, end_ms: int, now_ms: int) -> tuple[pd.DataFrame, dict]:
    guard_development(start_ms, end_ms)
    if start_ms % STEP_MS or end_ms % STEP_MS:
        raise ValueError("Unaligned range")
    report = {
        "status": "failed",
        "errors": [],
        "duplicates_removed": 0,
        "incomplete_removed": 0,
        "zero_volume_bars": 0,
    }
    unique = {}
    for row in rows:
        if not isinstance(row, list) or len(row) != 12:
            raise ValueError("Expected Binance kline schema with 12 fields")
        timestamp = int(row[0])
        if timestamp != float(row[0]):
            raise ValueError("Nonintegral timestamp")
        if timestamp in unique:
            if row != unique[timestamp]:
                report["errors"].append(f"Conflicting duplicate at {timestamp}")
            else:
                report["duplicates_removed"] += 1
            continue
        unique[timestamp] = row
    records = []
    for timestamp, row in sorted(unique.items()):
        if not start_ms <= timestamp < end_ms:
            raise ValueError("Data outside declared development range")
        if int(row[6]) >= now_ms:
            report["incomplete_removed"] += 1
            continue
        records.append([timestamp, *map(float, row[1:6]), int(row[6])])
    frame = pd.DataFrame(records, columns=COLUMNS)
    expected = np.arange(start_ms, end_ms, STEP_MS, dtype=np.int64)
    actual = frame.open_time.to_numpy(dtype=np.int64)
    missing = np.setdiff1d(expected, actual)
    report["missing_open_times_utc"] = [
        pd.Timestamp(int(t), unit="ms", tz="UTC").isoformat() for t in missing
    ]
    report["expected_bars"] = len(expected)
    report["actual_bars"] = len(frame)
    if len(missing):
        report["errors"].append(f"Missing {len(missing)} complete scheduled bars")
    if len(frame):
        numeric = frame[["open", "high", "low", "close", "volume"]]
        invalid = ~np.isfinite(numeric).all(axis=1)
        invalid |= (frame[["open", "high", "low", "close"]] <= 0).any(axis=1)
        invalid |= frame.volume < 0
        invalid |= frame.low > frame[["open", "close"]].min(axis=1)
        invalid |= frame.high < frame[["open", "close"]].max(axis=1)
        invalid |= frame.low > frame.high
        invalid |= frame.open_time % STEP_MS != 0
        report["invalid_ohlcv_or_open_time_count"] = int(invalid.sum())
        unusual_close = frame.close_time != frame.open_time + STEP_MS - 1
        report["nonstandard_close_times"] = [
            {
                "open_time_ms": int(row.open_time),
                "close_time_ms": int(row.close_time),
                "expected_close_time_ms": int(row.open_time + STEP_MS - 1),
            }
            for row in frame.loc[unusual_close].itertuples()
        ]
        invalid |= unusual_close
        report["invalid_open_times_ms"] = frame.loc[invalid, "open_time"].tolist()
        if invalid.any():
            report["errors"].append(f"Invalid OHLCV or timestamps in {int(invalid.sum())} bars")
        report["zero_volume_bars"] = int((frame.volume == 0).sum())
    frame.index = pd.to_datetime(frame.open_time, unit="ms", utc=True)
    frame.index.name = "timestamp"
    if not report["errors"]:
        report["status"] = "passed"
    return frame, report
