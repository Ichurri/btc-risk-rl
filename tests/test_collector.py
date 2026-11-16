"""Synthetic collector integrity: no files of market data are read."""

from dataclasses import replace

import numpy as np
import pytest


def fixture(config):
    from btc_risk_rl.agents.collector import Collector
    from btc_risk_rl.agents.models import Actor, FrozenPolicy
    from btc_risk_rl.agents.synthetic import SyntheticMarket

    source = SyntheticMarket(config, routes=3)
    policy = FrozenPolicy(Actor(hidden=4, seed=3), generation=0)
    return source, policy, Collector(source, seed=11, run_id="synthetic-test")


def test_fragments_preserve_identity_clock_portfolio_and_rng(config):
    from btc_risk_rl.agents.collector import Collector

    source, policy, collector = fixture(config)
    whole = Collector(source, seed=11, run_id="synthetic-test")
    fragmented = collector.collect(policy, role="A", iteration=0, count=2, fragment_steps=37)
    direct = whole.collect(policy, role="A", iteration=0, count=2, fragment_steps=180)
    assert len({x.realization for x in fragmented}) == 2
    for left, right in zip(fragmented, direct):
        assert left.policy_version == right.policy_version == policy.version
        assert left.route_id == right.route_id
        for field in ("observations", "actions", "log_probs", "rewards", "times"):
            np.testing.assert_array_equal(getattr(left, field), getattr(right, field))
        assert left.observations.shape == (181, 13)
        assert left.observations[-1, 12] == 0
        assert left.terminated[-1] and not left.truncated.any()
        with pytest.raises(ValueError):
            left.rewards[0] = 999


def test_assembly_rejects_mixed_policy_realization_route_and_gaps(config):
    from btc_risk_rl.agents.collector import assemble

    _, policy, collector = fixture(config)
    trajectory = collector.collect(policy, role="Q", iteration=0, count=1)[0]
    fragments = [trajectory.fragment(0, 60), trajectory.fragment(60, 180)]
    assert assemble(fragments).realization == trajectory.realization
    for field, value in [
        ("policy_version", "other"),
        ("realization", "other"),
        ("route_id", "other"),
        ("start", 59),
    ]:
        broken = [fragments[0], replace(fragments[1], **{field: value})]
        with pytest.raises(ValueError):
            assemble(broken)
    with pytest.raises(ValueError):
        assemble(fragments[:1])


def test_auxiliary_streams_cannot_shift_A(config):
    from btc_risk_rl.agents.collector import Collector

    source, policy, c = fixture(config)
    reference = Collector(source, seed=11, run_id="synthetic-test")
    c.collect(policy, role="Q", iteration=0, count=3)
    c.collect(policy, role="B", iteration=1, count=2)
    a = c.collect(policy, role="A", iteration=0, count=2)
    b = reference.collect(policy, role="A", iteration=0, count=2)
    for x, y in zip(a, b):
        np.testing.assert_array_equal(x.actions, y.actions)
        assert x.route_id == y.route_id
    with pytest.raises(ValueError, match="reused"):
        c.collect(policy, role="A", iteration=0, count=2)


def test_batch_failure_aborts_without_selective_replacement(config, monkeypatch):
    from btc_risk_rl.agents.collector import BatchAbort

    source, policy, collector = fixture(config)
    calls = []
    original = source.environment

    def broken(route):
        env = original(route)
        original_step = env.step

        def step(action):
            calls.append(action)
            if len(calls) == 185:
                raise ValueError("injected failure")
            return original_step(action)

        env.step = step
        return env

    monkeypatch.setattr(source, "environment", broken)
    with pytest.raises(BatchAbort) as error:
        collector.collect(policy, role="A", iteration=0, count=3)
    assert len(calls) == 185
    assert error.value.diagnostic["completed_trajectories"] == 1
    assert error.value.diagnostic["replica"] == 1
    assert collector.failed
    with pytest.raises(ValueError, match="failed"):
        collector.collect(policy, role="Q", iteration=1, count=1)


