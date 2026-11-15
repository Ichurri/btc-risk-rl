"""Synthetic buy-and-hold and dedicated final-source gate checks."""

import importlib.util
import math
from pathlib import Path

import pytest


def _module():
    script = Path(__file__).resolve().parents[1] / "scripts/oos_buy_hold_reference.py"
    spec = importlib.util.spec_from_file_location("oos_buy_hold_reference", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_buy_once_at_first_executable_open_and_hold_to_last_close():
    calculator = _module().calculate_buy_hold
    result = calculator(
        opens=[90.0, 100.0, 110.0], closes=[95.0, 99.0, 105.0],
        initial_cash=10_000.0, fee=0.001, slip=0.0005,
    )
    quantity = 10_000 / (100 * 1.0005 * 1.001)
    first_return = quantity * 99 / 10_000 - 1
    second_return = 105 / 99 - 1
    downside = math.sqrt((first_return**2 + 0) / 2)
    expected_sortino = math.sqrt(2190) * (first_return + second_return) / 2 / downside
    assert result["steps"] == 2
    assert result["first_open_price"] == 100.0
    assert result["last_close_price"] == 105.0
    assert result["btc_purchased"] == pytest.approx(quantity, rel=1e-14)
    assert result["cash_after_purchase"] == 0.0
    assert result["commission_total"] == pytest.approx(quantity * 100 * 1.0005 * 0.001)
    assert result["slippage_total"] == pytest.approx(quantity * 100 * 0.0005)
    assert result["final_equity"] == pytest.approx(quantity * 105)
    assert result["cumulative_net_return_fraction"] == pytest.approx(quantity * 105 / 10_000 - 1)
    assert result["sortino_annualized"] == pytest.approx(expected_sortino)
    assert result["returns"] == pytest.approx([first_return, second_return])
    assert result["independent_audit_passed"] is True


def test_buy_hold_has_no_final_liquidation_or_repeated_costs():
    result = _module().calculate_buy_hold(
        opens=[10.0, 10.0, 12.0, 1.0], closes=[10.0, 10.0, 12.0, 15.0],
        initial_cash=100.0, fee=0.01, slip=0.02,
    )
    assert result["steps"] == 3
    assert result["trade_count"] == 1
    assert result["btc_purchased"] > 0
    assert result["cash_after_purchase"] == 0.0
    assert result["final_equity"] == pytest.approx(result["btc_purchased"] * 15)
    assert result["commission_total"] > 0 and result["slippage_total"] > 0


def test_undefined_sortino_remains_undefined():
    result = _module().calculate_buy_hold(
        opens=[10.0, 10.0, 11.0], closes=[10.0, 11.0, 12.0],
        initial_cash=100.0, fee=0.0, slip=0.0,
    )
    assert result["sortino_annualized"] is None
    assert result["downside_deviation_4h"] == 0.0


def test_closed_or_forged_reference_permit_rejects_before_source(tmp_path, monkeypatch):
    module = _module()
    monkeypatch.setattr(module, "ENABLED", False)
    with pytest.raises(PermissionError, match="disabled"):
        module.read_pinned_permission(tmp_path)
    assert not list(tmp_path.iterdir())
    monkeypatch.setattr(module, "ENABLED", True)
    monkeypatch.setattr(module, "APPROVAL_PATH", Path("approval.json"))
    monkeypatch.setattr(module, "APPROVAL_SHA256", "0" * 64)
    (tmp_path / "approval.json").write_text('{"status":"approved"}')
    with pytest.raises(PermissionError, match="hash"):
        module.read_pinned_permission(tmp_path)


def test_permission_pins_reused_execution_code_before_source(tmp_path, monkeypatch):
    import hashlib
    import json

    module = _module()
    approval = {
        "status": "approved", "scope": "single_descriptive_buy_hold_2024_2025",
        "steps": 4386, "output_path": module.OUTPUT_PATH.as_posix(),
        "normalized_code_sha256": module.normalized_code_sha256(),
        "evaluation_execution_code_sha256": "a" * 64,
        "partition": "final_2024_2025",
        "first_trade": "buy_to_target_weight_one_at_first_executable_open",
        "holding": "no_further_trades_or_cash_interest",
        "last_valuation": "final_close_without_liquidation",
        "initial_cash_usdt": 10000.0,
        "commission_fraction": 0.001,
        "slippage_fraction": 0.0005,
        "role": "post_contrast_descriptive_reference_only_not_primary_hypothesis_or_selection",
    }
    path = tmp_path / "approval.json"
    path.write_text(json.dumps(approval))
    monkeypatch.setattr(module, "APPROVAL_PATH", Path("approval.json"))
    monkeypatch.setattr(module, "APPROVAL_SHA256", hashlib.sha256(path.read_bytes()).hexdigest())
    monkeypatch.setattr(module, "ENABLED", True)
    monkeypatch.setattr(module, "execution_code_sha256", lambda _root: "b" * 64)
    with pytest.raises(PermissionError, match="code"):
        module.read_pinned_permission(tmp_path)
    monkeypatch.setattr(module, "execution_code_sha256", lambda _root: "a" * 64)
    assert module.read_pinned_permission(tmp_path) == approval
    approval["last_valuation"] = "sell_at_final_open"
    path.write_text(json.dumps(approval))
    monkeypatch.setattr(module, "APPROVAL_SHA256", hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(PermissionError, match="identity"):
        module.read_pinned_permission(tmp_path)
