"""Algebraic fixtures for the P3 v1.1 proposal; no market or agents."""

from __future__ import annotations

import json
from decimal import Decimal as D
from pathlib import Path

EPS = D("1e-12")


def exact_ratio(mse: D, z: D) -> D | None:
    return mse / z if z > 0 else None


def normalized_bias(mean_error: D, z: D) -> D | None:
    return mean_error / z.sqrt() if z > 0 else None


def informative(z: D) -> bool:
    return z > EPS


def pair_pass(b0: dict[str, D], b1: dict[str, D]) -> bool:
    for arm in (b0, b1):
        if not all(informative(arm[name]) for name in ("z_early", "z_d", "z_a", "z_d3")):
            return False
    d0, d1 = exact_ratio(b0["m_d"], b0["z_d"]), exact_ratio(b1["m_d"], b1["z_d"])
    d30 = exact_ratio(b0["m_d3"], b0["z_d3"])
    d31 = exact_ratio(b1["m_d3"], b1["z_d3"])
    a0, a1 = exact_ratio(b0["m_a"], b0["z_a"]), exact_ratio(b1["m_a"], b1["z_a"])
    bias1 = normalized_bias(b1["mean_error_d"], b1["z_d"])
    assert None not in (d0, d1, d30, d31, a0, a1, bias1)
    return all(
        (
            b1["m_d"] <= D("0.95") * b1["z_d"],
            d1 - d0 <= D("-0.05"),
            d31 - d30 <= D("-0.10"),
            a1 - a0 <= D("0.10"),
            abs(bias1) <= D("0.25"),
            d1 - a1 <= D("0.5"),
        )
    )


def main() -> None:
    small_z = D("1e-11")
    old_ratio = small_z / (small_z + EPS)
    assert informative(small_z)
    assert old_ratio == D(10) / D(11) and old_ratio <= D("0.95")
    assert not small_z <= D("0.95") * small_z

    tiny_z = D("1e-13")
    assert tiny_z / (tiny_z + EPS) == D(1) / D(11)
    assert not informative(tiny_z)
    assert not tiny_z <= D("0.95") * tiny_z
    assert D("0.94") <= D("0.95") * D(1)

    paired_r0 = exact_ratio(D("0.9"), D(1))
    paired_r1 = exact_ratio(D("1.6"), D(2))
    assert paired_r1 - paired_r0 == D("-0.1")
    assert D("1.6") - D("0.9") == D("0.7")

    full_late_z_b0 = (D(3) * EPS + D(3) * EPS + D(0)) / D(3)
    full_late_z_b1 = (D(3) * EPS + D(3) * EPS + D(3) * EPS) / D(3)
    assert informative(full_late_z_b0) and informative(full_late_z_b1)
    assert not informative(D(0)) and informative(D(3) * EPS)
    assert exact_ratio(D(0), D(0)) is None
    assert normalized_bias(D(0), D(0)) is None
    assert exact_ratio(tiny_z, tiny_z) == D(1) and not informative(tiny_z)
    assert normalized_bias(D("0.4"), D(4)) == D("0.2")

    control = {
        "z_early": D(1), "z_d": D(1), "z_a": D(1), "z_d3": D(1),
        "m_d": D("0.9"), "m_a": D("0.7"), "m_d3": D("0.9"),
        "mean_error_d": D(0),
    }
    treatment = {
        "z_early": D(1), "z_d": D(1), "z_a": D(1), "z_d3": D(1),
        "m_d": D("0.8"), "m_a": D("0.75"), "m_d3": D("0.75"),
        "mean_error_d": D("0.1"),
    }
    assert pair_pass(control, treatment)
    missing_last_third = {**control, "z_d3": D(0)}
    assert not pair_pass(missing_last_third, treatment)
    failing_treatment = {**treatment, "m_d": D(1)}
    assert not pair_pass(control, failing_treatment)
    blocks = [
        [pair_pass(control, treatment) for _ in ("C0", "C5", "C10")],
        [pair_pass(control, treatment) for _ in ("C0", "C5", "C10")],
        [pair_pass(control, failing_treatment) for _ in ("C0", "C5", "C10")],
    ]
    passing_seed_blocks = sum(all(conditions) for conditions in blocks)
    assert passing_seed_blocks == 2

    results = {
        "scope": "synthetic_algebra_only_no_market_no_training",
        "epsilon": str(EPS),
        "zero_predictor_above_epsilon": {
            "z": str(small_z), "mse": str(small_z),
            "old_ratio": str(old_ratio), "old_rule_passes": True,
            "new_exact_rule_passes": False, "information_gate_passes": True,
        },
        "zero_predictor_below_epsilon": {
            "z": str(tiny_z), "old_ratio": str(tiny_z / (tiny_z + EPS)),
            "new_exact_rule_passes": False, "information_gate_passes": False,
        },
        "paired_distinct_targets": {
            "beta0_ratio": str(paired_r0), "beta1_ratio": str(paired_r1),
            "paired_difference": str(paired_r1 - paired_r0),
            "raw_mse_difference": "0.7",
        },
        "last_third": {
            "beta0_late_z": str(full_late_z_b0),
            "beta0_third3_z": "0", "beta1_late_z": str(full_late_z_b1),
            "late_gate_passes_both": True, "third3_gate_passes_both": False,
        },
        "undefined": {"ratio_at_z0": None, "bias_at_z0": None,
                      "small_positive_z_defined_but_ineligible": True},
        "seed_blocks": {"conditions": blocks, "passing_blocks": passing_seed_blocks,
                        "advance_if_integrity_passes": True},
        "checks": "passed",
    }
    output = Path(__file__).with_name("results.json")
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{output}: {results['checks']}")


if __name__ == "__main__":
    main()
