"""P2R infrastructure contracts; all commands and ledgers here are synthetic."""

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from btc_risk_rl.pilots.p2r import (
    P2RJournal,
    P2RSharedBudget,
    check_resources,
    check_service_context,
    read_power,
    read_worker_progress,
    run_fixture_unit,
)


def epoch(day, hour=10):
    return datetime(2026, 10, day, hour, tzinfo=ZoneInfo("America/La_Paz")).timestamp()


def power_fixture(tmp_path, *, online="1", capacity="55"):
    root = tmp_path / "power"
    for name, kind, field, value in (
        ("ADP1", "Mains", "online", online),
        ("BAT1", "Battery", "capacity", capacity),
    ):
        item = root / name
        item.mkdir(parents=True)
        (item / "type").write_text(kind)
        (item / field).write_text(value)
        if kind == "Battery":
            (item / "scope").write_text("System")
    return root


def test_power_and_resources_fail_closed(tmp_path):
    root = power_fixture(tmp_path)
    peripheral = root / "hidpp_battery_0"
    peripheral.mkdir()
    (peripheral / "type").write_text("Battery")
    (peripheral / "scope").write_text("Device")
    (peripheral / "capacity").write_text("1")
    assert read_power(root) == (True, 55)
    assert check_resources(root, memory_available=4 * 1024**3, disk_free=10 * 1024**3,
                           stage="preflight") == "ready"
    with pytest.raises(ValueError, match="Invalid P2R resource"):
        check_resources(root, memory_available=float("nan"), disk_free=10 * 1024**3,
                        stage="preflight")
    (root / "BAT1" / "capacity").write_text("45")
    with pytest.raises(ValueError, match="battery"):
        check_resources(root, memory_available=8 * 1024**3, disk_free=20 * 1024**3,
                        stage="preflight")
    assert check_resources(root, memory_available=4 * 1024**3, disk_free=10 * 1024**3,
                           stage="unit") == "ready"
    (root / "ADP1" / "online").write_text("0")
    with pytest.raises(ValueError, match="AC"):
        check_resources(root, memory_available=8 * 1024**3, disk_free=20 * 1024**3,
                        stage="unit")
    (root / "ADP1" / "online").unlink()
    with pytest.raises(ValueError, match="power"):
        read_power(root)


def test_incomplete_external_debit_and_excluded_day(tmp_path):
    artifacts = tmp_path / "artifacts"
    old = artifacts / "p2-approved-v1"
    old.mkdir(parents=True)
    day = "2026-10-01"
    (old / "ledger.jsonl").write_text(json.dumps({
        "status": "failed", "days": {day: {"active_seconds": 0}},
    }) + "\n")
    with P2RSharedBudget(artifacts, "p2r-synthetic", now=epoch(1)) as budget:
        assert budget.external_seconds == 10800
        assert budget.sources[0]["reason"] == "incomplete_debit"
        with pytest.raises(ValueError, match="global daily budget"):
            P2RSharedBudget(artifacts, "p2r-other", now=epoch(1))
    with P2RSharedBudget(artifacts, "p2r-synthetic", now=epoch(2)) as budget:
        assert budget.external_seconds == 0
    (old / "ledger.jsonl").write_text(json.dumps({
        "status": "running", "days": {day: {"active_seconds": 0}},
    }) + "\n")
    with pytest.raises(ValueError, match="running"):
        P2RSharedBudget(artifacts, "p2r-synthetic", now=epoch(2))
    with pytest.raises(ValueError, match="excluded"):
        P2RSharedBudget(artifacts, "p2r-synthetic", now=epoch(1) - 86400)
    (old / "ledger.jsonl").write_text(json.dumps({
        "status": "failed", "days": {day: {"charged_wall_seconds": 125.5}},
    }) + "\n")
    with P2RSharedBudget(artifacts, "p2r-synthetic", now=epoch(1)) as budget:
        assert budget.external_seconds == 125.5
    (old / "ledger.jsonl").write_text(json.dumps({
        "status": "failed", "pending": {"kind": "iteration"},
        "days": {day: {"charged_wall_seconds": 125.5}},
    }) + "\n")
    with P2RSharedBudget(artifacts, "p2r-synthetic", now=epoch(1)) as budget:
        assert budget.external_seconds == 10800
    (old / "ledger.jsonl").write_text(json.dumps({
        "status": "completed", "days": {day: {"active_seconds": 125.5}},
    }) + "\n")
    with P2RSharedBudget(artifacts, "p2r-synthetic", now=epoch(1)) as budget:
        assert budget.external_seconds == 10800


