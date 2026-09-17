"""Strict configuration and immutable development boundary."""

import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

FINAL_START = datetime(2024, 1, 1, tzinfo=timezone.utc)
STEP_MS = 4 * 60 * 60 * 1000


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DataConfig(Strict):
    symbol: Literal["BTCUSDT"]
    interval: Literal["4h"]
    timezone: Literal["UTC"]
    warmup_start: datetime
    train_start: datetime
    validation_start: datetime
    test_start: datetime
    test_end: datetime
    endpoint: Literal["https://api.binance.com/api/v3/klines"]
    final_test_locked: Literal[True]
    missing_bar_policy: Literal["fail"]
    secondary_source_status: str

    @model_validator(mode="after")
    def boundaries(self):
        dates = [
            self.warmup_start,
            self.train_start,
            self.validation_start,
            self.test_start,
            self.test_end,
        ]
        if any(d.tzinfo is None or d.utcoffset().total_seconds() != 0 for d in dates):
            raise ValueError("All boundaries must be explicit UTC")
        if not all(a < b for a, b in zip(dates, dates[1:])):
            raise ValueError("Boundaries must be strictly chronological")
        if self.test_start != FINAL_START:
            raise ValueError("Final boundary is locked; requires a reviewed protocol change")
        if any(int(d.timestamp() * 1000) % STEP_MS for d in dates):
            raise ValueError("Boundaries must align with 4h UTC")
        return self


class FeatureConfig(Strict):
    version: Literal["market10_portfolio2_v1"]
    return_windows: tuple[Literal[1], Literal[6], Literal[42]]
    rolling_windows: tuple[Literal[6], Literal[42]]
    volatility_ddof: Literal[0]
    normalization: Literal["train_zscore_no_clip"]


class EnvConfig(Strict):
    initial_cash: float = Field(gt=0, allow_inf_nan=False)
    commission: float = Field(ge=0, lt=1, allow_inf_nan=False)
    slippage: float = Field(ge=0, lt=1, allow_inf_nan=False)
    episode_steps: int = Field(gt=0)
    action: Literal["target_btc_weight_after_costs"]
    reward: Literal["net_log_equity"]
    end_position: Literal["mark_to_market_no_liquidation"]
    horizon_mode: Literal["continuing_window_truncation"]
    cash_interest: Literal[0.0]
    accounting_dtype: Literal["float64"]


class ResearchConfig(Strict):
    conditions: tuple[Literal["C0"], Literal["C5"], Literal["C10"]]
    tail_fractions: tuple[Literal[0.05], Literal[0.10]]
    training_enabled: Literal[False]
    risk_contract_status: Literal["blocked_pending_ADR_002"]
    seeds_status: str
    budget_status: str
    trajectory_batch_status: str
    risk_bound_status: str
    ppo_discount_status: str


class Config(Strict):
    schema_version: Literal[1]
    status: Literal["initial_working_not_confirmatory"]
    data: DataConfig
    features: FeatureConfig
    environment: EnvConfig
    research: ResearchConfig
    hardware_reported: dict


def load_config(path: Path) -> Config:
    with path.open("rb") as f:
        return Config.model_validate(tomllib.load(f))


def utc_ms(value: datetime) -> int:
    if value.tzinfo is None:
        raise ValueError("Naive timestamp")
    return int(value.timestamp() * 1000)


def guard_development(start_ms: int, end_ms: int) -> None:
    if start_ms >= end_ms or end_ms > utc_ms(FINAL_START):
        raise ValueError("Development access cannot reach the reserved final test")
