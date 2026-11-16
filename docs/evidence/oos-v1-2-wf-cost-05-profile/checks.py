"""Summarize an already captured, read-only WF 05 preflight."""

import hashlib
import json
import sys
from pathlib import Path

from btc_risk_rl.pilots.protocol import ROOT
from btc_risk_rl.pilots.wf_cost_replacement_05 import inspect_candidate
from btc_risk_rl.pilots.wf_cost_replacement_05_exec import (
    CAMPAIGN,
    MARKET_EXECUTION_ENABLED,
    REGISTRATION,
    REGISTRATION_SHA256,
    SPEC,
    code_sha256,
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    raw_path = Path(sys.argv[1])
    payload = json.loads(raw_path.read_text())
    preflight = payload["preflight"]
    candidate = inspect_candidate()
    assert payload["protected_or_shared_csv_opened"] is False
    assert payload["market_trajectories_generated"] == 0
    assert payload["optimizer_steps"] == 0
    assert preflight["status"] == "blocked"
    assert "WF replacement campaign has no active approval" in preflight["blockers"]
    assert preflight["inputs"]["ok"] and candidate["historical_artifacts_verified"]
    assert not CAMPAIGN.exists() and not REGISTRATION.exists()
    assert not MARKET_EXECUTION_ENABLED and REGISTRATION_SHA256 is None
    opened = sorted(set(payload["files_opened"]))
    destination = Path(__file__).with_name("opened-files.txt")
    destination.write_text("\n".join(opened) + "\n")
    result = {
        "status": preflight["status"],
        "observed_utc": preflight["observed_utc"],
        "git_commit": payload["git_commit"],
        "blockers": preflight["blockers"],
        "root_05_absent": not CAMPAIGN.exists(),
        "approval_05_absent": not REGISTRATION.exists(),
        "gate_05_closed": not MARKET_EXECUTION_ENABLED and REGISTRATION_SHA256 is None,
        "historical_roots": candidate["historical_roots"],
        "base_design_sha256": sha(ROOT / "docs/protocols/OOS-v1-2-wf-cost-executor-v1.json"),
        "profile_05_sha256": sha(SPEC),
        "code_sha256": code_sha256(),
        "preflight_sha256": sha(raw_path),
        "files_opened_count": len(opened),
        "opened_files_manifest_sha256": sha(destination),
        "protected_or_shared_csv_opened": False,
        "folds": {fold: {key: meta[key] for key in (
            "episodes", "fit_rows", "scaler_sha256", "training_shard_manifest_sha256",
            "validation_observations_loaded", "trajectories_generated")}
                  for fold, meta in payload["fold_metadata"].items()},
        "host": preflight["host"],
        "budget": {key: preflight["budget"][key] for key in (
            "ok", "day_la_paz", "global_spent", "remaining_before_reserve",
            "active_campaigns")},
        "market_trajectories_generated": 0,
        "optimizer_steps": 0,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
