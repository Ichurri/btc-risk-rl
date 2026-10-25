"""Read-only cost and seed arithmetic for the unadopted OOS v1.2 proposal.

Only two versioned JSON summaries are read. No market, policy, or checkpoint
file is opened, and the script never runs training or evaluation.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[3]
P3_CLOSURE = ROOT / "docs/evidence/p3-market-2026-10-13/final-closure.json"
V11_AUDIT = ROOT / "docs/evidence/pilot-closure-v1-1/cpcv-index-results.json"
EXPECTED = {
    P3_CLOSURE: "1d96dd5ed2cb4af27a0f3993501ea7c40ece67ccc5862fe0f9d7b0049c033c6d",
    V11_AUDIT: "30c793e4765b6615169123117dfb6719b07b8ed662d4617df864a225acb6ff2c",
}
DAY_SECONDS = 10_800
DAILY_RESERVE_SECONDS = 2_700
WORK_SECONDS = DAY_SECONDS - DAILY_RESERVE_SECONDS
EVALUATION_2023_CAP = 10_800
FINAL_EVALUATION_CAP = 10_800
AUDIT_REFIT_INFERENCE_CAP = 21_600
HISTORICAL_SEEDS = {
    410031, 410047, 410081,
    510031, 510047, 510081,
    610031, 610047, 610081,
    710031, 710047, 710081,
}


def checked_json(path: Path) -> dict:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != EXPECTED[path]:
        raise ValueError(f"Versioned cost input changed: {path}")
    return json.loads(data)


def seeds(namespace: str, count: int) -> list[int]:
    result = []
    for index in range(count):
        label = f"btc-risk-rl/oos-v1.2/{namespace}/{index:02d}"
        digest = hashlib.sha256(label.encode("ascii")).digest()
        result.append(1 + int.from_bytes(digest[:8], "big") % (2**31 - 1))
    if len(set(result)) != count or set(result) & HISTORICAL_SEEDS:
        raise ValueError("Seed collision with another candidate or pilot")
    return result


def budget(main_blocks: int, forward_blocks: int, run_wall_seconds: float) -> dict:
    main_runs = main_blocks * 3
    forward_runs = 2 * forward_blocks * 3
    main = main_runs * run_wall_seconds
    forward = forward_runs * run_wall_seconds
    productive = (main + forward + EVALUATION_2023_CAP + FINAL_EVALUATION_CAP
                  + AUDIT_REFIT_INFERENCE_CAP)
    days = math.ceil(productive / WORK_SECONDS)
    reserve = days * DAILY_RESERVE_SECONDS
    return {
        "main_blocks": main_blocks,
        "main_training_runs": main_runs,
        "main_training_scaled_seconds_not_measured": main,
        "walk_forward_blocks_per_cut": forward_blocks,
        "walk_forward_training_runs": forward_runs,
        "walk_forward_scaled_seconds_not_measured": forward,
        "evaluation_2023_planning_cap_seconds_not_measured": EVALUATION_2023_CAP,
        "final_evaluation_planning_cap_seconds_not_measured": FINAL_EVALUATION_CAP,
        "audit_refit_inference_planning_cap_seconds_not_measured": AUDIT_REFIT_INFERENCE_CAP,
        "productive_seconds_planned_or_scaled": productive,
        "minimum_active_days_if_every_cap_and_scaled_rate_hold": days,
        "daily_reserve_seconds": DAILY_RESERVE_SECONDS,
        "aggregate_reserved_seconds": reserve,
        "components_plus_reserved_seconds": productive + reserve,
        "total_daily_windows_seconds": days * DAY_SECONDS,
        "unallocated_work_seconds_in_windows": days * WORK_SECONDS - productive,
    }


def sensitivity(blocks: int, effect: float = 0.5) -> dict:
    normal = NormalDist()
    critical = normal.inv_cdf(0.975)  # First Holm threshold, one-sided 0.025.
    for_power = {}
    for sd in (0.5, 1.0, 1.5):
        for_power[str(sd)] = {
            "assumed_paired_sortino_sd": sd,
            "normal_approx_95pct_half_width": critical * sd / math.sqrt(blocks),
            "normal_approx_power_for_effect_0_5_first_Holm_threshold": normal.cdf(
                math.sqrt(blocks) * effect / sd - critical
            ),
            "blocks_for_80pct_normal_approx_power": math.ceil(
                ((critical + normal.inv_cdf(0.8)) * sd / effect) ** 2
            ),
        }
    return for_power


def main() -> dict:
    closure = checked_json(P3_CLOSURE)
    prior = checked_json(V11_AUDIT)
    if (closure["campaign_status"] != "completed"
            or closure["accepted_units"] != 198
            or prior["training_index_counts"]["episode_starts"] != 7048):
        raise ValueError("Prior evidence does not match accepted P3/H1 scope")
    beta0 = [row for row in closure["runs"] if row["beta"] == 0]
    if len(beta0) != 9 or len({row["seed"] for row in beta0}) != 3:
        raise ValueError("P3 beta=0 timing sample is incomplete")
    measured = sum(row["ledger_wall_seconds"] for row in beta0)
    mean_run = measured / len(beta0)
    main_seeds = seeds("main", 36)
    forward_seeds = seeds("walk-forward", 3)
    if set(main_seeds) & set(forward_seeds):
        raise ValueError("Main and forward seed streams must be disjoint")
    roster = {"main_36": main_seeds, "walk_forward_3": forward_seeds}
    roster_bytes = json.dumps(roster, sort_keys=True, separators=(",", ":")).encode()
    return {
        "status": "proposal_not_authorized_no_execution",
        "inputs_sha256": {str(path.relative_to(ROOT)): value
                          for path, value in EXPECTED.items()},
        "observed_p3_beta0": {
            "run_count": len(beta0),
            "unit_wall_seconds": measured,
            "mean_unit_wall_seconds_per_run": mean_run,
            "D_wall_seconds_inside_unit_wall": sum(row["D_wall_seconds"] for row in beta0),
            "campaign_unit_wall_seconds_both_betas": closure["total_ledger_unit_wall_seconds"],
            "campaign_charged_seconds_both_betas": sum(
                day["charged_wall_seconds"] for day in closure["days"].values()
            ),
        },
        "roster": roster,
        "roster_canonical_json_sha256": hashlib.sha256(roster_bytes).hexdigest(),
        "budget_assumptions": {
            "global_day_seconds_America_La_Paz": DAY_SECONDS,
            "daily_closure_reserve_seconds": DAILY_RESERVE_SECONDS,
            "admissible_productive_seconds_per_day": WORK_SECONDS,
            "evaluation_caps_are_allowances_not_timings": True,
            "walk_forward_same_full_run_rate_is_unverified": True,
        },
        "budgets": {
            "candidate_36_main_3_forward": budget(36, 3, mean_run),
            "stress_36_main_36_forward": budget(36, 36, mean_run),
            "exploratory_12_main_3_forward": budget(12, 3, mean_run),
        },
        "sortino_delta_0_5_normal_only": {
            "36_blocks": sensitivity(36),
            "12_blocks": sensitivity(12),
        },
        "forward_index_coverage_from_v1_1": prior["forward_alternative"],
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
