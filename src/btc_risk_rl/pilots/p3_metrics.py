"""P3 v1.1 exact zero-predictor comparison and paired seed-block gate."""

import math

from btc_risk_rl.pilots.p2_metrics import EPS


def pool_exact(metrics):
    """Pool observation sums; stabilized ratios are descriptive only."""
    if not metrics:
        raise ValueError("No P3 observations to pool")
    n = sum(row["count"] for row in metrics)
    sse = sum(row["sse"] for row in metrics)
    q = sum(row["target_sq"] for row in metrics)
    error = sum(row["error_sum"] for row in metrics)
    v_sum = sum(row["prediction_stats"]["mean"] * row["count"] for row in metrics)
    v_sq = sum(
        (row["prediction_stats"]["std"] ** 2 + row["prediction_stats"]["mean"] ** 2)
        * row["count"] for row in metrics
    )
    g_sum = sum(row["target_stats"]["mean"] * row["count"] for row in metrics)
    if (n <= 0 or not all(math.isfinite(x) for x in (sse, q, error, v_sum, v_sq, g_sum))
            or min(sse, q, v_sq) < 0):
        raise ValueError("Invalid P3 observation sums")
    m, z, bias = sse / n, q / n, error / n
    v_mean, g_mean = v_sum / n, g_sum / n
    v2 = v_sq / n
    vg = (v2 + z - m) / 2
    return dict(
        n=n, sse=sse, target_sq=q, error_sum=error, m=m, z=z,
        bias=bias, r0=m / z if z > 0 else None,
        b0=bias / math.sqrt(z) if z > 0 else None,
        r_epsilon=m / (z + EPS), informative=z > EPS,
        prediction_mean=v_mean,
        prediction_std_sample=math.sqrt(max(0.0, (v_sq - n * v_mean**2) / (n - 1)))
        if n >= 2 else None,
        target_mean=g_mean,
        target_std_sample=math.sqrt(max(0.0, (q - n * g_mean**2) / (n - 1)))
        if n >= 2 else None,
        e_v2=v2, e_vg=vg, excess_mse=m - z,
    )


def _windows(records):
    if [r["iteration"] for r in records] != list(range(10)):
        raise ValueError("P3 requires ten consecutive D/A iterations")
    result = {}
    for batch in ("A", "D"):
        for stage in ("pre", "post"):
            for window, indices in (("early", (0, 1, 2)), ("late", (7, 8, 9))):
                result[f"{batch}_{stage}_{window}"] = pool_exact(
                    [records[k][batch][stage] for k in indices]
                )
                for third in range(3):
                    result[f"{batch}_{stage}_{window}_third{third + 1}"] = pool_exact(
                        [records[k][batch][stage]["thirds"][third] for k in indices]
                    )
    return result


def assess_pair(control, treatment):
    """Compare β arms using each arm's own D/A targets and denominator."""
    arms = {"control": _windows(control), "treatment": _windows(treatment)}
    gates = ("D_post_early", "D_post_late", "A_post_late", "D_post_late_third3")
    missing = [f"{arm}/{name.replace('_post', '')}"
               for arm, windows in arms.items() for name in gates
               if not windows[name]["informative"]]

    def difference(name):
        left, right = arms["control"][name], arms["treatment"][name]
        if not left["informative"] or not right["informative"]:
            return None
        return right["r0"] - left["r0"]

    d = difference("D_post_late")
    d3 = difference("D_post_late_third3")
    a = difference("A_post_late")
    treated_d, treated_a = arms["treatment"]["D_post_late"], arms["treatment"]["A_post_late"]
    h1 = treated_d["r0"] - treated_a["r0"] if (treated_d["informative"]
                                                    and treated_a["informative"]) else None
    checks = dict(
        zero_exact=treated_d["informative"] and treated_d["m"] <= 0.95 * treated_d["z"],
        delta_d=d is not None and d <= -0.05,
        delta_d3=d3 is not None and d3 <= -0.10,
        delta_a=a is not None and a <= 0.10,
        bias=treated_d["informative"] and abs(treated_d["b0"]) <= 0.25,
        gap=h1 is not None and h1 <= 0.5,
    )
    return dict(
        **arms, informative=not missing, missing_z_gates=missing,
        delta_d=d, delta_d3=d3, delta_a=a, h1=h1, checks=checks,
        advance=not missing and all(checks.values()),
    )


def assess_campaign(runs):
    from btc_risk_rl.pilots.p3_market import roster

    expected = set(roster())
    identities = [(row.get("seed"), row.get("condition"), row.get("beta")) for row in runs]
    if (len(runs) != 18 or len(set(identities)) != 18 or set(identities) != expected
            or any(type(row.get("seed")) is not int or type(row.get("beta")) is not int
                   for row in runs)
            or any(row.get("status") != "passed" or row.get("integrity", True) is not True
                   for row in runs)):
        return dict(decision="not_evaluable", reason="eighteen intact P3 runs required")
    indexed = {(r["seed"], r["condition"], r["beta"]): r for r in runs}
    try:
        pairs = {
            f"{seed}/{condition}": assess_pair(
                indexed[seed, condition, 0]["records"],
                indexed[seed, condition, 1]["records"],
            )
            for seed in (710031, 710047, 710081)
            for condition in ("C0", "C5", "C10")
        }
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        return dict(decision="not_evaluable", reason=f"Invalid P3 metric records: {exc}")
    blocks = {
        seed: all(pairs[f"{seed}/{condition}"]["advance"]
                  for condition in ("C0", "C5", "C10"))
        for seed in (710031, 710047, 710081)
    }
    return dict(
        decision="advance_to_discussion" if sum(blocks.values()) >= 2 else "review",
        independent_seed_blocks=3, seed_blocks_passing=sum(blocks.values()),
        blocks=blocks, pairs=pairs,
        interpretation="development_diagnostic_not_temporal_generalization",
    )
