"""Analytical examples for the post-closure secondary statistics."""

import math
import runpy
from pathlib import Path

import numpy as np
import pytest

MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/secondary_metrics.py"))


def test_metrics_against_two_known_periods():
    result = MODULE["summarize"]([100, 80, 100], [0, 0.4, 0.1], periods_per_year=2)
    assert result["return_net"] == 0
    assert result["sharpe"] == pytest.approx(1 / 9)
    assert result["sortino"] == pytest.approx(0.25)
    assert result["max_drawdown"] == pytest.approx(0.2)
    assert result["calmar"] == 0
    assert result["cvar_05"] == pytest.approx(0.2)
    assert result["turnover"] == pytest.approx(0.7)


def test_cvar_fractional_boundary_and_tie():
    returns = np.array([-0.3, -0.1, -0.1] + [0.02] * 27)
    assert MODULE["tail_loss"](returns, 0.05) == pytest.approx(0.35 / 1.5)


def test_undefined_denominators_and_geometric_calmar():
    constant = MODULE["summarize"]([100, 100, 100], [0, 0, 0])
    assert all(constant[metric] is None for metric in ("sharpe", "sortino", "calmar"))
    assert constant["max_drawdown"] == 0
    result = MODULE["summarize"]([100, 80, 120], [0, 0.4, 0.4], periods_per_year=4)
    assert result["calmar"] == pytest.approx((1.2**2 - 1) / 0.2)
    assert math.isfinite(result["sharpe"])


def test_drawdown_keeps_initial_equity_and_rolling_peak():
    assert MODULE["drawdown"]([100, 80, 120, 90, 125]).tolist() == pytest.approx(
        [0, 0.20, 0, 0.25, 0]
    )


def test_paired_interval_uses_same_block_and_propagates_undefined():
    assert MODULE["paired_summary"]([3, 9, 15], [1, 7, 13]) == (3, 2, 0, 2, 2)
    assert MODULE["paired_summary"]([3, None, 15], [1, 7, 13]) == (2, None, None, None, None)


def test_hash_mismatch_stops_reading(tmp_path):
    path = tmp_path / "trace.jsonl"
    path.write_bytes(b"altered")
    with pytest.raises(ValueError, match="SHA-256"):
        MODULE["read_verified"](path, "0" * 64)


def test_output_rejects_closed_evidence_and_symlink_alias(tmp_path):
    protected = tmp_path / "artifacts" / "oos-v12-final-2024-2025-01"
    protected.mkdir(parents=True)
    alias = tmp_path / "alias"
    alias.symlink_to(protected, target_is_directory=True)
    for path in (protected / "new", alias / "new"):
        with pytest.raises(ValueError, match="protegida"):
            MODULE["output_path"](tmp_path, path)
