"""Static preparation of a long, synthetic-only supervised logout probe."""

import os
import sys
from pathlib import Path

import pytest

from btc_risk_rl.pilots.p2r import P2RJournal
from btc_risk_rl.pilots.p2r_hold import main as hold_main
from btc_risk_rl.pilots.p2r_units import synthetic_worker_command


def test_supervised_hold_command_is_synthetic_only():
    request = Path("/tmp/p2r-synthetic-request.json")
    command = synthetic_worker_command(request, 900)
    assert command == [sys.executable, "-m", "btc_risk_rl.pilots.p2r_hold",
                       "900", str(request)]
    assert synthetic_worker_command(request, 0) == [
        sys.executable, "-m", "btc_risk_rl.pilots.p2_runner",
        "--synthetic-request", str(request),
    ]
    for invalid in (-1, 901, 1.5, True):
        with pytest.raises(ValueError, match="synthetic hold"):
            synthetic_worker_command(request, invalid)


def test_hold_execs_only_synthetic_worker_after_wait(monkeypatch):
    import btc_risk_rl.pilots.p2r_hold as hold

    calls = []
    monkeypatch.setattr(sys, "argv", ["p2r_hold", "900", "/tmp/request.json"])
    monkeypatch.setattr(hold.time, "sleep", lambda seconds: calls.append(("sleep", seconds)))

    def capture_exec(binary, argv):
        calls.append(("exec", binary, argv))
        raise RuntimeError("exec intercepted")

    monkeypatch.setattr(os, "execv", capture_exec)
    with pytest.raises(RuntimeError, match="exec intercepted"):
        hold_main()
    assert calls == [
        ("sleep", 900),
        ("exec", sys.executable,
         [sys.executable, "-m", "btc_risk_rl.pilots.p2_runner",
          "--synthetic-request", "/tmp/request.json"]),
    ]


def test_hold_rejects_unsafe_arguments_before_wait(monkeypatch):
    import btc_risk_rl.pilots.p2r_hold as hold

    monkeypatch.setattr(hold.time, "sleep", lambda _: pytest.fail("must not sleep"))
    for argv in (["p2r_hold", "901", "/tmp/request.json"],
                 ["p2r_hold", "900", "--market-request"],
                 ["p2r_hold", "900"]):
        monkeypatch.setattr(sys, "argv", argv)
        with pytest.raises(ValueError):
            hold_main()


def test_journal_records_systemd_invocation_identity(tmp_path, monkeypatch):
    monkeypatch.setenv("INVOCATION_ID", "synthetic-invocation-123")
    journal = P2RJournal(tmp_path / "events.jsonl", campaign="p2r-test")
    journal.record("supervisor_started")
    assert journal.last["invocation_id"] == "synthetic-invocation-123"
    assert P2RJournal(journal.path, campaign="p2r-test").last == journal.last
