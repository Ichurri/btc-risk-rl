"""Evaluation export reader tested exclusively with invented OHLCV files."""

import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from btc_risk_rl.config import STEP_MS
from btc_risk_rl.evaluation.historical_path import PERIODS
from btc_risk_rl.features.market import FEATURES, TrainScaler


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _scaler():
    return TrainScaler(FEATURES, [0.0] * 10, [1.0] * 10,
                       "2018-01-01T00:00:00+00:00", "2023-01-01T00:00:00+00:00", 10073)


def _export(tmp_path, partition="technical_2023"):
    start, end, steps = PERIODS[partition]
    n = steps + 43  # 42 context bars and 2,191/4,387 path observations.
    times = start - 43 * STEP_MS + STEP_MS * np.arange(n, dtype=np.int64)
    prices = 100.0 + np.arange(n) * 0.001
    bars = pd.DataFrame({
        "open_time_ms": times,
        "close_time_ms": times + STEP_MS - 1,
        "open": prices, "high": prices + 0.3, "low": prices - 0.3,
        "close": prices + 0.1, "volume": np.full(n, 50.0),
    })
    root = tmp_path / "invented-evaluation-export"
    root.mkdir()
    bars.to_csv(root / "bars.csv", index=False, float_format="%.17g")
    manifest = {
        "schema": "oos_v12_evaluation_export_v1", "status": "accepted",
        "partition": partition, "start_ms": start,
        "end_exclusive_ms": end, "warmup_bars": 42,
        "rows": n, "bars_sha256": _sha(root / "bars.csv"),
        "training_scaler_sha256": "a" * 64,
        "source_manifest_sha256": "b" * 64,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, sort_keys=True))
    return root, manifest


@pytest.mark.parametrize("partition", ["technical_2023", "final_2024_2025"])
def test_evaluation_export_loads_complete_synthetic_partition(tmp_path, partition):
    from btc_risk_rl.evaluation.export_reader import load_evaluation_export

    root, _ = _export(tmp_path, partition)
    path, provenance = load_evaluation_export(
        root, partition=partition, expected_manifest_sha256=_sha(root / "manifest.json"),
        scaler=_scaler(), expected_scaler_sha256="a" * 64,
    )
    assert len(path.times) == PERIODS[partition][2] + 1
    assert path.times[0] == PERIODS[partition][0] - STEP_MS
    assert path.times[-1] == PERIODS[partition][1] - STEP_MS
    assert path.features.shape == (PERIODS[partition][2] + 1, 10)
    assert provenance["bars_sha256"] == _sha(root / "bars.csv")


def test_export_identity_rejected_before_opening_bars(tmp_path, monkeypatch):
    from btc_risk_rl.evaluation.export_reader import load_evaluation_export

    root, _ = _export(tmp_path)
    opened = []
    original = pd.read_csv

    def watched(path, *args, **kwargs):
        opened.append(str(path))
        return original(path, *args, **kwargs)

    monkeypatch.setattr(pd, "read_csv", watched)
    with pytest.raises(ValueError, match="partition"):
        load_evaluation_export(root, partition="final_2024_2025",
                               expected_manifest_sha256=_sha(root / "manifest.json"),
                               scaler=_scaler(), expected_scaler_sha256="a" * 64)
    assert opened == []


def test_export_tamper_and_missing_candle_are_rejected(tmp_path):
    from btc_risk_rl.evaluation.export_reader import load_evaluation_export

    root, manifest = _export(tmp_path)
    bars = pd.read_csv(root / "bars.csv")
    bars.loc[80, "close_time_ms"] -= 60_000
    bars.to_csv(root / "bars.csv", index=False)
    with pytest.raises(ValueError, match="bars hash"):
        load_evaluation_export(root, partition="technical_2023",
                               expected_manifest_sha256=_sha(root / "manifest.json"),
                               scaler=_scaler(), expected_scaler_sha256="a" * 64)
    manifest["bars_sha256"] = _sha(root / "bars.csv")
    (root / "manifest.json").write_text(json.dumps(manifest, sort_keys=True))
    with pytest.raises(ValueError, match="complete candles"):
        load_evaluation_export(root, partition="technical_2023",
                               expected_manifest_sha256=_sha(root / "manifest.json"),
                               scaler=_scaler(), expected_scaler_sha256="a" * 64)


def test_export_rejects_gap_and_symlink_even_with_rewritten_manifest(tmp_path):
    from btc_risk_rl.evaluation.export_reader import load_evaluation_export

    root, manifest = _export(tmp_path)
    bars = pd.read_csv(root / "bars.csv")
    bars.loc[500, "open_time_ms"] += STEP_MS
    bars.loc[500, "close_time_ms"] += STEP_MS
    bars.to_csv(root / "bars.csv", index=False)
    manifest["bars_sha256"] = _sha(root / "bars.csv")
    (root / "manifest.json").write_text(json.dumps(manifest, sort_keys=True))
    with pytest.raises(ValueError, match="complete candles"):
        load_evaluation_export(root, partition="technical_2023",
                               expected_manifest_sha256=_sha(root / "manifest.json"),
                               scaler=_scaler(), expected_scaler_sha256="a" * 64)
    target = root / "original-bars.csv"
    (root / "bars.csv").rename(target)
    (root / "bars.csv").symlink_to(target)
    with pytest.raises(ValueError, match="symlinks"):
        load_evaluation_export(root, partition="technical_2023",
                               expected_manifest_sha256=_sha(root / "manifest.json"),
                               scaler=_scaler(), expected_scaler_sha256="a" * 64)


def test_full_synthetic_final_export_uses_continuous_accounting(tmp_path, config):
    from btc_risk_rl.evaluation.export_reader import load_evaluation_export
    from btc_risk_rl.evaluation.historical_path import evaluate_in_memory

    class HalfPolicy:
        calls = 0

        def deterministic_action(self, observation):
            self.calls += 1
            assert observation.shape == (13,)
            assert observation[-1] == 1
            return 0.5

    root, _ = _export(tmp_path, "final_2024_2025")
    path, _ = load_evaluation_export(
        root, partition="final_2024_2025",
        expected_manifest_sha256=_sha(root / "manifest.json"),
        scaler=_scaler(), expected_scaler_sha256="a" * 64,
    )
    policy = HalfPolicy()
    result = evaluate_in_memory(path, policy, config)
    assert result["status"] == "audited_in_memory"
    assert policy.calls == 4386
    assert result["metrics"]["periods"] == 4386
    assert result["trace"][0]["observation_ms"] == path.times[0]
    assert result["trace"][-1]["execution_ms"] == path.times[-1]
