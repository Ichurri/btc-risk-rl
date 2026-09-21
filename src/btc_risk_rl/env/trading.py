"""Causal spot simulator. Collection cuts never liquidate or imply economic terminality."""

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from btc_risk_rl.config import STEP_MS, Config, utc_ms
from btc_risk_rl.env.accounting import rebalance
from btc_risk_rl.env.market import MarketPath


class TradingEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, path: MarketPath, config: Config):
        self.path, self.config = path, config
        self.initial_cash = np.float64(config.environment.initial_cash)
        self._steps = len(path.times) - 1
        lo = utc_ms(
            config.data.train_start if path.partition == "train" else config.data.validation_start
        )
        hi = utc_ms(
            config.data.validation_start if path.partition == "train" else config.data.test_start
        )
        if path.times[1] < lo or path.times[-1] >= hi:
            raise ValueError("Scored transitions cross a partition boundary")
        if path.partition == "train" and self._steps != config.environment.episode_steps:
            raise ValueError("Training path must use a complete indexed episode")
        if path.partition == "validation" and (
            path.times[1] != lo
            or path.times[-1] != hi - STEP_MS
            or self._steps != (hi - lo) // STEP_MS
        ):
            raise ValueError("Validation must be one full continuous path")
        self.action_space = spaces.Box(0.0, 1.0, shape=(1,), dtype=np.float64)
        self.observation_space = spaces.Box(
            np.array([-np.inf] * 10 + [0.0, -np.inf], dtype=np.float64),
            np.array([np.inf] * 10 + [1.0, np.inf], dtype=np.float64),
            dtype=np.float64,
        )
        self._ready = False

    def _observation(self, i, cash, btc):
        equity = cash + btc * self.path.closes[i]
        if not np.isfinite(equity) or equity <= 0:
            raise ValueError("Equity must remain finite and positive")
        obs = np.r_[
            self.path.features[i],
            btc * self.path.closes[i] / equity,
            np.log(equity) - np.log(self.initial_cash),
        ].astype(np.float64)
        if not np.isfinite(obs).all():
            raise ValueError("Nonfinite observation")
        return obs, np.float64(equity)

    def _info(self):
        return dict(
            step=self._i,
            observation_open_time_ms=int(self.path.times[self._i]),
            observation_close_time_ms=int(self.path.times[self._i] + STEP_MS - 1),
            partition=self.path.partition,
            segment_id=self.path.segment_id,
            cash=float(self._cash),
            btc=float(self._btc),
            equity=float(self._equity),
            provenance=self.path.provenance,
            adr_002_status="pending_discount_and_bootstrap",
        )

    def reset(self, *, seed=None, options=None):
        if options:
            raise ValueError("Select an accepted path before constructing the environment")
        super().reset(seed=seed)
        self._i = 0
        self._cash, self._btc = self.initial_cash, np.float64(0)
        obs, self._equity = self._observation(0, self._cash, self._btc)
        self._ready = True
        return obs, self._info()

    def step(self, action):
        if not self._ready:
            raise RuntimeError("Reset required before stepping or after a path ends")
        value = np.asarray(action, dtype=np.float64)
        if value.shape not in {(), (1,)} or not np.isfinite(value).all():
            raise ValueError("Action must be one finite target weight")
        weight = float(value.item())
        if not 0 <= weight <= 1:
            raise ValueError("Target weight must belong to [0,1]; no clipping")
        next_i = self._i + 1
        trade = rebalance(
            self._cash,
            self._btc,
            self.path.opens[next_i],
            weight,
            self.config.environment.commission,
            self.config.environment.slippage,
        )
        observation, equity = self._observation(next_i, trade.cash, trade.btc)
        reward = float(np.log(equity) - np.log(self._equity))
        if not np.isfinite(reward):
            raise ValueError("Nonfinite reward")
        previous_equity = float(self._equity)
        self._i, self._cash, self._btc, self._equity = next_i, trade.cash, trade.btc, equity
        truncated = next_i == self._steps
        self._ready = not truncated
        info = self._info()
        info.update(
            target_weight=weight,
            delta_btc=trade.delta_btc,
            execution_open_time_ms=int(self.path.times[next_i]),
            reference_price=trade.reference_price,
            execution_price=trade.execution_price,
            commission=trade.commission,
            slippage_cost=trade.slippage_cost,
            equity_previous_close=previous_equity,
            equity_open_before=trade.equity_before,
            equity_open_after=trade.equity_after,
            end_reason=self.path.end_reason if truncated else None,
        )
        return observation, reward, False, truncated, info
