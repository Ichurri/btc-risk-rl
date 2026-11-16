"""Synthetic-only evaluation path and integrity oracles."""

import json
import math

import numpy as np
import pytest


def test_synthetic_sortino_uses_all_periods_and_undefined_downside():
    from btc_risk_rl.evaluation.synthetic import summarize_returns

    result = summarize_returns(np.array([0.10, -0.05, 0.02], dtype=np.float64))
    expected_downside = math.sqrt(0.05**2 / 3)
    assert result["downside_deviation_4h"] == pytest.approx(expected_downside)
    assert result["sortino_annualized"] == pytest.approx(
        math.sqrt(2190) * (0.10 - 0.05 + 0.02) / 3 / expected_downside
    )
    assert summarize_returns(np.array([0.01, 0.02]))["sortino_annualized"] is None
    with pytest.raises(ValueError):
        summarize_returns(np.array([0.01, float("nan")]))


def test_continuous_portfolio_matches_independent_two_step_cashflows(config):
    from btc_risk_rl.env.accounting import rebalance
    from btc_risk_rl.evaluation.synthetic import SyntheticPath, evaluate_continuous

    class HalfPolicy:
        def deterministic_action(self, observation):
            assert observation.shape == (13,) and observation[-1] == 1.0
            return 0.5

    path = SyntheticPath(
        opens=np.array([100.0, 110.0, 130.0]),
        closes=np.array([100.0, 120.0, 140.0]),
        features=np.zeros((3, 10), dtype=np.float64),
    )
    rows = evaluate_continuous(path, HalfPolicy(), config)
    first = rebalance(10000, 0, 110, 0.5, 0.001, 0.0005)
    equity1 = first.cash + first.btc * 120
    second = rebalance(first.cash, first.btc, 130, 0.5, 0.001, 0.0005)
    equity2 = second.cash + second.btc * 140
    assert len(rows) == 2
    assert rows[0]["equity"] == pytest.approx(equity1)
    assert rows[1]["equity"] == pytest.approx(equity2)
    assert rows[0]["simple_return"] == pytest.approx(equity1 / 10000 - 1)
    assert rows[1]["simple_return"] == pytest.approx(equity2 / equity1 - 1)
    assert rows[1]["cash_before"] == pytest.approx(first.cash)
    assert rows[1]["btc_before"] == pytest.approx(first.btc)


def test_auditor_rejects_partial_tampered_and_incompatible_trace(config):
    from btc_risk_rl.evaluation.synthetic import SyntheticPath, audit_trace, evaluate_continuous

    class HalfPolicy:
        def deterministic_action(self, observation):
            return 0.5

    path = SyntheticPath(
        np.array([100.0, 100.0, 100.0]),
        np.array([100.0, 101.0, 99.0]),
        np.zeros((3, 10)),
    )
    trace = evaluate_continuous(path, HalfPolicy(), config)
    assert audit_trace(trace, expected_steps=2)["accepted"]
    with pytest.raises(ValueError, match="Incomplete"):
        audit_trace(trace[:1], expected_steps=2)
    bad = [dict(row) for row in trace]
    bad[1]["cash_after"] += 1
    with pytest.raises(ValueError, match="cashflow"):
        audit_trace(bad, expected_steps=2)
    bad = [dict(row) for row in trace]
    bad[0]["clock"] = 0.5
    with pytest.raises(ValueError, match="clock"):
        audit_trace(bad, expected_steps=2)
    bad = [dict(row) for row in trace]
    bad[0]["slippage_cost"] += 1
    with pytest.raises(ValueError, match="cost"):
        audit_trace(bad, expected_steps=2)
    bad = [dict(row) for row in trace]
    bad[0]["action"] = 0.7
    with pytest.raises(ValueError, match="target weight"):
        audit_trace(bad, expected_steps=2)


def test_fixed_input_loader_rejects_bad_hash_before_deserialization(tmp_path):
    from btc_risk_rl.evaluation.synthetic import load_verified_actor

    corrupt = tmp_path / "state.pt"
    corrupt.write_bytes(b"not a checkpoint")
    with pytest.raises(ValueError, match="hash mismatch"):
        load_verified_actor(corrupt, expected_sha256="0" * 64)


def test_synthetic_generator_is_reproducible_and_finite():
    from btc_risk_rl.evaluation.synthetic import make_synthetic_path
    from btc_risk_rl.features.market import FEATURES, TrainScaler

    scaler = TrainScaler(FEATURES, [0.0] * 10, [1.0] * 10, "x", "y", 1)
    a = make_synthetic_path(50, seed=910031, scaler=scaler)
    b = make_synthetic_path(50, seed=910031, scaler=scaler)
    np.testing.assert_array_equal(a.opens, b.opens)
    np.testing.assert_array_equal(a.features, b.features)
    assert a.features.shape == (51, 10) and np.isfinite(a.features).all()


def test_full_supervised_synthetic_route_closes_and_reproduces(tmp_path):
    from btc_risk_rl.evaluation.synthetic_runner import run

    first = run(tmp_path / "first", steps=8, seed=910031)
    second = run(tmp_path / "second", steps=8, seed=910031)
    assert first["status"] == second["status"] == "completed_synthetic"
    assert first["supervisor"]["status"] == "passed"
    assert first["trace_sha256"] == second["trace_sha256"]
    assert first["metrics"] == second["metrics"]
    assert first["steps"] == second["steps"] == 8
    assert first["wall_seconds_before_closure"] >= first["supervisor"]["wall_seconds"]
    assert first["worker_rss_peak_bytes"] > 0
    assert (tmp_path / "first" / "audit.json").is_file()
    assert (tmp_path / "first" / "worker.log").is_file()
    assert (tmp_path / "first" / "closure.json").is_file()
    assert first["started_wall_utc"] < first["closed_utc"]
    assert all("validation" not in path and "segmented-B-h1" not in path
               for path in first["opened_data_files"])


def test_supervised_synthetic_route_fails_closed_for_forged_checkpoint(tmp_path):
    from btc_risk_rl.evaluation.synthetic_runner import run

    result = run(tmp_path / "forged", steps=3, seed=910031, checkpoint_sha="0" * 64)
    assert result["status"] == "failed"
    assert result["supervisor"]["status"] == "failed"
    assert not (tmp_path / "forged" / "audit.json").exists()
    assert not (tmp_path / "forged" / "trace.csv").exists()


def test_public_output_guard_never_targets_prior_campaign_or_data(tmp_path):
    from btc_risk_rl.evaluation.synthetic_runner import guard_public_output

    for path in (tmp_path / "artifacts/p3-approved-v1/new", tmp_path / "data/new"):
        with pytest.raises(ValueError):
            guard_public_output(path, repo=tmp_path)
    guard_public_output(tmp_path / "artifacts/oos-synthetic-evaluation-01/run", repo=tmp_path)


def test_parent_rejects_worker_report_with_forged_cost_total(tmp_path, monkeypatch):
    from btc_risk_rl.evaluation import synthetic_runner as runner

    actual_supervise = runner.supervise
    output = tmp_path / "forged-cost"

    def forge_after_worker(*args, **kwargs):
        result = actual_supervise(*args, **kwargs)
        report = output / "worker-result.json"
        value = json.loads(report.read_text())
        value["commission_total"] += 1.0
        report.write_text(json.dumps(value))
        return result

    monkeypatch.setattr(runner, "supervise", forge_after_worker)
    closure = runner.run(output, steps=3, seed=910031)
    assert closure["status"] == "failed"
    assert not (output / "audit.json").exists()
