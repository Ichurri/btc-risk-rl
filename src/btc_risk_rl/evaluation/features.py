"""Pure evaluation feature calculation over supplied bars; no file access.

The historical reader and its separate permission are not implemented here.
Only that future reader may supply protected arrays to this function.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from btc_risk_rl.features.market import (
    FEATURES,
    TrainScaler,
    _market_feature_values,
)

TRAIN_END_EXCLUSIVE = pd.Timestamp("2023-01-01T00:00:00Z")
WARMUP_BARS = 42


def evaluation_features(frame: pd.DataFrame, scaler: TrainScaler) -> pd.DataFrame:
    """Apply H1 formulas and a frozen training scaler to in-memory bars.

    `frame` begins with 42 contiguous warmup bars; the output starts at the
    first eligible observation. No fit is performed and the development
    `market_features` and `TrainScaler.transform` guards stay in force.
    """
    if type(scaler) is not TrainScaler:
        raise ValueError("Training-only scaler required")
    try:
        fit_start = pd.Timestamp(scaler.fit_start)
        fit_end = pd.Timestamp(scaler.fit_end_exclusive)
    except (TypeError, ValueError) as exc:
        raise ValueError("Training-only scaler dates invalid") from exc
    if (fit_start.tzinfo is None or fit_end.tzinfo is None
            or fit_start >= fit_end or fit_end > TRAIN_END_EXCLUSIVE
            or scaler.fit_count <= 0 or scaler.columns != FEATURES):
        raise ValueError("Training-only scaler provenance invalid")
    mean = np.asarray(scaler.mean, dtype=np.float64)
    scale = np.asarray(scaler.scale, dtype=np.float64)
    if (mean.shape != (len(FEATURES),) or scale.shape != mean.shape
            or not np.isfinite(mean).all() or not np.isfinite(scale).all()
            or (scale <= 0).any()):
        raise ValueError("Training-only scaler parameters invalid")
    if len(frame) <= WARMUP_BARS:
        raise ValueError("Evaluation requires 42 warmup bars and an observation")
    raw = _market_feature_values(frame, allow_final=True).iloc[WARMUP_BARS:]
    values = raw.to_numpy(dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError("Evaluation features are nonfinite after warmup")
    result = pd.DataFrame((values - mean) / scale, index=raw.index, columns=FEATURES)
    if not np.isfinite(result.to_numpy()).all():
        raise ValueError("Evaluation normalized features are nonfinite")
    return result
