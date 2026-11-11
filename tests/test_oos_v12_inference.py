"""Algebraic checks for the frozen seed-block comparison; no market data."""

import math

import pytest


def test_constant_positive_and_zero_effects_obey_centered_bootstrap_and_holm():
    from btc_risk_rl.evaluation.inference import compare_blocks

    rows = [(float(i), float(i + 1), float(i)) for i in range(36)]
    result = compare_blocks(rows)
    five, ten = result["C5_minus_C0"], result["C10_minus_C0"]
    assert five["mean_difference"] == pytest.approx(1)
    assert five["p_one_sided"] == pytest.approx(1 / 20000)
    assert five["p_holm"] == pytest.approx(2 / 20000)
    assert five["interval_95"] == pytest.approx([1, 1])
    assert five["reject_null"] is True
    assert five["meets_minimum_effect"] is True
    assert five["paired_dz"] is None
    assert ten["p_one_sided"] == 1
    assert ten["p_holm"] == 1
    assert ten["reject_null"] is False
    assert ten["meets_minimum_effect"] is False


def test_negative_effect_cannot_be_rescued_by_shared_level_or_holm():
    from btc_risk_rl.evaluation.inference import compare_blocks

    rows = [(1000 + float(i), 999 + float(i), 998 + float(i)) for i in range(36)]
    result = compare_blocks(rows)
    for name, expected in (("C5_minus_C0", -1), ("C10_minus_C0", -2)):
        item = result[name]
        assert item["mean_difference"] == expected
        assert item["p_one_sided"] == 1
        assert item["p_holm"] == 1
        assert item["reject_null"] is False


def test_missing_or_undefined_triplet_refuses_primary_contrast():
    from btc_risk_rl.evaluation.inference import compare_blocks

    complete = [(0.0, 1.0, 2.0)] * 36
    with pytest.raises(ValueError, match="36 complete"):
        compare_blocks(complete[:-1])
    for bad in (None, math.nan, math.inf):
        rows = list(complete)
        rows[12] = (0.0, bad, 2.0)
        with pytest.raises(ValueError, match="finite"):
            compare_blocks(rows)


def test_seed_block_pairing_uses_position_not_condition_level():
    from btc_risk_rl.evaluation.inference import compare_blocks

    rows = [(float(i), float(i + i % 3), float(i - i % 2)) for i in range(36)]
    shifted = [(a + 1000 * i, b + 1000 * i, c + 1000 * i)
               for i, (a, b, c) in enumerate(rows)]
    left, right = compare_blocks(rows), compare_blocks(shifted)
    for name in ("C5_minus_C0", "C10_minus_C0"):
        assert left[name]["mean_difference"] == pytest.approx(
            right[name]["mean_difference"])
        assert left[name]["p_one_sided"] == right[name]["p_one_sided"]


def test_audited_records_reject_pilot_or_partial_and_pair_exact_roster():
    from btc_risk_rl.evaluation.inference import compare_audited_records

    seeds = tuple(range(100, 136))
    records = [dict(seed=seed, condition=condition,
                    profile="main-2018-2022", partition="final_2024_2025",
                    status="completed", audit_accepted=True, steps=4386,
                    boundary="after_dual_and_D", sortino_annualized=float(value))
               for seed in seeds for condition, value in
               (("C0", 0), ("C5", 1), ("C10", 2))]
    result = compare_audited_records(records, expected_seeds=seeds)
    assert result["C5_minus_C0"]["mean_difference"] == 1
    for changes in ({"profile": "p3-approved-v1"}, {"status": "partial"},
                    {"partition": "technical_2023"}, {"audit_accepted": False},
                    {"steps": 180}, {"sortino_annualized": None}):
        altered = [dict(row) for row in records]
        altered[0].update(changes)
        with pytest.raises(ValueError):
            compare_audited_records(altered, expected_seeds=seeds)
    with pytest.raises(ValueError, match="Duplicate|missing"):
        compare_audited_records(records[1:] + [records[1]], expected_seeds=seeds)
