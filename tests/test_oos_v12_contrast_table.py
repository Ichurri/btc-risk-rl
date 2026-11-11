"""Confirmatory table formatting uses invented completed records only."""

import pytest


def _records():
    rows = []
    for seed in range(100, 136):
        for condition, sortino in (("C0", 0.5), ("C5", 1.1), ("C10", 0.4)):
            rows.append({
                "seed": seed, "condition": condition,
                "profile": "main-2018-2022", "partition": "final_2024_2025",
                "status": "completed", "audit_accepted": True,
                "steps": 4386, "boundary": "after_dual_and_D",
                "sortino_annualized": sortino,
            })
    return rows


def test_contrast_table_lists_every_paired_block_and_frozen_decisions():
    from btc_risk_rl.reporting.oos_contrast import render_contrast_table

    table = render_contrast_table(_records(), expected_seeds=tuple(range(100, 136)),
                                  source="invented reports SHA-256 " + "a" * 64)
    assert "36 bloques pareados" in table
    assert "C5−C0" in table and "C10−C0" in table
    assert table.count("| 100 |") == 1
    assert table.count("| 135 |") == 1
    assert "+0,600" in table and "−0,100" in table
    assert "Holm" in table and "Sortino anualizado" in table
    assert "evaluación fuera de muestra" in table


def test_contrast_table_rejects_a_missing_run():
    from btc_risk_rl.reporting.oos_contrast import render_contrast_table

    with pytest.raises(ValueError, match="108"):
        render_contrast_table(_records()[:-1], expected_seeds=tuple(range(100, 136)),
                              source="invented")
