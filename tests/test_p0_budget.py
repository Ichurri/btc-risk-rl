"""P0 global ledger and supervisor tests use invented clocks/processes, never market."""

import sys

import pytest


def test_global_day_shared_across_runs_and_restart(tmp_path):
    from btc_risk_rl.pilots.budget import CampaignLedger

    t = 1790222400.0  # arbitrary UTC epoch, not a measured duration
    with CampaignLedger(tmp_path, now=t, identity="synthetic") as ledger:
        ledger.preflight_done(t + 10)
        assert ledger.admit("C0", "q0", t + 10) == "start"
        ledger.begin("r0", "q0", t + 10)
        ledger.finish(t + 110, resources={"trajectories": 2, "transitions": 360}, condition="C0")
        start = ledger.day["started_utc_epoch"]
        deadline = ledger.day["work_deadline"]
    with CampaignLedger(tmp_path, now=t + 200, identity="synthetic") as ledger:
        assert ledger.day["started_utc_epoch"] == start
        assert ledger.day["work_deadline"] == deadline
        assert ledger.state["resources"]["transitions"] == 360
        assert ledger.admit("C5", "iteration", deadline - 2699) == "pause"
        assert ledger.admit("C5", "iteration", deadline - 2700) == "start"


def test_interrupted_unit_invalidates_campaign_and_blocks_resume(tmp_path):
    from btc_risk_rl.pilots.budget import CampaignLedger

    with CampaignLedger(tmp_path, now=1790222400, identity="synthetic") as ledger:
        ledger.preflight_done(1790222410)
        ledger.begin("r0", "q0", 1790222410)
    with pytest.raises(ValueError, match="interrupted"):
        with CampaignLedger(tmp_path, now=1790222420, identity="synthetic"):
            pass
    with pytest.raises(ValueError):
        with CampaignLedger(tmp_path, now=1790308800, identity="synthetic"):
            pass


def test_lapaz_midnight_global_window_and_session_limit(tmp_path):
    from datetime import datetime

    from btc_risk_rl.pilots.budget import CampaignLedger

    t = datetime.fromisoformat("2026-09-24T03:40:00+00:00").timestamp()
    with CampaignLedger(tmp_path, now=t, identity="synthetic") as ledger:
        ledger.preflight_done(t + 5)
        assert ledger.day_key == "2026-09-23"
        assert ledger.admit("C0", "q0", t + 5) == "pause"
    for offset in range(3):
        now = t + 86400 * offset + 3600
        with CampaignLedger(tmp_path, now=now, identity="synthetic") as ledger:
            ledger.preflight_done(now + 5)
            ledger.begin("r0", "iteration", now + 5)
            ledger.finish(now + 15, resources={}, condition="C0")
    with CampaignLedger(tmp_path, now=t + 3 * 86400 + 3600, identity="synthetic") as ledger:
        ledger.preflight_done(t + 3 * 86400 + 3605)
        with pytest.raises(ValueError, match="sessions"):
            ledger.begin("r0", "iteration", t + 3 * 86400 + 3605)


def test_measured_estimate_monotone_and_not_synthetic_cross_profile(tmp_path):
    from btc_risk_rl.pilots.budget import CampaignLedger

    with CampaignLedger(tmp_path, now=1790222400, identity="synthetic") as ledger:
        ledger.preflight_done(1790222401)
        ledger.begin("r", "iteration", 1790222401)
        ledger.finish(1790222501, resources={}, condition="C0")
        assert ledger.required("C0", "iteration") == 150
        assert ledger.required("C5", "iteration") == 2700
    with pytest.raises(ValueError, match="identity"):
        with CampaignLedger(tmp_path, now=1790222600, identity="market"):
            pass


def test_campaign_lock_excludes_second_writer(tmp_path):
    from btc_risk_rl.pilots.budget import CampaignLedger

    with CampaignLedger(tmp_path, now=1790222400, identity="synthetic"):
        with pytest.raises(ValueError, match="active"):
            with CampaignLedger(tmp_path, now=1790222401, identity="synthetic"):
                pass


