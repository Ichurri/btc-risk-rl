"""In-memory temporal guard for a future historical evaluation reader.

It has no file loader or data access permission. Tests use fabricated arrays.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from btc_risk_rl.config import STEP_MS
from btc_risk_rl.evaluation.synthetic import (
    audit_trace,
    evaluate_continuous,
)

PERIODS = {
    "technical_2023": (1672531200000, 1704067200000, 2190),
    "final_2024_2025": (1704067200000, 1767225600000, 4386),
}


@dataclass(frozen=True)
class HistoricalEvaluationPath:
    partition: str
    times: np.ndarray
    opens: np.ndarray
    closes: np.ndarray
    features: np.ndarray

    def __post_init__(self):
        if self.partition not in PERIODS:
            raise ValueError("Unknown evaluation partition")
        start, end, steps = PERIODS[self.partition]
        times = np.asarray(self.times)
        if (times.shape != (steps + 1,)
                or not np.issubdtype(times.dtype, np.integer)
                or int(times[0]) != start - STEP_MS
                or int(times[-1]) != end - STEP_MS):
            raise ValueError("Evaluation requires complete partition")
        if not (np.diff(times) == STEP_MS).all():
            raise ValueError("Evaluation path must be contiguous")
        frozen_times = np.array(times, dtype=np.int64, copy=True)
        frozen_times.setflags(write=False)
        object.__setattr__(self, "times", frozen_times)
        for name, shape in (("opens", (steps + 1,)),
                            ("closes", (steps + 1,)),
                            ("features", (steps + 1, 10))):
            array = np.array(getattr(self, name), dtype=np.float64, copy=True)
            if array.shape != shape or not np.isfinite(array).all():
                raise ValueError(f"Evaluation {name} must be finite and complete")
            if name in {"opens", "closes"} and (array <= 0).any():
                raise ValueError("Evaluation prices must be positive")
            array.setflags(write=False)
            object.__setattr__(self, name, array)


def evaluate_in_memory(path: HistoricalEvaluationPath, policy, config) -> dict:
    """Evaluate already verified arrays; no market file reader or permission."""
    if type(path) is not HistoricalEvaluationPath:
        raise ValueError("Complete historical evaluation path required")
    trace = evaluate_continuous(path, policy, config)
    for index, row in enumerate(trace):
        if (row["open_price"] != path.opens[index + 1]
                or row["close_price"] != path.closes[index + 1]):
            raise ValueError("Evaluation trace differs from path price")
        row["observation_ms"] = int(path.times[index])
        row["execution_ms"] = int(path.times[index + 1])
    audit = audit_trace(trace, expected_steps=len(path.times) - 1,
                        fee=config.environment.commission,
                        slip=config.environment.slippage)
    return {
        "status": "audited_in_memory",
        "partition": path.partition,
        "steps": len(trace),
        "metrics": audit["metrics"],
        "trace": trace,
        "commission_total": audit["commission_total"],
        "slippage_total": audit["slippage_total"],
    }
