"""Read-only audit of the failed WF 04 continuation; writes JSON to stdout."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CAMPAIGN = ROOT / "artifacts/oos-v12-wf-cost-only-04"
Q0 = ROOT / "docs/evidence/oos-v1-2-wf-cost-04-q0-20261030/audit-q0.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def chained(path, *, field, previous):
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    prior = None
    for row in rows:
        assert row[previous] == prior, (path, "broken chain")
        expected = hashlib.sha256(
            json.dumps({k: v for k, v in row.items() if k != field},
                       sort_keys=True, allow_nan=False).encode()
        ).hexdigest()
        assert row[field] == expected, (path, "broken digest")
        prior = row[field]
    return rows


def main():
    original = json.loads(Q0.read_text())
    files = {str(path.relative_to(CAMPAIGN)): sha(path)
             for path in sorted(CAMPAIGN.rglob("*")) if path.is_file()}
    immutable = ("folds/", "wf-2021/checkpoint-0/", "wf-2021/unit-0.json",
                 "wf-2021/request-0.json", "wf-2021/closing-0.json",
                 "wf-2021/worker-0.log")
    assert all(files.get(name) == digest
               for name, digest in original["root_files_sha256"].items()
               if name.startswith(immutable))
    rows = chained(CAMPAIGN / "ledger.jsonl", field="state_hash",
                   previous="previous_hash")
    state = rows[-1]
    assert state["status"] == "failed" and len(state["units"]) == 8
    assert state["pending"]["unit"] == 8
    assert [item["unit"] for item in state["units"]] == list(range(8))
    assert state["failure"]["error"] == "WF cost resources lost during unit"
    sessions = chained(CAMPAIGN / "sessions.jsonl", field="sha256",
                       previous="previous")
    assert [row["event"] for row in sessions] == ["start", "end", "start", "end"]
    assert [row["status"] for row in sessions if row["event"] == "end"] == [
        "ready", "failed"]
    supervisor = chained(CAMPAIGN / "supervisor.jsonl", field="sha256",
                         previous="previous")
    accepted = []
    for unit, item in enumerate(state["units"]):
        work = CAMPAIGN / "wf-2021"
        report_path = work / f"unit-{unit}.json"
        report = json.loads(report_path.read_text())
        checkpoint = work / f"checkpoint-{unit}"
        manifest = json.loads((checkpoint / "manifest.json").read_text())
        checkpoint_sha = sha(checkpoint / "state.pt")
        assert item["report_sha256"] == sha(report_path)
        assert item["checkpoint_sha256"] == checkpoint_sha
        assert report["checkpoint_sha256"] == checkpoint_sha
        assert manifest["state_sha256"] == checkpoint_sha
        assert report["report"]["boundary"] == (
            "after_q0" if unit == 0 else "after_dual_and_D")
        assert report["report"]["market_training_executed"] is (unit > 0)
        expected = (8 * unit, 16 * unit)
        assert (report["report"]["actor_updates"],
                report["report"]["critic_updates"]) == expected
        d_rows = [phase for phase in report["report"]["telemetry"]
                  if phase["phase"] == "D" and phase["iteration"] == unit - 1]
        assert len(d_rows) == (0 if unit == 0 else 1)
        accepted.append({
            "unit": unit, "ledger_wall_seconds": item["seconds"],
            "algorithm_seconds": report["algorithm_seconds"],
            "save_seconds": report["save_seconds"],
            "diagnostic_D_seconds": None if not d_rows else d_rows[0]["wall_seconds"],
            "resources": report["resources"],
            "report_sha256": sha(report_path),
            "checkpoint_sha256": checkpoint_sha,
            "checkpoint_manifest_sha256": sha(checkpoint / "manifest.json"),
        })
    assert not (CAMPAIGN / "wf-2021/unit-8.json").exists()
    assert not (CAMPAIGN / "wf-2021/checkpoint-8").exists()
    prior_roots = {}
    for number in ("01", "02", "03"):
        path = ROOT / f"artifacts/oos-v12-wf-cost-only-{number}"
        mapping = {str(item.relative_to(path)): sha(item)
                   for item in sorted(path.rglob("*")) if item.is_file()}
        mapping_sha = hashlib.sha256(json.dumps(mapping, sort_keys=True).encode()).hexdigest()
        assert mapping_sha == original["prior_roots"][number]["mapping_sha256"]
        prior_roots[number] = {"files": len(mapping), "mapping_sha256": mapping_sha}
    result = {
        "status": state["status"], "accepted_units": len(accepted),
        "pending_unit_not_accepted": state["pending"]["unit"],
        "failure": state["failure"],
        "ledger_sha256": sha(CAMPAIGN / "ledger.jsonl"),
        "ledger_rows": len(rows), "sessions_sha256": sha(CAMPAIGN / "sessions.jsonl"),
        "session_rows": len(sessions), "session_02_wall_seconds": sessions[-1]["wall_seconds"],
        "q0_session_wall_seconds": sessions[1]["wall_seconds"],
        "supervisor_sha256": sha(CAMPAIGN / "supervisor.jsonl"),
        "supervisor_rows": len(supervisor),
        "checkpoint_q0_unchanged": files["wf-2021/checkpoint-0/state.pt"],
        "accepted": accepted, "resources_total": state["resources"],
        "ledger_day_charge_seconds": state["days"]["2026-10-30"]["charged_wall_seconds"],
        "prior_roots": prior_roots, "root_file_count": len(files),
        "root_mapping_sha256": hashlib.sha256(
            json.dumps(files, sort_keys=True).encode()).hexdigest(),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
