from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from btc_risk_rl.config import FINAL_START

FEATURES = [
    "return_1",
    "return_6",
    "return_42",
    "body",
    "range",
    "trend_6",
    "trend_42",
    "volatility_6",
    "volatility_42",
    "log_volume",
]


def market_features(frame: pd.DataFrame) -> pd.DataFrame:
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("Features require ordered, unique bars")
    if len(frame) and frame.index[-1] >= pd.Timestamp(FINAL_START):
        raise ValueError("Final test is reserved")
    if len(frame) > 1 and not (np.diff(frame.index.asi8) == 14_400_000_000_000).all():
        raise ValueError("Features cannot cross missing bars")
    c = frame.close
    r = np.log(c / c.shift(1))
    out = pd.DataFrame(index=frame.index)
    for window in (1, 6, 42):
        out[f"return_{window}"] = np.log(c / c.shift(window))
    out["body"] = np.log(c / frame.open)
    out["range"] = np.log(frame.high / frame.low)
    for window in (6, 42):
        out[f"trend_{window}"] = np.log(c / c.rolling(window).mean())
        out[f"volatility_{window}"] = r.rolling(window).std(ddof=0)
    out["log_volume"] = np.log1p(frame.volume)
    return out[FEATURES]


@dataclass(frozen=True)
class TrainScaler:
    columns: list[str]
    mean: list[float]
    scale: list[float]
    fit_start: str
    fit_end_exclusive: str
    fit_count: int

    @classmethod
    def fit(cls, features: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp):
        if start >= end or end > pd.Timestamp(FINAL_START):
            raise ValueError("Invalid development fitting boundary")
        selected = features.loc[(features.index >= start) & (features.index < end)]
        if selected.empty or not np.isfinite(selected.to_numpy()).all():
            raise ValueError("Training features are empty or nonfinite")
        scale = selected.std(ddof=0)
        scale = scale.where(scale != 0, 1.0)
        return cls(
            list(selected.columns),
            selected.mean().tolist(),
            scale.tolist(),
            start.isoformat(),
            end.isoformat(),
            len(selected),
        )

    def transform(self, features: pd.DataFrame) -> pd.DataFrame:
        if list(features.columns) != self.columns:
            raise ValueError("Feature schema mismatch")
        if len(features) and features.index.max() >= pd.Timestamp(FINAL_START):
            raise ValueError("Final test is reserved")
        return (features - np.array(self.mean)) / np.array(self.scale)

    def to_dict(self):
        return asdict(self)
