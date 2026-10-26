"""Verify closed synthetic evaluation probes and recalculate conditional cost."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROBES = ROOT / "artifacts/oos-synthetic-evaluation-20261026-final"
GUARD_PROBE = ROOT / "artifacts/oos-synthetic-evaluation-20261026-guard"
PRIOR = ROOT / "docs/evidence/pilot-closure-v1-2/results.json"
OUT = Path(__file__).with_name("results.json")
HISTORICAL_SEEDS = {
    410031, 410047, 410081, 510031, 510047, 510081,
    610031, 610047, 610081, 710031, 710047, 710081,
}
RUNS = (
    ("run-1979", "1979", 1979),
    ("run-2190-a", "2190-a", 2190),
    ("run-2190-b", "2190-b", 2190),
    ("run-4386-final", "4386-final", 4386),
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def cost_seed(year: int) -> int:
    value = hashlib.sha256(f"btc-risk-rl/oos-v1.2/wf-cost-only/{year}".encode()).digest()
    return 1 + int.from_bytes(value[:8], "big") % (2**31 - 1)


def read_probe(run_name: str, label: str, steps: int, *, probe_root: Path = PROBES) -> dict:
    root = probe_root / run_name
    closure = json.loads((root / "closure.json").read_text(encoding="utf-8"))
    audit = json.loads((root / "audit.json").read_text(encoding="utf-8"))
    worker = json.loads((root / "worker-result.json").read_text(encoding="utf-8"))
    trace = root / "trace.csv"
    if (closure["status"] != "completed_synthetic" or closure["steps"] != steps
            or closure["supervisor"]["status"] != "passed"
            or worker["trace_sha256"] != sha(trace)
            or audit["trace_sha256"] != sha(trace)
            or not audit["accepted"] or audit["metrics"] != closure["metrics"]):
        raise ValueError("Incomplete or inconsistent synthetic closure")
    if (worker["opened_data_files"] != [
        str(ROOT / "artifacts/p3-approved-v1/run-00-C0-b0/checkpoint-10/state.pt"),
        str(ROOT / "data/processed/p2r-training-h1/manifest.json"),
        str(ROOT / "data/processed/p2r-training-h1/scaler.json"),
        str(ROOT / "configs/initial.toml"),
    ] or any("2023" in path or "2024" in path or "2025" in path
             for path in worker["opened_data_files"])):
        raise ValueError("Probe opened an unexpected data file")
    timing = (probe_root / f"outer-{label}-time.txt").read_text(encoding="utf-8")
    match = re.search(r"elapsed_wall_seconds=([0-9.]+)", timing)
    if match is None:
        raise ValueError("Missing whole-process elapsed wall time")
    if "Finished with result: success" not in timing or "Memory peak:" not in timing:
        raise ValueError("systemd closure or memory measurement missing")
    journal = probe_root / f"journal-{label}.log"
    if "Started oos-v12-synthetic" not in journal.read_text(encoding="utf-8"):
        raise ValueError("systemd journal lacks start record")
    journal_json = probe_root / f"journal-{label}.jsonl"
    invocation_ids = {
        row["_SYSTEMD_INVOCATION_ID"]
        for row in (json.loads(line) for line in journal_json.read_text().splitlines())
        if row.get("_SYSTEMD_INVOCATION_ID")
    }
    if len(invocation_ids) != 1:
        raise ValueError("Expected one systemd invocation per synthetic probe")
    total_bytes = sum(path.stat().st_size for path in root.iterdir() if path.is_file())
    return {
        "steps": steps, "external_wall_seconds_measured": float(match.group(1)),
        "parent_wall_before_closure_seconds": closure["wall_seconds_before_closure"],
        "supervisor_wall_seconds": closure["supervisor"]["wall_seconds"],
        "worker_rss_peak_bytes": closure["worker_rss_peak_bytes"],
        "systemd_memory_peak_reported": re.search(r"Memory peak: ([^\n]+)", timing).group(1),
        "worker_phase_seconds": worker["timings"],
        "parent_audit_seconds": closure["parent_audit_seconds"],
        "run_file_bytes": total_bytes,
        "trace_sha256": sha(trace),
        "closure_sha256": sha(root / "closure.json"),
        "journal_sha256": sha(journal),
        "journal_json_sha256": sha(journal_json),
        "systemd_invocation_id": invocation_ids.pop(),
        "launch_sha256": sha(probe_root / f"launch-{label}.log"),
        "outer_time_sha256": sha(probe_root / f"outer-{label}-time.txt"),
        "checkpoint_sha256": closure["checkpoint_sha256"],
        "scaler_sha256": closure["scaler_sha256"],
        "config_sha256": closure["config_sha256"],
    }


def main() -> dict:
    rows = {name: read_probe(name, label, steps) for name, label, steps in RUNS}
    rows["run-2190-guard"] = read_probe("run-2190", "2190", 2190, probe_root=GUARD_PROBE)
    if len({rows[name]["trace_sha256"] for name in (
        "run-2190-a", "run-2190-b", "run-2190-guard"
    )}) != 1:
        raise ValueError("Equal synthetic runs are not reproducible")
    prior = json.loads(PRIOR.read_text(encoding="utf-8"))
    roster = set(prior["roster"]["main_36"] + prior["roster"]["walk_forward_3"])
    seeds = {str(year): cost_seed(year) for year in (2021, 2022)}
    if len(set(seeds.values())) != 2 or set(seeds.values()) & (roster | HISTORICAL_SEEDS):
        raise ValueError("Cost-only seed collision")
    p3_units = json.loads((ROOT / "artifacts/p3-approved-v1/ledger.jsonl").read_text().splitlines()[-1])["units"]
    p3_max = {kind: max(row["seconds"] for row in p3_units if row["kind"] == kind)
              for kind in ("q0", "iteration")}
    proposed_q0_cap, proposed_iteration_cap, proposed_cost_cap = 120, 180, 5400
    proposed_units = 2 * (1 + 10)
    if (proposed_units != 22 or 2 * (proposed_q0_cap + 10 * proposed_iteration_cap)
            > proposed_cost_cap or p3_max["q0"] >= proposed_q0_cap
            or p3_max["iteration"] >= proposed_iteration_cap):
        raise ValueError("Proposed cost-study unit bounds fail static audit")
    training_rate = prior["observed_p3_beta0"]["mean_unit_wall_seconds_per_run"]
    wf21 = rows["run-1979"]["external_wall_seconds_measured"]
    mean_2190 = sum(rows[name]["external_wall_seconds_measured"] for name in (
        "run-2190-a", "run-2190-b", "run-2190-guard"
    )) / 3
    final = rows["run-4386-final"]["external_wall_seconds_measured"]
    scaled_synthetic = 9 * wf21 + (9 + 108) * mean_2190 + 108 * final
    training_scaled = 126 * training_rate
    allowances = 2 * 10800 + 21600
    productive = training_scaled + allowances
    output = {
        "status": "synthetic_full_process_calibration_only_protocol_not_adopted",
        "probe_root": str(PROBES.relative_to(ROOT)),
        "final_guard_probe_root": str(GUARD_PROBE.relative_to(ROOT)),
        "runs": rows,
        "cost_only_training_seed_proposal": seeds,
        "p3_historical_unit_max_seconds_measured": p3_max,
        "cost_study_proposal_static": {
            "units_exact": proposed_units,
            "q0_hard_cap_seconds": proposed_q0_cap,
            "iteration_hard_cap_seconds": proposed_iteration_cap,
            "sum_unit_hard_caps_seconds": 2 * (proposed_q0_cap + 10 * proposed_iteration_cap),
            "total_productive_cap_seconds": proposed_cost_cap,
            "per_day_productive_cap_seconds": 3600,
            "max_active_days": 2,
        },
        "budget": {
            "global_seconds_per_day": 10800,
            "daily_reserve_seconds": 2700,
            "productive_seconds_per_day": 8100,
            "days_proposed": 20,
            "productive_cap_seconds": 162000,
            "training_126_runs_extrapolated_seconds": training_scaled,
            "evaluation_and_audit_allowances_seconds_not_measured": allowances,
            "synthetic_234_complete_processes_scaled_seconds_not_historical_measurement": scaled_synthetic,
            "plan_training_scaled_plus_allowances_seconds": productive,
            "conditional_days": math.ceil(productive / 8100),
            "conditional_headroom_seconds": 162000 - productive,
            "if_cost_study_5400_charged_to_same_envelope_headroom_seconds": 162000 - productive - 5400,
            "if_cost_study_5400_charged_to_same_envelope_days": math.ceil((productive + 5400) / 8100),
            "training_rate_threshold_seconds_per_run_if_allowances_hold": (162000 - allowances) / 126,
            "training_rate_threshold_seconds_per_run_with_cost_study_cap": (
                162000 - allowances - 5400
            ) / 126,
        },
        "limits": [
            "No historical 2023 or final dataset was opened or evaluated.",
            "Four local systemd units provide two 2190-step replicates but only one 1979 and one 4386 measurement.",
            "Synthetic features and years are fabricated; historical data loading, evaluator adaptation and future training costs remain unknown.",
            "The shell time includes systemd startup, Python imports, supervision, audit and closure; source paths are pinned.",
        ],
    }
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    result = main()
    print(json.dumps({"result": str(OUT), "sha256": sha(OUT),
                      "conditional_headroom_seconds": result["budget"]["conditional_headroom_seconds"]}, sort_keys=True))
