"""Read-only 10 November capacity calculation from existing accepted ledgers."""

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def read(path):
    return json.loads(path.read_text().splitlines()[-1])


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    old = ROOT / "artifacts/oos-v12-wf-cost-only-05/ledger.jsonl"
    new = ROOT / "artifacts/oos-v12-wf-cost-only-2022-03/ledger.jsonl"
    closure = ROOT / "docs/evidence/oos-wf-2022-03-relaunch-20261110/closure-summary.json"
    p3 = ROOT / "docs/evidence/pilot-closure-v1-2/results.json"
    wf21 = sum(u["seconds"] for u in read(old)["units"])
    wf22 = sum(u["seconds"] for u in read(new)["units"])
    actual = json.loads(closure.read_text())
    p3_rate = json.loads(p3.read_text())["observed_p3_beta0"]["mean_unit_wall_seconds_per_run"]
    available = 8100 - actual["own_total_union_seconds"] + 6 * 8100
    auxiliary = 9 * (wf21 + wf22)
    result = dict(
        status="capacity_sensitivity_not_campaign_result",
        source_sha256={str(p.relative_to(ROOT)): digest(p) for p in (old, new, closure, p3)},
        measured_seconds=dict(wf2021_11_units=wf21, wf2022_11_units=wf22,
                              p3_beta0_mean_run=p3_rate,
                              wf2022_03_global_charge=actual["own_total_union_seconds"]),
        assumptions=dict(days_10_to_16_inclusive=7,
                         global_daily_seconds=10800,
                         daily_closing_reserve_seconds=2700,
                         productive_seconds_today_after_wf2022_03=8100-actual["own_total_union_seconds"],
                         productive_seconds_next_six_days=6*8100,
                         overhead_scenarios_seconds_per_day=[0, 500, 900]),
        extrapolated_seconds=dict(auxiliary_18_runs=auxiliary,
                                  main_108_runs=108*p3_rate,
                                  total_126_runs=auxiliary+108*p3_rate),
        productive_capacity_seconds=available,
        block_sensitivity=[
            dict(assumed_daily_overhead_seconds=overhead,
                 main_runs_continuous_equivalent=(available-auxiliary-7*overhead)/p3_rate,
                 complete_main_triplets_upper_bound=max(0, math.floor(
                     (available-auxiliary-7*overhead)/(3*p3_rate))))
            for overhead in (0, 500, 900)
        ],
        first_admissible_night_20261111=dict(
            note="11–16 November only; all rates extrapolated from prior campaigns",
            productive_capacity_seconds=6 * 8100,
            block_sensitivity=[
                dict(assumed_daily_overhead_seconds=overhead,
                     complete_main_triplets_upper_bound=max(0, math.floor(
                         (6 * 8100 - auxiliary - 6 * overhead) / (3 * p3_rate))))
                for overhead in (0, 500, 900)
            ],
        ),
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
