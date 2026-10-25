"""Summarize read-only training-shard and synthetic cost probes."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROBES = ROOT / "artifacts/oos-cost-v12-20261025"
PRIOR = ROOT / "docs/evidence/pilot-closure-v1-2/results.json"
OUT = Path(__file__).with_name("results.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name: str) -> tuple[dict, str]:
    path = PROBES / name / "result.json"
    return json.loads(path.read_text(encoding="utf-8")), digest(path)


def main() -> dict:
    names = [
        "fold-2021-products", "fold-2022-products", "checkpoint",
        "synthetic-wf-2021-equivalent", "synthetic-wf-2022-equivalent",
        "synthetic-2023-equivalent", "synthetic-final-equivalent",
        "audit-wf-2021-equivalent", "audit-wf-2022-equivalent",
        "audit-2023-final-code", "audit-final-final-code",
    ]
    reports = {name: read(name) for name in names}
    fold21, fold22 = (reports[f"fold-{year}-products"][0] for year in (2021, 2022))
    if (fold21["fit_rows"], fold21["episodes"], fold22["fit_rows"], fold22["episodes"]) != (
        5764, 3639, 7703, 4678
    ):
        raise ValueError("Fold coverage differs from accepted index audit")
    if any("segmented-B-h1" in path for fold in (fold21, fold22) for path in fold["opened_files"]):
        raise ValueError("Shared H1 CSV opened")
    for year, fold in ((2021, fold21), (2022, fold22)):
        for name, expected in fold["fold_product_sha256"].items():
            if digest(PROBES / f"fold-{year}-products" / name) != expected:
                raise ValueError("Derived fold product hash mismatch")
    synthetic = {name: reports[f"synthetic-{name}"][0] for name in (
        "wf-2021-equivalent", "wf-2022-equivalent", "2023-equivalent", "final-equivalent"
    )}
    if [synthetic[name]["steps"] for name in synthetic] != [1979, 2190, 2190, 4386]:
        raise ValueError("Synthetic lengths differ from proposed paths")
    if synthetic["wf-2022-equivalent"]["return_sha256"] != synthetic["2023-equivalent"]["return_sha256"]:
        raise ValueError("Equal-length synthetic path is not reproducible")
    for item in synthetic.values():
        if digest(Path(item["return_file"])) != item["return_sha256"]:
            raise ValueError("Synthetic return hash mismatch")
    checkpoint = reports["checkpoint"][0]
    if digest(ROOT / "artifacts/p3-approved-v1/run-00-C0-b0/checkpoint-10/state.pt") != checkpoint["checkpoint_sha256"]:
        raise ValueError("Original checkpoint hash changed")
    prior = json.loads(PRIOR.read_text(encoding="utf-8"))
    training_rate = prior["observed_p3_beta0"]["mean_unit_wall_seconds_per_run"]
    if not math.isclose(training_rate, 726.9355381859673, abs_tol=1e-9):
        raise ValueError("P3 training baseline changed")
    load_samples = [reports["checkpoint"][0], *(item["checkpoint"] for item in synthetic.values())]
    mean_load = sum(item["deserialize_seconds"] + item["load_weights_seconds"] for item in load_samples) / len(load_samples)
    counts = {"wf-2021-equivalent": 9, "wf-2022-equivalent": 9, "2023-equivalent": 108, "final-equivalent": 108}
    fold_measured = sum(item["total_seconds_before_report"] for item in (fold21, fold22))
    synthetic_walks = sum(counts[key] * item["walk_seconds"] for key, item in synthetic.items())
    synthetic_saves = sum(counts[key] * item["save_returns_seconds"] for key, item in synthetic.items())
    synthetic_loads = sum(counts.values()) * mean_load
    audits = {
        "wf-2021-equivalent": "audit-wf-2021-equivalent",
        "wf-2022-equivalent": "audit-wf-2022-equivalent",
        "2023-equivalent": "audit-2023-final-code",
        "final-equivalent": "audit-final-final-code",
    }
    audit_metrics = sum(
        counts[key] * reports[audits[key]][0]["total_seconds_before_report"] for key in counts
    )
    measured_kernel_scaled = fold_measured + synthetic_walks + synthetic_saves + synthetic_loads + audit_metrics
    training_scaled = training_rate * 126
    old_allowances = 10800 + 10800 + 21600
    productive_cap = 20 * 8100
    old_plan = training_scaled + old_allowances
    output = {
        "status": "technical_calibration_only_protocol_not_adopted",
        "local_probe_root": str(PROBES.relative_to(ROOT)),
        "probe_report_sha256": {name: sha for name, (_, sha) in reports.items()},
        "proposal_input_sha256": digest(PRIOR),
        "training_shard_manifest_sha256": fold21["source_sha256"][str(ROOT / "data/processed/p2r-training-h1/manifest.json")],
        "folds_measured_seconds": {str(year): {key: item[key] for key in (
            "rebuild_seconds", "refit_and_transform_seconds", "save_fold_products_seconds",
            "total_seconds_before_report", "fold_product_bytes", "peak_rss_kib",
            "fit_rows", "episodes", "transitions"
        )} for year, item in ((2021, fold21), (2022, fold22))},
        "checkpoint_measured": {"samples_seconds": [item["deserialize_seconds"] + item["load_weights_seconds"] for item in load_samples], "mean_seconds": mean_load, "state_bytes": checkpoint["checkpoint_bytes"], "peak_rss_kib": checkpoint["peak_rss_kib"], "fixed_checkpoint_sha256": checkpoint["checkpoint_sha256"]},
        "synthetic_paths_measured": {key: {k: item[k] for k in (
            "steps", "walk_seconds", "save_returns_seconds", "peak_rss_kib", "return_sha256"
        )} for key, item in synthetic.items()},
        "conditional_scaled_kernel_seconds_not_campaign_measurement": {
            "folds_measured_once": fold_measured,
            "234_checkpoint_loads_scaled_from_five_samples": synthetic_loads,
            "234_synthetic_walks_scaled_from_four_samples": synthetic_walks,
            "synthetic_saves_scaled": synthetic_saves,
            "synthetic_metric_audits_scaled": audit_metrics,
            "total": measured_kernel_scaled,
        },
        "budget": {
            "active_days_cap": 20,
            "global_seconds_per_day": 10800,
            "closure_reserve_seconds_per_day": 2700,
            "productive_seconds_cap": productive_cap,
            "p3_beta0_training_rate_measured_seconds_per_run": training_rate,
            "126_training_runs_extrapolated_seconds": training_scaled,
            "evaluation_and_audit_allowances_unmeasured_seconds": old_allowances,
            "old_plan_seconds_scaled_plus_allowances": old_plan,
            "old_plan_minimum_days_conditional": math.ceil(old_plan / 8100),
            "headroom_seconds_conditional": productive_cap - old_plan,
            "max_mean_training_seconds_per_run_if_other_allowances_hold": (productive_cap - old_allowances) / 126,
            "training_cost_factor_limit_if_other_allowances_hold": (productive_cap - old_allowances) / training_scaled,
            "scenarios_other_allowances_unchanged": {str(factor): {"productive_seconds": training_scaled * factor + old_allowances, "minimum_days": math.ceil((training_scaled * factor + old_allowances) / 8100), "within_20_days": training_scaled * factor + old_allowances <= productive_cap} for factor in (1.0, 1.2, 1.3, 1.5)},
        },
        "limitations": [
            "Synthetic accounting loop is not the future validated continuous evaluator.",
            "Per-process import, systemd, preflight, checkpoint creation, training variation and actual future data loading are not included in kernel timings.",
            "No 2023 or 2024-2025 data were opened; full-path evaluation cost remains unmeasured.",
        ],
    }
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    result = main()
    print(json.dumps({"result": str(OUT), "sha256": digest(OUT), "headroom_seconds_conditional": result["budget"]["headroom_seconds_conditional"]}, sort_keys=True))
