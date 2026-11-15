"""Frozen paired seed-block inference for OOS v1.2.

Inputs are annualized Sortino values from complete final trajectories. This
module never reads market files, checkpoints, or campaign artifacts.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

BLOCKS = 36
RESAMPLES = 19_999
SEED = 910031
FAMILY_ALPHA = 0.05
MINIMUM_EFFECT = 0.5


def compare_blocks(rows: Sequence[tuple[float, float, float]]) -> dict:
    """Compare C5/C10 to C0 using the same resampled seed blocks.

    Rows must follow the frozen main-seed order. A missing or undefined
    Sortino invalidates the complete primary comparison.
    """
    if len(rows) != BLOCKS or any(len(row) != 3 for row in rows):
        raise ValueError("Primary inference requires 36 complete triplets")
    for row in rows:
        if any(type(value) not in (int, float, np.float64) or
               not math.isfinite(float(value)) for value in row):
            raise ValueError("Primary inference requires finite Sortino values")
    data = np.asarray(rows, dtype=np.float64)
    differences = np.column_stack((data[:, 1] - data[:, 0],
                                   data[:, 2] - data[:, 0]))
    if not np.isfinite(differences).all():
        raise ValueError("Primary inference requires finite differences")
    indices = np.random.default_rng(SEED).integers(0, BLOCKS, size=(RESAMPLES, BLOCKS))
    observed = differences.mean(axis=0)
    uncentered = differences[indices].mean(axis=1)
    centered = differences - observed
    null_means = centered[indices].mean(axis=1)
    p_values = (1 + (null_means >= observed).sum(axis=0)) / (RESAMPLES + 1)
    order = np.argsort(p_values, kind="stable")
    adjusted = np.empty(2, dtype=np.float64)
    previous = 0.0
    for rank, index in enumerate(order):
        previous = max(previous, min(1.0, float((2 - rank) * p_values[index])))
        adjusted[index] = previous
    result = {}
    for index, name in enumerate(("C5_minus_C0", "C10_minus_C0")):
        difference = differences[:, index]
        sd = float(difference.std(ddof=1))
        mean = float(observed[index])
        result[name] = {
            "blocks": BLOCKS,
            "mean_difference": mean,
            "sample_sd_difference": sd,
            "paired_dz": mean / sd if sd > 0 else None,
            "interval_95": [float(value) for value in
                            np.quantile(uncentered[:, index], [0.025, 0.975])],
            "p_one_sided": float(p_values[index]),
            "p_holm": float(adjusted[index]),
            "reject_null": bool(adjusted[index] <= FAMILY_ALPHA and mean > 0),
            "meets_minimum_effect": bool(mean >= MINIMUM_EFFECT),
            "minimum_effect": MINIMUM_EFFECT,
        }
    return result


def compare_audited_records(records: Sequence[dict], *, expected_seeds: Sequence[int]) -> dict:
    """Reject cross-pilot or partial rows before constructing the 36 pairs.

    The caller must independently verify each report, trace and checkpoint
    hash. This function enforces their declared identity and completeness.
    """
    seeds = tuple(expected_seeds)
    if (len(seeds) != BLOCKS or len(set(seeds)) != BLOCKS
            or any(type(seed) is not int for seed in seeds)
            or len(records) != BLOCKS * 3):
        raise ValueError("Expected 36 distinct seeds and 108 audited records")
    indexed = {}
    for row in records:
        seed, condition = row.get("seed"), row.get("condition")
        key = (seed, condition)
        if key in indexed or seed not in seeds or condition not in {"C0", "C5", "C10"}:
            raise ValueError("Duplicate or unexpected seed-condition record")
        if (row.get("profile") != "main-2018-2022"
                or row.get("partition") != "final_2024_2025"
                or row.get("status") != "completed"
                or row.get("audit_accepted") is not True
                or row.get("steps") != 4386
                or row.get("boundary") != "after_dual_and_D"):
            raise ValueError("Pilot, partial or incompatible final evaluation record")
        value = row.get("sortino_annualized")
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError("Undefined or nonfinite primary metric")
        indexed[key] = float(value)
    try:
        paired = [(indexed[(seed, "C0")], indexed[(seed, "C5")],
                   indexed[(seed, "C10")]) for seed in seeds]
    except KeyError as exc:
        raise ValueError("Missing seed-condition record") from exc
    return compare_blocks(paired)