def test_external_full_day_cannot_admit_q0(tmp_path):
    from btc_risk_rl.pilots.p2_budget import P2Ledger

    artifacts = tmp_path / "artifacts"
    old = artifacts / "p2-approved-v1"
    old.mkdir(parents=True)
    (old / "ledger.jsonl").write_text(json.dumps({
        "status": "failed", "days": {"2026-10-01": {"active_seconds": 0}},
    }) + "\n")
    at = epoch(1)
    with P2RSharedBudget(artifacts, "p2r-approved-v1", now=at) as budget:
        with P2Ledger(artifacts / "p2r-approved-v1", now=at,
                      identity={"profile": "p2r_synthetic_budget_fixture"},
                      external_seconds=budget.external_seconds) as ledger:
            ledger.preflight_done(at + 1)
            assert ledger.admit("C0", "q0", at + 1) == "pause"


def test_journal_chain_and_recovery(tmp_path):
    path = tmp_path / "journal.jsonl"
    journal = P2RJournal(path, campaign="fixture")
    journal.record("ready", phase="preflight", run_id="r0", unit=0, counters={})
    journal.record("heartbeat", phase="A", run_id="r0", unit=1,
                   counters={"transitions": 7}, power={"ac": True, "battery": 60})
    assert P2RJournal(path, campaign="fixture").last["event"] == "heartbeat"
    with path.open("a") as f:
        f.write('{"bad":true}\n')
    with pytest.raises(ValueError, match="journal"):
        P2RJournal(path, campaign="fixture")


def test_fixture_default_heartbeat_has_recorded_margin(tmp_path):
    artifacts = tmp_path / "artifacts"
    root = artifacts / "p2r-heartbeat-fixture-clock"
    state = run_fixture_unit(
        root, [sys.executable, "-c", "import time; time.sleep(11)"],
        artifacts=artifacts, fixture_window=True,
    )
    assert state["status"] == "completed"
    rows = [json.loads(line) for line in (root / "supervisor.jsonl").read_text().splitlines()]
    stamps = [datetime.fromisoformat(row["utc"]) for row in rows
              if row["event"] == "heartbeat"]
    gaps = [(later - earlier).total_seconds()
            for earlier, later in zip(stamps, stamps[1:])]
    assert len(gaps) >= 2
    assert max(gaps) <= 5.0, gaps


def test_progress_markers_report_partial_not_complete(tmp_path):
    assert read_worker_progress(tmp_path, 0) == ("Q0", {})
    (tmp_path / "progress.json").write_text(json.dumps({
        "unit": 0, "phase": "A", "counters": {"transitions": 17},
    }))
    assert read_worker_progress(tmp_path, 0) == ("A", {"transitions": 17})
    (tmp_path / "phase-0.json").write_text(json.dumps({"phase": "D"}))
    assert read_worker_progress(tmp_path, 0) == ("D", {"transitions": 17})
    (tmp_path / "progress.json").write_text("not-json")
    with pytest.raises(ValueError):
        read_worker_progress(tmp_path, 0)


def test_preflight_sensor_failure_blocks_before_worker(tmp_path):
    power = power_fixture(tmp_path, capacity="bad")
    artifacts = tmp_path / "artifacts"
    root = artifacts / "p2r-preflight"
    with pytest.raises(ValueError, match="power sensor"):
        run_fixture_unit(root, [sys.executable, "-c", "pass"], artifacts=artifacts,
                         power_root=power, fixture_window=True)
    assert not (root / "worker.log").exists()
    events = [json.loads(s)["event"] for s in
              (root / "supervisor.jsonl").read_text().splitlines()]
    assert events == ["supervisor_started", "preflight_rejected", "supervisor_exit"]


