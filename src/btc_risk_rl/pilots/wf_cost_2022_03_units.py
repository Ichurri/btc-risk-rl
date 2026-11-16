"""Supervised 2022-only WF units under the metered pre-ledger attempt."""

from __future__ import annotations

import json
import os
import shutil
import signal
import sys
import time
import uuid
from dataclasses import asdict
from pathlib import Path

from btc_risk_rl.agents.checkpoint import provenance
from btc_risk_rl.pilots.budget import utc
from btc_risk_rl.pilots.p2r import (
    P2RJournal,
    _cgroup,
    check_service_context,
    read_power,
    read_worker_progress,
)
from btc_risk_rl.pilots.p2r_units import _verify_completion
from btc_risk_rl.pilots.supervisor import rss_bytes, supervise
from btc_risk_rl.pilots.wf_cost import CONFIG, WFCostSettings, digest, inspect_budget, inspect_host
from btc_risk_rl.pilots.wf_cost_2022_03_exec import (
    CAMPAIGN,
    EXPECTED_FIT_ROWS,
    EXPECTED_ROUTES,
    WF2022Ledger,
    code_sha256,
    inspect_inputs,
    launch_memory_ready,
    require_campaign,
    require_recent_prepare,
)
from btc_risk_rl.pilots.wf_cost_2022_03_orchestrator import (
    CHECKS_NAME,
    UNIT_CAPS,
    BudgetAttempt,
    PreflightBlocked,
)
from btc_risk_rl.pilots.wf_cost_replacement_05_units import (
    observe_resource_guard,
    resource_ready,
)
from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal
from btc_risk_rl.pilots.wf_cost_source import build_fold_source
from btc_risk_rl.pilots.worker import write_json


def _resources():
    try:
        ac, battery = read_power()
        power = dict(ac=ac, battery_percent=battery)
    except (OSError, ValueError) as exc:
        power = dict(ac=False, battery_percent=-1,
                     values_observed=False, sensor_error=str(exc))
    available = next((int(line.split()[1]) * 1024
                      for line in Path("/proc/meminfo").read_text().splitlines()
                      if line.startswith("MemAvailable:")), None)
    return dict(power=power, memory_available_bytes=available,
                disk_free_bytes=shutil.disk_usage(CAMPAIGN.parent).free)


def _external(now):
    result = inspect_budget(now=now, campaign=CAMPAIGN)
    if not result["ok"]:
        raise PreflightBlocked("Another campaign is active")
    return result["global_spent"]


def _preflight():
    check_service_context(require_linger=True)
    host = inspect_host()
    if (not resource_ready(host)
            or host["linger"] != "yes" or host["user_manager"] != "running"):
        raise PreflightBlocked("WF 2022 host preflight blocked")
    if not launch_memory_ready(host.get("memory_available_bytes")):
        raise PreflightBlocked("WF 2022 launch memory headroom insufficient")
    inputs = inspect_inputs()
    budget = inspect_budget(campaign=CAMPAIGN)
    if not inputs["ok"]:
        raise ValueError("WF 2022 input integrity failed")
    if not budget["ok"]:
        raise PreflightBlocked("WF 2022 shared budget blocked")
    if CAMPAIGN.is_symlink():
        raise ValueError("WF 2022 campaign root is a symlink")
    if CAMPAIGN.exists() and not (CAMPAIGN / "ledger.jsonl").is_file():
        raise ValueError("WF 2022 root exists without a ledger")
    return host, inputs, budget


def run_units(*, stop_after_q0: bool = False, stop_after_unit: int | None = None):
    """Run through complete frontiers; Q0 may be separated for first audit."""
    if stop_after_unit is not None and (type(stop_after_unit) is not int
                                        or not 0 <= stop_after_unit < 10):
        raise ValueError("WF 2022 pause boundary invalid")
    require_campaign()
    checks = CAMPAIGN.parent / "shared-pilot-budget" / CHECKS_NAME
    with BudgetAttempt(CAMPAIGN.parent, gate=require_campaign,
                       authorize=require_campaign, external_spent=_external,
                       night_window=True) as attempt:
        def check_prepare():
            try:
                require_recent_prepare(checks, now=time.time())
            except ValueError as exc:
                raise PreflightBlocked(str(exc)) from exc

        attempt.run_check("prepare_freshness",
                          check_prepare)
        host, inputs, budget = attempt.run_check("service_preflight", _preflight)
        # The attempt is durable before any training source is loaded or root is created.
        source = attempt.run_check("build_2022_fold", lambda: build_fold_source("2022"))
        if (len(source.route_ids) != EXPECTED_ROUTES
                or source.audit.get("fit_count") != EXPECTED_FIT_ROWS
                or source.audit.get("validation_observations_loaded")):
            raise ValueError("WF 2022 fold count or provenance changed")
        CAMPAIGN.mkdir(exist_ok=True)
        with WFCostSessionJournal(CAMPAIGN / "sessions.jsonl",
                                  campaign=CAMPAIGN.name) as sessions:
            session_token = sessions.start(now=time.time(), monotonic=time.monotonic(),
                                           invocation_id=os.environ.get("INVOCATION_ID"))
            try:
                state = _run_locked(attempt, sessions, session_token, source, host, inputs, budget,
                                    stop_after_q0=stop_after_q0,
                                    stop_after_unit=stop_after_unit)
            except BaseException as exc:
                sessions.end(session_token, now=time.time(), monotonic=time.monotonic(),
                             status="failed", reason=str(exc))
                raise
            sessions.end(session_token, now=time.time(), monotonic=time.monotonic(),
                         status="ready" if state["status"] in {"ready", "completed"}
                         else "failed", reason=state.get("failure", {}).get("reason"))
            return state


