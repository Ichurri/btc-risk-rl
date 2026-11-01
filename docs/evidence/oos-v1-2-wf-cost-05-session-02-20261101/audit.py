"""Read-only audit of the second WF 05 historical service session."""

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

ROOT_05 = ROOT / "artifacts/oos-v12-wf-cost-only-05"
EVIDENCE = Path(__file__).resolve().parent
INVOCATION = "16d210a2098e4ab58f83cf8fbb7d0423"
CODE_COMMIT = "0b06b7e70d88bdf66f6db47e0fc33152857fec6a"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert require_campaign()["campaign"] == ROOT_05.name
    preflight = json.loads((EVIDENCE / "preflight-launch.json").read_text())
    assert preflight["git_commit"] == CODE_COMMIT
    assert preflight["preflight"]["status"] == "ready"
    assert not preflight["preflight"]["blockers"]
    assert preflight["protected_or_shared_csv_opened"] is False
    assert preflight["market_trajectories_generated"] == preflight["optimizer_steps"] == 0
    original_q0 = json.loads((EVIDENCE / "q0-before.json").read_text())
    published_q0 = json.loads((ROOT / "docs/evidence/oos-v1-2-wf-cost-05-q0-20261101"
                               / "audit-q0.json").read_text())
    assert original_q0 == published_q0

    ledger_path = ROOT_05 / "ledger.jsonl"
    ledger_rows = [json.loads(line) for line in ledger_path.read_text().splitlines()]
    previous = None
    for row in ledger_rows:
        assert row["previous_hash"] == previous and row["state_hash"] == state_hash(row)
        previous = row["state_hash"]
    state = ledger_rows[-1]
    assert state["status"] == "ready" and state["pending"] is None
    assert len(state["units"]) == 11 and state.get("failure") is None
    assert [(unit["run_id"], unit["unit"]) for unit in state["units"]] == [
        ("wf-2021", unit) for unit in range(11)]
    assert state["cursor"] == 1
    assert not (ROOT_05 / "wf-2022/unit-0.json").exists()
    assert not (ROOT_05 / "wf-2022/checkpoint-0").exists()

    accepted = []
    for unit, ledger_unit in enumerate(state["units"]):
        work = ROOT_05 / "wf-2021"
        report_path = work / f"unit-{unit}.json"
        payload = json.loads(report_path.read_text())
        checkpoint = work / f"checkpoint-{unit}"
        state_path = checkpoint / "state.pt"
        manifest_path = checkpoint / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        checkpoint_sha = sha(state_path)
        expected_boundary = "after_q0" if unit == 0 else "after_dual_and_D"
        assert ledger_unit["checkpoint_sha256"] == checkpoint_sha
        assert ledger_unit["report_sha256"] == sha(report_path)
        assert payload["checkpoint_sha256"] == manifest["state_sha256"] == checkpoint_sha
        assert payload["report"]["boundary"] == manifest["boundary"] == expected_boundary
        assert payload["report"]["market_training_executed"] is (unit > 0)
        assert payload["report"]["final_test_accessed"] is False
        assert (payload["report"]["actor_updates"],
                payload["report"]["critic_updates"]) == (8 * unit, 16 * unit)
        assert manifest["git_commit"] == (
            published_q0["code_commit"] if unit == 0 else CODE_COMMIT)
        d_rows = [phase for phase in payload["report"]["telemetry"]
                  if phase["phase"] == "D" and phase["iteration"] == unit - 1]
        assert len(d_rows) == (0 if unit == 0 else 1)
        accepted.append({
            "unit": unit,
            "ledger_wall_seconds": ledger_unit["seconds"],
            "algorithm_seconds": payload["algorithm_seconds"],
            "save_seconds": payload["save_seconds"],
            "diagnostic_D_seconds": None if not d_rows else d_rows[0]["wall_seconds"],
            "resources": payload["resources"],
            "report_sha256": sha(report_path),
            "checkpoint_sha256": checkpoint_sha,
            "checkpoint_manifest_sha256": sha(manifest_path),
        })
    final_point = ROOT_05 / "wf-2021/checkpoint-10/state.pt"
    final_state = torch.load(final_point, map_location="cpu", weights_only=True)
    attrs = final_state["attrs"]
    assert attrs["boundary"] == "after_dual_and_D"
    assert attrs["next_iteration"] == 10
    assert attrs["actor_updates"] == 80 and attrs["critic_updates"] == 160
    assert accepted[0]["checkpoint_sha256"] == published_q0["checkpoint"]["state_sha256"]

    sessions_path = ROOT_05 / "sessions.jsonl"
    with WFCostSessionJournal(sessions_path, campaign=ROOT_05.name, read_only=True) as sessions:
        assert len(sessions.sessions) == 2
        first, second = sessions.sessions
        assert first["end"]["status"] == second["end"]["status"] == "ready"
        assert second["start"]["invocation_id"] == INVOCATION
        charges = sessions.charges(state, now=second["end"]["epoch"])
        assert not charges.blocked
    supervisor_path = ROOT_05 / "supervisor.jsonl"
    journal = P2RJournal(supervisor_path, campaign=ROOT_05.name)
    events = [json.loads(line) for line in supervisor_path.read_text().splitlines()]
    current_events = [row for row in events if row.get("invocation_id") == INVOCATION]
    assert journal.last["event"] == "supervisor_exit"
    assert journal.last["status"] == "ready"
    assert len([row for row in current_events if row["event"] == "unit_completed"]) == 10
    assert current_events[-2]["event"] == "paused"
    assert current_events[-2]["reason"] == "budget"
    assert not any(row["event"] == "resource_guard_failed" for row in current_events)
    systemd_show = (EVIDENCE / "systemd-show.txt").read_text()
    systemd_journal = (EVIDENCE / "systemd-journal.txt").read_text()
    assert "Result=success" in systemd_show and "ExecMainStatus=0" in systemd_show
    assert '{"status": "ready", "units": 11}' in systemd_journal

    prior = inspect_candidate()
    prior_baseline = json.loads((ROOT / "docs/evidence/oos-v1-2-wf-cost-05-profile"
                                 / "results.json").read_text())["historical_roots"]
    assert prior["historical_roots"] == prior_baseline
    # Anchor the budget snapshot to this session's close, not audit rerun time.
    external = inspect_budget(now=second["end"]["epoch"])
    assert external["ok"] and not external["active_campaigns"]
    day = "2026-11-01"
    ledger_charge = state["days"][day]["charged_wall_seconds"]
    session_gap = charges.extra_by_day[day]
    total_charge = external["global_spent"] + ledger_charge + session_gap
    assert total_charge < 10800 - 2700
    assert ledger_charge + 120 > 3600  # Next Q0 cannot be admitted today.
    mapping = {str(path.relative_to(ROOT_05)): sha(path)
               for path in sorted(ROOT_05.rglob("*")) if path.is_file()}
    result = {
        "status": state["status"], "accepted_units": len(accepted),
        "pending": state["pending"], "next_unit": "wf-2022/Q0",
        "pause_reason": "budget", "failure": state.get("failure"),
        "unit": "oos-wf-cost-20261101-05-session-02.service",
        "invocation_id": INVOCATION, "systemd_result": "success",
        "ledger_sha256": sha(ledger_path), "ledger_rows": len(ledger_rows),
        "ledger_state_hash": state["state_hash"],
        "sessions_sha256": sha(sessions_path),
        "session_02_start_utc": second["start"]["utc"],
        "session_02_end_utc": second["end"]["utc"],
        "session_02_wall_seconds": second["end"]["wall_seconds"],
        "session_01_wall_seconds": first["end"]["wall_seconds"],
        "supervisor_sha256": sha(supervisor_path),
        "supervisor_rows": len(events),
        "resource_guard_failed_events": 0,
        "accepted": accepted,
        "resources_total": state["resources"],
        "checkpoint_q0_unchanged": accepted[0]["checkpoint_sha256"],
        "checkpoint_10_sha256": accepted[-1]["checkpoint_sha256"],
        "budget_accounting": {
            "day_la_paz": day, "external_campaign_seconds": external["global_spent"],
            "own_ledger_span_seconds": ledger_charge,
            "own_session_gap_seconds": session_gap,
            "global_charged_seconds": total_charge,
            "remaining_global_before_reserve_seconds": 10800 - 2700 - total_charge,
            "remaining_own_daily_seconds": 3600 - (ledger_charge + session_gap),
            "next_unit_cap_seconds": 120,
        },
        "prior_roots": prior["historical_roots"],
        "root_file_count": len(mapping),
        "root_mapping_sha256": hashlib.sha256(
            json.dumps(mapping, sort_keys=True).encode()).hexdigest(),
        "preflight_sha256": sha(EVIDENCE / "preflight-launch.json"),
        "systemd_journal_sha256": sha(EVIDENCE / "systemd-journal.txt"),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