def test_power_loss_inside_unit_finishes_then_records_pause(tmp_path):
    power = power_fixture(tmp_path)
    artifacts = tmp_path / "artifacts"
    root = artifacts / "p2r-power-loss"
    capacity = power / "BAT1" / "capacity"
    worker = f"import time; from pathlib import Path; time.sleep(.1); Path({str(capacity)!r}).write_text('35'); time.sleep(.35)"
    result = run_fixture_unit(root, [sys.executable, "-c", worker],
                              artifacts=artifacts, power_root=power,
                              fixture_window=True, heartbeat_seconds=.05)
    assert result["status"] == "completed"
    assert result["units"][0]["availability_lost"] == "battery"
    events = [json.loads(s)["event"] for s in
              (root / "supervisor.jsonl").read_text().splitlines()]
    assert events.index("availability_lost") < events.index("unit_completed")
    assert events.index("unit_completed") < events.index("paused")


def test_service_context_requires_real_unit_and_linger():
    with pytest.raises(ValueError, match="systemd user service"):
        check_service_context(invocation_id="forged", cgroup="/user.slice/user-1.scope/session-1.scope",
                              linger="yes")
    with pytest.raises(ValueError, match="systemd user service"):
        check_service_context(invocation_id="forged", cgroup="/user.slice/user@1.service/app.slice/codex.scope",
                              linger="yes")
    cgroup = "0::/user.slice/user-1000.slice/user@1000.service/app.slice/p2r-test.service"
    with pytest.raises(ValueError, match="linger"):
        check_service_context(invocation_id="known", cgroup=cgroup, linger="no")
    assert check_service_context(invocation_id="known", cgroup=cgroup,
                                 linger="yes") == "ready"


def test_abrupt_supervisor_death_invalidates_pending_unit(tmp_path):
    artifacts = tmp_path / "artifacts"
    root = artifacts / "p2r-synthetic"
    command = [sys.executable, "-c", "import time; time.sleep(30)"]
    script = (
        "from btc_risk_rl.pilots.p2r import run_fixture_unit; "
        "import json,sys; run_fixture_unit(sys.argv[1], json.loads(sys.argv[2]), "
        "artifacts=sys.argv[3], heartbeat_seconds=.2, fixture_window=True)"
    )
    proc = subprocess.Popen([sys.executable, "-c", script, str(root), json.dumps(command),
                             str(artifacts)], env=dict(os.environ, PYTHONUNBUFFERED="1"))
    try:
        deadline = time.monotonic() + 10
        journal = root / "supervisor.jsonl"
        while time.monotonic() < deadline:
            if journal.exists() and '"event": "heartbeat"' in journal.read_text():
                break
            time.sleep(.05)
        else:
            pytest.fail("fixture heartbeat did not appear")
        heartbeat = next(json.loads(s) for s in journal.read_text().splitlines()
                         if '"event": "heartbeat"' in s)
        os.kill(proc.pid, signal.SIGKILL)
        assert proc.wait(timeout=10) < 0
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            status = Path(f"/proc/{heartbeat['pid_worker']}/status")
            try:
                state = status.read_text()
            except OSError:
                break
            if "State:\tZ" in state:
                break
            time.sleep(.05)
        else:
            pytest.fail("orphaned worker remained running")
        with pytest.raises(ValueError, match="interrupted"):
            run_fixture_unit(root, command, artifacts=artifacts, fixture_window=True)
        state = json.loads((root / "ledger.jsonl").read_text().splitlines()[-1])
        assert state["status"] == "failed"
        assert state["failure"]["reason"] == "interrupted_supervisor_or_unit"
        assert not any(x.get("checkpoint") for x in state["units"])
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def test_signal_during_unit_fails_and_does_not_retry(tmp_path):
    root = tmp_path / "artifacts" / "p2r-synthetic"
    command = [sys.executable, "-c", "import time; time.sleep(30)"]
    script = (
        "from btc_risk_rl.pilots.p2r import run_fixture_unit; "
        "import json,sys; "
        "run_fixture_unit(sys.argv[1], json.loads(sys.argv[2]), "
        "artifacts=sys.argv[3], now=None, heartbeat_seconds=.2, fixture_window=True)"
    )
    artifacts = tmp_path / "artifacts"
    proc = subprocess.Popen([sys.executable, "-c", script, str(root), json.dumps(command),
                             str(artifacts)], env=dict(os.environ, PYTHONUNBUFFERED="1"))
    try:
        deadline = time.monotonic() + 10
        journal = root / "supervisor.jsonl"
        while time.monotonic() < deadline:
            if journal.exists() and '"event": "unit_started"' in journal.read_text():
                break
            time.sleep(.05)
        else:
            pytest.fail("fixture unit did not start")
        os.kill(proc.pid, signal.SIGTERM)
        assert proc.wait(timeout=10) != 0
        states = [json.loads(s) for s in (root / "ledger.jsonl").read_text().splitlines()]
        assert states[-1]["status"] == "failed"
        assert not any(x.get("checkpoint") for x in states[-1]["units"])
        events = [json.loads(s) for s in journal.read_text().splitlines()]
        assert any(x["event"] == "signal" for x in events)
        assert any(x["event"] == "unit_failed" for x in events)
        with pytest.raises(ValueError, match="failed"):
            run_fixture_unit(root, command, artifacts=artifacts, now=None,
                             fixture_window=True)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def test_signal_between_units_pauses_without_worker(tmp_path):
    artifacts = tmp_path / "artifacts"
    root = artifacts / "p2r-between-units"
    result = run_fixture_unit(
        root, [sys.executable, "-c", "raise RuntimeError('must not run')"],
        artifacts=artifacts, fixture_window=True,
        before_unit=lambda: os.kill(os.getpid(), signal.SIGINT),
    )
    assert result["status"] == "ready" and result["units"] == []
    assert not (root / "worker.log").exists()
    events = [json.loads(s) for s in (root / "supervisor.jsonl").read_text().splitlines()]
    assert [e["event"] for e in events] == ["supervisor_started", "signal", "paused",
                                             "supervisor_exit"]
    assert events[1]["phase"] == "between_units"


