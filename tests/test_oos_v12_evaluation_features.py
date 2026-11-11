"""Synthetic-only feature parity; no protected market files are read."""

import numpy as np
import pandas as pd
import pytest

from btc_risk_rl.features.market import FEATURES, TrainScaler, market_features


def _synthetic_bars(start: str, length: int = 60) -> pd.DataFrame:
    index = pd.date_range(start, periods=length, freq="4h", tz="UTC")
    close = 100 + np.arange(length, dtype=float) * 0.2
    return pd.DataFrame({
        "open": close - 0.1, "high": close + 0.3,
        "low": close - 0.4, "close": close,
        "volume": 50 + np.arange(length, dtype=float),
    }, index=index)


def test_evaluation_features_match_h1_on_synthetic_development_bars():
    from btc_risk_rl.evaluation.features import evaluation_features

    bars = _synthetic_bars("2022-01-01")
    raw = market_features(bars)
    scaler = TrainScaler.fit(raw.iloc[42:], raw.index[42], pd.Timestamp("2022-02-01T00:00:00Z"))
    actual = evaluation_features(bars, scaler)
    expected = scaler.transform(raw.iloc[42:])
    assert list(actual.columns) == FEATURES
    np.testing.assert_array_equal(actual.to_numpy(), expected.to_numpy())


def test_final_dated_synthetic_features_do_not_refit_or_relax_training_guard():
    from btc_risk_rl.evaluation.features import evaluation_features

    training = _synthetic_bars("2022-01-01")
    raw = market_features(training)
    scaler = TrainScaler.fit(raw.iloc[42:], raw.index[42], pd.Timestamp("2022-02-01T00:00:00Z"))
    before = scaler.to_dict()
    final_bars = _synthetic_bars("2024-01-01")
    with pytest.raises(ValueError, match="Final test is reserved"):
        market_features(final_bars)
    actual = evaluation_features(final_bars, scaler)
    assert actual.shape == (18, len(FEATURES))
    assert np.isfinite(actual.to_numpy()).all()
    assert scaler.to_dict() == before


def test_evaluation_features_require_warmup_and_contiguous_bars():
    from btc_risk_rl.evaluation.features import evaluation_features

    bars = _synthetic_bars("2022-01-01")
    raw = market_features(bars)
    scaler = TrainScaler.fit(raw.iloc[42:], raw.index[42], pd.Timestamp("2022-02-01T00:00:00Z"))
    with pytest.raises(ValueError, match="42 warmup"):
        evaluation_features(bars.iloc[:42], scaler)
    gapped = bars.drop(bars.index[20])
    with pytest.raises(ValueError, match="missing bars"):
        evaluation_features(gapped, scaler)


def test_evaluation_features_reject_scaler_fit_from_future():
    from btc_risk_rl.evaluation.features import evaluation_features

    bars = _synthetic_bars("2022-01-01")
    raw = market_features(bars)
    scaler = TrainScaler.fit(raw.iloc[42:], raw.index[42], pd.Timestamp("2022-02-01T00:00:00Z"))
    unsafe = TrainScaler(scaler.columns, scaler.mean, scaler.scale,
                         scaler.fit_start, "2024-01-01T00:00:00+00:00", scaler.fit_count)
    with pytest.raises(ValueError, match="Training-only scaler"):
        evaluation_features(bars, unsafe)