def test_non_synthetic_source_is_blocked_before_access(config):
    from btc_risk_rl.agents.collector import Collector

    class MarketSource:
        def environment(self, _):
            raise AssertionError("Must not read market data")

    with pytest.raises(ValueError, match="synthetic"):
        Collector(MarketSource(), seed=1, run_id="blocked")


def test_mutated_snapshot_invalidates_batch(config):
    import torch

    from btc_risk_rl.agents.collector import BatchAbort

    _, policy, collector = fixture(config)
    with torch.no_grad():
        next(policy._actor.parameters()).add_(1)
    with pytest.raises(BatchAbort, match="Frozen policy changed"):
        collector.collect(policy, role="Q", iteration=0, count=1)
    assert collector.transitions == 0


def test_assembly_rejects_changed_boundary_state_and_early_terminal(config):
    from btc_risk_rl.agents.collector import assemble

    _, policy, c = fixture(config)
    t = c.collect(policy, role="A", iteration=0, count=1)[0]
    a, b = t.fragment(0, 60), t.fragment(60, 180)
    obs = b.observations.copy()
    obs[0, 10] += 0.01
    with pytest.raises(ValueError, match="Discontinuous"):
        assemble([a, replace(b, observations=obs)])
    terminal = a.terminated.copy()
    terminal[-1] = True
    with pytest.raises(ValueError, match="Censored"):
        assemble([replace(a, terminated=terminal), b])


@pytest.mark.parametrize("reason", ["collection_window", "segment_boundary", "partition_boundary"])
def test_terminal_provenance_is_retained_separately(config, monkeypatch, reason):
    from btc_risk_rl.config import STEP_MS, utc_ms
    from btc_risk_rl.env.trading import TradingEnv

    source, policy, c = fixture(config)

    def environment(route):
        p = source.path(route)
        if reason == "partition_boundary":
            p = replace(
                p, times=p.times + utc_ms(config.data.validation_start) - STEP_MS - p.times[-1]
            )
        return TradingEnv(replace(p, end_reason=reason), config)

    monkeypatch.setattr(source, "environment", environment)
    t = c.collect(policy, role="A", iteration=0, count=1, fragment_steps=37)[0]
    assert t.end_reason == reason and t.terminated[-1] and not t.truncated.any()


def test_versioned_serialization_roundtrip_and_schema_rejection(config, tmp_path):
    import json

    from btc_risk_rl.agents.collector import load_trajectory, save_trajectory

    _, policy, c = fixture(config)
    t = c.collect(policy, role="A", iteration=0, count=1)[0]
    path = tmp_path / "trajectory.npz"
    save_trajectory(path, t)
    back = load_trajectory(path)
    assert back.realization == t.realization and back.policy_version == t.policy_version
    assert back.route_id == t.route_id and back.end_reason == t.end_reason
    np.testing.assert_array_equal(back.observations, t.observations)
    np.testing.assert_array_equal(back.log_probs, t.log_probs)
    with pytest.raises(FileExistsError):
        save_trajectory(path, t)
    with np.load(path, allow_pickle=False) as data:
        content = {k: data[k] for k in data.files}
    meta = json.loads(content["metadata"].tobytes())
    meta["schema_version"] = "wrong"
    content["metadata"] = np.frombuffer(json.dumps(meta).encode(), dtype=np.uint8)
    damaged = tmp_path / "bad.npz"
    np.savez(damaged, **content)
    with pytest.raises(ValueError, match="schema"):
        load_trajectory(damaged)


def test_serialized_rewards_must_match_portfolio_path(config, tmp_path):
    from btc_risk_rl.agents.collector import load_trajectory, save_trajectory

    _, policy, c = fixture(config)
    t = c.collect(policy, role="A", iteration=0, count=1)[0]
    path = tmp_path / "good.npz"
    save_trajectory(path, t)
    with np.load(path, allow_pickle=False) as data:
        content = {k: data[k] for k in data.files}
    # Preserve total reward, corrupt per-transition rewards.
    content["rewards"][0] += 0.01
    content["rewards"][1] -= 0.01
    bad = tmp_path / "corrupt.npz"
    np.savez(bad, **content)
    with pytest.raises(ValueError, match="reward"):
        load_trajectory(bad)
