"""P2R synthetic Q0/Q-A-B-D units under a durable, fail-closed supervisor.

This module has no historical-market entrypoint. The worker is the existing P2
synthetic worker, so the learning algorithm and its RNG remain unchanged.
"""

import json
import math
import os
import signal
import sys
import time
from dataclasses import asdict
from pathlib import Path

from btc_risk_rl.agents.checkpoint import provenance
from btc_risk_rl.agents.synthetic import SyntheticMarket
from btc_risk_rl.config import load_config
from btc_risk_rl.pilots.budget import CAPS
from btc_risk_rl.pilots.p2 import P2SyntheticSettings, file_hash
from btc_risk_rl.pilots.p2_budget import P2Ledger
from btc_risk_rl.pilots.p2r import (
    P2RJournal,
    P2RSharedBudget,
    _cgroup,
    check_resources,
    check_service_context,
    read_power,
    read_worker_progress,
)
from btc_risk_rl.pilots.supervisor import rss_bytes, supervise
from btc_risk_rl.pilots.worker import write_json


def _expected(settings, unit):
    batches = math.ceil(settings.n_a / settings.minibatch)
    learning = settings.n_q if unit == 0 else settings.n_a + settings.n_q + settings.n_b
    diagnostic = 0 if unit == 0 else 2
    return dict(
        trajectories=learning,
        transitions=180 * learning,
        diagnostic_trajectories=diagnostic,
        diagnostic_transitions=180 * diagnostic,
        actor_updates=0 if unit == 0 else settings.actor_epochs * batches,
        critic_updates=0 if unit == 0 else settings.critic_epochs * batches,
    )


def synthetic_worker_command(request_path, hold_seconds=0):
    """Build a synthetic-only command; the bounded hold stays under supervise."""
    if type(hold_seconds) is not int or not 0 <= hold_seconds <= 900:
        raise ValueError("Invalid synthetic hold seconds")
    request_path = Path(request_path)
    if hold_seconds:
        return [sys.executable, "-m", "btc_risk_rl.pilots.p2r_hold",
                str(hold_seconds), str(request_path)]
    return [sys.executable, "-m", "btc_risk_rl.pilots.p2_runner",
            "--synthetic-request", str(request_path)]


def _verify_completion(work, unit, settings, condition, run_id, result, expected_provenance):
    payload_path = work / f"unit-{unit}.json"
    payload = json.loads(payload_path.read_text())
    point = work / f"checkpoint-{unit}"
    manifest = json.loads((point / "manifest.json").read_text())
    worker_provenance = manifest.get("provenance", {})
    boundary = "after_q0" if unit == 0 else "after_dual_and_D"
    if (payload.get("status") != "passed" or payload.get("unit") != unit
            or payload.get("resources") != _expected(settings, unit)
            or payload.get("checkpoint") != str(point)
            or payload.get("checkpoint_sha256") != file_hash(point / "state.pt")
            or manifest.get("state_sha256") != payload["checkpoint_sha256"]
            or manifest.get("boundary") != boundary
            or manifest.get("schema_version") != "p2_complete_boundary_v1"
            or manifest.get("profile") != settings.purpose
            or any(worker_provenance.get(key) != value
                   for key, value in expected_provenance.items())
            or worker_provenance.get("threads") != 1
            or worker_provenance.get("deterministic") is not True
            or manifest.get("settings") != asdict(settings)
            or manifest.get("condition") != condition
            or manifest.get("run_id") != run_id
            or result["status"] != "passed"):
        raise ValueError("P2R incomplete or incompatible worker result")
    return payload, boundary


