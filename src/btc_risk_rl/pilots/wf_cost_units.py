"""Future isolated supervisor for the fixed 2×(Q0+10 Q/A/B+D) cost study."""

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
    P2RSharedBudget,
    _cgroup,
    check_service_context,
    read_power,
    read_worker_progress,
)
from btc_risk_rl.pilots.p2r_units import _verify_completion
from btc_risk_rl.pilots.supervisor import rss_bytes, supervise
from btc_risk_rl.pilots.wf_cost import (
    CAMPAIGN,
    CONFIG,
    WFCostLedger,
    WFCostSettings,
    digest,
    inspect_budget,
    inspect_host,
    inspect_inputs,
    require_campaign,
    roster,
    unit_cap,
)
from btc_risk_rl.pilots.wf_cost_source import build_fold_source
from btc_risk_rl.pilots.worker import write_json


def _launch_readiness():
    """No output writes. Require every host and input guard before root creation."""
    require_campaign()
    check_service_context(require_linger=True)
    host = inspect_host()
    if (not resource_ready(host)
            or host["linger"] != "yes" or host["user_manager"] != "running"):
        raise ValueError("WF cost host preflight blocked")
    inputs = inspect_inputs()
    budget = inspect_budget()
    if not inputs["ok"] or not budget["ok"] or budget["remaining_before_reserve"] < 120:
        raise ValueError("WF cost input or global budget preflight blocked")
    if CAMPAIGN.exists() and not (CAMPAIGN / "ledger.jsonl").is_file():
        raise ValueError("WF cost root exists without a valid ledger")
    return inputs, budget


def resource_ready(host):
    power = host["power"]
    return (power.get("ac") is True and power.get("battery_percent", -1) >= 50
            and host.get("memory_available_bytes") is not None
            and host["memory_available_bytes"] >= 4 * 1024**3
            and host.get("disk_free_bytes", 0) >= 20 * 1024**3)


def _unit_resources():
    try:
        ac, battery = read_power()
        power = dict(ac=ac, battery_percent=battery)
    except (OSError, ValueError):
        power = dict(ac=False, battery_percent=-1)
    available = next((int(line.split()[1]) * 1024
                      for line in Path("/proc/meminfo").read_text().splitlines()
                      if line.startswith("MemAvailable:")), None)
    return dict(power=power, memory_available_bytes=available,
                disk_free_bytes=shutil.disk_usage(CAMPAIGN.parent).free)


def _source_identity(sources):
    return {fold: source.identity() for fold, source in sources.items()}


def _record_fold_manifests(sources):
    """Persist cutoff/source hashes after approval, before any trajectory."""
    for fold, source in sources.items():
        directory = CAMPAIGN / "folds" / f"wf-{fold}"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "manifest.json"
        payload = dict(schema_version="wf_cost_fold_in_memory_v1", fold=fold,
                       source_identity=source.identity(),
                       episodes=len(source.route_ids),
                       fit_rows=source.audit["fit_count"],
                       trajectories_generated=0,
                       validation_observations_loaded=False)
        if path.exists():
            import json

            if json.loads(path.read_text()) != payload:
                raise ValueError("WF cost fold manifest changed on resume")
        else:
            write_json(path, payload)


def first_q0_audit_pause(state):
    """Require a supervised session boundary after the first accepted Q0."""
    return (state["status"] == "ready" and len(state["units"]) == 1
            and state["pending"] is None)


