"""Accepted-market collection adapter. Exposes training paths only, no optimization."""

from hashlib import sha256

from btc_risk_rl.config import utc_ms
from btc_risk_rl.env.market import AcceptedMarket
from btc_risk_rl.env.trading import TradingEnv


class TrainingMarket:
    profile = "accepted_train_collection_only"

    def __init__(self, config, prepared, *, expected_manifest):
        self.config = config
        self._view = AcceptedMarket.training_only(
            config, prepared, expected_manifest=expected_manifest
        )
        self.route_ids = self._view.episode_ids
        self.audit = self._view.audit
        self._identity = dict(
            profile=self.profile,
            manifest_sha256=expected_manifest,
            scaler_sha256=self.audit["product_hashes"]["scaler.json"],
            files=self.audit["product_hashes"],
            config_sha256=sha256(config.model_dump_json().encode()).hexdigest(),
        )

    def identity(self):
        from copy import deepcopy

        return deepcopy(self._identity)

    def environment(self, route):
        path = self._view.training_path(route)
        if path.partition != "train" or path.times[-1] >= utc_ms(self.config.data.validation_start):
            raise ValueError("Only accepted training paths accessible")
        return TradingEnv(path, self.config)

    def route_identity(self, route, path):
        h = sha256(self._identity["manifest_sha256"].encode())
        for values in (path.times, path.opens, path.closes, path.features):
            h.update(values.tobytes())
        return f"accepted-train:{route}:{h.hexdigest()}"
