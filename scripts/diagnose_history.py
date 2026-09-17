"""Read-only inventory and hypothetical segmentation; never emits training data."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from btc_risk_rl.config import STEP_MS, load_config, utc_ms
from btc_risk_rl.data.binance import read_raw, sha256


def iso(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat(timespec="milliseconds")


def contiguous_runs(grid, excluded):
    runs, current = [], []
    for t in grid:
        if t in excluded:
            if current:
                runs.append(current)
                current = []
        else:
            current.append(t)
    if current:
        runs.append(current)
    return runs


def impact(grid, excluded, lo, hi, history=42, horizon=180):
    details = []
    for run in contiguous_runs(grid, excluded):
        # observation at j-1 requires 42 preceding bars => first scored target j=43
        usable = [t for j, t in enumerate(run) if j >= history + 1 and lo <= t < hi]
        raw = sum(lo <= t < hi for t in run)
        if raw:
            details.append(
                dict(
                    start_utc=iso(run[0]),
                    end_exclusive_utc=iso(run[-1] + STEP_MS),
                    raw_partition_bars=raw,
                    usable_transitions=len(usable),
                    candidate_starts_180=max(0, len(usable) - horizon + 1),
                    nonoverlapping_windows_180=len(usable) // horizon,
                )
            )
    return dict(
        segments=len(details),
        retained_partition_bars=sum(x["raw_partition_bars"] for x in details),
        usable_transitions=sum(x["usable_transitions"] for x in details),
        candidate_starts_180=sum(x["candidate_starts_180"] for x in details),
        nonoverlapping_windows_180=sum(x["nonoverlapping_windows_180"] for x in details),
        segments_with_180=sum(x["candidate_starts_180"] > 0 for x in details),
        details=details,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    c = load_config(Path("configs/initial.toml"))
    rows, manifest = read_raw(Path("data/raw/development"))
    start, end = utc_ms(c.data.warmup_start), utc_ms(c.data.test_start)
    grid = list(range(start, end, STEP_MS))
    observed = {int(r[0]): r for r in rows}
    missing = set(grid) - set(observed)
    early = {t for t, r in observed.items() if int(r[6]) < t + STEP_MS - 1}
    assert len(missing & early) == 0
    excluded = missing | early
    successors = {
        t + STEP_MS for t in excluded if t + STEP_MS not in excluded and t + STEP_MS < end
    }
    inventory = []
    for t in sorted(excluded):
        inventory.append(
            dict(
                open_utc=iso(t),
                type="missing" if t in missing else "early_close",
                close_utc="" if t in missing else iso(int(observed[t][6])),
                expected_close_utc=iso(t + STEP_MS - 1),
                partition="train",
                rule="absent_from_UTC_grid" if t in missing else "close_time_before_nominal_end",
            )
        )
    bounds = [
        ("warmup", start, utc_ms(c.data.train_start)),
        ("train", utc_ms(c.data.train_start), utc_ms(c.data.validation_start)),
        ("validation", utc_ms(c.data.validation_start), end),
    ]
    counts = {
        name: dict(
            days=(hi - lo) // 86400000,
            expected=(hi - lo) // STEP_MS,
            received=sum(lo <= t < hi for t in observed),
            missing=sum(lo <= t < hi for t in missing),
            early_close=sum(lo <= t < hi for t in early),
        )
        for name, lo, hi in bounds
    }
    scenarios = {}
    for name, bad in [
        ("nominal_continuous_counterfactual", set()),
        ("A_quarantine", excluded),
        ("B_quarantine_plus_reopening", excluded | successors),
    ]:
        scenarios[name] = {part: impact(grid, bad, lo, hi) for part, lo, hi in bounds[1:]}
    result = dict(
        mode="diagnostic_only_no_policy_applied",
        counts=counts,
        overlap_count=0,
        anomaly_blocks=sum(t - STEP_MS not in excluded for t in excluded),
        reopening_candidates=[iso(t) for t in sorted(successors)],
        scenarios=scenarios,
        raw_manifest_sha256=sha256(Path("data/raw/development/manifest.json")),
        final_test_accessed=False,
    )
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "impact.json").write_text(json.dumps(result, indent=2) + "\n")
    with (args.output / "inventory.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(inventory[0]))
        writer.writeheader()
        writer.writerows(inventory)
    print(
        json.dumps(
            {
                "counts": counts,
                "scenarios": {
                    k: {p: {a: b for a, b in v.items() if a != "details"} for p, v in z.items()}
                    for k, z in scenarios.items()
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
