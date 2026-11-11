"""Synthetic arrays labelled as periods; no 2023/2024/2025 files opened."""

import numpy as np
import pytest

from btc_risk_rl.config import STEP_MS


def _path(partition):
    from btc_risk_rl.evaluation.historical_path import HistoricalEvaluationPath

    start, steps = ((1672531200000, 2190) if partition == "technical_2023"
                    else (1704067200000, 4386))
    times = start - STEP_MS + STEP_MS * np.arange(steps + 1, dtype=np.int64)
    return HistoricalEvaluationPath(partition, times, np.ones(steps + 1),
                                    np.ones(steps + 1), np.zeros((steps + 1, 10)))


@pytest.mark.parametrize("partition,steps", (("technical_2023", 2190),
                                           ("final_2024_2025", 4386)))
def test_only_complete_contiguous_period_is_eligible(partition, steps):
    path = _path(partition)
    assert len(path.opens) - 1 == steps
    assert path.times[-1] - path.times[0] == steps * STEP_MS


def test_gap_or_partial_period_is_rejected_before_continuous_accounting():
    from btc_risk_rl.evaluation.historical_path import HistoricalEvaluationPath

    path = _path("technical_2023")
    gap_times = path.times.copy()
    gap_times[500] += STEP_MS
    with pytest.raises(ValueError, match="contiguous"):
        HistoricalEvaluationPath(path.partition, gap_times, path.opens,
                                 path.closes, path.features)
    with pytest.raises(ValueError, match="complete"):
        HistoricalEvaluationPath(path.partition, path.times[:-1], path.opens[:-1],
                                 path.closes[:-1], path.features[:-1])


def test_path_arrays_are_immutable_and_finite():
    from btc_risk_rl.evaluation.historical_path import HistoricalEvaluationPath

    path = _path("technical_2023")
    with pytest.raises(ValueError):
        path.opens[0] = 2
    prices = path.opens.copy()
    prices[4] = np.nan
    with pytest.raises(ValueError, match="finite"):
        HistoricalEvaluationPath(path.partition, path.times, prices,
                                 path.closes, path.features)
