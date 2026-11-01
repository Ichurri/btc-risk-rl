"""Read-only audit of WF 05 reentry blocked before launch."""

import hashlib
import json
from pathlib import Path

from btc_risk_rl.pilots.protocol import ROOT

EVIDENCE = Path(__file__).resolve().parent
MIN_MEMORY = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    payload = json.loads((EVIDENCE / "preflight.json").read_text())
    preflight = payload["preflight"]
    before = json.loads((EVIDENCE / "q0-audit-before.json").read_text())
    after = json.loads((EVIDENCE / "q0-audit-after.json").read_text())
    original = json.loads((ROOT / "docs/evidence/oos-v1-2-wf-cost-05-q0-20261101"
                           / "audit-q0.json").read_text())
    assert before == after == original
    assert preflight["status"] == "blocked"
    assert preflight["blockers"] == ["Power, battery, memory or disk guard failed"]
    host = preflight["host"]
    assert host["power"]["ac"] and host["power"]["battery_percent"] >= 50
    assert host["memory_available_bytes"] < MIN_MEMORY
    assert host["disk_free_bytes"] >= 20 * 1024**3
    assert host["linger"] == "yes" and host["user_manager"] == "running"
    budget = preflight["budget"]
    assert budget["ok"] and not budget["active_campaigns"]
    assert budget["remaining_before_reserve"] >= 180
    assert preflight["root_exists"] and preflight["market_execution_enabled"]
    assert preflight["inputs"]["ok"]
    assert payload["protected_or_shared_csv_opened"] is False
    assert payload["market_trajectories_generated"] == payload["optimizer_steps"] == 0
    assert before["ledger_status"] == "ready" and before["accepted_units"] == 1
    assert before["pending"] is None and before["next_unit"] == 1
    assert (EVIDENCE / "systemd-running-units.txt").read_text().strip() == (
        "UNIT LOAD ACTIVE SUB DESCRIPTION\n\n0 loaded units listed.")
    assert sha(EVIDENCE / "q0-audit-before.json") == sha(EVIDENCE / "q0-audit-after.json")
    result = {
        "status": "blocked_before_session_02",
        "observed_utc": preflight["observed_utc"],
        "git_commit": payload["git_commit"],
        "blockers": preflight["blockers"],
        "memory_available_bytes": host["memory_available_bytes"],
        "memory_min_bytes": MIN_MEMORY,
        "memory_deficit_bytes": MIN_MEMORY - host["memory_available_bytes"],
        "ac": host["power"]["ac"],
        "battery_percent": host["power"]["battery_percent"],
        "disk_free_bytes": host["disk_free_bytes"],
        "linger": host["linger"],
        "user_manager": host["user_manager"],
        "global_budget_external_seconds": budget["global_spent"],
        "q0_global_charged_seconds": before["budget_accounting"]["global_charged_seconds"],
        "remaining_before_reserve_with_q0_seconds": 10800 - 2700
        - budget["global_spent"] - before["budget_accounting"]["global_charged_seconds"],
        "accepted_units_after": after["accepted_units"],
        "ledger_status_after": after["ledger_status"],
        "pending_after": after["pending"],
        "q0_checkpoint_sha256": after["checkpoint"]["state_sha256"],
        "q0_root_mapping_sha256": after["current_root_mapping_sha256"],
        "q0_audit_sha256": sha(EVIDENCE / "q0-audit-before.json"),
        "preflight_sha256": sha(EVIDENCE / "preflight.json"),
        "files_opened_count": len(payload["files_opened"]),
        "protected_or_shared_csv_opened": False,
        "new_units_started": 0,
        "market_trajectories_generated_by_preflight": 0,
        "optimizer_steps_by_preflight": 0,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
