"""P2R lifecycle infrastructure. Historical campaign entry is deliberately absent."""

import fcntl
import hashlib
import json
import math
import os
import shutil
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path

from btc_risk_rl.pilots.budget import LA_PAZ, utc
from btc_risk_rl.pilots.p2_budget import P2Ledger
from btc_risk_rl.pilots.supervisor import rss_bytes, supervise

DAY_LIMIT = 10800
EXCLUDED_DAY = "2026-09-30"


def read_power(root=Path("/sys/class/power_supply")):
    """Read system battery and AC; peripherals never qualify as host battery."""
    supplies = []
    for path in Path(root).iterdir():
        kind = (path / "type").read_text().strip() if (path / "type").exists() else ""
        if kind == "Battery":
            scope = (path / "scope").read_text().strip() if (path / "scope").exists() else None
            if scope != "System" and (scope is not None or not path.name.startswith("BAT")):
                continue
        if kind in {"Battery", "Mains"}:
            supplies.append((path, kind))
    ac = [p for p, kind in supplies if kind == "Mains"]
    battery = [p for p, kind in supplies if kind == "Battery"]
    if not ac or not battery:
        raise ValueError("Missing host power sensor")
    try:
        online = [int((p / "online").read_text().strip()) for p in ac]
        levels = [int((p / "capacity").read_text().strip()) for p in battery]
    except (OSError, ValueError) as exc:
        raise ValueError("Unreadable host power sensor") from exc
    if any(v not in (0, 1) for v in online) or any(not 0 <= v <= 100 for v in levels):
        raise ValueError("Incoherent host power sensor")
    return any(online), min(levels)


def check_resources(power_root=Path("/sys/class/power_supply"), *, memory_available=None,
                    disk_free=None, stage, disk_path=None):
    """Read or validate availability, failing closed at both P2R thresholds."""
    if stage not in {"preflight", "unit"}:
        raise ValueError("Unknown P2R resource stage")
    ac, battery = read_power(power_root)
    if not ac:
        raise ValueError("AC not connected")
    if battery < (50 if stage == "preflight" else 40):
        raise ValueError("Host battery below P2R threshold")
    if memory_available is None:
        line = next((s for s in Path("/proc/meminfo").read_text().splitlines()
                     if s.startswith("MemAvailable:")), None)
        if line is None:
            raise ValueError("Memory availability unavailable")
        memory_available = int(line.split()[1]) * 1024
    if disk_free is None:
        if disk_path is None:
            raise ValueError("Disk path required")
        disk_free = shutil.disk_usage(disk_path).free
    if any(not isinstance(value, (int, float)) or not math.isfinite(value)
           for value in (memory_available, disk_free)):
        raise ValueError("Invalid P2R resource measurement")
    if memory_available < 4 * 1024**3 or disk_free < 10 * 1024**3:
        raise ValueError("Insufficient P2R memory or disk")
    return "ready"


def check_service_context(*, invocation_id=None, cgroup=None, linger=None,
                          require_linger=True):
    """Require a real user-service cgroup; logout survival additionally needs linger."""
    if invocation_id is None:
        invocation_id = os.environ.get("INVOCATION_ID")
    if cgroup is None:
        cgroup = _cgroup(os.getpid())
    unit = cgroup.strip().split("/")[-1] if cgroup else ""
    if (not invocation_id or not cgroup or "user.slice" not in cgroup
            or not unit.startswith("p2r-") or not unit.endswith(".service")):
        raise ValueError("P2R requires a systemd user service, not a chat/terminal child")
    if require_linger:
        if linger is None:
            result = subprocess.run(["loginctl", "show-user", str(os.getuid()),
                                     "-p", "Linger", "--value"],
                                    capture_output=True, text=True, check=True)
            linger = result.stdout.strip()
        if linger != "yes":
            raise ValueError("P2R user manager lacks verified linger for logout")
    return "ready"


