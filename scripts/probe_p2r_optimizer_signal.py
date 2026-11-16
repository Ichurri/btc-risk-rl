"""One synthetic P2R Q/A/B+D signal probe; no market entry or campaign permit."""

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from btc_risk_rl.pilots.p2 import P2SyntheticSettings
from btc_risk_rl.pilots.p2_budget import state_hash
from btc_risk_rl.pilots.p2r import P2RJournal
from btc_risk_rl.pilots.p2r_units import run_synthetic_units


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat()


def power_fixture(root):
    for name, kind, field, value in (
        ("ADP1", "Mains", "online", "1"),
        ("BAT1", "Battery", "capacity", "80"),
    ):
        item = root / name
        item.mkdir(parents=True)
        (item / "type").write_text(kind)
        (item / field).write_text(value)
        if kind == "Battery":
            (item / "scope").write_text("System")


def run(root, summary):
    root, summary = root.resolve(), summary.resolve()
    if not root.name.startswith("p2r-synthetic-optimizer-signal-") or root.exists():
        raise ValueError("New p2r-synthetic-optimizer-signal-* root required")
    power = root.parent / (root.name + "-power")
    if power.exists() or summary.exists():
        raise ValueError("Probe refuses to overwrite evidence")
    power_fixture(power)
    settings = P2SyntheticSettings(
        iterations=1, hidden=4, n_a=1, n_q=2, n_b=2,
        actor_epochs=1, critic_epochs=4, seed=610031,
    )
    config = Path("configs/initial.toml")
    q0 = run_synthetic_units(
        root, config, settings, "C5", max_units=1, power_root=power,
        memory_available=4 * 1024**3, disk_free=10 * 1024**3,
        fixture_window=True, heartbeat_seconds=.05,
    )
    if q0["status"] != "ready" or len(q0["units"]) != 1:
        raise RuntimeError("Synthetic Q0 did not close cleanly")
    work = root / "run-00-C5"
    previous = work / "checkpoint-0"
    before = {name: sha(previous / name) for name in ("state.pt", "manifest.json")}
    marker = work / "optimizer-calculation.json"
    supervisor = Path("tests/fixtures/p2r_optimizer_probe_supervisor.py").resolve()
    launched = time.time()
    with (root / "probe-supervisor.log").open("x") as log:
        proc = subprocess.Popen(
            [sys.executable, str(supervisor), str(root), str(power), str(marker)],
            stdout=log, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 150
            sample = None
            while time.monotonic() < deadline:
                if marker.exists():
                    sample = json.loads(marker.read_text())
                    if sample["iterations"] >= 101:
                        break
                if proc.poll() is not None:
                    raise RuntimeError("Supervisor exited before optimizer marker")
                time.sleep(.02)
            else:
                raise TimeoutError("Optimizer calculation marker not reached")
            signaled = time.time()
            os.kill(proc.pid, signal.SIGTERM)
            status = proc.wait(timeout=35)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
    ledger = json.loads((root / "ledger.jsonl").read_text().splitlines()[-1])
    if ledger["state_hash"] != state_hash(ledger):
        raise ValueError("Probe ledger hash mismatch")
    P2RJournal(root / "supervisor.jsonl", campaign=root.name)
    after = {name: sha(previous / name) for name in before}
    result = dict(
        kind="p2r_synthetic_signal_during_optimizer_gradient_calculation",
        root=str(root), supervisor_pid=proc.pid, worker_pid=sample["pid"],
        launched_utc=utc(launched), marker_utc=utc(sample["utc_epoch"]),
        signal_utc=utc(signaled), signal="SIGTERM to supervisor main PID",
        signal_number=signal.SIGTERM, optimizer_marker=sample,
        supervisor_exit_code=status, ledger_status=ledger["status"],
        failure=ledger.get("failure"), accepted_units=len(ledger["units"]),
        pending=ledger.get("pending"), checkpoint_0_before=before,
        checkpoint_0_after=after,
        checkpoint_1_exists=(work / "checkpoint-1").exists(),
        unit_1_result_exists=(work / "unit-1.json").exists(),
        ledger_sha256=sha(root / "ledger.jsonl"),
        supervisor_journal_sha256=sha(root / "supervisor.jsonl"),
        worker_log_sha256=sha(work / "worker-1.log"),
        fixture_only=True, historical_market_trajectories=0,
    )
    if (status != 1 or ledger["status"] != "failed" or len(ledger["units"]) != 1
            or ledger.get("pending", {}).get("unit") != 1
            or before != after or result["checkpoint_1_exists"]
            or result["unit_1_result_exists"]):
        raise AssertionError("Synthetic optimizer interruption contract failed")
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output, args.summary)
    print(json.dumps(dict(status=result["ledger_status"],
                          accepted_units=result["accepted_units"],
                          signal_utc=result["signal_utc"])))


if __name__ == "__main__":
    main()
