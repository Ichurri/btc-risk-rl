"""Read-only closure audit of the first accepted historical WF 05 Q0."""

import hashlib
import json
from pathlib import Path

import torch

from btc_risk_rl.pilots.p2_budget import state_hash
from btc_risk_rl.pilots.p2r import P2RJournal
from btc_risk_rl.pilots.protocol import ROOT
from btc_risk_rl.pilots.wf_cost_replacement_05 import inspect_candidate
from btc_risk_rl.pilots.wf_cost_replacement_05_exec import inspect_budget, require_campaign
from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal

CAMPAIGN = ROOT / "artifacts/oos-v12-wf-cost-only-05"
EVIDENCE = Path(__file__).resolve().parent
INVOCATION = "d69d5d0157544abc96f3235ab9d339c3"
COMMIT = "cacf6a90d81587ed5de352ffa0f49a54471fdee3"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    approval = require_campaign()
    assert approval["campaign"] == CAMPAIGN.name
    preflight = json.loads((EVIDENCE / "preflight-launch.json").read_text())
    assert preflight["git_commit"] == COMMIT
    assert preflight["preflight"]["status"] == "ready"
    assert preflight["protected_or_shared_csv_opened"] is False
    assert preflight["market_trajectories_generated"] == 0
    assert preflight["optimizer_steps"] == 0

    ledger_path = CAMPAIGN / "ledger.jsonl"
    rows = [json.loads(line) for line in ledger_path.read_text().splitlines()]
    assert rows and all(row["state_hash"] == state_hash(row) for row in rows)
    assert all(row["previous_hash"] == rows[i - 1]["state_hash"]
               for i, row in enumerate(rows) if i)
    state = rows[-1]
    assert state["status"] == "ready" and state["pending"] is None
    assert len(state["units"]) == 1 and state["units"][0]["unit"] == 0
    assert state["units"][0]["run_id"] == "wf-2021"
    assert state["cursor"] == 0
    assert not (CAMPAIGN / "wf-2021/checkpoint-1").exists()
    assert not (CAMPAIGN / "wf-2021/unit-1.json").exists()

    point = CAMPAIGN / "wf-2021/checkpoint-0"
    manifest_path = point / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    state_path = point / "state.pt"
    state_sha = sha(state_path)
    assert manifest["schema_version"] == "p2_complete_boundary_v1"
    assert manifest["git_commit"] == COMMIT
    assert manifest["boundary"] == "after_q0"
    assert manifest["state_sha256"] == state_sha == state["units"][0]["checkpoint_sha256"]
    saved = torch.load(state_path, map_location="cpu", weights_only=True)
    attrs = saved["attrs"]
    assert attrs["boundary"] == "after_q0" and attrs["next_iteration"] == 0
    assert attrs["actor_updates"] == attrs["critic_updates"] == 0
    payload_path = CAMPAIGN / "wf-2021/unit-0.json"
    payload = json.loads(payload_path.read_text())
    assert sha(payload_path) == state["units"][0]["report_sha256"]
    assert payload["checkpoint_sha256"] == state_sha
    assert payload["report"]["boundary"] == "after_q0"
    assert payload["report"]["market_training_executed"] is False
    assert payload["report"]["final_test_accessed"] is False
    assert payload["resources"]["actor_updates"] == 0
    assert payload["resources"]["critic_updates"] == 0
    assert payload["resources"]["trajectories"] == 400
    assert payload["resources"]["transitions"] == 72000
    assert payload["resources"]["diagnostic_trajectories"] == 0

    sessions_path = CAMPAIGN / "sessions.jsonl"
    with WFCostSessionJournal(sessions_path, campaign=CAMPAIGN.name, read_only=True) as sessions:
        assert len(sessions.sessions) == 1
        start, end = sessions.sessions[0]["start"], sessions.sessions[0]["end"]
        assert start["invocation_id"] == INVOCATION
        assert end["status"] == "ready"
        charges = sessions.charges(state, now=end["epoch"])
        assert not charges.blocked
    journal_path = CAMPAIGN / "supervisor.jsonl"
    journal = P2RJournal(journal_path, campaign=CAMPAIGN.name)
    events = [json.loads(line) for line in journal_path.read_text().splitlines()]
    assert journal.last["event"] == "supervisor_exit"
    assert journal.last["status"] == "ready"
    assert all(event["invocation_id"] == INVOCATION for event in events)
    assert [event["event"] for event in events if event["event"] == "unit_completed"] == [
        "unit_completed"]
    assert any(event["event"] == "paused" and event.get("reason") == "first_q0_audit"
               for event in events)
    systemd = (EVIDENCE / "systemd-journal.txt").read_text()
    assert '"status": "ready", "units": 1' in systemd
    assert "Consumed" in systemd and "memory peak" in systemd

    prior = inspect_candidate()
    assert prior["historical_artifacts_verified"] and prior["failed_04_pending"]
    baseline = json.loads((ROOT / "docs/evidence/oos-v1-2-wf-cost-05-profile/results.json")
                          .read_text())["historical_roots"]
    assert prior["historical_roots"] == baseline
    day = "2026-11-01"
    own_ledger = state["days"][day]["charged_wall_seconds"]
    own_session_gap = charges.extra_by_day[day]
    external = inspect_budget()
    assert external["ok"] and not external["active_campaigns"]
    global_charged = external["global_spent"] + own_ledger + own_session_gap
    assert global_charged + 2700 <= 10800
    mapping = {str(path.relative_to(CAMPAIGN)): sha(path)
               for path in sorted(CAMPAIGN.rglob("*")) if path.is_file()}
    result = {
        "campaign": CAMPAIGN.name,
        "code_commit": COMMIT,
        "unit": "oos-wf-cost-20261101-05-session-01.service",
        "invocation_id": INVOCATION,
        "systemd_result": "success",
        "ledger_status": state["status"],
        "accepted_units": len(state["units"]),
        "pending": state["pending"],
        "next_unit": 1,
        "ledger": {"sha256": sha(ledger_path), "rows": len(rows),
                   "state_hash": state["state_hash"],
                   "unit_seconds": state["units"][0]["seconds"]},
        "checkpoint": {"boundary": manifest["boundary"],
                       "state_sha256": state_sha, "manifest_sha256": sha(manifest_path),
                       "actor_updates": attrs["actor_updates"],
                       "critic_updates": attrs["critic_updates"],
                       "next_iteration": attrs["next_iteration"]},
        "report_sha256": sha(payload_path),
        "resources": payload["resources"],
        "sessions": {"sha256": sha(sessions_path), "start_utc": start["utc"],
                     "end_utc": end["utc"], "wall_seconds": end["wall_seconds"],
                     "elapsed_seconds": end["elapsed_seconds"]},
        "supervisor": {"sha256": sha(journal_path), "events": len(events)},
        "budget_accounting": {
            "day_la_paz": day, "external_seconds": external["global_spent"],
            "own_ledger_seconds": own_ledger, "own_session_gap_seconds": own_session_gap,
            "global_charged_seconds": global_charged,
            "remaining_before_reserve_seconds": 10800 - global_charged - 2700,
        },
        "prior_roots": prior["historical_roots"],
        "current_root_files": len(mapping),
        "current_root_mapping_sha256": hashlib.sha256(
            json.dumps(mapping, sort_keys=True).encode()).hexdigest(),
        "preflight_sha256": sha(EVIDENCE / "preflight-launch.json"),
        "systemd_journal_sha256": sha(EVIDENCE / "systemd-journal.txt"),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
