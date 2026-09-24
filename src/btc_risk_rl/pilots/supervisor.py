"""Linux worker watchdog: separate work/save deadlines, RSS and parent-death signal."""

import ctypes
import json
import os
import signal
import subprocess
import time
from pathlib import Path


def rss_bytes(pid):
    try:
        fields = Path(f"/proc/{pid}/status").read_text().splitlines()
        return next(int(line.split()[1]) * 1024 for line in fields if line.startswith("VmRSS:"))
    except (OSError, StopIteration):
        return 0


def supervise(
    command,
    *,
    output,
    seconds,
    rss_limit,
    poll=1.0,
    grace=10.0,
    env=None,
    closing_marker=None,
    closing_seconds=None,
):
    if seconds <= 0 or rss_limit <= 0:
        raise ValueError("Positive supervisor limits required")
    if closing_marker is not None and (closing_seconds is None or closing_seconds < seconds):
        raise ValueError("Closing deadline must cover work")
    parent = os.getpid()

    def parent_death():
        if ctypes.CDLL(None).prctl(1, signal.SIGKILL, 0, 0, 0) != 0:
            os._exit(125)
        if os.getppid() != parent:
            os._exit(125)

    start, utc_start = time.monotonic(), time.time()
    peak, reason, closed = 0, None, None

    def read_marker():
        nonlocal closed
        if closed is None and closing_marker is not None and Path(closing_marker).exists():
            closed = json.loads(Path(closing_marker).read_text())
        if closed is not None:
            work = closed["work_done_monotonic"] - start
            if not 0 <= work <= seconds:
                return "time"
        return None

    with Path(output).open("x") as log:
        child = subprocess.Popen(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
            preexec_fn=parent_death,
        )
        try:
            while child.poll() is None:
                elapsed = time.monotonic() - start
                peak = max(peak, rss_bytes(child.pid))
                reason = read_marker()
                limit = closing_seconds if closed is not None else seconds
                if elapsed >= limit:
                    reason = "time"
                elif peak > rss_limit:
                    reason = "memory"
                elif abs((time.time() - utc_start) - elapsed) > 2:
                    reason = "clock_discontinuity"
                if reason:
                    break
                time.sleep(min(poll, max(0.001, limit - elapsed)))
            if reason:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=grace)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
            elif child.returncode != 0:
                reason = "child_failure"
            else:
                reason = read_marker()
                if closing_marker is not None and closed is None:
                    reason = "missing_closing_marker"
                if time.monotonic() - start > (closing_seconds if closed is not None else seconds):
                    reason = "time"
        except BaseException:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
            raise
    elapsed = time.monotonic() - start
    return dict(
        status="failed" if reason else "passed",
        reason=reason,
        returncode=child.returncode,
        wall_seconds=elapsed,
        rss_peak_bytes=peak,
        pid=child.pid,
        work_seconds=closed["work_done_monotonic"] - start if closed else elapsed,
        work_ended=closed["work_done_utc"] if closed else time.time(),
    )
