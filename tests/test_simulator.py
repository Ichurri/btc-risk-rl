"""Independent accounting oracles and explicitly synthetic market paths."""

from decimal import Decimal, localcontext

import numpy as np
import pytest

from btc_risk_rl.env.accounting import rebalance


def cashflow_oracle(cash, btc, price, weight, fee, slip):
    """Decimal bisection on post-trade cashflows; no production sizing formula."""
    with localcontext() as ctx:
        ctx.prec = 60
        c, q, p, w, f, s = map(lambda x: Decimal(str(x)), (cash, btc, price, weight, fee, slip))
        buy = w > q * p / (c + q * p)
        execution = p * (1 + s if buy else 1 - s)
        lo = Decimal(0) if buy else -q
        hi = c / (execution * (1 + f)) if buy else Decimal(0)
        for _ in range(220):
            d = (lo + hi) / 2
            c_new = c - d * execution - abs(d) * execution * f
            q_new = q + d
            actual = q_new * p / (c_new + q_new * p)
            if actual < w:
                lo = d
            else:
                hi = d
        d = (lo + hi) / 2
        return [
            float(c - d * execution - abs(d) * execution * f),
            float(q + d),
            float(abs(d) * execution * f),
            float(abs(d) * p * s),
        ]


@pytest.mark.parametrize(
    "cash,btc,p,w",
    [
        (10000, 0, 100, 1),
        (10000, 0, 100, 0.6),
        (5000, 50, 100, 0.2),
        (0, 100, 100, 0),
        (0, 100, 100, 0.75),
        (1, 0.00001, 65000, 0.000001),
        (10000, 0, 100, 0.999999999999),
        (1e-8, 1e-8, 50000, 0.3),
    ],
)
def test_sizing_matches_independent_cashflow_root(cash, btc, p, w):
    trade = rebalance(cash, btc, p, w, 0.001, 0.0005)
    oracle = cashflow_oracle(cash, btc, p, w, 0.001, 0.0005)
    np.testing.assert_allclose(
        [trade.cash, trade.btc, trade.commission, trade.slippage_cost],
        oracle,
        rtol=3e-12,
        atol=1e-12,
    )
    assert trade.cash >= 0 and trade.btc >= 0
    assert trade.btc * p / (trade.cash + trade.btc * p) == pytest.approx(w, abs=2e-15)
    assert trade.cash == pytest.approx(
        cash - trade.delta_btc * trade.execution_price - trade.commission, abs=2e-11
    )
    assert trade.cash + trade.btc * p == pytest.approx(
        cash + btc * p - trade.commission - trade.slippage_cost
    )


def test_manual_all_in_then_all_out_costs():
    buy = rebalance(10000, 0, 100, 1, 0.001, 0.0005)
    q = 10000 / (100.05 * 1.001)
    assert buy.cash == 0
    assert buy.btc == pytest.approx(q)
    assert buy.commission == pytest.approx(q * 100.05 * 0.001)
    sell = rebalance(buy.cash, buy.btc, 100, 0, 0.001, 0.0005)
    assert sell.btc == 0
    assert sell.cash == pytest.approx(q * 99.95 * 0.999)
    assert sell.cash < 10000


def test_zero_cost_and_exact_no_trade():
    trade = rebalance(10000, 0, 100, 0.5, 0, 0)
    assert (trade.cash, trade.btc, trade.commission, trade.slippage_cost) == (5000, 50, 0, 0)
    same = rebalance(5000, 50, 100, 0.5, 0.001, 0.0005)
    assert (same.cash, same.btc, same.delta_btc, same.commission) == (5000, 50, 0, 0)


@pytest.mark.parametrize(
    "field,value",
    [
        (0, -1),
        (1, -1),
        (2, 0),
        (2, float("nan")),
        (3, -0.1),
        (3, 1.1),
        (3, float("inf")),
        (4, -1),
        (4, 1),
        (5, 1),
    ],
)
def test_invalid_accounting_inputs_raise(field, value):
    args = [10000, 0, 100, 0.5, 0.001, 0.0005]
    args[field] = value
    with pytest.raises(ValueError):
        rebalance(*args)


