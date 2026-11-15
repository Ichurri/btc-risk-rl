"""One authorized, descriptive BTC buy-and-hold reference for OOS 2024–2025.

The final evaluation gates stay closed. This entry point has its own pinned
read permission and writes only a new, small reference result.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np

from btc_risk_rl.config import load_config
from btc_risk_rl.env.accounting import rebalance
from btc_risk_rl.evaluation.code_identity import execution_code_sha256
from btc_risk_rl.evaluation.export_reader import load_evaluation_export
from btc_risk_rl.evaluation.synthetic import load_verified_scaler, summarize_returns

ROOT = Path(__file__).resolve().parents[1]
APPROVAL_PATH = Path("docs/protocols/OOS-v1-2-buy-hold-reference-approval.json")
OUTPUT_PATH = Path("docs/evidence/oos-v12-buy-hold-20261115/result.json")
ENABLED = False
APPROVAL_SHA256 = None

EXPORT = Path("data/processed/oos-v12-final-2024-2025-01")
RAW_MANIFEST = Path("data/raw/oos-v12-final-2024-2025-01/manifest.json")
SOURCE_AUDIT = Path("docs/evidence/oos-v12-evaluation-20261115/final-source-audit.json")
SCALER_ROOT = Path("data/processed/p2r-training-h1")
CONFIG = Path("configs/initial.toml")
METHOD = Path("docs/protocols/OOS-v1-2-evaluation-method-freeze-20261111.json")
FINAL_LEDGER = Path("artifacts/oos-v12-final-2024-2025-01/ledger.jsonl")
FINAL_CONTRAST = Path("artifacts/oos-v12-final-2024-2025-01/final-contrast.json")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_code_sha256() -> str:
    """Pin every calculation byte while allowing only gate-value commits."""
    lines = Path(__file__).read_bytes().splitlines(keepends=True)
    found = set()
    for index, line in enumerate(lines):
        for declaration in (b"ENABLED = ", b"APPROVAL_SHA256 = "):
            if line.startswith(declaration):
                if declaration in found:
                    raise ValueError("Duplicate reference gate declaration")
                found.add(declaration)
                lines[index] = declaration + b"<pinned gate>\n"
    if len(found) != 2:
        raise ValueError("Reference gate declaration missing")
    return hashlib.sha256(b"".join(lines)).hexdigest()


def read_pinned_permission(repo_root: Path) -> dict:
    """Reject before touching the protected source if the limited gate is off."""
    if ENABLED is not True:
        raise PermissionError("Buy-and-hold reference disabled")
    approval_path = Path(repo_root) / APPROVAL_PATH
    if (not isinstance(APPROVAL_SHA256, str) or len(APPROVAL_SHA256) != 64
            or approval_path.is_symlink() or not approval_path.is_file()
            or _sha(approval_path) != APPROVAL_SHA256):
        raise PermissionError("Buy-and-hold reference approval hash mismatch")
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    if (type(approval) is not dict or approval.get("status") != "approved"
            or approval.get("scope") != "single_descriptive_buy_hold_2024_2025"
            or approval.get("partition") != "final_2024_2025"
            or approval.get("steps") != 4386
            or approval.get("first_trade") != "buy_to_target_weight_one_at_first_executable_open"
            or approval.get("holding") != "no_further_trades_or_cash_interest"
            or approval.get("last_valuation") != "final_close_without_liquidation"
            or approval.get("initial_cash_usdt") != 10000.0
            or approval.get("commission_fraction") != 0.001
            or approval.get("slippage_fraction") != 0.0005
            or approval.get("role") !=
            "post_contrast_descriptive_reference_only_not_primary_hypothesis_or_selection"
            or approval.get("output_path") != OUTPUT_PATH.as_posix()
            or approval.get("normalized_code_sha256") != normalized_code_sha256()):
        raise PermissionError("Buy-and-hold reference approval identity mismatch")
    if approval.get("evaluation_execution_code_sha256") != execution_code_sha256(repo_root):
        raise PermissionError("Buy-and-hold reference execution code mismatch")
    return approval


def calculate_buy_hold(opens, closes, *, initial_cash: float, fee: float, slip: float) -> dict:
    """Buy at opens[1], then hold through closes[-1] without liquidation."""
    opening = np.asarray(opens, dtype=np.float64)
    closing = np.asarray(closes, dtype=np.float64)
    if (opening.ndim != 1 or opening.size < 2 or closing.shape != opening.shape
            or not np.isfinite(opening).all() or not np.isfinite(closing).all()
            or (opening <= 0).any() or (closing <= 0).any()):
        raise ValueError("Complete positive price path required")
    trade = rebalance(initial_cash, 0.0, float(opening[1]), 1.0, fee, slip)
    equity = trade.cash + trade.btc * closing[1:]
    if not np.isfinite(equity).all() or (equity <= 0).any():
        raise ValueError("Nonpositive buy-and-hold equity")
    returns = equity / np.r_[initial_cash, equity[:-1]] - 1.0
    metrics = summarize_returns(returns)

    # Independent single-purchase cashflow and return-ratio calculation.
    direct_btc = initial_cash / (opening[1] * (1 + slip) * (1 + fee))
    direct_returns = np.r_[direct_btc * closing[1] / initial_cash - 1,
                           closing[2:] / closing[1:-1] - 1]
    direct_downside = math.sqrt(float(np.mean(np.minimum(direct_returns, 0) ** 2)))
    direct_sortino = (math.sqrt(2190) * float(np.mean(direct_returns)) / direct_downside
                      if direct_downside > 0 else None)
    if (not math.isclose(trade.btc, direct_btc, rel_tol=1e-13)
            or trade.cash != 0.0
            or not np.allclose(returns, direct_returns, rtol=1e-12, atol=1e-14)
            or not math.isclose(equity[-1], direct_btc * closing[-1], rel_tol=1e-13)
            or not math.isclose(trade.commission,
                                direct_btc * opening[1] * (1 + slip) * fee, rel_tol=1e-12,
                                abs_tol=1e-12)
            or not math.isclose(trade.slippage_cost,
                                direct_btc * opening[1] * slip, rel_tol=1e-12, abs_tol=1e-12)
            or (direct_sortino is None) != (metrics["sortino_annualized"] is None)
            or (direct_sortino is not None and not math.isclose(
                direct_sortino, metrics["sortino_annualized"], rel_tol=1e-12))):
        raise ArithmeticError("Independent buy-and-hold audit disagrees")
    return {
        "steps": len(returns), "trade_count": 1,
        "first_open_price": float(opening[1]),
        "last_close_price": float(closing[-1]),
        "btc_purchased": trade.btc,
        "cash_after_purchase": trade.cash,
        "execution_price": trade.execution_price,
        "commission_total": trade.commission,
        "slippage_total": trade.slippage_cost,
        "final_equity": float(equity[-1]),
        "cumulative_net_return_fraction": float(equity[-1] / initial_cash - 1),
        "mean_simple_return_4h": metrics["mean_simple_return_4h"],
        "downside_deviation_4h": metrics["downside_deviation_4h"],
        "sortino_annualized": metrics["sortino_annualized"],
        "returns": returns.tolist(),
        "independent_audit_passed": True,
    }


def run(repo_root: Path = ROOT) -> dict:
    approval = read_pinned_permission(repo_root)
    root = Path(repo_root)
    pinned = {
        "config_sha256": CONFIG,
        "method_sha256": METHOD,
        "source_audit_sha256": SOURCE_AUDIT,
        "source_manifest_sha256": RAW_MANIFEST,
        "export_manifest_sha256": EXPORT / "manifest.json",
        "bars_sha256": EXPORT / "bars.csv",
        "training_manifest_sha256": SCALER_ROOT / "manifest.json",
        "scaler_sha256": SCALER_ROOT / "scaler.json",
        "final_ledger_sha256": FINAL_LEDGER,
        "final_contrast_sha256": FINAL_CONTRAST,
    }
    for name, relative in pinned.items():
        path = root / relative
        if (path.is_symlink() or not path.is_file()
                or _sha(path) != approval.get(name)):
            raise ValueError(f"Reference source identity mismatch: {name}")
    audit = json.loads((root / SOURCE_AUDIT).read_text(encoding="utf-8"))
    if (audit.get("status") != "accepted_source_only"
            or audit.get("evaluation_transitions_available") != 4386
            or audit.get("export_manifest_sha256") != approval["export_manifest_sha256"]
            or audit.get("export_bars_sha256") != approval["bars_sha256"]
            or audit.get("raw_manifest_sha256") != approval["source_manifest_sha256"]
            or audit.get("scaler_sha256") != approval["scaler_sha256"]):
        raise ValueError("Accepted final source audit differs")
    scaler, scaler_sha = load_verified_scaler(
        root / SCALER_ROOT / "manifest.json", root / SCALER_ROOT / "scaler.json",
        manifest_sha256=approval["training_manifest_sha256"],
    )
    path, provenance = load_evaluation_export(
        root / EXPORT, partition="final_2024_2025",
        expected_manifest_sha256=approval["export_manifest_sha256"],
        scaler=scaler, expected_scaler_sha256=scaler_sha,
    )
    if (provenance["bars_sha256"] != approval["bars_sha256"]
            or provenance["source_manifest_sha256"] != approval["source_manifest_sha256"]
            or len(path.times) != 4387):
        raise ValueError("Final path identity differs")
    config = load_config(root / CONFIG)
    environment = config.environment
    if (environment.initial_cash != 10000.0 or environment.commission != 0.001
            or environment.slippage != 0.0005
            or environment.end_position != "mark_to_market_no_liquidation"):
        raise ValueError("Frozen evaluation accounting differs")
    result = calculate_buy_hold(
        path.opens, path.closes, initial_cash=environment.initial_cash,
        fee=environment.commission, slip=environment.slippage,
    )
    if result["steps"] != 4386:
        raise ValueError("Reference did not cover the final partition")
    result.pop("returns")
    report = {
        "schema": "oos_v12_buy_hold_reference_v1", "status": "audited_descriptive_reference",
        "scope": approval["scope"], "partition": "final_2024_2025",
        "first_execution_ms": int(path.times[1]),
        "last_valuation_ms": int(path.times[-1]),
        "initial_cash_usdt": environment.initial_cash,
        "final_liquidation": False,
        "approval_sha256": APPROVAL_SHA256,
        "normalized_code_sha256": normalized_code_sha256(),
        "source_manifest_sha256": approval["source_manifest_sha256"],
        "export_manifest_sha256": approval["export_manifest_sha256"],
        "bars_sha256": approval["bars_sha256"],
        "final_ledger_sha256": approval["final_ledger_sha256"],
        "final_contrast_sha256": approval["final_contrast_sha256"],
        **result,
    }
    output = root / OUTPUT_PATH
    if output.exists() or output.is_symlink():
        raise FileExistsError("Reference result already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return report


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, allow_nan=False))
