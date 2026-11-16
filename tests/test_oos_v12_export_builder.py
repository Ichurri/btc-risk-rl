"""Invented bars exercise the future partition export, without real data."""

import hashlib

import numpy as np
import pandas as pd
import pytest

from btc_risk_rl.config import STEP_MS
from btc_risk_rl.evaluation.historical_path import PERIODS
from btc_risk_rl.features.market import FEATURES, TrainScaler


def _bars(partition):
    start, _, steps = PERIODS[partition]
    n = steps + 43
    times = start - 43 * STEP_MS + np.arange(n, dtype=np.int64) * STEP_MS
    prices = 100 + 0.001 * np.arange(n)
    return pd.DataFrame({
        "open_time_ms": times,
        "close_time_ms": times + STEP_MS - 1,
        "open": prices,
        "high": prices + 0.3,
        "low": prices - 0.3,
        "close": prices + 0.1,
        "volume": np.full(n, 50.0),
    })


@pytest.mark.parametrize("partition", ["technical_2023", "final_2024_2025"])
def test_invented_export_roundtrips_through_verified_reader(tmp_path, partition):
    from btc_risk_rl.evaluation.export_builder import write_evaluation_export
    from btc_risk_rl.evaluation.export_reader import load_evaluation_export

    bars = _bars(partition)
    output = tmp_path / "new-export"
    manifest = write_evaluation_export(
        bars, output, partition=partition,
        source_manifest_sha256="a" * 64, training_scaler_sha256="b" * 64,
    )
    assert manifest["status"] == "accepted"
    assert manifest["rows"] == len(bars)
    scaler = TrainScaler(FEATURES, [0.0] * 10, [1.0] * 10,
                         "2018-01-01T00:00:00+00:00", "2023-01-01T00:00:00+00:00", 10073)
    path, provenance = load_evaluation_export(
        output, partition=partition,
        expected_manifest_sha256=hashlib.sha256((output / "manifest.json").read_bytes()).hexdigest(),
        scaler=scaler, expected_scaler_sha256="b" * 64,
    )
    assert len(path.times) == PERIODS[partition][2] + 1
    assert provenance["source_manifest_sha256"] == "a" * 64
    with pytest.raises(FileExistsError):
        write_evaluation_export(bars, output, partition=partition,
                                source_manifest_sha256="a" * 64,
                                training_scaler_sha256="b" * 64)


def test_gap_rejected_without_creating_export(tmp_path):
    from btc_risk_rl.evaluation.export_builder import write_evaluation_export

    bars = _bars("technical_2023")
    bars.loc[100, "open_time_ms"] += STEP_MS
    bars.loc[100, "close_time_ms"] += STEP_MS
    output = tmp_path / "invalid-export"
    with pytest.raises(ValueError, match="contiguous"):
        write_evaluation_export(bars, output, partition="technical_2023",
                                source_manifest_sha256="a" * 64,
                                training_scaler_sha256="b" * 64)
    assert not output.exists()
