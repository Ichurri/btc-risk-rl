"""A signal arriving during fsync must not break the durable journal chain."""

import os
import signal


def test_signal_during_journal_append_is_recorded_after_atomic_row(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import p2r

    journal = p2r.P2RJournal(tmp_path / "supervisor.jsonl", campaign="fixture")
    original_fsync = os.fsync
    fired = False

    def send_once(fd):
        nonlocal fired
        if not fired:
            fired = True
            os.kill(os.getpid(), signal.SIGTERM)
        return original_fsync(fd)

    old = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGTERM, lambda _signum, _frame: journal.record("signal"))
    monkeypatch.setattr(p2r.os, "fsync", send_once)
    try:
        journal.record("unit_started")
    finally:
        signal.signal(signal.SIGTERM, old)
    reopened = p2r.P2RJournal(journal.path, campaign="fixture")
    assert reopened.last["event"] == "signal"
