"""Fabricated H4 fixtures; no market-file loader or market-training entry point."""

from dataclasses import dataclass
from hashlib import sha256

import numpy as np

from btc_risk_rl.config import STEP_MS, Config, utc_ms
from btc_risk_rl.env.market import MarketPath
from btc_risk_rl.env.trading import TradingEnv


class SyntheticMarket:
    profile = "synthetic"

    def __init__(self, config: Config, *, routes=3):
        if type(routes) is not int or not 1 <= routes <= 10:
            raise ValueError("Small synthetic route set required")
        self.config = config
        self.route_ids = tuple(range(routes))

    def path(self, route):
        if route not in self.route_ids:
            raise ValueError("Unknown synthetic route")
        j = np.arange(181)
        t = utc_ms(self.config.data.train_start) + (j + route * 200 - 1) * STEP_MS
        p = 100 * np.exp(0.001 * np.sin(j / 8 + route) + 0.0002 * j * (route - 1))
        features = np.sin(j[:, None] / 21 + np.arange(10)[None, :] + route)
        return MarketPath(
            t,
            p,
            p * np.exp(0.0003 * np.cos(j / 11)),
            features,
            "train",
            route,
            "collection_window",
            "synthetic_h4_generated",
        )

    def route_identity(self, route, path=None):
        path = self.path(route) if path is None else path
        h = sha256(self.config.model_dump_json().encode())
        for x in (path.times, path.opens, path.closes, path.features):
            h.update(x.tobytes())
        return f"synthetic-route-{route}:{h.hexdigest()}"

    def identity(self):
        return dict(
            profile=self.profile,
            config_sha256=sha256(self.config.model_dump_json().encode()).hexdigest(),
            routes=[self.route_identity(i) for i in self.route_ids],
            scaler_sha256=None,
        )

    def environment(self, route):
        return TradingEnv(self.path(route), self.config)


@dataclass(frozen=True)
class SyntheticSettings:
    """Test values ONLY. No approved pilot hyperparameters."""

    purpose: str = "synthetic_tests_only"
    hidden: int = 8
    iterations: int = 2
    n_a: int = 2
    n_q: int = 3
    n_b: int = 3
    actor_epochs: int = 2
    critic_epochs: int = 2
    minibatch: int = 1
    actor_lr: float = 1e-4
    critic_lr: float = 1e-3
    dual_lr: float = 0.1
    clip: float = 0.2
    bound: float = 0.0
    seed: int = 20260922
    fragment_steps: int = 60

    def __post_init__(self):
        if self.purpose != "synthetic_tests_only":
            raise ValueError("Only synthetic tests authorized")
        for key, limit in [
            ("hidden", 64),
            ("iterations", 3),
            ("n_a", 16),
            ("n_q", 16),
            ("n_b", 16),
            ("actor_epochs", 4),
            ("critic_epochs", 4),
            ("minibatch", 16),
            ("fragment_steps", 180),
        ]:
            v = getattr(self, key)
            if type(v) is not int or not 1 <= v <= limit:
                raise ValueError(f"Small synthetic {key} required")
        if type(self.seed) is not int or self.seed < 0:
            raise ValueError("Nonnegative seed required")
        if not np.isfinite(
            [self.actor_lr, self.critic_lr, self.dual_lr, self.clip, self.bound]
        ).all():
            raise ValueError("Nonfinite synthetic settings")
        if min(self.actor_lr, self.critic_lr, self.dual_lr) <= 0 or not 0 < self.clip < 1:
            raise ValueError("Invalid synthetic optimization settings")
