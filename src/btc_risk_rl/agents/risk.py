"""ADR-002 complete returns and loss-tail arithmetic, independent of optimizers."""

from fractions import Fraction

import numpy as np


def losses_array(losses, alpha):
    x = np.asarray(losses, dtype=np.float64)
    if x.ndim != 1 or not len(x) or not np.isfinite(x).all() or not 0 < alpha < 1:
        raise ValueError("Finite nonempty loss vector and tail fraction in (0,1) required")
    return x


def monte_carlo(rewards):
    r = np.asarray(rewards, dtype=np.float64)
    if r.ndim != 2 or r.shape[1] != 180 or not len(r) or not np.isfinite(r).all():
        raise ValueError("Monte Carlo requires complete finite [N,180] rewards")
    return np.cumsum(r[:, ::-1], axis=1)[:, ::-1].copy()


def variational(losses, alpha, eta):
    x = losses_array(losses, alpha)
    if not np.isfinite(eta):
        raise ValueError("Finite eta required")
    return float(eta + np.maximum(x - eta, 0).mean() / alpha)


def empirical_tail(losses, alpha):
    x = losses_array(losses, alpha)
    mass_exact = Fraction(str(alpha)) * len(x)
    # ceil(N - alpha*N) = N - floor(alpha*N); one-based lower quantile.
    rank = len(x) - mass_exact.numerator // mass_exact.denominator
    eta = float(np.sort(x)[rank - 1])
    greater, tied = x > eta, x == eta
    mass = float(mass_exact)
    weights = greater.astype(np.float64)
    weights[tied] = (mass - int(greater.sum())) / int(tied.sum())
    return dict(
        eta=eta,
        rho=float(weights @ x / mass),
        weights=weights.tolist(),
        mass=mass,
        ties=int(tied.sum()),
        greater=int(greater.sum()),
        n=len(x),
        quantile_rank=rank,
    )


def dual_update(multiplier, f_value, bound, rate, *, enabled):
    if not np.isfinite([multiplier, f_value, bound, rate]).all() or multiplier < 0 or rate < 0:
        raise ValueError("Invalid dual inputs")
    return max(0.0, float(multiplier + rate * (f_value - bound))) if enabled else 0.0