def run_units():
    """Run only under a registered user service; never called by preflight."""
    inputs, budget = _launch_readiness()
    sources = {fold: build_fold_source(fold) for fold, _, _ in roster()}
    identity = dict(profile="wf_cost_training_folds_only", roster=roster(),
                    source=_source_identity(sources),
                    input_sha256=inputs["sha256"], config_sha256=digest(CONFIG),
                    code={fold: {k: v for k, v in provenance(source).items()
                                 if k not in {"threads", "deterministic"}}
                          for fold, source in sources.items()},
                    diagnostic_n=64)
    entered = time.time()
    with P2RSharedBudget(CAMPAIGN.parent, CAMPAIGN.name, now=entered) as shared:
        if shared.external_seconds > budget["global_spent"]:
            budget = inspect_budget()
        if shared.external_seconds > budget["global_spent"]:
            raise ValueError("Shared-budget debit changed during preflight")
        CAMPAIGN.mkdir(exist_ok=True)
        _record_fold_manifests(sources)
        journal = P2RJournal(CAMPAIGN / "supervisor.jsonl", campaign=CAMPAIGN.name)
        invocation = os.environ.get("INVOCATION_ID")
        write_json(CAMPAIGN / f"preflight-{uuid.uuid4().hex}.json",
                   dict(observed_utc=utc(time.time()), invocation_id=invocation,
                        host=inspect_host(), budget=budget, inputs=inputs,
                        fold_source_identity=_source_identity(sources)))
        journal.record("supervisor_started", phase="preflight", run_id="wf-2021",
                       unit=None, counters={}, external_seconds=shared.external_seconds)
        with WFCostLedger(CAMPAIGN, now=entered, identity=identity,
                          external_seconds=shared.external_seconds) as ledger:
            if ledger.state["status"] == "completed":
                return ledger.state
            ledger.preflight_done(time.time())
            interrupted = {"signum": None}
            current = {"fold": None, "unit": None, "phase": "between_units"}
            old_handlers = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT)}

            def handle(signum, _frame):
                interrupted["signum"] = signum
                journal.record("signal", phase=current["phase"],
                               run_id=(f"wf-{current['fold']}" if current["fold"]
                                       else "wf-cost"), unit=current["unit"],
                               counters={}, signum=signum)

            for signum in old_handlers:
                signal.signal(signum, handle)
            try:
                while len(ledger.state["units"]) < 22:
                    if interrupted["signum"] is not None:
                        journal.record("paused", phase="between_units", run_id="wf-cost",
                                       unit=None, counters={}, reason="signal")
                        return ledger.state
                    index = len(ledger.state["units"])
                    fold, seed, condition = roster()[index // 11]
                    unit = index % 11
                    current.update(fold=fold, unit=unit)
                    if not resource_ready(_unit_resources()):
                        journal.record("paused", phase="between_units", run_id=f"wf-{fold}",
                                       unit=unit, counters={}, reason="resources")
                        return ledger.state
                    decision = ledger.admit_unit(fold, unit, time.time())
                    if decision == "incomplete":
                        ledger.state["status"] = "incomplete"
                        ledger.persist(time.time())
                        return ledger.state
                    if decision == "pause":
                        journal.record("paused", phase="between_units", run_id=f"wf-{fold}",
                                       unit=unit, counters={}, reason="budget")
                        return ledger.state
                    work = CAMPAIGN / f"wf-{fold}"
                    work.mkdir(exist_ok=True)
                    prior = ledger.state["runs"].get(f"wf-{fold}", {}).get("checkpoint")
                    if unit > 0 and not prior:
                        raise ValueError("WF cost prior complete checkpoint absent")
                    settings = WFCostSettings(seed=seed)
                    token = uuid.uuid4().hex
                    request = dict(root=str(work), fold=fold, settings=asdict(settings),
                                   config=str(CONFIG), run_id=f"wf-{fold}", condition=condition,
                                   unit=unit, previous=prior, token=token,
                                   atomic_checkpoint=True)
                    request_path = work / f"request-{unit}.json"
                    write_json(request_path, request)
                    ledger.begin_unit(fold, unit, time.time())
                    ledger.state["pending"].update(token=token, supervisor_pid=os.getpid(),
                                                    request_sha256=digest(request_path))
                    ledger.persist(time.time())
                    current["phase"] = "unit"
                    command = [sys.executable, "-m", "btc_risk_rl.pilots.wf_cost_worker",
                               str(request_path)]
                    journal.record("unit_started", phase="Q0" if unit == 0 else "Q/A/B+D",
                                   run_id=f"wf-{fold}", unit=unit, counters={},
                                   worker_command=command)
                    last_heartbeat = [None]

                    def tick(pid, _elapsed, peak):
                        stamp = time.monotonic()
                        if last_heartbeat[0] is not None and stamp - last_heartbeat[0] < 4:
                            return
                        if not resource_ready(_unit_resources()):
                            raise ValueError("WF cost resources lost during unit")
                        phase, counters = read_worker_progress(work, unit, allow_previous=True)
                        journal.record("heartbeat", phase=phase, run_id=f"wf-{fold}",
                                       unit=unit, counters=counters, pid_worker=pid,
                                       cgroup=_cgroup(pid), rss_worker=peak,
                                       rss_supervisor=rss_bytes(os.getpid()))
                        observed = journal.last["monotonic"]
                        if last_heartbeat[0] is not None and observed - last_heartbeat[0] > 5:
                            raise ValueError("WF cost heartbeat exceeded five seconds")
                        last_heartbeat[0] = observed

                    result = supervise(
                        command,
                        output=work / f"worker-{unit}.log", seconds=unit_cap(unit),
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
                        ledger.fail(time.time(), "interrupted_supervisor_or_unit",
                                    supervisor=result, signum=interrupted["signum"])
                        journal.record("unit_failed", phase=current["phase"],
                                       run_id=f"wf-{fold}", unit=unit, counters={},
                                       reason=result.get("reason", "signal"))
                        return ledger.state
                    payload, boundary = _verify_completion(
                        work, unit, settings, condition, f"wf-{fold}", result,
                        identity["code"][fold], diagnostic_n=64)
                    if interrupted["signum"] is not None:
                        ledger.fail(time.time(), "signal_during_commit")
                        return ledger.state
                    prior_mask = signal.pthread_sigmask(signal.SIG_BLOCK,
                                                       {signal.SIGTERM, signal.SIGINT})
                    try:
                        ledger.accept_unit(fold, unit, time.time(), Path(payload["checkpoint"]),
                                           report=payload["report"],
                                           resources=payload["resources"],
                                           evidence=dict(report_sha256=digest(
                                               work / f"unit-{unit}.json"), supervisor=result))
                        journal.record("unit_completed", phase=boundary,
                                       run_id=f"wf-{fold}", unit=unit,
                                       counters=payload["resources"],
                                       checkpoint_sha256=payload["checkpoint_sha256"])
                    finally:
                        signal.pthread_sigmask(signal.SIG_SETMASK, prior_mask)
                    current["phase"] = "between_units"
                    if first_q0_audit_pause(ledger.state):
                        journal.record("paused", phase="between_units",
                                       run_id=f"wf-{fold}", unit=None, counters={},
                                       reason="first_q0_audit")
                        return ledger.state
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
                journal.record("supervisor_exit", phase=current["phase"],
                               run_id=f"wf-{current['fold']}", unit=current["unit"],
                               counters={}, status=ledger.state["status"])
                for signum, handler in old_handlers.items():
                    signal.signal(signum, handler)