@pytest.mark.parametrize("kind", ["time", "memory"])
def test_real_supervisor_kills_synthetic_process(tmp_path, kind):
    from btc_risk_rl.pilots.supervisor import supervise

    result = supervise(
        [sys.executable, "-c", "import time; x=bytearray(30_000_000); time.sleep(60)"],
        output=tmp_path / "child.log",
        seconds=0.3 if kind == "time" else 10,
        rss_limit=10**10 if kind == "time" else 1_000_000,
        poll=0.02,
        grace=0.1,
    )
    assert result["status"] == "failed" and result["reason"] == kind
    assert result["wall_seconds"] < 5


def test_backward_clock_and_truncated_ledger_rejected(tmp_path):
    from btc_risk_rl.pilots.budget import CampaignLedger

    with CampaignLedger(tmp_path, now=1790222400, identity="synthetic"):
        pass
    with pytest.raises(ValueError, match="backwards"):
        with CampaignLedger(tmp_path, now=1790222399, identity="synthetic"):
            pass
    with (tmp_path / "ledger.jsonl").open("a") as f:
        f.write('{"status":')
    with pytest.raises(ValueError):
        with CampaignLedger(tmp_path, now=1790222420, identity="synthetic"):
            pass


def test_supervisor_death_kills_worker(tmp_path):
    import os
    import signal
    import subprocess
    import time
    from pathlib import Path

    code = (
        "from btc_risk_rl.pilots.supervisor import supervise; import sys; "
        f"supervise([sys.executable, '-c', \"import os,time; open({str(tmp_path / 'pid')!r}, 'w').write(str(os.getpid())); time.sleep(60)\"], "
        f"output={str(tmp_path / 'log')!r}, seconds=50, rss_limit=10**10)"
    )
    parent = subprocess.Popen([sys.executable, "-c", code])
    try:
        deadline = time.monotonic() + 5
        while not (tmp_path / "pid").exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        pid = int((tmp_path / "pid").read_text())
        os.kill(parent.pid, signal.SIGKILL)
        parent.wait(timeout=3)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            try:
                status = Path(f"/proc/{pid}/status").read_text()
            except FileNotFoundError:
                return
            if "State:\tZ" in status:
                return
            time.sleep(0.02)
        pytest.fail("Worker survived supervisor death")
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.wait()


def test_all_runs_share_day_and_27_run_day_sessions_not_27_dates(tmp_path):
    from btc_risk_rl.pilots.budget import CampaignLedger

    with CampaignLedger(tmp_path, now=1790222400, identity="synthetic") as ledger:
        ledger.preflight_done(1790222405)
        for i in range(9):
            ledger.begin(f"r{i}", "q0", 1790222410 + i * 10)
            ledger.finish(1790222411 + i * 10, resources={"trajectories": 2}, condition="C0")
        assert len(ledger.state["days"]) == 1
        assert sum(len(r["days"]) for r in ledger.state["runs"].values()) == 9
        assert ledger.state["resources"]["trajectories"] == 18


def test_checkpoint_can_use_closing_reserve_without_extending_work(tmp_path):
    from btc_risk_rl.pilots.budget import CampaignLedger

    t = 1790222400
    with CampaignLedger(tmp_path, now=t, identity="synthetic") as ledger:
        ledger.preflight_done(t + 10)
        stop = ledger.day["work_deadline"]
        ledger.begin("r0", "iteration", stop - 100)
        ledger.finish(stop + 60, resources={}, condition="C0", work_ended=stop - 1, work_seconds=99)
        assert ledger.state["status"] == "ready"
        assert ledger.required("C0", "iteration") == 148.5


def test_supervisor_separates_work_and_save_deadlines(tmp_path):
    from btc_risk_rl.pilots.supervisor import supervise

    marker = tmp_path / "closing.json"
    code = (
        "import time,json; "
        f"open({str(marker)!r}, 'w').write(json.dumps(dict(work_done_monotonic=time.monotonic(),work_done_utc=time.time()))); "
        "time.sleep(.35)"
    )
    result = supervise(
        [sys.executable, "-c", code],
        output=tmp_path / "log",
        seconds=0.2,
        rss_limit=10**10,
        poll=0.01,
        closing_marker=marker,
        closing_seconds=2,
    )
    assert result["status"] == "passed" and result["wall_seconds"] > 0.2
    assert result["work_seconds"] < 0.2
