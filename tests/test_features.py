import numpy as np
import pandas as pd
import pytest

from btc_risk_rl.features.market import FEATURES, TrainScaler, market_features


def test_features_match_independent_formula(bars):
    f = market_features(bars)
    assert list(f.columns) == FEATURES
    i = 100
    assert f.return_42.iloc[i] == pytest.approx(
        np.log(bars.close.iloc[i] / bars.close.iloc[i - 42])
    )
    expected = np.log(bars.close.iloc[i] / bars.close.iloc[i - 5 : i + 1].mean())
    assert f.trend_6.iloc[i] == pytest.approx(expected)
    returns = np.log(bars.close.to_numpy()[1:] / bars.close.to_numpy()[:-1])
    assert f.volatility_42.iloc[i] == pytest.approx(np.std(returns[i - 42 : i], ddof=0))
    assert f.iloc[42:].notna().all().all()


def test_future_mutation_and_prefix_invariance(bars):
    original = market_features(bars)
    changed = bars.copy()
    changed.loc[changed.index[150:], ["open", "high", "low", "close", "volume"]] *= 5
    pd.testing.assert_frame_equal(original.iloc[:150], market_features(changed).iloc[:150])
    pd.testing.assert_frame_equal(original.iloc[:150], market_features(bars.iloc[:150]))


def test_scaler_not_affected_by_validation(bars):
    f = market_features(bars)
    lo, hi = f.index[42], f.index[150]
    scaler = TrainScaler.fit(f, lo, hi)
    changed = f.copy()
    changed.iloc[150:] *= 1000
    assert scaler == TrainScaler.fit(changed, lo, hi)
    normalized = scaler.transform(f).loc[(f.index >= lo) & (f.index < hi)]
    np.testing.assert_allclose(normalized.mean(), 0, atol=1e-10)
    np.testing.assert_allclose(normalized.std(ddof=0), 1, atol=1e-10)


def test_constant_features_no_nan(bars):
    f = market_features(bars).iloc[42:] * 0
    scaler = TrainScaler.fit(f, f.index[0], f.index[-1])
    assert scaler.scale == [1.0] * 10
    assert np.isfinite(scaler.transform(f)).all().all()


def test_gap_and_final_test_rejected(bars):
    with pytest.raises(ValueError, match="missing"):
        market_features(bars.drop(bars.index[150]))
    future = bars.copy()
    future.index = pd.date_range("2024-01-01", periods=len(future), freq="4h", tz="UTC")
    with pytest.raises(ValueError, match="reserved"):
        market_features(future)


def test_feature_order_enforced(bars):
    f = market_features(bars).iloc[42:]
    scaler = TrainScaler.fit(f, f.index[0], f.index[-1])
    with pytest.raises(ValueError, match="schema"):
        scaler.transform(f[FEATURES[::-1]])