def run_synthetic_units(root, config_path, settings, condition, *, max_units=None,
                        power_root=None, memory_available=None, disk_free=None,
                        fixture_window=False, heartbeat_seconds=5.0,
                        require_service=False, synthetic_hold_seconds=0):
    """Run at most ``max_units`` complete synthetic units; never load market data.

    ``fixture_window`` and injected sensor readings are test-only. Neither can
    be supplied to a historical runner because this function requires the exact
    synthetic settings type and constructs SyntheticMarket itself.
    """
    if type(settings) is not P2SyntheticSettings or condition not in {"C0", "C5", "C10"}:
        raise PermissionError("P2R unit integration accepts synthetic profile only")
    if max_units is not None and (type(max_units) is not int or max_units < 0):
        raise ValueError("Invalid synthetic unit limit")
    if not 0 < heartbeat_seconds <= 5:
        raise ValueError("P2R heartbeat must be at most five seconds")
    if type(synthetic_hold_seconds) is not int or not 0 <= synthetic_hold_seconds <= 900:
        raise ValueError("Invalid synthetic hold seconds")
    if require_service:
        check_service_context(require_linger=False)
    root = Path(root).resolve()
    if not root.name.startswith("p2r-synthetic-"):
        raise ValueError("P2R synthetic units require a separate p2r-synthetic-* root")
    config_path = Path(config_path).resolve()
    source = SyntheticMarket(load_config(config_path))
    stable_provenance = {key: value for key, value in provenance(source).items()
                         if key not in {"threads", "deterministic"}}
    identity = dict(
        profile="p2r_synthetic_units",
        config=str(config_path),
        config_sha256=file_hash(config_path),
        code=stable_provenance,
        settings=asdict(settings),
        condition=condition,
        synthetic_hold_seconds=synthetic_hold_seconds,
        runner_sha256=file_hash(Path(__file__)),
    )
    entered = time.time()
    active_start = time.monotonic()
    run_id = f"run-00-{condition}"
    with P2RSharedBudget(root.parent, root.name, now=entered, synthetic_fixture=True) as shared:
        root.mkdir(exist_ok=True)
        journal = P2RJournal(root / "supervisor.jsonl", campaign=root.name)
        journal.record("supervisor_started", phase="preflight", run_id=run_id,
                       unit=None, counters={}, external_seconds=shared.external_seconds)
        try:
            ledger = P2Ledger(root, now=entered, identity=identity,
                              external_seconds=shared.external_seconds)
        except ValueError as exc:
            journal.record("recovery_rejected", phase="preflight", run_id=run_id,
                           unit=None, counters={}, reason=str(exc))
            raise
        ledger.iterations = settings.iterations
        with ledger:
            if ledger.state["status"] == "completed":
                journal.record("supervisor_exit", phase="complete", run_id=run_id,
                               unit=settings.iterations, counters={}, status="completed_no_replay")
                return ledger.state
            interrupted = {"signum": None}
            phase = ["between_units"]
            current_unit = [None]
            latest = [{}]

            def handle(signum, _frame):
                interrupted["signum"] = signum
                journal.record("signal", phase=phase[0], run_id=run_id,
                               unit=current_unit[0], counters=latest[0], signum=signum)

            old = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT)}
            for s in old:
                signal.signal(s, handle)
            try:
                check_resources(power_root or Path("/sys/class/power_supply"),
                                memory_available=memory_available, disk_free=disk_free,
                                disk_path=root, stage="preflight")
                if fixture_window:
                    ledger.day["work_deadline"] = time.time() + 3600
                    ledger.day["hard_deadline"] = time.time() + 5400
                    ledger.persist(time.time())
                ledger.preflight_done(time.time())
                completed_here = 0
                while ledger.state["runs"].get(run_id, {}).get("next_unit", 0) <= settings.iterations:
                    if max_units is not None and completed_here >= max_units:
                        journal.record("paused", phase="between_units", run_id=run_id,
                                       unit=None, counters={}, reason="synthetic_unit_limit")
                        return ledger.state
                    unit = ledger.state["runs"].get(run_id, {}).get("next_unit", 0)
                    current_unit[0] = unit
                    work = root / run_id
                    work.mkdir(exist_ok=True)
                    if interrupted["signum"] is not None:
                        journal.record("paused", phase="between_units", run_id=run_id,
                                       unit=unit, counters={}, reason="signal")
                        return ledger.state
                    try:
                        check_resources(power_root or Path("/sys/class/power_supply"),
                                        memory_available=memory_available, disk_free=disk_free,
                                        disk_path=root, stage="unit")
                    except ValueError as exc:
                        journal.record("paused", phase="between_units", run_id=run_id,
                                       unit=unit, counters={}, reason=str(exc))
                        return ledger.state
                    kind = "q0" if unit == 0 else "iteration"
                    if ledger.admit(condition, kind, time.time()) != "start":
                        journal.record("paused", phase="between_units", run_id=run_id,
                                       unit=unit, counters={}, reason="budget")
                        return ledger.state
                    prior = ledger.state["runs"].get(run_id, {}).get("checkpoint")
                    if unit > 0 and not prior:
                        raise ValueError("Complete preceding checkpoint required")
                    request = dict(settings=asdict(settings), config=str(config_path),
                                   root=str(work), condition=condition, run_id=run_id,
                                   unit=unit, previous=prior, token=None)
                    request_path = work / f"request-{unit}.json"
                    write_json(request_path, request)
                    ledger.begin(run_id, kind, time.time())
                    ledger.state["pending"].update(unit=unit,
                        request_sha256=file_hash(request_path), supervisor_pid=os.getpid())
                    ledger.persist(time.time())
                    phase[0] = "unit"
                    journal.record("unit_started", phase="Q0" if unit == 0 else "Q/A/B+D",
                                   run_id=run_id, unit=unit, counters={}, pid_worker=None)
                    last_heartbeat = [None]
                    availability_lost = [None]

                    def tick(pid, elapsed, peak):
                        if (last_heartbeat[0] is not None
                                and time.monotonic() - last_heartbeat[0]
                                < min(heartbeat_seconds, 4.0)):
                            return
                        worker_phase, counters = read_worker_progress(work, unit,
                                                                       allow_previous=True)
                        latest[0] = counters
                        power = None
                        try:
                            check_resources(power_root or Path("/sys/class/power_supply"),
                                            memory_available=memory_available,
                                            disk_free=disk_free, disk_path=root, stage="unit")
                            ac, battery = read_power(power_root or Path("/sys/class/power_supply"))
                            power = dict(ac=ac, battery=battery)
                        except ValueError as exc:
                            if availability_lost[0] is None:
                                availability_lost[0] = str(exc)
                                journal.record("availability_lost", phase=worker_phase,
                                               run_id=run_id, unit=unit, counters=counters,
                                               reason=str(exc))
                        journal.record("heartbeat", phase=worker_phase, run_id=run_id,
                                       unit=unit, counters=counters, pid_worker=pid,
                                       cgroup=_cgroup(pid), rss_worker=peak,
                                       rss_supervisor=rss_bytes(os.getpid()),
                                       power=power)
                        recorded = journal.last["monotonic"]
                        if last_heartbeat[0] is not None:
                            observed = recorded - last_heartbeat[0]
                            if not 0 <= observed <= 5.0:
                                raise ValueError(
                                    f"P2R heartbeat interval exceeded five seconds: {observed:.6f}"
                                )
                        last_heartbeat[0] = recorded

                    cap = min(CAPS[kind], ledger.day["work_deadline"] - time.time())
                    result = supervise(
                        synthetic_worker_command(request_path, synthetic_hold_seconds),
                        output=work / f"worker-{unit}.log", seconds=cap,
                        rss_limit=10 * 1024**3, poll=min(.2, heartbeat_seconds),
                        env=dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                                 MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1"),
                        closing_marker=work / f"closing-{unit}.json",
                        phase_marker=work / f"phase-{unit}.json",
                        closing_seconds=ledger.day["hard_deadline"] - time.time(),
                        on_poll=tick,
                        stop_requested=lambda: interrupted["signum"] is not None,
                    )
                    if interrupted["signum"] is not None:
                        result.update(status="failed", reason="signal_during_unit")
                    if result["status"] != "passed":
                        ledger.fail(time.time(), "interrupted_supervisor_or_unit",
                                    supervisor=result, signum=interrupted["signum"],
                                    observed_counters=latest[0])
                        journal.record("unit_failed", phase="Q0" if unit == 0 else "Q/A/B+D",
                                       run_id=run_id, unit=unit, counters=latest[0],
                                       reason=result["reason"])
                        return ledger.state
                    payload, boundary = _verify_completion(work, unit, settings, condition,
                                                           run_id, result, identity["code"])
                    ledger.finish(time.time(), resources=payload["resources"],
                                  condition=condition, checkpoint=payload["checkpoint"],
                                  checkpoint_sha256=payload["checkpoint_sha256"],
                                  work_seconds=result["work_seconds"],
                                  work_ended=result["work_ended"], supervisor=result,
                                  availability_lost=availability_lost[0])
                    if interrupted["signum"] is not None:
                        ledger.fail(time.time(), "interrupted_supervisor_or_unit",
                                    signum=interrupted["signum"])
                        journal.record("unit_failed", phase=boundary, run_id=run_id,
                                       unit=unit, counters=latest[0],
                                       reason="signal_during_commit")
                        return ledger.state
                    phase[0] = "between_units"
                    journal.record("unit_completed", phase=boundary, run_id=run_id,
                                   unit=unit, counters=payload["resources"],
                                   checkpoint_sha256=payload["checkpoint_sha256"],
                                   supervisor=result)
                    completed_here += 1
                    if availability_lost[0] is not None:
                        journal.record("paused", phase="between_units", run_id=run_id,
                                       unit=unit + 1, counters={},
                                       reason="availability_lost_after_unit")
                        return ledger.state
                ledger.state["status"] = "completed"
                ledger.persist(time.time())
                return ledger.state
            except BaseException as exc:
                if ledger.state["status"] not in {"failed", "incomplete"}:
                    ledger.fail(time.time(), "interrupted_supervisor_or_unit", error=str(exc),
                                signum=interrupted["signum"], observed_counters=latest[0])
                    journal.record("unit_failed", phase=phase[0], run_id=run_id,
                                   unit=current_unit[0], counters=latest[0], reason=str(exc))
                raise
            finally:
                ledger.day["active_seconds"] += time.monotonic() - active_start
                ledger.day["charged_wall_seconds"] = max(
                    ledger.day.get("charged_wall_seconds", 0),
                    time.time() - ledger.day["started_utc_epoch"],
                )
                ledger.persist(time.time())
                journal.record("supervisor_exit", phase=phase[0], run_id=run_id,
                               unit=current_unit[0], counters=latest[0],
                               status=ledger.state["status"])
                for s, handler in old.items():
                    signal.signal(s, handler)
