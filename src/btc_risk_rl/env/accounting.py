"""Self-financing spot rebalance, target weight marked at the reference open."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Trade:
    cash: float
    btc: float
    delta_btc: float
    reference_price: float
    execution_price: float
    commission: float
    slippage_cost: float
    equity_before: float
    equity_after: float


def rebalance(cash, btc, price, weight, fee, slip) -> Trade:
    c, q, p, w, f, s = np.asarray([cash, btc, price, weight, fee, slip], dtype=np.float64)
    if (
        not np.isfinite([c, q, p, w, f, s]).all()
        or c < 0
        or q < 0
        or p <= 0
        or not 0 <= w <= 1
        or not 0 <= f < 1
        or not 0 <= s < 1
    ):
        raise ValueError("Invalid portfolio, price, target or costs")
    before = c + q * p
    if not np.isfinite(before) or before <= 0:
        raise ValueError("Equity must be finite and positive")
    demand = w * c - (1 - w) * q * p
    if demand > 0:
        execution = p * (1 + s)
        k = s + f + s * f
        delta = demand / (p * (1 + w * k))
        new_q = q + delta
        # Algebraic cashflow solution, stable and exactly zero for all-in.
        new_c = (1 - w) * (c + q * p * (1 + k)) / (1 + w * k)
    elif demand < 0:
        execution = p * (1 - s)
        k = s + f - s * f
        delta = demand / (p * (1 - w * k))
        new_c = c - delta * execution * (1 - f)
        # Algebraic BTC solution, stable and exactly zero for all-out.
        new_q = w * (c + q * p * (1 - k)) / (p * (1 - w * k))
    else:
        execution, delta, new_c, new_q = p, np.float64(0), c, q
    commission = abs(delta) * execution * f
    slippage = abs(delta) * p * s
    after = new_c + new_q * p
    if not np.isfinite([new_c, new_q, execution, delta, commission, slippage, after]).all():
        raise ValueError("Nonfinite accounting result")
    if new_c < 0 or new_q < 0 or after <= 0:
        raise ValueError("Invalid post-trade balances")
    # Only numerical comparisons use tolerances. Balances/actions are never clipped.
    tol = 64 * np.finfo(np.float64).eps
    if (
        abs(new_c - (c - delta * execution - commission)) > tol * before
        or abs(new_q - (q + delta)) * p > tol * before
        or abs(after - (before - commission - slippage)) > tol * before
        or abs(new_q * p / after - w) > tol
    ):
        raise ArithmeticError("Self-financing or target-weight identity failed")
    return Trade(
        *map(float, (new_c, new_q, delta, p, execution, commission, slippage, before, after))
    )
