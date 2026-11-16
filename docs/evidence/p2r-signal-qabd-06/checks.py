"""Read-only checks for the single synthetic Q/A/B+D SIGTERM probe 06."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT = ROOT / "artifacts/p2r-synthetic-signal-qabd-review-06"
RECORD = ROOT / "artifacts/p2r-signal-qabd-review-06-record"
RUN = ARTIFACT / "run-00-C5"
INVOCATION = "797f0e422bac4b138c13a0829261a752"
EVIDENCE = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def chain_digest(row, omitted):
    payload = {key: value for key, value in row.items() if key != omitted}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def check():
    manifest_lines = (EVIDENCE / "SHA256SUMS.txt").read_text().splitlines()
    assert len(manifest_lines) == 25
    for line in manifest_lines:
        expected, relative = line.split("  ", 1)
        assert sha256(ROOT / relative) == expected
    for filename in ("before-signal.json", "after-signal.json", "systemd-journal.txt"):
        assert sha256(EVIDENCE / filename) == sha256(RECORD / filename)

    journal = read_rows(ARTIFACT / "supervisor.jsonl")
    ledger = read_rows(ARTIFACT / "ledger.jsonl")
    previous = None
    for row in journal:
        assert row["campaign"] == ARTIFACT.name
        assert row["invocation_id"] == INVOCATION
        assert row["previous"] == previous
        assert row["sha256"] == chain_digest(row, "sha256")
        previous = row["sha256"]
    previous = None
    for row in ledger:
        assert row["previous_hash"] == previous
        assert row["state_hash"] == chain_digest(row, "state_hash")
        previous = row["state_hash"]

    events = [row["event"] for row in journal]
    assert events.count("unit_started") == 2
    assert events.count("unit_completed") == 1
    assert events.count("signal") == events.count("unit_failed") == 1
    assert events[-1] == "supervisor_exit"
    significant = [row for row in journal if row["event"] != "heartbeat"]
    assert [(row["event"], row["unit"]) for row in significant] == [
        ("supervisor_started", None),
        ("unit_started", 0),
        ("unit_completed", 0),
        ("unit_started", 1),
        ("signal", 1),
        ("unit_failed", 1),
        ("supervisor_exit", 1),
    ]
    assert significant[2]["phase"] == "after_q0"
    assert significant[3]["phase"] == significant[5]["phase"] == "Q/A/B+D"
    assert significant[4]["signum"] == 15
    assert significant[5]["reason"] == "signal_during_unit"
    assert significant[6]["status"] == "failed"
    assert all(
        datetime.fromisoformat(a["utc"]) < datetime.fromisoformat(b["utc"])
        for a, b in zip(significant, significant[1:])
    )

    before = json.loads((RECORD / "before-signal.json").read_text())
    after = json.loads((RECORD / "after-signal.json").read_text())
    assert before["invocation_id"] == INVOCATION
    assert before["ledger_status"] == "running"
    assert before["pending_unit"] == 1 and before["accepted_units"] == 1
    assert after["ledger_status"] == "failed"
    assert after["failure_reason"] == "interrupted_supervisor_or_unit"
    assert after["signal"] == 15 and after["pending_unit"] == 1
    assert after["accepted_units"] == 1 and not after["checkpoint1_exists"]
    assert datetime.fromisoformat(before["read_utc"]) < datetime.fromisoformat(
        (RECORD / "signal-request-before-utc.txt").read_text().strip()
    ) < datetime.fromisoformat(after["read_utc"])

    state = RUN / "checkpoint-0/state.pt"
    manifest_path = RUN / "checkpoint-0/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["boundary"] == before["checkpoint0_boundary"] == "after_q0"
    assert manifest["git_commit"] == "d840d6a32334ca4ddd104efa9e60358a29c19928"
    assert manifest["state_sha256"] == sha256(state)
    assert before["checkpoint0_state_sha256"] == after["checkpoint0_state_sha256"] == sha256(state)
    assert before["checkpoint0_manifest_sha256"] == after["checkpoint0_manifest_sha256"] == sha256(manifest_path)
    assert significant[2]["checkpoint_sha256"] == ledger[-1]["units"][0]["checkpoint_sha256"] == sha256(state)
    assert len(ledger[-1]["units"]) == 1
    assert ledger[-1]["units"][0]["unit"] == 0
    assert ledger[-1]["status"] == "failed"
    assert ledger[-1]["pending"]["unit"] == 1
    assert ledger[-1]["failure"]["reason"] == "interrupted_supervisor_or_unit"
    assert ledger[-1]["failure"]["signum"] == 15
    assert ledger[-1]["failure"]["supervisor"]["returncode"] == -15
    assert not (RUN / "checkpoint-1").exists()
    assert not (RUN / "closing-1.json").exists()
    assert not (RUN / "unit-1.json").exists()
    assert (RUN / "worker-1.log").stat().st_size == 0

    request0 = json.loads((RUN / "request-0.json").read_text())
    request1 = json.loads((RUN / "request-1.json").read_text())
    assert request0["settings"]["purpose"] == request1["settings"]["purpose"] == "p2_synthetic_tests_only"
    assert request1["previous"] == str(RUN / "checkpoint-0")
    assert request1["unit"] == 1
    unit_state = (RECORD / "after-unit.txt").read_text()
    assert "Result=exit-code" in unit_state
    assert "ExecMainStatus=1" in unit_state
    assert "ActiveState=failed" in unit_state
    assert f"InvocationID={INVOCATION}" in unit_state
    systemd_journal = (RECORD / "systemd-journal.txt").read_text()
    assert systemd_journal.count("Sent signal SIGTERM to main process") == 1
    assert "Failed with result 'exit-code'" in systemd_journal

    heartbeats = {}
    for unit in (0, 1):
        times = [datetime.fromisoformat(row["utc"]) for row in journal
                 if row["event"] == "heartbeat" and row["unit"] == unit]
        intervals = [(b - a).total_seconds() for a, b in zip(times, times[1:])]
        assert intervals and all(0 < seconds <= 5 for seconds in intervals)
        heartbeats[str(unit)] = {
            "count": len(times),
            "intervals": len(intervals),
            "max_interval_seconds": max(intervals),
        }
    return {
        "kind": "synthetic_artifact_checks",
        "probe": "06",
        "invocation_id": INVOCATION,
        "significant_events_utc": {f"{row['event']}_{row['unit']}": row["utc"] for row in significant},
        "checkpoint0_state_sha256": sha256(state),
        "checkpoint0_manifest_sha256": sha256(manifest_path),
        "accepted_units": len(ledger[-1]["units"]),
        "checkpoint1_exists": False,
        "ledger_status": ledger[-1]["status"],
        "systemd_result": "exit-code",
        "heartbeats": heartbeats,
        "worker1_log_bytes": 0,
        "limitation": "Signal during supervised hold before Q/A/B+D calculations",
    }


if __name__ == "__main__":
    print(json.dumps(check(), indent=2, sort_keys=True))
