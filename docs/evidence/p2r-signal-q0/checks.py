"""Read-only verification of the two synthetic Q0 SIGTERM probes."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def digest(row, omitted):
    return hashlib.sha256(
        json.dumps({k: v for k, v in row.items() if k != omitted},
                   sort_keys=True, allow_nan=False).encode()
    ).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def verify(number, invocation_id, expected_systemd_result):
    root = ROOT / f"artifacts/p2r-synthetic-signal-q0-review-{number}"
    record = ROOT / f"artifacts/p2r-signal-q0-review-{number}-record"
    journal = rows(root / "supervisor.jsonl")
    ledger = rows(root / "ledger.jsonl")
    previous = None
    for row in journal:
        assert row["campaign"] == root.name
        assert row["previous"] == previous
        assert row["sha256"] == digest(row, "sha256")
        assert row["invocation_id"] == invocation_id
        previous = row["sha256"]
    previous = None
    for row in ledger:
        assert row["previous_hash"] == previous
        assert row["state_hash"] == digest(row, "state_hash")
        previous = row["state_hash"]

    events = [row["event"] for row in journal]
    assert events[0] == "supervisor_started"
    assert events.count("unit_started") == 1
    assert events.count("signal") == 1
    assert events.count("unit_failed") == 1
    assert events[-1] == "supervisor_exit"
    assert "unit_completed" not in events
    started, signalled, failed, exited = (
        next(row for row in journal if row["event"] == event)
        for event in ("unit_started", "signal", "unit_failed", "supervisor_exit")
    )
    assert started["unit"] == signalled["unit"] == failed["unit"] == 0
    assert signalled["signum"] == 15
    assert failed["reason"] == "signal_during_unit"
    assert exited["status"] == "failed"
    assert all(datetime.fromisoformat(a["utc"]) < datetime.fromisoformat(b["utc"])
               for a, b in zip((started, signalled, failed),
                               (signalled, failed, exited)))
    assert any(row["event"] == "heartbeat" and row["phase"] == "Q0"
               and row["monotonic"] < signalled["monotonic"] for row in journal)
    assert any(row["status"] == "running" and row.get("pending", {}).get("unit") == 0
               and row["units"] == [] for row in ledger)
    final = ledger[-1]
    assert final["status"] == "failed"
    assert final["failure"]["reason"] == "interrupted_supervisor_or_unit"
    assert final["failure"]["signum"] == 15
    assert final["failure"]["supervisor"]["reason"] == "signal_during_unit"
    assert final["failure"]["supervisor"]["returncode"] == -15
    assert final["units"] == []
    assert not list(root.rglob("checkpoint-*"))
    request = json.loads((root / "run-00-C5/request-0.json").read_text())
    assert request["unit"] == 0 and request["previous"] is None
    assert request["settings"]["purpose"] == "p2_synthetic_tests_only"
    systemd_journal = (record / "systemd-journal.txt").read_text()
    assert systemd_journal.count("Sent signal SIGTERM to main process") == 1
    assert f"p2r-signal-q0-review-{number}.service" in systemd_journal
    if expected_systemd_result == "exit-code":
        assert "Failed with result 'exit-code'" in systemd_journal
        assert "ExecMainStatus=1" in (record / "after-unit.txt").read_text()
    else:
        assert "Result=success" in (record / "after-unit.txt").read_text()
        assert "Failed with result" not in systemd_journal
    return {
        "probe": number,
        "invocation_id": invocation_id,
        "unit_started_utc": started["utc"],
        "signal_utc": signalled["utc"],
        "unit_failed_utc": failed["utc"],
        "supervisor_exit_utc": exited["utc"],
        "heartbeats": events.count("heartbeat"),
        "accepted_checkpoints": 0,
        "ledger_status": final["status"],
        "systemd_result": expected_systemd_result,
    }


if __name__ == "__main__":
    print(json.dumps({"kind": "synthetic_artifact_checks",
                      "probes": [verify("04", "38c31c62089643b78dc517b8a145adad",
                                        "success"),
                                 verify("05", "925cd90d9584425bac73d3612c7cb278",
                                        "exit-code")]}, indent=2, sort_keys=True))