def synthetic_path(config, partition="train", opens=None, closes=None, features=None):
    """A labeled synthetic path; never loaded from market files."""
    from btc_risk_rl.config import STEP_MS, utc_ms
    from btc_risk_rl.env.market import MarketPath

    if partition == "train":
        first = utc_ms(config.data.train_start)
        n = 180
    else:
        first = utc_ms(config.data.validation_start)
        n = (utc_ms(config.data.test_start) - first) // STEP_MS
    times = np.arange(first - STEP_MS, first + n * STEP_MS, STEP_MS, dtype=np.int64)
    return MarketPath(
        times,
        np.full(n + 1, 100.0) if opens is None else opens,
        np.full(n + 1, 100.0) if closes is None else closes,
        np.zeros((n + 1, 10)) if features is None else features,
        partition,
        0,
        "collection_window" if partition == "train" else "partition_boundary",
        "synthetic_fixture",
    )


def test_observation_next_open_and_gap_accounting(config):
    from btc_risk_rl.env.trading import TradingEnv

    opens, closes = np.full(181, 100.0), np.full(181, 100.0)
    opens[1], closes[1] = 110, 120
    opens[2], closes[2] = 140, 150
    features = np.zeros((181, 10))
    features[0], features[1] = np.arange(10), np.arange(10) + 10
    env = TradingEnv(synthetic_path(config, opens=opens, closes=closes, features=features), config)
    obs, info = env.reset(seed=3)
    np.testing.assert_array_equal(obs, np.r_[np.arange(10), 0.0, 0.0, 1.0])
    assert obs.dtype == np.float64 and info["equity"] == 10000
    obs1, r1, terminated, truncated, trade1 = env.step(np.array([1.0], dtype=np.float64))
    q = 10000 / (110 * 1.0005 * 1.001)
    assert trade1["btc"] == pytest.approx(q)
    assert trade1["equity"] == pytest.approx(q * 120)
    assert r1 == pytest.approx(np.log(q * 120 / 10000))
    np.testing.assert_array_equal(obs1[:10], features[1])
    assert not terminated and not truncated
    _, r2, _, _, trade2 = env.step(1.0)
    assert trade2["delta_btc"] == 0 and trade2["commission"] == 0
    assert r2 == pytest.approx(np.log(150 / 120))  # includes gap, not just open-to-close
    assert trade2["equity_open_before"] == pytest.approx(q * 140)


def test_no_lookahead_in_observation_or_order_sizing(config):
    from btc_risk_rl.env.trading import TradingEnv

    a = synthetic_path(config)
    changed = np.full(181, 100.0)
    changed[1:] = 200
    future_features = np.zeros((181, 10))
    future_features[1:] = 999
    b = synthetic_path(config, closes=changed, features=future_features)
    left, right = TradingEnv(a, config), TradingEnv(b, config)
    np.testing.assert_array_equal(left.reset()[0], right.reset()[0])
    _, _, _, _, i1 = left.step(0.6)
    _, _, _, _, i2 = right.step(0.6)
    for key in ["cash", "btc", "delta_btc", "commission", "execution_price", "slippage_cost"]:
        assert i1[key] == i2[key]
    assert i1["equity"] != i2["equity"]  # next close affects valuation only


def test_full_episode_terminates_without_liquidation_and_reward_telescopes(config):
    from btc_risk_rl.env.trading import TradingEnv

    env = TradingEnv(synthetic_path(config), config)
    env.reset()
    rewards = []
    for i in range(180):
        obs, r, terminal, cut, info = env.step(1.0)
        rewards.append(r)
        assert terminal == (i == 179) and not cut
    assert info["btc"] > 0 and info["cash"] == 0
    assert info["commission"] == 0 and info["delta_btc"] == 0
    assert info["end_reason"] == "collection_window"
    assert sum(rewards) == pytest.approx(np.log(info["equity"] / 10000), abs=1e-13)
    assert obs[11] == pytest.approx(sum(rewards))
    assert info["adr_002_status"] == "adopted_v2_1"
    with pytest.raises(RuntimeError):
        env.step(0.0)
    reset, reset_info = env.reset()
    assert reset_info["equity"] == 10000 and reset_info["btc"] == 0
    assert reset[11] == 0 and reset[12] == 1


@pytest.mark.parametrize("action", [-0.01, 1.01, float("nan"), float("inf"), [0, 1], [[0.5]]])
def test_invalid_action_does_not_mutate_portfolio(config, action):
    from btc_risk_rl.env.trading import TradingEnv

    env = TradingEnv(synthetic_path(config), config)
    before = env.reset()
    with pytest.raises(ValueError):
        env.step(action)
    after = env.step(0.0)
    assert after[-1]["cash"] == before[1]["cash"]
    assert after[-1]["step"] == 1