def test_signal_during_commit_invalidates_campaign(tmp_path, monkeypatch):
    from btc_risk_rl.pilots.p2_budget import P2Ledger

    original = P2Ledger.finish
    def signal_after_finish(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        os.kill(os.getpid(), signal.SIGINT)
        return result

    monkeypatch.setattr(P2Ledger, "finish", signal_after_finish)
    artifacts = tmp_path / "artifacts"
    root = artifacts / "p2r-commit-signal"
    with pytest.raises(RuntimeError, match="signal during unit commit"):
        run_fixture_unit(root, [sys.executable, "-c", "pass"],
                         artifacts=artifacts, fixture_window=True)
    state = json.loads((root / "ledger.jsonl").read_text().splitlines()[-1])
    assert state["status"] == "failed"
    assert state["failure"]["reason"] == "interrupted_supervisor_or_unit"


def test_completed_fixture_cannot_repeat(tmp_path):
    artifacts = tmp_path / "artifacts"
    root = artifacts / "p2r-complete"
    command = [sys.executable, "-c", "pass"]
    first = run_fixture_unit(root, command, artifacts=artifacts, fixture_window=True)
    assert first["status"] == "completed" and len(first["units"]) == 1
    original = (root / "worker.log").stat().st_mtime_ns
    second = run_fixture_unit(root, command, artifacts=artifacts, fixture_window=True)
    assert second["status"] == "completed" and len(second["units"]) == 1
    assert (root / "worker.log").stat().st_mtime_ns == original


def test_heartbeat_carries_worker_phase_and_partial_counter(tmp_path):
    artifacts = tmp_path / "artifacts"
    root = artifacts / "p2r-progress"
    progress = root / "progress.json"
    worker = (
        "import json,time; from pathlib import Path; "
        f"Path({str(progress)!r}).write_text(json.dumps({{'unit':0,'phase':'D',"
        "'counters':{'diagnostic_transitions':17}})); time.sleep(.35)"
    )
    result = run_fixture_unit(root, [sys.executable, "-c", worker],
                              artifacts=artifacts, fixture_window=True,
                              heartbeat_seconds=.1)
    assert result["status"] == "completed"
    events = [json.loads(s) for s in (root / "supervisor.jsonl").read_text().splitlines()]
    assert any(e["event"] == "heartbeat" and e["phase"] == "D" and
               e["counters"] == {"diagnostic_transitions": 17} for e in events)


@pytest.mark.parametrize("profile", ["market", "validation", "final"])
def test_market_cli_denied_before_artifacts(tmp_path, profile):
    out = tmp_path / profile
    result = subprocess.run([sys.executable, "scripts/run_p2r.py", "--profile", profile,
                             "--output", str(out), "--fixture-window"],
                            capture_output=True, text=True)
    assert result.returncode != 0
    assert "NOT AUTHORIZED" in result.stderr
    assert not out.exists()
