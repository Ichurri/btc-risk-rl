"""Synthetic H3 contract tests; no policy learning or market-file evaluation."""

from dataclasses import replace

import numpy as np
import pytest
from test_simulator import synthetic_path

from btc_risk_rl.config import STEP_MS, Config, utc_ms
from btc_risk_rl.env.trading import TradingEnv


@pytest.mark.parametrize("reason", ["collection_window", "segment_boundary", "partition_boundary"])
def test_horizon_clock_masks_and_terminal_observation(config, reason):
    path = synthetic_path(config)
    if reason == "partition_boundary":
        path = replace(
            path, times=path.times + utc_ms(config.data.validation_start) - STEP_MS - path.times[-1]
        )
    env = TradingEnv(replace(path, end_reason=reason), config)
    obs, info = env.reset()
    assert obs.shape == (13,) and obs.dtype == np.float64
    assert obs[12] == 1 and obs[10] == obs[11] == 0
    assert not info["cvar_eligible"]
    for j in range(1, 181):
        obs, _, terminal, cut, info = env.step(1.0)
        assert obs[12] == (180 - j) / 180
        assert terminal == (j == 180) and not cut
        assert info["objective_terminal"] == terminal
        assert info["bootstrap_mask"] == info["trace_mask"] == int(not terminal)
        assert info["cvar_eligible"] == info["trajectory_complete"] == terminal
        assert env.observation_space.contains(obs)
    assert info["end_reason"] == reason
    assert info["btc"] > 0 and info["delta_btc"] == 0  # no terminal liquidation
    assert obs[11] == pytest.approx(np.log(info["equity"] / 10000))
    with pytest.raises(RuntimeError):
        env.step(0)


def test_collection_checkpoint_waits_without_reset_or_extra_transition(config):
    path = synthetic_path(config)
    env, control = TradingEnv(path, config), TradingEnv(path, config)
    with pytest.raises(RuntimeError):
        env.collection_checkpoint()
    env.reset()
    control.reset()
    for j in range(180):
        action = (j % 7) / 6
        actual, expected = env.step(action), control.step(action)
        np.testing.assert_array_equal(actual[0], expected[0])
        assert actual[1:] == expected[1:]
        if j == 59:
            state, checkpoint = env.collection_checkpoint()
            np.testing.assert_array_equal(state, actual[0])
            assert checkpoint["step"] == 60
            assert checkpoint["collection_cut"] and not checkpoint["objective_terminal"]
            assert checkpoint["fragment_disposition"] == "wait_for_complete_episode"
            assert checkpoint["bootstrap_mask"] is checkpoint["trace_mask"] is None
            assert not checkpoint["cvar_eligible"]
            assert checkpoint["trajectory_start_ms"] == int(path.times[0])
            state[:] = -99  # returned snapshot must not mutate the environment
    assert actual[-1]["cvar_eligible"]
    with pytest.raises(RuntimeError):
        env.collection_checkpoint()


@pytest.mark.parametrize("reason", ["collection_window", "segment_boundary", "partition_boundary"])
def test_early_cut_is_integrity_error_not_partial_risk_sample(config, reason):
    path = synthetic_path(config)
    short = replace(
        path,
        times=path.times[:61],
        opens=path.opens[:61],
        closes=path.closes[:61],
        features=path.features[:61],
        end_reason=reason,
    )
    with pytest.raises(ValueError, match="complete indexed episode"):
        TradingEnv(short, config)


def test_continuous_clock_retains_real_portfolio_across_horizons(config):
    path = synthetic_path(config, "validation")
    env = TradingEnv(path, config)
    env.reset()
    for j in range(1, 2191):
        obs, _, terminal, cut, info = env.step(1.0)
        assert obs[12] == 1 and not terminal and cut == (j == 2190)
        assert info["bootstrap_mask"] is info["trace_mask"] is None
        assert not info["cvar_eligible"] and not info["objective_terminal"]
        assert obs[10] == 1 and obs[11] < 0  # h=1 with inherited holdings and costs
        if j in (180, 181, 360, 361, 2190):
            assert info["btc"] > 0 and info["cash"] == 0
            assert info["delta_btc"] == info["commission"] == 0
    with pytest.raises(RuntimeError):
        env.collection_checkpoint()


def test_versioned_config_enforces_adopted_contract(config):
    assert config.schema_version == 2
    assert config.environment.contract_version == "finite_horizon_v2"
    assert config.environment.gamma == 1
    assert config.environment.observation_version == "market10_portfolio2_clock1_v2"
    for key, value in [
        ("gamma", 0.99),
        ("episode_steps", 179),
        ("horizon_mode", "continuing_window_truncation"),
        ("validation_clock", "cyclic"),
    ]:
        data = config.model_dump()
        data["environment"][key] = value
        with pytest.raises(ValueError):
            Config.model_validate(data)


def legacy_config(config):
    """Explicit schema-1 fixture; not a permissive removal of unknown keys."""
    data = config.model_dump(mode="json")
    data["schema_version"] = 1
    for key in ("contract_version", "gamma", "observation_version", "validation_clock"):
        data["environment"].pop(key, None)
    data["environment"]["horizon_mode"] = "continuing_window_truncation"
    data["research"]["risk_contract_status"] = "blocked_pending_ADR_002"
    data["research"]["ppo_discount_status"] = "must_resolve_before_agent_implementation"
    return data


def test_legacy_compatibility_is_explicit_and_read_only(config):
    from copy import deepcopy

    from btc_risk_rl.data.config_compatibility import audit_config_compatibility

    legacy = legacy_config(config)
    before = deepcopy(legacy)
    report = audit_config_compatibility(legacy, config)
    assert report["mode"] == "h1_schema1_to_adr002_v2_1"
    assert legacy == before
    assert audit_config_compatibility(config.model_dump(mode="json"), config)["mode"] == "exact"


@pytest.mark.parametrize(
    "section,key,value",
    [
        ("environment", "commission", 0.002),
        ("environment", "episode_steps", 179),
        ("environment", "horizon_mode", "unknown"),
        ("data", "train_start", "2019-01-01T00:00:00Z"),
        ("features", "version", "different"),
        ("research", "training_enabled", True),
        ("environment", "gamma", 1),  # old schema may not smuggle new fields
    ],
)
def test_legacy_bridge_rejects_unapproved_differences(config, section, key, value):
    from btc_risk_rl.data.config_compatibility import audit_config_compatibility

    legacy = legacy_config(config)
    legacy[section][key] = value
    with pytest.raises(ValueError, match="Configuration mismatch"):
        audit_config_compatibility(legacy, config)
