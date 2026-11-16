"""Synthetic continuous transfer probe using H3 accounting and frozen policies.

This module has no historical evaluation path or training entry point.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from btc_risk_rl.agents.models import Actor, fingerprint
from btc_risk_rl.env.accounting import rebalance
from btc_risk_rl.features.market import FEATURES, TrainScaler, market_features


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class SyntheticPath:
    opens: np.ndarray
    closes: np.ndarray
    features: np.ndarray

    def __post_init__(self):
        opens = np.asarray(self.opens, dtype=np.float64)
        closes = np.asarray(self.closes, dtype=np.float64)
        features = np.asarray(self.features, dtype=np.float64)
        if (opens.ndim != 1 or len(opens) < 2 or closes.shape != opens.shape
                or features.shape != (len(opens), 10)):
            raise ValueError("Invalid synthetic path shape")
        if (not np.isfinite(opens).all() or not np.isfinite(closes).all()
                or not np.isfinite(features).all() or (opens <= 0).any()
                or (closes <= 0).any()):
            raise ValueError("Synthetic path has nonfinite or nonpositive values")
        for name, array in (("opens", opens), ("closes", closes), ("features", features)):
            frozen = array.copy()
            frozen.setflags(write=False)
            object.__setattr__(self, name, frozen)


def make_synthetic_path(steps: int, *, seed: int, scaler: TrainScaler) -> SyntheticPath:
    if type(steps) is not int or not 1 <= steps <= 4386 or type(seed) is not int:
        raise ValueError("Bounded synthetic length and integer seed required")
    rng = np.random.default_rng(seed)
    n = steps + 43  # 42 H1 warmup bars plus one initial observation.
    opens = 10000 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    closes = opens * np.exp(rng.normal(0, 0.002, n))
    high = np.maximum(opens, closes) * 1.002
    low = np.minimum(opens, closes) * 0.998
    volume = rng.lognormal(6, 0.5, n)
    # Arbitrary 2010 synthetic clock; these are not observations from any year.
    index = pd.date_range("2010-01-01", periods=n, freq="4h", tz="UTC")
    frame = pd.DataFrame(
        {"open": opens, "high": high, "low": low, "close": closes, "volume": volume},
        index=index,
    )
    raw = market_features(frame).iloc[42:]
    normalized = scaler.transform(raw)
    if list(normalized.columns) != FEATURES:
        raise ValueError("Frozen scaler feature schema differs from H3")
    return SyntheticPath(opens[42:], closes[42:], normalized.to_numpy(dtype=np.float64))


def load_verified_actor(path: Path, *, expected_sha256: str) -> tuple[Actor, str]:
    if sha256(path) != expected_sha256:
        raise ValueError("Checkpoint hash mismatch")
    state = torch.load(path, map_location="cpu", weights_only=True)
    if not isinstance(state, dict) or "actor" not in state:
        raise ValueError("Checkpoint lacks actor state")
    weights = state["actor"]
    hidden = int(weights["net.0.weight"].shape[0])
    actor = Actor(hidden=hidden, seed=0).eval().requires_grad_(False)
    actor.load_state_dict(weights, strict=True)
    if not all(torch.isfinite(value).all() for value in actor.state_dict().values()):
        raise ValueError("Checkpoint actor has nonfinite weights")
    return actor, fingerprint(actor)


def load_verified_scaler(manifest_path: Path, scaler_path: Path, *, manifest_sha256: str):
    if sha256(manifest_path) != manifest_sha256:
        raise ValueError("Training-only manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("status") != "accepted_for_p2r_training_only"
            or manifest.get("train_end_exclusive_ms") != 1672531200000
            or sha256(scaler_path) != manifest["files"]["scaler.json"]):
        raise ValueError("Training-only scaler provenance mismatch")
    scaler = TrainScaler(**json.loads(scaler_path.read_text(encoding="utf-8")))
    if scaler.columns != FEATURES or scaler.fit_count != 10073:
        raise ValueError("Unexpected frozen scaler population or schema")
    return scaler, sha256(scaler_path)


def evaluate_continuous(path: SyntheticPath, policy, config) -> list[dict]:
    cash, btc = float(config.environment.initial_cash), 0.0
    initial = cash
    previous_equity = initial
    rows = []
    for i in range(len(path.opens) - 1):
        equity_check = cash + btc * path.closes[i]
        if not np.isclose(equity_check, previous_equity, rtol=1e-13, atol=1e-10):
            raise ValueError("Synthetic portfolio continuity failed")
        observation = np.r_[
            path.features[i], btc * path.closes[i] / previous_equity,
            math.log(previous_equity / initial), 1.0,
        ].astype(np.float64)
        action = policy.deterministic_action(observation)
        trade = rebalance(
            cash, btc, path.opens[i + 1], action,
            config.environment.commission, config.environment.slippage,
        )
        equity = trade.cash + trade.btc * path.closes[i + 1]
        if not math.isfinite(equity) or equity <= 0:
            raise ValueError("Synthetic equity is nonfinite or nonpositive")
        rows.append({
            "step": i + 1, "clock": 1.0,
            "open_price": float(path.opens[i + 1]),
            "close_price": float(path.closes[i + 1]),
            "cash_before": cash, "btc_before": btc,
            "equity_before_close": previous_equity,
            "action": action, "delta_btc": trade.delta_btc,
            "execution_price": trade.execution_price,
            "commission": trade.commission, "slippage_cost": trade.slippage_cost,
            "cash_after": trade.cash, "btc_after": trade.btc,
            "equity": float(equity),
            "simple_return": float(equity / previous_equity - 1),
            "log_reward": float(math.log(equity / previous_equity)),
        })
        cash, btc, previous_equity = trade.cash, trade.btc, equity
    return rows


def summarize_returns(values: np.ndarray) -> dict:
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ValueError("Finite one-dimensional returns required")
    if (values <= -1).any():
        raise ValueError("Nonpositive equity implied by return")
    downside = math.sqrt(float(np.mean(np.minimum(values, 0.0) ** 2)))
    mean = float(np.mean(values))
    wealth = np.r_[1.0, np.cumprod(1 + values)]
    return {
        "periods": len(values),
        "mean_simple_return_4h": mean,
        "downside_deviation_4h": downside,
        "sortino_annualized": math.sqrt(2190) * mean / downside if downside > 0 else None,
        "net_log_return_sum": float(np.log1p(values).sum()),
        "max_drawdown_fraction": float(np.max(1 - wealth / np.maximum.accumulate(wealth))),
    }


def audit_trace(trace: list[dict], *, expected_steps: int, fee=0.001, slip=0.0005) -> dict:
    if len(trace) != expected_steps:
        raise ValueError("Incomplete synthetic trace")
    previous_equity = 10000.0
    previous_cash, previous_btc = 10000.0, 0.0
    for i, row in enumerate(trace, 1):
        numeric = [value for key, value in row.items() if key != "step"]
        if not np.isfinite(numeric).all() or row["step"] != i:
            raise ValueError("Nonfinite or unordered synthetic trace")
        if row["clock"] != 1.0:
            raise ValueError("Evaluation clock is not constant one")
        if not 0 < row["action"] < 1:
            raise ValueError("Action outside open logistic-normal support")
        scale = max(1.0, abs(previous_equity))

        def close(actual, expected):
            return abs(actual - expected) <= 1e-10 * scale

        if (not close(row["cash_before"], previous_cash)
                or not close(row["btc_before"] * row["open_price"],
                             previous_btc * row["open_price"])
                or not close(row["equity_before_close"], previous_equity)):
            raise ValueError("Portfolio continuity mismatch")
        if (not close(row["cash_after"], row["cash_before"]
                      - row["delta_btc"] * row["execution_price"] - row["commission"])
                or not close(row["btc_after"] * row["open_price"],
                             (row["btc_before"] + row["delta_btc"]) * row["open_price"])):
            raise ValueError("Synthetic cashflow mismatch")
        expected_execution = row["open_price"] * (
            1 + slip if row["delta_btc"] > 0 else 1 - slip if row["delta_btc"] < 0 else 1
        )
        if (not close(row["execution_price"], expected_execution)
                or not close(row["commission"], abs(row["delta_btc"])
                             * row["execution_price"] * fee)
                or not close(row["slippage_cost"], abs(row["delta_btc"])
                             * row["open_price"] * slip)):
            raise ValueError("Synthetic cost mismatch")
        equity_at_open = row["cash_after"] + row["btc_after"] * row["open_price"]
        if equity_at_open <= 0 or abs(
            row["btc_after"] * row["open_price"] / equity_at_open - row["action"]
        ) > 1e-10:
            raise ValueError("Synthetic target weight mismatch")
        if (row["commission"] < 0 or row["slippage_cost"] < 0
                or not close(row["equity"], row["cash_after"]
                             + row["btc_after"] * row["close_price"])
                or not close(row["simple_return"], row["equity"] / previous_equity - 1)
                or not close(row["log_reward"], math.log(row["equity"] / previous_equity))):
            raise ValueError("Synthetic accounting or return mismatch")
        previous_cash, previous_btc, previous_equity = (
            row["cash_after"], row["btc_after"], row["equity"]
        )
    metrics = summarize_returns(np.array([row["simple_return"] for row in trace]))
    return {
        "accepted": True,
        "metrics": metrics,
        "commission_total": float(sum(row["commission"] for row in trace)),
        "slippage_total": float(sum(row["slippage_cost"] for row in trace)),
        "final_equity": float(previous_equity),
    }
