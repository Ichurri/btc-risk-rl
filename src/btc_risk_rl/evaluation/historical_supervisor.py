"""Single-session, fail-closed OOS technical evaluator.

The source export and evaluation have different pinned permissions. The
public command never opens protected bars before the corresponding gate.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import sys
import time
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from btc_risk_rl.config import load_config
from btc_risk_rl.evaluation.access import (
    read_pinned_approval,
    require_evaluation_access,
    require_source_export_access,
)
from btc_risk_rl.evaluation.code_identity import execution_code_sha256
from btc_risk_rl.evaluation.complete_roster import verify_complete_main_roster
from btc_risk_rl.evaluation.export_builder import write_evaluation_export
from btc_risk_rl.evaluation.export_reader import load_evaluation_export
from btc_risk_rl.evaluation.ledger import EvaluationLedger
from btc_risk_rl.evaluation.runner import run_one_verified_unit
from btc_risk_rl.evaluation.source_h1 import load_h1_technical_bars
from btc_risk_rl.evaluation.synthetic import load_verified_scaler
from btc_risk_rl.evaluation.technical_closure import write_technical_closure
from btc_risk_rl.pilots.oos_v12_training import OOSSettings
from btc_risk_rl.pilots.supervisor import supervise
from btc_risk_rl.pilots.wf_cost import inspect_budget, inspect_host
from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal

ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "artifacts"
TRAINING_ROOT = ARTIFACTS / "oos-v12-training-main-01"
H1 = ROOT / "data/processed/segmented-B-h1"
SHARD = ROOT / "data/processed/p2r-training-h1"
EXPORT = ROOT / "data/processed/oos-v12-technical-2023-01"
CAMPAIGN = ARTIFACTS / "oos-v12-technical-2023-01"
SESSION_JOURNAL = ARTIFACTS / "shared-pilot-budget/oos-v12-evaluation-sessions.jsonl"
GLOBAL_LOCK = ARTIFACTS / "shared-pilot-budget/global.lock"
H1_SHA = "d7cd59b7cda003a0f69883a83a0bacf06a65c37f3653a2f466c249ddf41a6998"
RAW_SHA = "5608f59ca77d73c2afe564f94a0eddc50d26a477f73b6d3e38a47d930a9fb807"
SHARD_SHA = "62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9"
SCALER_SHA = "a598a99c368f1d50bba9f78fca2f803e46d77702d05547ccc12d076771e57479"
TRAINING_IDENTITY_SHA = "8b6211714d29f0cad71e3131ac582a8733b978b6c4832fbe2e12f78a77d6764b"
DAILY_LIMIT = 50400.0
CLOSURE_RESERVE = 2700.0
UNIT_INITIAL_RESERVE = 300.0
UNIT_LIMIT = 900.0
MIN_AVAILABLE = 4 * 1024**3
MIN_DISK = 20 * 1024**3
SESSION_NAME = "oos-v12-evaluation-v1"
BUDGET_PATH = ROOT / "docs/protocols/OOS-v1-2-technical-evaluation-budget-20261114.json"
BUDGET_SHA = "27e9ea9aaacd3d369a2efff1237e5b14cb95106da0f34d8bdf9a0f44e36305d3"
ADJUDICATION_PATH = ROOT / "docs/hitos/OOS-v1-2-adjudicacion-pre-evaluacion-20261114.md"
ADJUDICATION_SHA = "83554a665bd55622e12482407e8cd15fb6a5408fb7806a098d97ecf026d7e0e0"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(part)
    return digest.hexdigest()


def pinned_budget(approval: dict) -> None:
    if (BUDGET_PATH.is_symlink() or sha(BUDGET_PATH) != BUDGET_SHA
            or approval.get("budget_sha256") != BUDGET_SHA
            or ADJUDICATION_PATH.is_symlink()
            or sha(ADJUDICATION_PATH) != ADJUDICATION_SHA
            or approval.get("adjudication_sha256") != ADJUDICATION_SHA):
        raise PermissionError("OOS technical evaluation budget pin mismatch")
    policy = json.loads(BUDGET_PATH.read_text(encoding="utf-8"))
    if (policy.get("status") != "prospective_technical_2023_only"
            or policy.get("global_daily_seconds") != DAILY_LIMIT
            or policy.get("daily_closure_reserve_seconds") != CLOSURE_RESERVE
            or policy.get("first_unit_admission_seconds") != UNIT_INITIAL_RESERVE
            or policy.get("unit_supervisor_seconds_max") != UNIT_LIMIT):
        raise PermissionError("OOS technical evaluation budget changed")


def invocation_id() -> str:
    value = os.environ.get("INVOCATION_ID", "")
    if len(value) != 32 or any(char not in "0123456789abcdef" for char in value.lower()):
        raise PermissionError("OOS historical evaluation requires systemd --user invocation")
    return value


def host_blockers(host: dict) -> list[str]:
    blockers = []
    if host["power"].get("ac") is not True:
        blockers.append("AC disconnected")
    if host["power"].get("battery_percent", -1) < 50:
        blockers.append("Battery below 50 percent")
    if host["memory_available_bytes"] is None or host["memory_available_bytes"] < MIN_AVAILABLE:
        blockers.append("MemAvailable below 4 GiB")
    if host["disk_free_bytes"] < MIN_DISK:
        blockers.append("Disk below 20 GiB")
    if host["linger"] != "yes" or host["user_manager"] != "running":
        blockers.append("User systemd or linger unavailable")
    return blockers


@contextmanager
def exclusive_campaign():
    GLOBAL_LOCK.parent.mkdir(parents=True, exist_ok=True)
    with GLOBAL_LOCK.open("a") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def budget_snapshot(*, active_token: str | None = None) -> dict:
    return inspect_budget(now=time.time(), campaign=CAMPAIGN,
                          active_eval_token=active_token,
                          daily_limit_seconds=DAILY_LIMIT,
                          closure_reserve_seconds=CLOSURE_RESERVE)


def source_preflight(*, active_token: str | None = None) -> dict:
    """No 2023 rows are opened here, even when the source gate is enabled."""
    approval = read_pinned_approval("technical_2023_source", ROOT)
    pinned_budget(approval)
    roster = verify_complete_main_roster(ROOT)
    scaler, scaler_sha = load_verified_scaler(
        SHARD / "manifest.json", SHARD / "scaler.json", manifest_sha256=SHARD_SHA,
    )
    del scaler
    require_source_export_access(
        ROOT, training_ledger_sha256=roster["ledger_sha256"],
        h1_manifest_sha256=H1_SHA, raw_manifest_sha256=RAW_SHA,
        scaler_sha256=scaler_sha,
    )
    if (H1.is_symlink() or (H1 / "manifest.json").is_symlink()
            or sha(H1 / "manifest.json") != H1_SHA):
        raise ValueError("Accepted H1 source manifest changed before export")
    host, budget = inspect_host(), budget_snapshot(active_token=active_token)
    blockers = host_blockers(host)
    if not budget["ok"] or budget["remaining_before_reserve"] < UNIT_INITIAL_RESERVE:
        blockers.append("Shared budget or concurrent campaign")
    if (len(budget["oos_active_days"]) > 20
            or (len(budget["oos_active_days"]) == 20
                and budget["day_la_paz"] not in budget["oos_active_days"])):
        blockers.append("OOS active-day limit exhausted")
    if EXPORT.exists() or EXPORT.is_symlink():
        blockers.append("Technical source export root already exists")
    return {"status": "ready" if not blockers else "blocked", "blockers": blockers,
            "host": host, "budget": budget, "training_ledger_sha256": roster["ledger_sha256"],
            "source_approval_sha256": sha(ROOT / "docs/protocols/OOS-v1-2-technical-2023-source-approval-v2.json"),
            "code_sha256": approval["code_sha256"],
            "opened_protected_rows": False}


def export_technical_source() -> dict:
    """Export exact H1 2023 rows once, after the independent source permit."""
    read_pinned_approval("technical_2023_source", ROOT)
    invocation = invocation_id()
    with exclusive_campaign():
        with WFCostSessionJournal(SESSION_JOURNAL, campaign=SESSION_NAME) as journal:
            token = journal.start(now=time.time(), monotonic=time.monotonic(),
                                  invocation_id=invocation)
            try:
                preflight = source_preflight(active_token=token)
                if preflight["status"] != "ready":
                    journal.end(token, now=time.time(), monotonic=time.monotonic(),
                                status="ready", reason="blocked_before_source_export")
                    return preflight
                bars, source = load_h1_technical_bars(
                    H1, expected_h1_manifest_sha256=H1_SHA,
                    expected_raw_manifest_sha256=RAW_SHA,
                )
                manifest = write_evaluation_export(
                    bars, EXPORT, partition="technical_2023",
                    source_manifest_sha256=source["source_manifest_sha256"],
                    training_scaler_sha256=SCALER_SHA,
                )
                result = {"status": "exported", "rows": manifest["rows"],
                          "source_manifest_sha256": source["source_manifest_sha256"],
                          "export_manifest_sha256": sha(EXPORT / "manifest.json"),
                          "bars_sha256": sha(EXPORT / "bars.csv"),
                          "opened_files": [str(H1 / name) for name in
                                           ("manifest.json", "coverage.json", "bars.csv")],
                          "training_ledger_sha256": preflight["training_ledger_sha256"]}
            except BaseException as exc:
                journal.end(token, now=time.time(), monotonic=time.monotonic(),
                            status="failed", reason=f"source_export:{type(exc).__name__}:{exc}")
                raise
            journal.end(token, now=time.time(), monotonic=time.monotonic(), status="ready")
    return result


def _expected_roster(verified: dict) -> list[dict]:
    return [dict(run_id=row["run_id"], seed=row["seed"],
                 condition=row["condition"],
                 checkpoint_sha256=row["checkpoint_sha256"])
            for row in verified["runs"]]


def _technical_inputs(verified: dict) -> tuple[dict, dict]:
    approval = require_evaluation_access(
        "technical_2023", ROOT,
        training_ledger_sha256=verified["ledger_sha256"],
        export_manifest_sha256=sha(EXPORT / "manifest.json"),
        source_manifest_sha256=H1_SHA, scaler_sha256=SCALER_SHA,
    )
    pinned_budget(approval)
    if approval.get("export_root") != str(EXPORT.relative_to(ROOT)):
        raise PermissionError("Technical export root identity mismatch")
    scaler, scaler_sha = load_verified_scaler(
        SHARD / "manifest.json", SHARD / "scaler.json", manifest_sha256=SHARD_SHA,
    )
    if scaler_sha != SCALER_SHA:
        raise PermissionError("Frozen scaler identity mismatch")
    return approval, {"scaler": scaler, "config": load_config(ROOT / "configs/initial.toml")}


def _unit_inputs(run: dict, *, scaler, config) -> tuple[Path, dict]:
    run_dir = TRAINING_ROOT / run["run_id"]
    checkpoint = run_dir / "checkpoint-10"
    manifest = json.loads((checkpoint / "manifest.json").read_text(encoding="utf-8"))
    expected_settings = asdict(OOSSettings(seed=run["seed"]))
    source_identity = manifest.get("provenance", {}).get("data", {})
    identity_sha = hashlib.sha256(json.dumps(
        source_identity, sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()
    if (manifest.get("settings") != expected_settings
            or identity_sha != TRAINING_IDENTITY_SHA
            or source_identity.get("manifest_sha256") != H1_SHA
            or source_identity.get("scaler_sha256") != SCALER_SHA):
        raise ValueError("Frozen checkpoint settings or training source changed")
    return checkpoint, {
        "partition": "technical_2023", "export_manifest_sha256": sha(EXPORT / "manifest.json"),
        "source_manifest_sha256": H1_SHA, "scaler": scaler,
        "scaler_sha256": SCALER_SHA, "run_id": run["run_id"],
        "seed": run["seed"], "condition": run["condition"],
        "checkpoint_state_sha256": run["checkpoint_sha256"],
        "settings": expected_settings,
        "source_identity": source_identity,
        "actor_updates": 80, "critic_updates": 160,
    }


def _read_ledger_identity() -> dict:
    with (CAMPAIGN / "ledger.jsonl").open(encoding="utf-8") as stream:
        first = json.loads(next(stream))
    return first["identity"]


def worker(run_id: str, *, session_token: str, parent_pid: int) -> None:
    """Worker rechecks the permit and complete ledger identity before 2023 read."""
    read_pinned_approval("technical_2023", ROOT)
    invocation = invocation_id()
    if (type(parent_pid) is not int or parent_pid <= 1 or os.getppid() != parent_pid
            or type(session_token) is not str or len(session_token) != 32):
        raise PermissionError("Technical worker parent lease invalid")
    with WFCostSessionJournal(SESSION_JOURNAL, campaign=SESSION_NAME,
                              read_only=True) as sessions:
        if (not sessions.sessions or sessions.sessions[-1]["end"] is not None
                or sessions.sessions[-1]["start"]["token"] != session_token
                or sessions.sessions[-1]["start"]["invocation_id"] != invocation):
            raise PermissionError("Technical worker session lease invalid")
    identity = _read_ledger_identity()
    if identity["approval_sha256"] != sha(
        ROOT / "docs/protocols/OOS-v1-2-technical-2023-approval.json"
    ):
        raise PermissionError("Technical worker approval identity mismatch")
    ledger = EvaluationLedger.open(CAMPAIGN, identity)
    state = ledger.state
    if state["status"] != "ready" or identity["roster"][state["cursor"]]["run_id"] != run_id:
        raise ValueError("Technical worker roster boundary mismatch")
    run = identity["roster"][state["cursor"]]
    require_evaluation_access(
        "technical_2023", ROOT,
        training_ledger_sha256=identity["training_ledger_sha256"],
        export_manifest_sha256=identity["export_manifest_sha256"],
        source_manifest_sha256=H1_SHA, scaler_sha256=SCALER_SHA,
    )
    scaler, _ = load_verified_scaler(
        SHARD / "manifest.json", SHARD / "scaler.json", manifest_sha256=SHARD_SHA,
    )
    config = load_config(ROOT / "configs/initial.toml")
    checkpoint, kwargs = _unit_inputs(run, scaler=scaler, config=config)
    report = run_one_verified_unit(ledger, EXPORT, checkpoint, config=config,
                                   evaluation_kwargs=kwargs)
    print(json.dumps({"run_id": run_id, "status": report["status"]}), flush=True)


def technical_preflight() -> tuple[dict, dict, dict]:
    """Verify fixed training roster and the separately approved export."""
    read_pinned_approval("technical_2023", ROOT)
    verified = verify_complete_main_roster(ROOT)
    approval, inputs = _technical_inputs(verified)
    load_evaluation_export(
        EXPORT, partition="technical_2023",
        expected_manifest_sha256=sha(EXPORT / "manifest.json"),
        scaler=inputs["scaler"], expected_scaler_sha256=SCALER_SHA,
    )
    return verified, approval, inputs


def run_technical() -> dict:
    """Continue one accepted policy at a time; pause only at complete boundaries."""
    read_pinned_approval("technical_2023", ROOT)
    invocation = invocation_id()
    with exclusive_campaign(), WFCostSessionJournal(
        SESSION_JOURNAL, campaign=SESSION_NAME
    ) as journal:
        token = journal.start(now=time.time(), monotonic=time.monotonic(),
                              invocation_id=invocation)
        began = time.monotonic()
        try:
            return _run_technical_session(journal, token, began)
        except BaseException as exc:
            journal.end(token, now=time.time(), monotonic=time.monotonic(),
                        status="failed", reason=f"{type(exc).__name__}:{exc}")
            raise


def _run_technical_session(journal: WFCostSessionJournal, token: str, began: float) -> dict:
    verified, _approval, inputs = technical_preflight()
    host, budget = inspect_host(), budget_snapshot(active_token=token)
    budget_measured_at = time.monotonic()
    blockers = host_blockers(host)
    if not budget["ok"] or budget["remaining_before_reserve"] < UNIT_INITIAL_RESERVE:
        blockers.append("Shared budget or concurrent campaign")
    if (len(budget["oos_active_days"]) > 20
            or (len(budget["oos_active_days"]) == 20
                and budget["day_la_paz"] not in budget["oos_active_days"])):
        blockers.append("OOS active-day limit exhausted")
    if blockers:
        journal.end(token, now=time.time(), monotonic=time.monotonic(),
                    status="ready", reason="blocked_before_unit")
        return {"status": "blocked", "blockers": blockers, "host": host,
                "budget": budget}
    roster = _expected_roster(verified)
    identity = {"partition": "technical_2023", "roster": roster,
                "approval_sha256": sha(ROOT / "docs/protocols/OOS-v1-2-technical-2023-approval.json"),
                "training_ledger_sha256": verified["ledger_sha256"],
                "export_manifest_sha256": sha(EXPORT / "manifest.json"),
                "code_sha256": execution_code_sha256(ROOT)}
    if CAMPAIGN.exists():
        ledger = EvaluationLedger.open(CAMPAIGN, identity)
    else:
        ledger = EvaluationLedger.create(CAMPAIGN, identity)
    if ledger.state["status"] == "running":
        ledger.mark_interrupted("orphaned_unit_at_session_start")
        raise ValueError("Technical campaign failed in a partial unit")
    if ledger.state["status"] == "failed":
        raise ValueError("Technical campaign failed; no selective restart")
    if ledger.state["status"] == "completed":
        journal.end(token, now=time.time(), monotonic=time.monotonic(),
                    status="ready", reason="already_complete")
        return {"status": "completed", "accepted": ledger.state["cursor"]}
    unit_seconds = [row["seconds"] for row in ledger.state["accepted"]]
    try:
        while ledger.state["status"] == "ready":
            state = ledger.state
            required = min(UNIT_LIMIT, max(UNIT_INITIAL_RESERVE,
                                           1.5 * max(unit_seconds, default=0.0)))
            available = (budget["remaining_before_reserve"]
                         - (time.monotonic() - budget_measured_at))
            current_host = inspect_host()
            if host_blockers(current_host) or available < required:
                break
            run = roster[state["cursor"]]
            log = CAMPAIGN / f"worker-{state['cursor']:03d}.log"
            result = supervise(
                [sys.executable, "-m", "btc_risk_rl.evaluation.historical_supervisor",
                         "--worker", run["run_id"], "--session-token", token,
                         "--parent-pid", str(os.getpid())],
                output=log, seconds=required, rss_limit=2 * 1024**3,
                poll=0.5,
                on_poll=lambda _pid, _elapsed, _rss: _require_live_resources(),
            )
            if result["status"] != "passed":
                if ledger.state["status"] == "running":
                    ledger.mark_interrupted(f"supervisor:{result['reason']}")
                elif ledger.state["status"] == "ready":
                    ledger.fail_before_unit(f"supervisor:{result['reason']}")
                raise ValueError(f"Technical unit failed: {run['run_id']} {result['reason']}")
            after = ledger.state
            if after["cursor"] != state["cursor"] + 1 or after["pending"] is not None:
                raise ValueError("Worker did not accept exactly one complete policy")
            unit_seconds.append(result["wall_seconds"])
        status = ledger.state["status"]
        if status == "completed":
            closure = write_technical_closure(
                ledger, CAMPAIGN / "technical-closure.json",
                expected_roster=roster, config=inputs["config"],
                code_sha256=execution_code_sha256(ROOT),
            )
            status = closure["status"]
    except BaseException as exc:
        if ledger.state["status"] == "running":
            ledger.mark_interrupted(f"session:{type(exc).__name__}:{exc}")
        elif ledger.state["status"] == "ready":
            ledger.fail_before_unit(f"session:{type(exc).__name__}:{exc}")
        raise
    journal.end(token, now=time.time(), monotonic=time.monotonic(), status="ready")
    return {"status": status, "accepted": ledger.state["cursor"],
            "remaining_at_session_start_seconds": budget["remaining_before_reserve"],
            "session_elapsed_seconds": time.monotonic() - began,
            "technical_closure_sha256": (sha(CAMPAIGN / "technical-closure.json")
                                         if status == "passed" else None)}


def _require_live_resources() -> None:
    host = inspect_host()
    blockers = host_blockers(host)
    if blockers:
        raise ValueError("Resources lost during technical unit: " + ", ".join(blockers))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", nargs="?", choices=("source-preflight", "export-2023",
                                                    "technical-preflight", "run-2023"))
    parser.add_argument("--worker", metavar="RUN_ID")
    parser.add_argument("--session-token", help=argparse.SUPPRESS)
    parser.add_argument("--parent-pid", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker, session_token=args.session_token, parent_pid=args.parent_pid)
        return
    if args.mode is None:
        parser.error("mode required")
    if args.mode == "source-preflight":
        result = source_preflight()
    elif args.mode == "export-2023":
        result = export_technical_source()
    elif args.mode == "technical-preflight":
        verified, _approval, _ = technical_preflight()
        host, budget = inspect_host(), budget_snapshot()
        blockers = host_blockers(host)
        if not budget["ok"] or budget["remaining_before_reserve"] < UNIT_INITIAL_RESERVE:
            blockers.append("Shared budget or concurrent campaign")
        if len(budget["oos_active_days"]) >= 20 and budget["day_la_paz"] not in budget["oos_active_days"]:
            blockers.append("OOS active-day limit exhausted")
        result = {"status": "blocked" if blockers else "ready", "blockers": blockers,
                  "runs": verified["complete_runs"],
                  "approval_sha256": sha(ROOT / "docs/protocols/OOS-v1-2-technical-2023-approval.json"),
                  "budget": budget, "host": host}
    else:
        result = run_technical()
    print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)
    if result["status"] not in {"ready", "exported", "passed", "completed"}:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