def test_validation_is_one_continuous_2190_step_path(config):
    from btc_risk_rl.env.trading import TradingEnv

    env = TradingEnv(synthetic_path(config, "validation"), config)
    env.reset()
    for i in range(2190):
        _, _, terminal, cut, info = env.step(1.0)
        assert not terminal and cut == (i == 2189)
        assert info["step"] == i + 1
        if i:
            assert info["commission"] == 0
    assert info["btc"] > 0 and info["end_reason"] == "partition_boundary"


def test_path_copy_guards_final_gap_and_partition(config):
    from dataclasses import replace

    from btc_risk_rl.config import STEP_MS, utc_ms
    from btc_risk_rl.env.trading import TradingEnv

    path = synthetic_path(config)
    with pytest.raises(ValueError):
        path.closes[0] = 1
    with pytest.raises(ValueError):
        replace(path, times=path.times + utc_ms(config.data.test_start) - path.times[0])
    gaps = path.times.copy()
    gaps[-1] += STEP_MS
    with pytest.raises(ValueError):
        replace(path, times=gaps)
    crossing = path.times + utc_ms(config.data.validation_start) - path.times[-2]
    with pytest.raises(ValueError):
        TradingEnv(replace(path, times=crossing), config)


def test_reset_required_and_gymnasium_contract(config):
    from gymnasium.utils.env_checker import check_env

    from btc_risk_rl.env.trading import TradingEnv

    env = TradingEnv(synthetic_path(config), config)
    with pytest.raises(RuntimeError):
        env.step(0.5)
    # Unbounded z-scores/log equity intentionally trigger these two Box advisories.
    with pytest.warns(UserWarning, match="infinity") as warnings:
        check_env(env, skip_render_check=True)
    assert len(warnings) == 2


@pytest.fixture(scope="module")
def accepted_synthetic(tmp_path_factory):
    from pathlib import Path

    from test_segmentation import synthetic_raw_with_approved_anomalies

    from btc_risk_rl.config import load_config
    from btc_risk_rl.data.segmented_pipeline import prepare_segmented

    config = load_config(Path("configs/initial.toml"))
    base = tmp_path_factory.mktemp("simulator-synthetic-accepted")
    raw, diagnosis, out = base / "raw", base / "diagnosis", base / "out"
    synthetic_raw_with_approved_anomalies(config, raw, diagnosis)
    prepare_segmented(config, raw, out, diagnosis)
    return config, raw, out, diagnosis


def test_accepted_loader_all_indices_and_continuous_validation(accepted_synthetic):
    from btc_risk_rl.config import STEP_MS, utc_ms
    from btc_risk_rl.env.market import AcceptedMarket
    from btc_risk_rl.env.trading import TradingEnv

    c, raw, out, diagnosis = accepted_synthetic
    data = AcceptedMarket(c, raw, out, diagnosis)
    assert len(data.episode_ids) == 7048
    seen = set()
    for episode_id in data.episode_ids:
        path = data.training_path(episode_id)
        assert len(path.times) == 181
        assert path.times[-1] - path.times[0] == 180 * STEP_MS
        assert path.times[1] >= utc_ms(c.data.train_start)
        assert path.times[-1] < utc_ms(c.data.validation_start)
        seen.add(path.segment_id)
    assert len(seen) == 15
    assert data.validation_path().times.shape == (2191,)
    env = TradingEnv(data.training_path(0), c)
    assert env.observation_space.high[10] == 1
    assert env.reset()[0].shape == (13,)
    for wrong in [-1, 7048, 0.5, True]:
        with pytest.raises(ValueError):
            data.training_path(wrong)


def test_unaccepted_or_reserved_source_blocked_before_audit(config, tmp_path, monkeypatch):
    import json

    from btc_risk_rl.config import utc_ms
    from btc_risk_rl.env import market

    out, raw = tmp_path / "out", tmp_path / "raw"
    out.mkdir()
    raw.mkdir()
    (out / "manifest.json").write_text(json.dumps({"status": "pending_verification"}))
    with pytest.raises(ValueError, match="accepted"):
        market.AcceptedMarket(config, raw, out)
    (out / "manifest.json").write_text(json.dumps({"status": "accepted"}))
    (raw / "manifest.json").write_text(
        json.dumps(
            {
                "start_inclusive_ms": utc_ms(config.data.test_start),
                "end_exclusive_ms": utc_ms(config.data.test_end),
            }
        )
    )

    def no_audit(*args, **kwargs):
        raise AssertionError("Reserved manifest must fail before product audit")

    monkeypatch.setattr(market, "verify_segmented", no_audit)
    with pytest.raises(ValueError, match="reserved"):
        market.AcceptedMarket(config, raw, out)


