"""Canonical campaign, sequential workers, no CLI budget or parameter overrides."""

import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import sys
import time
import uuid
from pathlib import Path

from btc_risk_rl.pilots.budget import CAPS, CampaignLedger
from btc_risk_rl.pilots.protocol import CAMPAIGN, PROTOCOL_SHA, ROOT, approved, roster
from btc_risk_rl.pilots.supervisor import supervise


def fingerprint():
    files = sorted((ROOT / "src/btc_risk_rl").rglob("*.py")) + [
        ROOT / "scripts/run_pilot.py",
        ROOT / "uv.lock",
        ROOT / "configs/initial.toml",
        ROOT / "docs/evidence/segmented-h1/manifest.json",
    ]
    identity = dict(
        protocol_sha256=PROTOCOL_SHA,
        code={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        python=platform.python_version(),
        machine=platform.machine(),
        packages={
            n: importlib.metadata.version(n) for n in ("torch", "numpy", "pandas", "gymnasium")
        },
    )
    return identity


def preflight():
    approved()
    available = next(
        int(line.split()[1]) * 1024
        for line in Path("/proc/meminfo").read_text().splitlines()
        if line.startswith("MemAvailable:")
    )
    free = shutil.disk_usage(CAMPAIGN).free
    if available < 2 * 1024**3 or free < 5 * 1024**3:
        raise ValueError("Insufficient preflight memory/disk")
    if not importlib.metadata.version("torch").endswith("+cpu"):
        raise ValueError("CPU-only torch required")
    return dict(available_memory_bytes=available, free_disk_bytes=free)


def partial_failure(ledger, root, unit):
    failure = root / f"failure-{unit}.json"
    progress = root / "progress.json"
    payload, exact = {}, False
    try:
        if failure.exists():
            payload, exact = json.loads(failure.read_text()), True
        elif progress.exists():
            payload = json.loads(progress.read_text())
    except (OSError, ValueError):
        pass
    previous = ledger.state["runs"][ledger.state["pending"]["run_id"]]["resources"]
    counts = payload.get("counters") or {}
    delta = {k: max(0, v - previous.get(k, 0)) for k, v in counts.items()}
    return dict(
        worker_diagnostic=payload,
        partial_resources=delta,
        exact=exact,
        note="A killed process may have unrecorded partial work; counters then are lower bounds",
    )


def expected_resources(unit):
    return dict(
        trajectories=400 if unit == 0 else 864,
        transitions=72000 if unit == 0 else 155520,
        actor_updates=0 if unit == 0 else 8,
        critic_updates=0 if unit == 0 else 8,
    )


def run_campaign(invoked_at=None):
    invoked_at = time.time() if invoked_at is None else invoked_at
    identity = fingerprint()
    with CampaignLedger(CAMPAIGN, now=invoked_at, identity=identity) as ledger:
        active_start = time.monotonic()
        enforce_deadline = (
            ledger.state["status"] != "completed" and time.time() < ledger.day["work_deadline"]
        )
        try:
            if ledger.state["status"] == "completed":
                return ledger.state
            if not enforce_deadline:
                ledger.state["pause_reason"] = "daily_window_closed_no_work_started"
                return ledger.state
            checks = preflight()
            ledger.preflight_done(time.time())
            ledger.state["preflight"] = checks
            ledger.persist(time.time())
            while ledger.state["cursor"] < len(roster()):
                index = ledger.state["cursor"]
                _, condition = roster()[index]
                run_id = f"run-{index:02d}-{condition}"
                prior = ledger.state["runs"].get(run_id, {})
                unit = prior.get("next_unit", 0)
                kind = "q0" if unit == 0 else "iteration"
                if ledger.admit(condition, kind, time.time()) == "pause":
                    ledger.state["pause_reason"] = "shared_daily_window_no_room_for_complete_unit"
                    ledger.persist(time.time())
                    print(
                        json.dumps(
                            dict(
                                status="paused",
                                next_run=run_id,
                                next_unit=unit,
                                resume="same command on a later America/La_Paz day",
                            )
                        ),
                        flush=True,
                    )
                    return ledger.state
                token = uuid.uuid4().hex
                root = CAMPAIGN / run_id
                root.mkdir(exist_ok=True)
                ledger.begin(run_id, kind, time.time())
                ledger.state["pending"].update(
                    unit=unit,
                    previous=prior.get("checkpoint"),
                    supervisor_pid=os.getpid(),
                    token=token,
                )
                ledger.persist(time.time())
                remaining = min(CAPS[kind], ledger.day["work_deadline"] - time.time())
                env = dict(
                    os.environ,
                    OMP_NUM_THREADS="1",
                    MKL_NUM_THREADS="1",
                    OPENBLAS_NUM_THREADS="1",
                    NUMEXPR_NUM_THREADS="1",
                )
                print(
                    json.dumps(
                        dict(status="running", run=run_id, unit=unit, cap_seconds=remaining)
                    ),
                    flush=True,
                )
                supervised = supervise(
                    [sys.executable, "-m", "btc_risk_rl.pilots.worker", "--token", token],
                    output=root / f"supervisor-{unit}.log",
                    seconds=remaining,
                    rss_limit=10 * 1024**3,
                    env=env,
                    closing_marker=root / f"closing-{unit}.json",
                    closing_seconds=ledger.day["hard_deadline"] - time.time(),
                )
                if supervised["status"] != "passed":
                    partial = partial_failure(ledger, root, unit)
                    for k, v in partial["partial_resources"].items():
                        for totals in (
                            ledger.state["resources"],
                            ledger.state["runs"][run_id]["resources"],
                        ):
                            totals[k] = totals.get(k, 0) + v
                    ledger.fail(
                        time.time(), "supervised_unit_failed", supervisor=supervised, **partial
                    )
                    print(
                        json.dumps(dict(status="failed", run=run_id, unit=unit, **partial)),
                        flush=True,
                    )
                    return ledger.state
                result = json.loads((root / f"unit-{unit}.json").read_text())
                expected = expected_resources(unit)
                if result["resources"] != expected or result["unit"] != unit:
                    raise ValueError("Worker counters mismatch")
                ledger.finish(
                    time.time(),
                    resources=result["resources"],
                    condition=condition,
                    checkpoint=result["checkpoint"],
                    checkpoint_sha256=result["checkpoint_sha256"],
                    supervisor=supervised,
                    warnings=len(result["warnings"]),
                    algorithm_seconds=result["algorithm_seconds"],
                    save_seconds=result["save_seconds"],
                    work_seconds=supervised.get("work_seconds", supervised["wall_seconds"]),
                    work_ended=supervised.get("work_ended", time.time()),
                )
                print(
                    json.dumps(
                        dict(
                            status="unit_completed",
                            run=run_id,
                            unit=unit,
                            seconds=supervised["wall_seconds"],
                            resources=result["resources"],
                            cumulative_warning_entries=len(result["warnings"]),
                        )
                    ),
                    flush=True,
                )
            ledger.state["status"] = "completed"
            ledger.persist(time.time())
            return ledger.state
        except BaseException as exc:
            if ledger.state["status"] not in {"failed", "incomplete"}:
                ledger.fail(time.time(), f"{type(exc).__name__}: {exc}")
            raise
        finally:
            ledger.day["active_seconds"] += time.monotonic() - active_start
            ledger.day["charged_wall_seconds"] = (
                min(time.time(), ledger.day["hard_deadline"]) - ledger.day["started_utc_epoch"]
            )
            if enforce_deadline and time.time() > ledger.day["hard_deadline"]:
                ledger.state["status"] = "failed"
                ledger.state["deadline_violation"] = True
            ledger.persist(time.time())