class P2RSharedBudget:
    """Global lock with conservative debit for incomplete old campaigns."""

    def __init__(self, artifacts, campaign_name, *, now, synthetic_fixture=False):
        self.root = Path(artifacts)
        self.day = datetime.fromtimestamp(now, LA_PAZ).date().isoformat()
        if self.day == EXCLUDED_DAY and not synthetic_fixture:
            raise ValueError("P2R excluded day: original P2 debit unknown")
        self.audit = self.root / "shared-pilot-budget"
        self.audit.mkdir(parents=True, exist_ok=True)
        self.lock = (self.audit / "global.lock").open("a")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self.lock.close()
            raise ValueError("Another pilot holds the global daily budget") from exc
        self.name = campaign_name
        self.external_seconds = 0.0
        self.sources = []
        try:
            for path in sorted(self.root.glob("p*-approved-v*/ledger.jsonl")):
                if path.parent.name == campaign_name:
                    continue
                lines = path.read_text().splitlines()
                if not lines:
                    raise ValueError("Empty external campaign ledger")
                state = json.loads(lines[-1])
                if state["status"] == "running":
                    raise ValueError("Another campaign running or interrupted")
                day = state["days"].get(self.day)
                if day is None:
                    continue
                charged = day.get("charged_wall_seconds")
                incomplete = (charged is None or charged == 0 or
                              (state["status"] in {"failed", "incomplete"}
                               and state.get("pending")))
                if incomplete:
                    spent, reason = DAY_LIMIT, "incomplete_debit"
                elif charged is not None:
                    spent, reason = charged, "measured"
                if not isinstance(spent, (int, float)) or not math.isfinite(spent) or spent < 0:
                    raise ValueError("Invalid external daily consumption")
                self.external_seconds += spent
                self.sources.append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                         seconds=spent, reason=reason, day=self.day))
            self.record("entered")
        except BaseException:
            self.lock.close()
            raise

    def record(self, event):
        with (self.audit / "events.jsonl").open("a") as f:
            f.write(json.dumps(dict(utc=utc(time.time()), campaign=self.name, day=self.day,
                                    event=event, external_seconds=self.external_seconds,
                                    sources=self.sources), sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def __enter__(self):
        return self

    def __exit__(self, *_):
        try:
            self.record("exited")
        finally:
            self.lock.close()


class P2RJournal:
    """Append-only, fsynced and hash-chained lifecycle/heartbeat journal."""

    def __init__(self, path, *, campaign):
        self.path = Path(path)
        self.campaign = campaign
        self.previous = None
        self.last = None
        if self.path.exists():
            try:
                for line in self.path.read_text().splitlines():
                    row = json.loads(line)
                    digest = row.pop("sha256")
                    if row["campaign"] != campaign or row["previous"] != self.previous:
                        raise ValueError("P2R journal chain mismatch")
                    actual = hashlib.sha256(json.dumps(row, sort_keys=True, allow_nan=False).encode()).hexdigest()
                    if digest != actual:
                        raise ValueError("P2R journal digest mismatch")
                    self.previous = digest
                    self.last = {**row, "sha256": digest}
            except (OSError, KeyError, ValueError) as exc:
                raise ValueError("P2R journal corrupt") from exc

    def record(self, event, **fields):
        current = time.time()
        row = dict(campaign=self.campaign, event=event, previous=self.previous,
                   utc=utc(current), monotonic=time.monotonic(),
                   day=datetime.fromtimestamp(current, LA_PAZ).date().isoformat(),
                   pid=os.getpid(), **fields)
        digest = hashlib.sha256(json.dumps(row, sort_keys=True, allow_nan=False).encode()).hexdigest()
        row["sha256"] = digest
        self.path.parent.mkdir(parents=True, exist_ok=True)
        created = not self.path.exists()
        with self.path.open("a") as f:
            f.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        if created:
            directory = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        self.previous, self.last = digest, row


def read_worker_progress(root, unit):
    """Use existing P2 progress/phase markers without inventing completed counts."""
    root = Path(root)
    progress, phase = root / "progress.json", root / f"phase-{unit}.json"
    counters = {}
    label = "Q0" if unit == 0 else "unknown"
    if progress.exists():
        row = json.loads(progress.read_text())
        if row.get("unit") != unit or not isinstance(row.get("counters"), dict):
            raise ValueError("Invalid worker progress marker")
        counters = row["counters"]
        label = row.get("phase", label)
    if phase.exists():
        row = json.loads(phase.read_text())
        if not isinstance(row.get("phase"), str):
            raise ValueError("Invalid worker phase marker")
        label = row["phase"]
    return label, counters


def run_fixture_unit(root, command, *, artifacts, now=None, heartbeat_seconds=5.0,
                     power_root=None, require_service=False, fixture_window=False,
                     before_unit=None):
    """One synthetic lifecycle probe; it never imports or loads market data."""
    if require_service:
        check_service_context(require_linger=False)
    if not 0 < heartbeat_seconds <= 5:
        raise ValueError("P2R heartbeat must be at most five seconds")
    now = time.time() if now is None else now
    root = Path(root).resolve()
    artifacts = Path(artifacts).resolve()
    if root.parent != artifacts or not root.name.startswith("p2r-"):
        raise ValueError("P2R fixture requires a separate p2r-* artifacts root")
    with P2RSharedBudget(artifacts, root.name, now=now, synthetic_fixture=True) as shared:
        root.mkdir(exist_ok=True)
        journal = P2RJournal(root / "supervisor.jsonl", campaign=root.name)
        journal.record("supervisor_started", phase="preflight", run_id="fixture", unit=0,
                       counters={}, external_seconds=shared.external_seconds)
        try:
            ledger = P2Ledger(root, now=now, identity={"profile": "p2r_synthetic_fixture",
                                                        "command": command},
                              external_seconds=shared.external_seconds)
        except ValueError as exc:
            journal.record("recovery_rejected", phase="preflight", run_id="fixture",
                           unit=0, counters={}, reason=str(exc))
            raise
        with ledger:
            if ledger.state["status"] == "completed":
                journal.record("supervisor_exit", phase="after_q0", run_id="fixture", unit=0,
                               counters={}, status="completed_no_replay")
                return ledger.state
            if power_root is not None:
                try:
                    check_resources(power_root, memory_available=4 * 1024**3,
                                    disk_free=10 * 1024**3, stage="preflight")
                except ValueError as exc:
                    journal.record("preflight_rejected", phase="preflight", run_id="fixture",
                                   unit=0, counters={}, reason=str(exc))
                    journal.record("supervisor_exit", phase="preflight", run_id="fixture",
                                   unit=0, counters={}, status="blocked")
                    raise
            if fixture_window:
                # Explicit test-only clock window to exercise signal handling near midnight.
                ledger.day["work_deadline"] = time.time() + 3600
                ledger.day["hard_deadline"] = time.time() + 5400
                ledger.persist(time.time())
            ledger.preflight_done(time.time())
            if power_root is not None:
                try:
                    check_resources(power_root, memory_available=4 * 1024**3,
                                    disk_free=10 * 1024**3, stage="unit")
                except ValueError as exc:
                    journal.record("paused", phase="between_units", run_id="fixture", unit=0,
                                   counters={}, reason=str(exc))
                    journal.record("supervisor_exit", phase="between_units", run_id="fixture",
                                   unit=0, counters={}, status="paused")
                    return ledger.state
            interrupted = {"signum": None}
            phase = ["between_units"]
            def handle(signum, _frame):
                interrupted["signum"] = signum
                journal.record("signal", phase=phase[0], run_id="fixture", unit=0,
                               counters={}, signum=signum)
            old = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT)}
            for s in old:
                signal.signal(s, handle)
            if before_unit is not None:
                before_unit()
            if interrupted["signum"] is not None:
                journal.record("paused", phase="between_units", run_id="fixture", unit=0,
                               counters={}, reason="signal")
                journal.record("supervisor_exit", phase="between_units", run_id="fixture", unit=0,
                               counters={}, status="paused")
                for s, handler in old.items():
                    signal.signal(s, handler)
                return ledger.state
            if ledger.admit("fixture", "q0", time.time()) != "start":
                journal.record("paused", phase="between_units", run_id="fixture", unit=0,
                               counters={}, reason="budget")
                journal.record("supervisor_exit", phase="between_units", run_id="fixture", unit=0,
                               counters={}, status="paused")
                for s, handler in old.items():
                    signal.signal(s, handler)
                return ledger.state
            entered = time.monotonic()
            try:
                phase[0] = "unit"
                ledger.begin("fixture", "q0", time.time())
                journal.record("unit_started", phase="Q0", run_id="fixture", unit=0,
                               counters={}, pid_worker=None)
                last_heartbeat = [0.0]
                availability_lost = [None]
                def tick(pid, elapsed, peak):
                    if time.monotonic() - last_heartbeat[0] >= min(heartbeat_seconds, 4.0):
                        worker_phase, counters = read_worker_progress(root, 0)
                        power = None
                        if power_root is not None:
                            ac, battery = read_power(power_root)
                            power = dict(ac=ac, battery=battery)
                            if (not ac or battery < 40) and availability_lost[0] is None:
                                availability_lost[0] = "AC" if not ac else "battery"
                                journal.record("availability_lost", phase=worker_phase,
                                               run_id="fixture", unit=0, counters=counters,
                                               reason=availability_lost[0])
                        journal.record("heartbeat", phase=worker_phase, run_id="fixture", unit=0,
                                       counters=counters, pid_worker=pid, cgroup=_cgroup(pid),
                                       rss_worker=peak, rss_supervisor=rss_bytes(os.getpid()),
                                       power=power)
                        last_heartbeat[0] = time.monotonic()
                result = supervise(command, output=root / "worker.log", seconds=1800,
                                   rss_limit=10 * 1024**3, poll=min(.2, heartbeat_seconds),
                                   on_poll=tick, stop_requested=lambda: interrupted["signum"] is not None)
                if interrupted["signum"] is not None and result["status"] == "passed":
                    result["status"] = "failed"
                    result["reason"] = "signal_during_unit"
                if result["status"] != "passed":
                    ledger.fail(time.time(), "interrupted_supervisor_or_unit",
                                supervisor=result, signum=interrupted["signum"])
                    journal.record("unit_failed", phase="Q0", run_id="fixture", unit=0,
                                   counters={}, reason=result["reason"])
                    raise RuntimeError("P2R synthetic unit failed: " + str(result["reason"]))
                ledger.finish(time.time(), resources={}, condition="fixture",
                              work_seconds=result["work_seconds"],
                              work_ended=result["work_ended"], supervisor=result,
                              availability_lost=availability_lost[0])
                if interrupted["signum"] is not None:
                    ledger.fail(time.time(), "interrupted_supervisor_or_unit",
                                signum=interrupted["signum"])
                    journal.record("unit_failed", phase="Q0", run_id="fixture", unit=0,
                                   counters={}, reason="signal_during_commit")
                    raise RuntimeError("P2R signal during unit commit")
                phase[0] = "between_units"
                journal.record("unit_completed", phase="after_q0", run_id="fixture", unit=0,
                               counters={}, supervisor=result)
                if availability_lost[0] is not None:
                    journal.record("paused", phase="between_units", run_id="fixture", unit=0,
                                   counters={}, reason="availability_lost_after_unit")
                if interrupted["signum"] is not None:
                    journal.record("paused", phase="between_units", run_id="fixture", unit=0,
                                   counters={}, reason="signal")
                ledger.state["status"] = "completed"
                ledger.persist(time.time())
                return ledger.state
            except BaseException as exc:
                if ledger.state["status"] == "running":
                    ledger.fail(time.time(), "interrupted_supervisor_or_unit", error=str(exc))
                    journal.record("unit_failed", phase="Q0", run_id="fixture", unit=0,
                                   counters={}, reason=str(exc))
                raise
            finally:
                ledger.day["active_seconds"] += time.monotonic() - entered
                ledger.day["charged_wall_seconds"] = max(ledger.day.get("charged_wall_seconds", 0),
                                                         time.time() - ledger.day["started_utc_epoch"])
                ledger.persist(time.time())
                journal.record("supervisor_exit", phase=phase[0], run_id="fixture", unit=0,
                               counters={}, status=ledger.state["status"])
                for s, handler in old.items():
                    signal.signal(s, handler)


def _cgroup(pid):
    try:
        return Path(f"/proc/{pid}/cgroup").read_text().strip()
    except OSError:
        return None