def test_modified_products_are_rejected(accepted_synthetic, tmp_path):
    import shutil

    from btc_risk_rl.env.market import AcceptedMarket

    c, raw, out, diagnosis = accepted_synthetic
    damaged = tmp_path / "damaged"
    shutil.copytree(out, damaged)
    with (damaged / "episodes.csv").open("a") as f:
        f.write("invalid\n")
    with pytest.raises(ValueError, match="hash"):
        AcceptedMarket(c, raw, damaged, diagnosis)


def test_deterministic_random_portfolios_match_cashflow_oracle():
    rng = np.random.default_rng(20260921)
    for _ in range(120):
        c, q, p = 10.0 ** rng.uniform(-2, 5), 10.0 ** rng.uniform(-5, 2), 10.0 ** rng.uniform(1, 5)
        w = rng.uniform(0, 1)
        trade = rebalance(c, q, p, w, 0.001, 0.0005)
        expected = cashflow_oracle(c, q, p, w, 0.001, 0.0005)
        np.testing.assert_allclose(
            [trade.cash, trade.btc, trade.commission, trade.slippage_cost],
            expected,
            rtol=1e-10,
            atol=1e-10,
        )


def test_rollout_auditor_rejects_corrupt_cashflow(config, monkeypatch):
    import runpy

    from btc_risk_rl.env.trading import TradingEnv

    audit = runpy.run_path("scripts/verify_simulator.py")["audit_rollout"]
    result = audit(synthetic_path(config), config, None, "synthetic")
    assert result["steps"] == 180
    original = TradingEnv.step

    def corrupt(self, action):
        obs, reward, terminated, truncated, info = original(self, action)
        info["commission"] += 1
        return obs, reward, terminated, truncated, info

    monkeypatch.setattr(TradingEnv, "step", corrupt)
    with pytest.raises(AssertionError):
        audit(synthetic_path(config), config, None, "synthetic")


@pytest.mark.parametrize("fee,slip", [(0.0, 0.0005), (0.001, 0.0)])
def test_partial_sell_separates_fee_and_slippage(fee, slip):
    trade = rebalance(2000, 80, 100, 0.3, fee, slip)
    expected = cashflow_oracle(2000, 80, 100, 0.3, fee, slip)
    np.testing.assert_allclose(
        [trade.cash, trade.btc, trade.commission, trade.slippage_cost],
        expected,
        rtol=1e-13,
        atol=1e-12,
    )
    assert trade.delta_btc < 0
    if fee == 0:
        assert trade.commission == 0
    if slip == 0:
        assert trade.slippage_cost == 0


def test_environments_sharing_a_path_have_independent_balances(config):
    from btc_risk_rl.env.trading import TradingEnv

    path = synthetic_path(config)
    a, b = TradingEnv(path, config), TradingEnv(path, config)
    a.reset()
    b.reset()
    a.step(1.0)
    for i in range(180):
        obs, reward, terminal, cut, info = b.step(0.0)
        assert info["cash"] == 10000 and info["btc"] == 0
        assert reward == 0 and obs[11] == 0
        assert terminal == (i == 179) and not cut
    assert a.step(1.0)[-1]["btc"] > 0


def test_segment_cut_keeps_position_and_terminal_observation(accepted_synthetic):
    from btc_risk_rl.env.market import AcceptedMarket
    from btc_risk_rl.env.trading import TradingEnv

    c, raw, out, diagnosis = accepted_synthetic
    data = AcceptedMarket(c, raw, out, diagnosis)
    path = next(
        p for i in data.episode_ids if (p := data.training_path(i)).end_reason == "segment_boundary"
    )
    env = TradingEnv(path, c)
    env.reset()
    for _ in range(180):
        obs, _, terminal, cut, info = env.step(1.0)
    assert terminal and not cut
    assert info["end_reason"] == "segment_boundary"
    assert info["btc"] > 0 and info["delta_btc"] == 0 and info["commission"] == 0
    np.testing.assert_array_equal(obs[:10], path.features[-1])
    with pytest.raises(RuntimeError):
        env.step(1.0)
