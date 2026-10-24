"""Read-only CPCV coverage and cost inputs from accepted training-only indexes.

No price, feature-value, validation, final-test, policy, or optimizer file is opened.
The result estimates index eligibility; it does not implement or execute CPCV.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[3]
SHARD = ROOT / "data/processed/p2r-training-h1"
H1 = ROOT / "data/processed/segmented-B-h1"
STEP = 4 * 60 * 60 * 1000
LOOKBACK_BARS = 42
HORIZON = 180
YEARS = tuple(range(2018, 2023))
TRAIN_END = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
ACCEPTED_SHARD_MANIFEST_SHA256 = (
    "62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9"
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_index(path: Path, expected_hash: str, columns: tuple[str, ...]) -> list[dict]:
    actual = digest(path)
    if actual != expected_hash:
        raise ValueError(f"Index hash mismatch: {path}")
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != columns:
            raise ValueError(f"Unexpected index columns: {path}")
        rows = list(reader)
    if not rows or any(row["partition"] != "train" for row in rows):
        raise ValueError(f"Non-training index: {path}")
    return rows


def year_start(year: int) -> int:
    return int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def intervals(years: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    return tuple((year_start(year), year_start(year + 1)) for year in years)


def overlaps(start: int, end: int, years: tuple[int, ...]) -> bool:
    return any(start < hi and lo < end for lo, hi in intervals(years))


def post_test_embargo(initial_ms: int, years: tuple[int, ...], bars: int) -> bool:
    return any(hi <= initial_ms < hi + bars * STEP for _, hi in intervals(years))


def audit() -> dict:
    shard_manifest_path = SHARD / "manifest.json"
    h1_manifest_path = H1 / "manifest.json"
    if digest(shard_manifest_path) != ACCEPTED_SHARD_MANIFEST_SHA256:
        raise ValueError("Training shard manifest differs from the pinned P3 source")
    shard_manifest = json.loads(shard_manifest_path.read_text(encoding="utf-8"))
    h1_manifest = json.loads(h1_manifest_path.read_text(encoding="utf-8"))
    if (
        shard_manifest["status"] != "accepted_for_p2r_training_only"
        or h1_manifest["status"] != "accepted"
        or shard_manifest["train_end_exclusive_ms"] != TRAIN_END
    ):
        raise ValueError("Unexpected manifest scope")
    requested = (
        (SHARD / "episodes.csv", shard_manifest["files"]["episodes.csv"],
         ("episode_id", "segment_id", "partition", "initial_observation_ms",
          "first_target_ms", "last_target_ms", "transitions")),
        (SHARD / "transitions.csv", shard_manifest["files"]["transitions.csv"],
         ("segment_id", "partition", "observation_ms", "target_ms")),
        (H1 / "fit_observations.csv", h1_manifest["files"]["fit_observations.csv"],
         ("open_time", "segment_id", "partition")),
    )
    episodes, transitions, fit = [read_index(*item) for item in requested]
    episodes = [
        {key: int(value) if key != "partition" else value for key, value in row.items()}
        for row in episodes
    ]
    transitions = [
        {key: int(value) if key != "partition" else value for key, value in row.items()}
        for row in transitions
    ]
    fit = [
        {key: int(value) if key != "partition" else value for key, value in row.items()}
        for row in fit
    ]
    if len(episodes) != 7048 or len(transitions) != 10054 or len(fit) != 10073:
        raise ValueError("Unexpected accepted training index cardinality")
    if any(
        row["transitions"] != HORIZON
        or row["last_target_ms"] - row["initial_observation_ms"] != HORIZON * STEP
        or row["last_target_ms"] >= TRAIN_END
        for row in episodes
    ):
        raise ValueError("Episode boundary or horizon mismatch")
    if any(row["target_ms"] >= TRAIN_END for row in transitions):
        raise ValueError("Transition reaches validation")
    if any(row["open_time"] >= TRAIN_END for row in fit):
        raise ValueError("Fit index reaches validation")

    splits = []
    for test_years in combinations(YEARS, 2):
        raw_non_test = [
            row for row in episodes
            if not overlaps(row["first_target_ms"], row["last_target_ms"] + STEP, test_years)
        ]
        after_information_purge = [
            row for row in raw_non_test
            if not overlaps(
                row["initial_observation_ms"] - LOOKBACK_BARS * STEP,
                row["last_target_ms"] + STEP,
                test_years,
            )
        ]
        fit_non_test = [
            row for row in fit
            if not overlaps(row["open_time"] - LOOKBACK_BARS * STEP,
                            row["open_time"] + STEP, test_years)
        ]
        heldout_windows = sum(
            any(lo <= row["first_target_ms"] and row["last_target_ms"] < hi
                for lo, hi in intervals(test_years))
            for row in episodes
        )
        result = {
            "test_years": list(test_years),
            "test_transitions": sum(overlaps(row["target_ms"], row["target_ms"] + STEP,
                                             test_years) for row in transitions),
            "heldout_180_windows_within_one_year": heldout_windows,
            "raw_non_test_episode_starts": len(raw_non_test),
            "after_information_purge_starts": len(after_information_purge),
            "information_purge_removed_from_raw_non_test": len(raw_non_test)
            - len(after_information_purge),
            "embargo": {},
        }
        for embargo_bars in (LOOKBACK_BARS, HORIZON):
            kept = [
                row for row in after_information_purge
                if not post_test_embargo(row["initial_observation_ms"], test_years,
                                         embargo_bars)
            ]
            fit_kept = [
                row for row in fit_non_test
                if not post_test_embargo(row["open_time"], test_years, embargo_bars)
            ]
            result["embargo"][str(embargo_bars)] = {
                "eligible_episode_starts": len(kept),
                "usable_segments_with_starts": len({row["segment_id"] for row in kept}),
                "eligible_scaler_fit_timestamps": len(fit_kept),
                "extra_episode_starts_removed_by_embargo": len(after_information_purge)
                - len(kept),
            }
        splits.append(result)

    forward = []
    for test_year in (2021, 2022):
        cutoff = year_start(test_year) - HORIZON * STEP
        kept = [row for row in episodes if row["last_target_ms"] + STEP <= cutoff]
        fit_kept = [row for row in fit if row["open_time"] + STEP <= cutoff]
        forward.append({
            "train_end_before_gap_utc": datetime.fromtimestamp(cutoff / 1000, tz=timezone.utc)
            .isoformat(),
            "test_year": test_year,
            "eligible_training_episode_starts": len(kept),
            "eligible_scaler_fit_timestamps": len(fit_kept),
            "heldout_year_transitions": sum(
                year_start(test_year) <= row["target_ms"] < year_start(test_year + 1)
                for row in transitions
            ),
        })

    closure_path = ROOT / "docs/evidence/p3-market-2026-10-13/final-closure.json"
    closure = json.loads(closure_path.read_text(encoding="utf-8"))
    runs = closure["runs"]
    if closure["campaign_status"] != "completed" or len(runs) != 18:
        raise ValueError("P3 closure identity mismatch")
    beta0 = [row for row in runs if row["beta"] == 0]
    if len(beta0) != 9 or len({row["seed"] for row in beta0}) != 3:
        raise ValueError("Expected three beta=0 seed blocks")
    by_seed = Counter()
    for row in beta0:
        by_seed[row["seed"]] += row["ledger_wall_seconds"]
    measured_per_block = sum(by_seed.values()) / len(by_seed)
    measured_per_run = sum(by_seed.values()) / len(beta0)
    z_975 = NormalDist().inv_cdf(0.975)
    z_80 = NormalDist().inv_cdf(0.8)
    minimal_effect = 0.5
    precision = {}
    for n in (6, 12, 18, 24, 36):
        precision[str(n)] = {
            str(sigma): {
                "normal_approx_95pct_half_width": z_975 * sigma / math.sqrt(n),
                "normal_approx_power_one_sided_alpha_0_025": NormalDist().cdf(
                    math.sqrt(n) * minimal_effect / sigma - z_975
                ),
            }
            for sigma in (0.5, 1.0, 1.5)
        }
    cost = {
        name: {
            "run_count": runs_count,
            "scaled_unit_wall_seconds": measured_per_run * runs_count,
            "minimum_days_at_8100_work_seconds": math.ceil(
                measured_per_run * runs_count / 8100
            ),
        }
        for name, runs_count in (
            ("CPCV_3_seed_blocks", 90),
            ("CPCV_12_seed_blocks", 360),
            ("forward_2_splits_3_seed_blocks", 18),
            ("forward_2_splits_12_seed_blocks", 72),
        )
    }
    result = {
        "scope": "training-only metadata/index audit; no trajectories or model fitting",
        "inputs_opened": {
            str(path.relative_to(ROOT)): digest(path)
            for path in (shard_manifest_path, h1_manifest_path,
                         *(item[0] for item in requested), closure_path)
        },
        "information_interval": "[initial_observation_ms - 42*4h, last_target_ms + 4h)",
        "embargo_scenarios_bars": [42, 180],
        "years": list(YEARS),
        "training_index_counts": {
            "episode_starts": len(episodes),
            "transitions": len(transitions),
            "scaler_fit_timestamps": len(fit),
        },
        "cpcv": {
            "test_years_per_split": 2,
            "splits": splits,
            "split_count": math.comb(5, 2),
            "nominal_paths": 2 * math.comb(5, 2) // 5,
            "training_runs_at_3_seeds_3_conditions": 10 * 3 * 3,
            "training_runs_at_12_seeds_3_conditions": 10 * 12 * 3,
            "cost_scenarios_same_P3_beta0_rate_not_forecasts": cost,
        },
        "forward_alternative": forward,
        "sortino_precision_sensitivity": {
            "minimal_annualized_effect_proposal": minimal_effect,
            "assumed_paired_sd_scenarios": [0.5, 1.0, 1.5],
            "normal_approximation_only_not_power_validation": precision,
            "normal_approx_n_for_80pct_power_at_sd_1_by_effect": {
                str(effect): math.ceil(((z_975 + z_80) / effect) ** 2)
                for effect in (0.25, 0.5, 0.75)
            },
            "normal_approx_n_for_80pct_power_one_sided_alpha_0_025": {
                str(sigma): math.ceil(((z_975 + z_80) * sigma / minimal_effect) ** 2)
                for sigma in (0.5, 1.0, 1.5)
            },
        },
        "p3_beta0_measured": {
            "nine_run_unit_wall_seconds": sum(by_seed.values()),
            "three_seed_block_unit_wall_seconds": dict(by_seed),
            "mean_three_condition_block_unit_wall_seconds": measured_per_block,
            "nine_run_D_wall_seconds": sum(row["D_wall_seconds"] for row in beta0),
            "cost_scenarios_at_same_measured_rate_not_forecasts": {
                str(n): {
                    "three_condition_runs": 3 * n,
                    "unit_wall_seconds": n * measured_per_block,
                    "minimum_active_days_at_8100_work_seconds_per_day": math.ceil(
                        n * measured_per_block / 8100
                    ),
                }
                for n in (6, 12, 18, 24, 36)
            },
        },
    }
    return result


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
