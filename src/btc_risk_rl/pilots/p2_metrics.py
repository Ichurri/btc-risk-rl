"""P2 section 5–7: full fixed targets, additive pooling, joint seed gates."""

import math

import numpy as np

EPS = 1e-12
SEEDS = (610031, 610047, 610081)


def summarize(sse, target_sq, error_sum, count):
    if type(count) is not int or count <= 0 or not np.isfinite([sse, target_sq, error_sum]).all():
        raise ValueError("Invalid metric sums")
    if sse < 0 or target_sq < 0:
        raise ValueError("Negative square sum")
    mse, z, bias = sse / count, target_sq / count, error_sum / count
    return dict(
        sse=sse,
        target_sq=target_sq,
        error_sum=error_sum,
        count=count,
        mse=mse,
        z=z,
        denominator=z + EPS,
        relative_mse=mse / (z + EPS),
        bias=bias,
        normalized_bias=bias / math.sqrt(z + EPS),
        informative=z > EPS,
    )


def stats(x):
    return dict(mean=float(x.mean()), std=float(x.std()), min=float(x.min()), max=float(x.max()))


def metric(predictions, targets):
    p, g = np.asarray(predictions), np.asarray(targets)
    if p.shape != g.shape or p.ndim != 2 or not p.size or not np.isfinite([p, g]).all():
        raise ValueError("Finite matching trajectory targets required")
    error = p - g
    return dict(
        **summarize(float(np.sum(error**2)), float(np.sum(g**2)), float(error.sum()), int(g.size)),
        trajectories=len(g),
        prediction_stats=stats(p),
        target_stats=stats(g),
    )


def full_metric(predictions, targets):
    if np.shape(targets)[1] != 180:
        raise ValueError("Complete H180 targets required")
    return dict(
        **metric(predictions, targets),
        thirds=[metric(predictions[:, j : j + 60], targets[:, j : j + 60]) for j in (0, 60, 120)],
    )


def pool(metrics):
    if not metrics:
        raise ValueError("No observations to pool")
    return summarize(
        *(sum(m[k] for m in metrics) for k in ("sse", "target_sq", "error_sum", "count"))
    )


def fraction(n, d):
    return dict(numerator=n, denominator=d)


def overlap(d, a, learning):
    starts = [x["start"] for x in d]
    a_starts, l_starts = {x["start"] for x in a}, {x["start"] for x in learning}
    dt = [t for x in d for t in x["times"]]
    lt = {t for x in learning for t in x["times"]}
    return dict(
        duplicates=fraction(len(starts) - len(set(starts)), len(starts)),
        exact_A=fraction(sum(s in a_starts for s in starts), len(starts)),
        exact_learning=fraction(sum(s in l_starts for s in starts), len(starts)),
        transition_occurrences=fraction(sum(t in lt for t in dt), len(dt)),
        unique_transitions=fraction(len(set(dt) & lt), len(set(dt))),
    )


def seed_gate(records):
    if [r["iteration"] for r in records] != list(range(10)):
        raise ValueError("All ten iterations required; no checkpoint selection")
    early = pool([records[k]["D"]["post"] for k in (0, 1, 2)])
    late = pool([records[k]["D"]["post"] for k in (7, 8, 9)])
    a = pool([records[k]["A"]["post"] for k in (7, 8, 9)])
    checks = dict(
        informative=all(m["informative"] for m in (early, late, a)),
        zero=late["relative_mse"] <= 1,
        improvement=late["relative_mse"] <= 0.8 * early["relative_mse"],
        bias=abs(late["normalized_bias"]) <= 0.25,
        gap=late["relative_mse"] - a["relative_mse"] <= 0.5,
    )
    return dict(advance=all(checks.values()), checks=checks, early=early, late=late, A_late=a)


def campaign_gate(runs):
    expected = {(s, c) for s in SEEDS for c in ("C0", "C5", "C10")}
    if len(runs) != 9 or {(r["seed"], r["condition"]) for r in runs} != expected:
        return dict(decision="review", reason="nine unique approved seed/condition runs required")
    if any(r["status"] != "passed" for r in runs):
        return dict(decision="review", reason="incomplete or failed integrity")
    gates = {f"{r['seed']}/{r['condition']}": seed_gate(r["records"]) for r in runs}
    counts = {c: sum(gates[f"{s}/{c}"]["advance"] for s in SEEDS) for c in ("C0", "C5", "C10")}
    return dict(
        decision="advance_to_discussion" if all(n >= 2 for n in counts.values()) else "review",
        seeds_passing=counts,
        gates=gates,
        independent_seed_blocks=3,
    )


def warning_rates(records, expected=10):
    result = {}
    for batch in ("A", "D"):
        for stage in ("pre", "post"):
            for label, predicate in (
                ("relative_mse", lambda m: m["relative_mse"] > 1),
                ("normalized_bias", lambda m: abs(m["normalized_bias"]) > 0.25),
            ):
                result[f"{batch}/{stage}/{label}"] = dict(
                    **fraction(sum(predicate(r[batch][stage]) for r in records), len(records)),
                    expected=expected,
                )
    result["post_gap"] = dict(
        **fraction(sum(r["gap"] > 0.5 for r in records), len(records)), expected=expected
    )
    return result


def learning_rates(report):
    """Do not pool minibatches, full batches, or B into a single warning rate."""
    from btc_risk_rl.pilots.diagnostics import warnings

    rows = report["stability"]
    s = report["settings"]
    k = s["iterations"]
    batches = math.ceil(s["n_a"] / s["minibatch"])
    result = {}
    warning_rows = warnings(report)
    for phase, expected in (
        ("actor", k * s["actor_epochs"] * batches),
        ("critic", k * s["critic_epochs"] * batches),
        ("targets", k),
    ):
        opportunities = [r for r in rows if r["phase"] == phase]
        reasons = {
            reason for w in warning_rows if w.get("phase") == phase for reason in w["reasons"]
        }
        result[phase] = dict(
            completed=len(opportunities),
            expected=expected,
            reasons={
                reason: fraction(
                    sum(reason in w["reasons"] for w in warning_rows if w.get("phase") == phase),
                    len(opportunities),
                )
                for reason in reasons
            },
        )
    result["B"] = dict(
        completed=len(report["audits"]),
        expected=k,
        reasons={
            reason: fraction(
                sum(reason in w["reasons"] for w in warning_rows if w["kind"] == "risk"),
                len(report["audits"]),
            )
            for reason in ("q_b_cvar_gap", "tail_mass", "multiplier")
        },
    )
    risk = [r for r in rows if r["phase"] == "fixed_A" and r["measurement"] == "before_actor"]
    later = [r for r in risk if r["iteration"] >= 1]
    result["risk_active_iterations"] = dict(
        **fraction(sum(r["risk_penalty_nonzero"] > 0 for r in risk), len(risk)), expected=k
    )
    result["risk_active_after_initial"] = dict(
        **fraction(sum(r["risk_penalty_nonzero"] > 0 for r in later), len(later)), expected=k - 1
    )
    result["risk_A"] = [
        dict(
            iteration=r["iteration"],
            shortfalls=fraction(r["shortfall_count"], s["n_a"]),
            altered_coefficients=fraction(r["risk_penalty_nonzero"], s["n_a"]),
            initial_risk_gradient_norm=r["initial_risk_gradient_norm"],
        )
        for r in risk
    ]
    return result
