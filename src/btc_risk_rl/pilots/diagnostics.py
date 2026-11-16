"""Prespecified P0 warnings; never select, stop, or change the algorithm by performance."""

import math


def warnings(report):
    result = []
    for row in report["stability"]:
        if any(isinstance(v, (int, float)) and not math.isfinite(v) for v in row.values()):
            raise ValueError("Nonfinite stability diagnostic")
        reasons = []
        if row.get("ratio_min", 1) < 0.5 or row.get("ratio_max", 1) > 2:
            reasons.append("ratio_range")
        if row.get("surrogate_clip_fraction", 0) > 0.5:
            reasons.append("active_clip")
        if row.get("gradient_norm", 0) > 100:
            reasons.append("gradient_norm")
        if row.get("critic_relative_mse", row.get("relative_mc_mse", 0)) > 1:
            reasons.append("critic_relative_mse")
        if reasons:
            result.append(
                dict(
                    kind="stability",
                    phase=row["phase"],
                    iteration=row["iteration"],
                    reasons=reasons,
                )
            )
    for row in report["audits"]:
        reasons = []
        if abs(row["rho_q"] - row["rho_b"]) > 0.05:
            reasons.append("q_b_cvar_gap")
        if min(row["q_tail"]["mass"], row["b_tail"]["mass"]) < 20:
            reasons.append("tail_mass")
        if row["lambda_after"] > 1:
            reasons.append("multiplier")
        if reasons:
            result.append(dict(kind="risk", iteration=row["iteration"], reasons=reasons))
    for row in report["collection_diagnostics"]:
        if row.get("near_endpoint_fraction", 0) > 0.01:
            result.append(
                dict(
                    kind="actions",
                    role=row["role"],
                    iteration=row["iteration"],
                    reasons=["near_endpoint"],
                )
            )
    return result
