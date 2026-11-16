"""Controlled, synthetic WF 05 worker process for integration tests only."""

import os
import sys
from pathlib import Path
from types import SimpleNamespace


def controlled_source():
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.agents.synthetic import SyntheticMarket
    from btc_risk_rl.config import load_config
    from btc_risk_rl.pilots.wf_cost import SHARD_MANIFEST_SHA256

    config = load_config(Path("configs/initial.toml"))
    fabricated = SyntheticMarket(config, routes=1)
    source = TrainingMarket.__new__(TrainingMarket)
    source.config = config
    source._view = SimpleNamespace(training_path=fabricated.path)
    source.route_ids = (0,)
    source.audit = {"normalizer_refitted": False,
                    "validation_observations_loaded": False}
    source._identity = {
        "profile": source.profile, "fold": "2021", "manifest_sha256": "synthetic-only",
        "training_shard_manifest_sha256": SHARD_MANIFEST_SHA256,
        "scaler_sha256": "synthetic-only", "files": {},
    }
    return source


def small_settings():
    from btc_risk_rl.pilots.wf_cost import WFCostSettings

    original = WFCostSettings.__post_init__
    try:
        WFCostSettings.__post_init__ = lambda self: None
        return WFCostSettings(hidden=4, iterations=1, n_q=2, n_a=4, n_b=2,
                              actor_epochs=2, critic_epochs=4, minibatch=1,
                              fragment_steps=180)
    finally:
        WFCostSettings.__post_init__ = original


def main():
    from btc_risk_rl.pilots import wf_cost, wf_cost_source
    from btc_risk_rl.pilots import wf_cost_replacement_05_exec as profile
    from btc_risk_rl.pilots import wf_cost_replacement_05_worker as worker

    root, request = sys.argv[1:]
    wf_cost.WFCostSettings.__post_init__ = lambda self: None
    settings_type = wf_cost.WFCostSettings
    small = dict(hidden=4, iterations=1, n_q=2, n_a=4, n_b=2,
                 actor_epochs=2, critic_epochs=4, minibatch=1, fragment_steps=180)
    profile.WFCostSettings = lambda **values: settings_type(**{**small, **values})
    profile.CAMPAIGN = Path(root)
    profile.require_campaign = lambda: {"synthetic_fixture": True}
    profile.EXPECTED = {"2021": (1, 2), "2022": (1, 2)}
    wf_cost_source.build_fold_source = lambda fold: controlled_source()
    sys.argv = [sys.argv[0], request]
    worker.main()
    print(os.getpid())


if __name__ == "__main__":
    main()