def _run_locked(attempt, sessions, session_token, source, host, inputs, budget, *,
                stop_after_q0, stop_after_unit):
    identity = dict(profile="wf_2022_cost_only", roster=[["2022", 498614892, "C10"]],
                    source=source.identity(), code_sha256=code_sha256(),
                    input_sha256=inputs["sha256"], config_sha256=digest(CONFIG),
                    code={k: v for k, v in provenance(source).items()
                          if k not in {"threads", "deterministic"}}, diagnostic_n=64)
    fold_dir = CAMPAIGN / "folds/wf-2022"
    fold_dir.mkdir(parents=True, exist_ok=True)
    manifest = dict(schema_version="wf_2022_fold_in_memory_v1", fold="2022",
                    source_identity=source.identity(), episodes=len(source.route_ids),
                    fit_rows=source.audit["fit_count"], trajectories_generated=0,
                    validation_observations_loaded=False)
    manifest_path = fold_dir / "manifest.json"
    if manifest_path.exists():
        if json.loads(manifest_path.read_text()) != manifest:
            raise ValueError("WF 2022 fold manifest changed on resume")
    else:
        write_json(manifest_path, manifest)
    journal = P2RJournal(CAMPAIGN / "supervisor.jsonl", campaign=CAMPAIGN.name)
    write_json(CAMPAIGN / f"preflight-{uuid.uuid4().hex}.json",
               dict(observed_utc=utc(time.time()), invocation_id=os.environ.get("INVOCATION_ID"),
                    host=host, budget=budget, inputs=inputs,
                    fold_source_identity=source.identity()))
    journal.record("supervisor_started", phase="preflight", run_id="wf-2022",
                   unit=None, counters={}, budget=budget)
    with WF2022Ledger(CAMPAIGN, now=time.time(), identity=identity,
                      external_seconds=budget["global_spent"]) as ledger:
        if ledger.state["status"] == "completed":
            return ledger.state
        ledger.preflight_done(time.time())
        interrupted = {"signum": None}
        current = {"unit": None, "phase": "between_units"}
        old_handlers = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT)}

        def handle(signum, _frame):
            interrupted["signum"] = signum
            journal.record("signal", phase=current["phase"], run_id="wf-2022",
                           unit=current["unit"], counters={}, signum=signum)

        for signum in old_handlers:
            signal.signal(signum, handle)
        try:
            while len(ledger.state["units"]) < 11:
                if interrupted["signum"] is not None:
                    journal.record("paused", phase="between_units", run_id="wf-2022",
                                   unit=None, counters={}, reason="signal")
                    return ledger.state
                if time.time() > ledger.day["hard_deadline"]:
                    journal.record("paused", phase="between_units", run_id="wf-2022",
                                   unit=None, counters={}, reason="day_boundary")
                    return ledger.state
                unit = len(ledger.state["units"])
                current["unit"] = unit
                resources = _resources()
                if not observe_resource_guard(journal, resources, run_id="wf-2022",
                                              unit=unit, phase="between_units",
                                              disposition="pause"):
                    journal.record("paused", phase="between_units", run_id="wf-2022",
                                   unit=unit, counters={}, reason="resources")
                    return ledger.state
                work = CAMPAIGN / "wf-2022"
                previous = ledger.state["runs"].get("wf-2022", {}).get("checkpoint")
                if unit > 0 and not previous:
                    raise ValueError("WF 2022 prior checkpoint absent")
                settings = WFCostSettings(seed=498614892)
                token = uuid.uuid4().hex
                request = dict(root=str(work), fold="2022", settings=asdict(settings),
                               config=str(CONFIG), run_id="wf-2022", condition="C10",
                               unit=unit, previous=previous, token=token,
                               atomic_checkpoint=True)
                request_path = work / f"request-{unit}.json"

                def execute():
                    work.mkdir(exist_ok=True)
                    write_json(request_path, request)
                    ledger.begin_unit("wf-2022", unit, time.time())
                    ledger.state["pending"].update(
                        token=token, supervisor_pid=os.getpid(),
                        request_sha256=digest(request_path))
                    ledger.persist(time.time())
                    current["phase"] = "unit"
                    command = [sys.executable, "-m", "btc_risk_rl.pilots.wf_cost_2022_03_worker",
                               str(request_path)]
                    journal.record("unit_started", phase="Q0" if unit == 0 else "Q/A/B+D",
                                   run_id="wf-2022", unit=unit, counters={},
                                   worker_command=command)
                    last_heartbeat = [None]

                    def tick(pid, _elapsed, peak):
                        stamp = time.monotonic()
                        if last_heartbeat[0] is not None and stamp - last_heartbeat[0] < 4:
                            return
                        sample = _resources()
                        if not observe_resource_guard(journal, sample, run_id="wf-2022",
                                                      unit=unit, phase="unit",
                                                      disposition="fail"):
                            raise ValueError("WF 2022 resources lost during unit")
                        phase, counters = read_worker_progress(work, unit, allow_previous=True)
                        journal.record("heartbeat", phase=phase, run_id="wf-2022", unit=unit,
                                       counters=counters, pid_worker=pid, cgroup=_cgroup(pid),
                                       rss_worker=peak, rss_supervisor=rss_bytes(os.getpid()))
                        observed = journal.last["monotonic"]
                        if last_heartbeat[0] is not None and observed - last_heartbeat[0] > 5:
                            raise ValueError("WF 2022 heartbeat exceeded five seconds")
                        last_heartbeat[0] = observed

                    result = supervise(
                        command, output=work / f"worker-{unit}.log", seconds=UNIT_CAPS[unit],
                        rss_limit=10 * 1024**3, poll=0.2,
                        env=dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                                 MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1"),
                        closing_marker=work / f"closing-{unit}.json",
                        phase_marker=work / f"phase-{unit}.json",
                        closing_seconds=ledger.day["hard_deadline"] - time.time(),
                        on_poll=tick,
                        stop_requested=lambda: interrupted["signum"] is not None,
                    )
                    if interrupted["signum"] is not None or result["status"] != "passed":
                        raise ValueError("WF 2022 interrupted or failed unit")
                    payload, boundary = _verify_completion(
                        work, unit, settings, "C10", "wf-2022", result,
                        identity["code"], diagnostic_n=64)
                    return payload, boundary, result

                try:
                    completed = attempt.run_unit(ledger.state, unit=unit,
                                                 operation=execute, sessions=sessions,
                                                 session_token=session_token)
                    if isinstance(completed, str):
                        if completed == "incomplete":
                            ledger.state["status"] = "incomplete"
                            ledger.persist(time.time())
                        else:
                            journal.record("paused", phase="between_units",
                                           run_id="wf-2022", unit=unit,
                                           counters={}, reason="budget_or_window")
                        return ledger.state
                    payload, boundary, result = completed
                    if interrupted["signum"] is not None:
                        raise ValueError("WF 2022 signal during commit")
                    prior_mask = signal.pthread_sigmask(signal.SIG_BLOCK,
                                                        {signal.SIGTERM, signal.SIGINT})
                    try:
                        ledger.accept_unit(
                            unit, time.time(), Path(payload["checkpoint"]),
                            report=payload["report"], resources=payload["resources"],
                            evidence=dict(report_sha256=digest(work / f"unit-{unit}.json"),
                                          supervisor=result))
                        journal.record("unit_completed", phase=boundary, run_id="wf-2022",
                                       unit=unit, counters=payload["resources"],
                                       checkpoint_sha256=payload["checkpoint_sha256"])
                    finally:
                        signal.pthread_sigmask(signal.SIG_SETMASK, prior_mask)
                    current["phase"] = "between_units"
                    if (unit == 0 and stop_after_q0) or unit == stop_after_unit:
                        journal.record("paused", phase="between_units", run_id="wf-2022",
                                       unit=None, counters={}, reason="first_q0_audit")
                        return ledger.state
                except PreflightBlocked as exc:
                    journal.record("paused", phase="between_units", run_id="wf-2022",
                                   unit=unit, counters={}, reason=str(exc))
                    return ledger.state
                except BaseException as exc:
                    if ledger.state["status"] not in {"failed", "incomplete"}:
                        ledger.fail(time.time(), "interrupted_supervisor_or_unit", error=str(exc))
                    raise
            return ledger.state
        except BaseException as exc:
            if ledger.state["status"] not in {"failed", "incomplete"}:
                ledger.fail(time.time(), "interrupted_supervisor_or_unit", error=str(exc))
            raise
        finally:
            day = ledger.day
            day["charged_wall_seconds"] = max(day.get("charged_wall_seconds", 0),
                                               time.time() - day["started_utc_epoch"])
            ledger.persist(time.time())
            journal.record("supervisor_exit", phase=current["phase"], run_id="wf-2022",
                           unit=current["unit"], counters={}, status=ledger.state["status"])
            for signum, handler in old_handlers.items():
                signal.signal(signum, handler)
