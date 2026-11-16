"""Pure descriptive metrics and shared constants for the closed OOS report."""

import hashlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/oos-v12-secondary-metrics-20261116"
CONDITIONS = ("C0", "C5", "C10")
REFERENCE = "Comprar y mantener"
METRICS = {
    "return_net": ("Retorno acumulado neto", "%"),
    "sharpe": ("Sharpe anualizado", "razón"),
    "sortino": ("Sortino anualizado", "razón"),
    "max_drawdown": ("Maximum Drawdown", "%"),
    "calmar": ("Calmar", "razón"),
    "cvar_05": ("CVaR periódico al 5 %", "%"),
    "turnover": ("Turnover anualizado", "% por año"),
}
PERIODS = 2190
BOOTSTRAP_SEED = 912016
BOOTSTRAP_SAMPLES = 20000
SCOPE = "Análisis descriptivo posterior al cierre de la prueba confirmatoria."
PROVENANCE = "Elaboración propia 2026, con base en las trazas de la prueba final"
FIGURES = {
    "curva-patrimonio": "Patrimonio durante la prueba final",
    "curva-drawdown": "Caída del patrimonio desde su máximo previo",
    "sortino-por-condicion": "Distribución de Sortino por condición",
    "exposicion-media": "Exposición a BTC por condición",
}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def read_verified(path, expected):
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError(f"Entrada con enlace simbólico: {path}")
    raw = path.read_bytes()
    if sha256(raw) != expected:
        raise ValueError(f"SHA-256 no coincide: {path}")
    return raw


def output_path(root, path):
    target = path.resolve()
    for relative in ("artifacts", "docs/evidence/oos-v12-evaluation-20261115",
                     "docs/evidence/oos-v12-buy-hold-20261115", "docs/protocols", "data"):
        protected = (root / relative).resolve()
        if target == protected or protected in target.parents:
            raise ValueError(f"Ruta de salida protegida: {target}")
    return target


def drawdown(equity):
    equity = np.asarray(equity, dtype=float)
    return 1 - equity / np.maximum.accumulate(equity)


def tail_loss(returns, fraction):
    ordered = np.sort(returns)
    mass = len(ordered) * fraction
    whole = int(mass)
    partial = mass - whole
    total = ordered[:whole].sum()
    if partial:
        total += partial * ordered[whole]
    return float(-total / mass)


def summarize(equity, exposure, periods_per_year=PERIODS):
    equity, exposure = (np.asarray(series, dtype=float) for series in (equity, exposure))
    if (equity.ndim != 1 or len(equity) < 2 or equity.shape != exposure.shape
            or not np.isfinite(equity).all() or not np.isfinite(exposure).all()
            or np.any(equity <= 0) or np.any((exposure < 0) | (exposure > 1))):
        raise ValueError("Patrimonio o exposición no válidos")
    returns = equity[1:] / equity[:-1] - 1
    mean = returns.mean()
    sd = returns.std(ddof=1) if len(returns) > 1 else 0
    downside = np.sqrt(np.mean(np.minimum(returns, 0)**2))
    maximum_drawdown = drawdown(equity).max()
    ratio = equity[-1] / equity[0]
    geometric = np.expm1(np.log(ratio) * periods_per_year / len(returns))
    annual = np.sqrt(periods_per_year)
    return {
        "return_net": float(ratio - 1),
        "sharpe": float(annual * mean / sd) if sd else None,
        "sortino": float(annual * mean / downside) if downside else None,
        "max_drawdown": float(maximum_drawdown),
        "calmar": float(geometric / maximum_drawdown) if maximum_drawdown else None,
        "cvar_05": tail_loss(returns, 0.05),
        "turnover": float(np.mean(np.abs(np.diff(exposure))) * periods_per_year),
    }


def paired_summary(treatment, control):
    if len(treatment) != len(control):
        raise ValueError("Los brazos deben tener los mismos bloques")
    differences = np.array([a - b for a, b in zip(treatment, control, strict=True)
                            if a is not None and b is not None])
    n = len(differences)
    if n < 2 or n != len(control):
        return n, None, None, None, None
    rng = np.random.Generator(np.random.PCG64(BOOTSTRAP_SEED))
    sample = rng.integers(0, n, size=(BOOTSTRAP_SAMPLES, n))
    low, high = np.percentile(differences[sample].mean(axis=1), [2.5, 97.5])
    return n, float(differences.mean()), float(differences.std(ddof=1)), float(low), float(high)


def format_number(value, decimals=6):
    return "No definido" if value is None else f"{value:.{decimals}f}".rstrip("0").rstrip(".").replace(".", ",")
