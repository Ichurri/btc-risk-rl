"""Gated final source acquisition and continuous evaluation of fixed K10 policies.

The source and policy-evaluation permits are separate. No final rows are read
while either permit is closed. A failed source or unit is never retried in its
root; all charges share the training campaign lock and session journal.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from btc_risk_rl.config import load_config
from btc_risk_rl.evaluation.access import (
    read_pinned_approval,
    require_evaluation_access,
    require_final_source_access,
)
from btc_risk_rl.evaluation.code_identity import execution_code_sha256
from btc_risk_rl.evaluation.complete_roster import verify_complete_main_roster
from btc_risk_rl.evaluation.export_builder import write_evaluation_export
from btc_risk_rl.evaluation.export_reader import COLUMNS, load_evaluation_export
from btc_risk_rl.evaluation.final_fetch import fetch_final_pages
from btc_risk_rl.evaluation.historical_supervisor import (
    H1_SHA,
    SCALER_SHA,
    SHARD,
    SHARD_SHA,
    TRAINING_IDENTITY_SHA,
    TRAINING_ROOT,
    exclusive_campaign,
    host_blockers,
    invocation_id,
    sha,
)
from btc_risk_rl.evaluation.inference import compare_audited_records
from btc_risk_rl.evaluation.ledger import EvaluationLedger
from btc_risk_rl.evaluation.runner import run_one_verified_unit, verify_accepted_outputs
from btc_risk_rl.evaluation.source_final import load_final_binance_bars
from btc_risk_rl.evaluation.synthetic import load_verified_scaler
from btc_risk_rl.pilots.oos_v12_training import OOSSettings
from btc_risk_rl.pilots.supervisor import supervise
from btc_risk_rl.pilots.wf_cost import inspect_budget, inspect_host
from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal

ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "artifacts"
RAW = ROOT / "data/raw/oos-v12-final-2024-2025-01"
EXPORT = ROOT / "data/processed/oos-v12-final-2024-2025-01"
TECH_EXPORT = ROOT / "data/processed/oos-v12-technical-2023-01"
TECH_CAMPAIGN = ARTIFACTS / "oos-v12-technical-2023-01"
TECH_CLOSURE = TECH_CAMPAIGN / "technical-closure.json"
CAMPAIGN = ARTIFACTS / "oos-v12-final-2024-2025-01"
SESSION_JOURNAL = ARTIFACTS / "shared-pilot-budget/oos-v12-evaluation-sessions.jsonl"
SESSION_NAME = "oos-v12-evaluation-v1"
BUDGET_PATH = ROOT / "docs/protocols/OOS-v1-2-final-evaluation-budget-20261115.json"
BUDGET_SHA = "bb89506b74760785922da01e6229eec702b80df829051a68d859f172ebfd6517"
DAILY_LIMIT = 50400.0
CLOSURE_RESERVE = 2700.0
UNIT_INITIAL_RESERVE = 300.0
UNIT_LIMIT = 900.0


def pinned_budget(approval: dict) -> None:
    if (BUDGET_PATH.is_symlink() or sha(BUDGET_PATH) != BUDGET_SHA
            or approval.get("budget_sha256") != BUDGET_SHA):
        raise PermissionError("OOS final budget pin mismatch")
    policy = json.loads(BUDGET_PATH.read_text(encoding="utf-8"))
    if (policy.get("status") != "prospective_final_2024_2025_only"
            or policy.get("global_daily_seconds") != DAILY_LIMIT
            or policy.get("daily_closure_reserve_seconds") != CLOSURE_RESERVE
            or policy.get("first_unit_admission_seconds") != UNIT_INITIAL_RESERVE
            or policy.get("unit_supervisor_seconds_max") != UNIT_LIMIT):
        raise PermissionError("OOS final budget changed")


def budget_snapshot(*, active_token: str | None = None) -> dict:
    return inspect_budget(now=time.time(), campaign=CAMPAIGN,
                          active_eval_token=active_token,
                          daily_limit_seconds=DAILY_LIMIT,
                          closure_reserve_seconds=CLOSURE_RESERVE)


def host_budget(*, active_token: str | None = None) -> dict:
    host, budget = inspect_host(), budget_snapshot(active_token=active_token)
    blockers = host_blockers(host)
    if not budget["ok"] or budget["remaining_before_reserve"] < UNIT_INITIAL_RESERVE:
        blockers.append("Shared budget or concurrent campaign")
    if (len(budget["oos_active_days"]) > 20
            or (len(budget["oos_active_days"]) == 20
                and budget["day_la_paz"] not in budget["oos_active_days"])):
        blockers.append("OOS active-day limit exhausted")
    return {"status": "ready" if not blockers else "blocked",
            "blockers": blockers, "host": host, "budget": budget}


def _audit_technical_prerequisites(approval: dict) -> None:
    if (TECH_CLOSURE.is_symlink()
            or sha(TECH_CLOSURE) != approval.get("technical_closure_sha256")):
        raise ValueError("Technical closure changed")
    closure = json.loads(TECH_CLOSURE.read_text(encoding="utf-8"))
    if (closure.get("status") != "passed"
            or closure.get("partition") != "technical_2023"
            or closure.get("complete_policies") != 108
            or (TECH_CAMPAIGN / "ledger.jsonl").is_symlink()
            or sha(TECH_CAMPAIGN / "ledger.jsonl")
            != closure.get("evaluation_ledger_sha256")):
        raise ValueError("Technical ledger or closure changed")
    manifest_path = TECH_EXPORT / "manifest.json"
    bars_path = TECH_EXPORT / "bars.csv"
    if (TECH_EXPORT.is_symlink() or manifest_path.is_symlink()
            or bars_path.is_symlink()
            or sha(manifest_path) != approval.get("technical_export_sha256")
            or sha(manifest_path) != closure.get("export_manifest_sha256")):
        raise ValueError("Technical export manifest changed")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha(bars_path) != manifest.get("bars_sha256"):
        raise ValueError("Technical export bars changed")


def _verified_final_prerequisites(scope: str) -> dict:
    partition = ("final_2024_2025_source" if scope == "source"
                 else "final_2024_2025")
    approval = read_pinned_approval(partition, ROOT)
    pinned_budget(approval)
    verified = verify_complete_main_roster(ROOT)
    _audit_technical_prerequisites(approval)
    scaler, scaler_sha = load_verified_scaler(
        SHARD / "manifest.json", SHARD / "scaler.json", manifest_sha256=SHARD_SHA,
    )
    if scaler_sha != SCALER_SHA:
        raise PermissionError("OOS frozen scaler hash mismatch")
    if scope == "source":
        require_final_source_access(
            ROOT, training_ledger_sha256=verified["ledger_sha256"],
            technical_closure_path=TECH_CLOSURE,
            technical_export_sha256=sha(TECH_EXPORT / "manifest.json"),
            h1_manifest_sha256=H1_SHA, scaler_sha256=scaler_sha,
        )
    else:
        require_evaluation_access(
            partition, ROOT, training_ledger_sha256=verified["ledger_sha256"],
            export_manifest_sha256=sha(EXPORT / "manifest.json"),
            source_manifest_sha256=sha(RAW / "manifest.json"),
            scaler_sha256=scaler_sha, technical_closure_path=TECH_CLOSURE,
        )
    return {"approval": approval, "verified": verified, "scaler": scaler}


def final_source_preflight(*, active_token: str | None = None) -> dict:
    """Inspect source permit and host; never open 2024–2025 rows."""
    prerequisites = _verified_final_prerequisites("source")
    status = host_budget(active_token=active_token)
    if status["budget"]["remaining_before_reserve"] < UNIT_LIMIT:
        status["blockers"].append("Final source budget below full 900 s acquisition reserve")
    if RAW.exists() or RAW.is_symlink():
        status["blockers"].append("Final raw root already exists")
    if EXPORT.exists() or EXPORT.is_symlink():
        status["blockers"].append("Final export root already exists")
    status["status"] = "ready" if not status["blockers"] else "blocked"
    status.update({
        "training_ledger_sha256": prerequisites["verified"]["ledger_sha256"],
        "technical_closure_sha256": sha(TECH_CLOSURE),
        "final_source_approval_sha256": sha(
            ROOT / "docs/protocols/OOS-v1-2-final-source-approval.json"),
        "opened_final_rows": False,
    })
    return status


def acquire_final_source() -> dict:
    """One supervised, immutable fetch and audit; no policy is evaluated."""
    read_pinned_approval("final_2024_2025_source", ROOT)
    invocation = invocation_id()
    with exclusive_campaign(), WFCostSessionJournal(
        SESSION_JOURNAL, campaign=SESSION_NAME,
    ) as journal:
        token = journal.start(now=time.time(), monotonic=time.monotonic(),
                              invocation_id=invocation)
        try:
            preflight = final_source_preflight(active_token=token)
            if preflight["status"] != "ready":
                journal.end(token, now=time.time(), monotonic=time.monotonic(),
                            status="ready", reason="blocked_before_final_fetch")
                return preflight
            technical_manifest = json.loads((TECH_EXPORT / "manifest.json").read_text())
            if sha(TECH_EXPORT / "bars.csv") != technical_manifest["bars_sha256"]:
                raise ValueError("2023 context bars hash mismatch")
            context = pd.read_csv(TECH_EXPORT / "bars.csv", float_precision="round_trip")
            if tuple(context.columns) != COLUMNS:
                raise ValueError("2023 context schema changed")
            context = context.iloc[-43:].reset_index(drop=True)
            fetch_final_pages(RAW, endpoint="https://api.binance.com/api/v3/klines")
            source_sha = sha(RAW / "manifest.json")
            bars, audit = load_final_binance_bars(
                RAW, expected_manifest_sha256=source_sha,
                expected_h1_context=context,
            )
            manifest = write_evaluation_export(
                bars, EXPORT, partition="final_2024_2025",
                source_manifest_sha256=source_sha,
                training_scaler_sha256=SCALER_SHA,
            )
            result = {"status": "exported", "rows": manifest["rows"],
                      "page_count": audit["page_count"],
                      "raw_manifest_sha256": source_sha,
                      "export_manifest_sha256": sha(EXPORT / "manifest.json"),
                      "bars_sha256": sha(EXPORT / "bars.csv"),
                      "technical_closure_sha256": preflight["technical_closure_sha256"]}
        except BaseException as exc:
            journal.end(token, now=time.time(), monotonic=time.monotonic(),
                        status="failed", reason=f"final_source:{type(exc).__name__}:{exc}")
            raise
        journal.end(token, now=time.time(), monotonic=time.monotonic(), status="ready")
    return result


def _read_ledger_identity() -> dict:
    with (CAMPAIGN / "ledger.jsonl").open(encoding="utf-8") as stream:
        return json.loads(next(stream))["identity"]


def _unit_inputs(run: dict, *, scaler) -> tuple[Path, dict]:
    checkpoint = TRAINING_ROOT / run["run_id"] / "checkpoint-10"
    manifest = json.loads((checkpoint / "manifest.json").read_text(encoding="utf-8"))
    settings = asdict(OOSSettings(seed=run["seed"]))
    identity = manifest.get("provenance", {}).get("data", {})
    identity_sha = hashlib.sha256(json.dumps(
        identity, sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()
    if (manifest.get("settings") != settings
            or identity_sha != TRAINING_IDENTITY_SHA
            or identity.get("manifest_sha256") != H1_SHA
            or identity.get("scaler_sha256") != SCALER_SHA):
        raise ValueError("Final checkpoint settings or training source changed")
    return checkpoint, {
        "partition": "final_2024_2025",
        "export_manifest_sha256": sha(EXPORT / "manifest.json"),
        "source_manifest_sha256": sha(RAW / "manifest.json"),
        "scaler": scaler, "scaler_sha256": SCALER_SHA,
        "run_id": run["run_id"], "seed": run["seed"],
        "condition": run["condition"],
        "checkpoint_state_sha256": run["checkpoint_sha256"],
        "settings": settings, "source_identity": identity,
        "actor_updates": 80, "critic_updates": 160,
    }


def worker(run_id: str, *, session_token: str, parent_pid: int) -> None:
    read_pinned_approval("final_2024_2025", ROOT)
    invocation = invocation_id()
    if (type(parent_pid) is not int or parent_pid <= 1 or os.getppid() != parent_pid
            or type(session_token) is not str or len(session_token) != 32):
        raise PermissionError("Final worker parent lease invalid")
    with WFCostSessionJournal(SESSION_JOURNAL, campaign=SESSION_NAME,
                              read_only=True) as sessions:
        if (not sessions.sessions or sessions.sessions[-1]["end"] is not None
                or sessions.sessions[-1]["start"]["token"] != session_token
                or sessions.sessions[-1]["start"]["invocation_id"] != invocation):
            raise PermissionError("Final worker session lease invalid")
    identity = _read_ledger_identity()
    if identity["approval_sha256"] != sha(
        ROOT / "docs/protocols/OOS-v1-2-final-2024-2025-approval.json"
    ):
        raise PermissionError("Final worker approval identity mismatch")
    ledger = EvaluationLedger.open(CAMPAIGN, identity)
    state = ledger.state
    if state["status"] != "ready" or identity["roster"][state["cursor"]]["run_id"] != run_id:
        raise ValueError("Final worker roster boundary mismatch")
    run = identity["roster"][state["cursor"]]
    require_evaluation_access(
        "final_2024_2025", ROOT,
        training_ledger_sha256=identity["training_ledger_sha256"],
        export_manifest_sha256=identity["export_manifest_sha256"],
        source_manifest_sha256=sha(RAW / "manifest.json"),
        scaler_sha256=SCALER_SHA, technical_closure_path=TECH_CLOSURE,
    )
    scaler, _ = load_verified_scaler(
        SHARD / "manifest.json", SHARD / "scaler.json", manifest_sha256=SHARD_SHA,
    )
    checkpoint, kwargs = _unit_inputs(run, scaler=scaler)
    report = run_one_verified_unit(
        ledger, EXPORT, checkpoint, config=load_config(ROOT / "configs/initial.toml"),
        evaluation_kwargs=kwargs,
    )
    print(json.dumps({"run_id": run_id, "status": report["status"]}), flush=True)


def final_preflight() -> dict:
    prerequisites = _verified_final_prerequisites("evaluation")
    approval, scaler = prerequisites["approval"], prerequisites["scaler"]
    if approval.get("export_root") != str(EXPORT.relative_to(ROOT)):
        raise PermissionError("Final export root identity mismatch")
    technical_manifest = json.loads((TECH_EXPORT / "manifest.json").read_text())
    if sha(TECH_EXPORT / "bars.csv") != technical_manifest["bars_sha256"]:
        raise ValueError("2023 context bars hash mismatch")
    context = pd.read_csv(TECH_EXPORT / "bars.csv", float_precision="round_trip")
    if tuple(context.columns) != COLUMNS:
        raise ValueError("2023 context schema changed")
    load_final_binance_bars(
        RAW, expected_manifest_sha256=sha(RAW / "manifest.json"),
        expected_h1_context=context.iloc[-43:].reset_index(drop=True),
    )
    load_evaluation_export(
        EXPORT, partition="final_2024_2025",
        expected_manifest_sha256=sha(EXPORT / "manifest.json"),
        scaler=scaler, expected_scaler_sha256=SCALER_SHA,
    )
    return prerequisites


def _close_final(ledger: EvaluationLedger, *, roster: list[dict]) -> dict:
    if (ledger.state["status"] != "completed" or ledger.state["cursor"] != 108
            or ledger.state["pending"] is not None):
        raise ValueError("Final roster incomplete")
    config = load_config(ROOT / "configs/initial.toml")
    if verify_accepted_outputs(ledger, config=config) != 108:
        raise ValueError("Final traces incomplete")
    records = []
    for run in roster:
        report = json.loads((CAMPAIGN / run["run_id"] / "report.json").read_text())
        records.append(report)
    seeds = [roster[index]["seed"] for index in range(0, 108, 3)]
    comparison = compare_audited_records(records, expected_seeds=seeds)
    destination = CAMPAIGN / "final-contrast.json"
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    result = {
        "schema": "oos_v12_final_contrast_v1", "status": "passed",
        "partition": "final_2024_2025", "complete_policies": 108,
        "blocks": 36, "training_ledger_sha256": ledger.identity["training_ledger_sha256"],
        "final_ledger_sha256": sha(ledger.path),
        "technical_closure_sha256": sha(TECH_CLOSURE),
        "source_manifest_sha256": sha(RAW / "manifest.json"),
        "export_manifest_sha256": sha(EXPORT / "manifest.json"),
        "approval_sha256": ledger.identity["approval_sha256"],
        "code_sha256": execution_code_sha256(ROOT),
        "comparisons": comparison,
        "run_records": [{"run_id": row["run_id"], "seed": row["seed"],
                         "condition": row["condition"],
                         "sortino_annualized": row["sortino_annualized"],
                         "report_sha256": sha(CAMPAIGN / row["run_id"] / "report.json")}
                        for row in records],
    }
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return result


def run_final() -> dict:
    read_pinned_approval("final_2024_2025", ROOT)
    invocation = invocation_id()
    with exclusive_campaign(), WFCostSessionJournal(
        SESSION_JOURNAL, campaign=SESSION_NAME,
    ) as journal:
        token = journal.start(now=time.time(), monotonic=time.monotonic(),
                              invocation_id=invocation)
        began = time.monotonic()
        try:
            return _run_final_session(journal, token, began)
        except BaseException as exc:
            journal.end(token, now=time.time(), monotonic=time.monotonic(),
                        status="failed", reason=f"{type(exc).__name__}:{exc}")
            raise


def _run_final_session(journal, token: str, began: float) -> dict:
    prerequisites = final_preflight()
    status = host_budget(active_token=token)
    if status["status"] != "ready":
        journal.end(token, now=time.time(), monotonic=time.monotonic(),
                    status="ready", reason="blocked_before_unit")
        return status
    verified = prerequisites["verified"]
    roster = [{"run_id": row["run_id"], "seed": row["seed"],
               "condition": row["condition"],
               "checkpoint_sha256": row["checkpoint_sha256"]}
              for row in verified["runs"]]
    identity = {
        "partition": "final_2024_2025", "roster": roster,
        "approval_sha256": sha(ROOT / "docs/protocols/OOS-v1-2-final-2024-2025-approval.json"),
        "training_ledger_sha256": verified["ledger_sha256"],
        "export_manifest_sha256": sha(EXPORT / "manifest.json"),
        "code_sha256": execution_code_sha256(ROOT),
    }
    ledger = (EvaluationLedger.open(CAMPAIGN, identity) if CAMPAIGN.exists()
              else EvaluationLedger.create(CAMPAIGN, identity))
    if ledger.state["status"] == "running":
        ledger.mark_interrupted("orphaned_final_unit_at_session_start")
        raise ValueError("Final campaign failed in partial unit")
    if ledger.state["status"] == "failed":
        raise ValueError("Final campaign failed; no selective restart")
    if ledger.state["status"] == "completed":
        journal.end(token, now=time.time(), monotonic=time.monotonic(),
                    status="ready", reason="already_complete")
        return {"status": "completed", "accepted": ledger.state["cursor"]}
    unit_seconds = [row["seconds"] for row in ledger.state["accepted"]]
    budget = status["budget"]
    budget_measured_at = time.monotonic()
    try:
        while ledger.state["status"] == "ready":
            state = ledger.state
            required = min(UNIT_LIMIT, max(UNIT_INITIAL_RESERVE,
                                           1.5 * max(unit_seconds, default=0.0)))
            available = budget["remaining_before_reserve"] - (time.monotonic() - budget_measured_at)
            if host_blockers(inspect_host()) or available < required:
                break
            run = roster[state["cursor"]]
            result = supervise(
                [sys.executable, "-m", "btc_risk_rl.evaluation.historical_final_supervisor",
                 "--worker", run["run_id"], "--session-token", token,
                 "--parent-pid", str(os.getpid())],
                output=CAMPAIGN / f"worker-{state['cursor']:03d}.log",
                seconds=required, rss_limit=2 * 1024**3, poll=0.5,
                on_poll=lambda _pid, _elapsed, _rss: _require_live_resources(),
            )
            if result["status"] != "passed":
                if ledger.state["status"] == "running":
                    ledger.mark_interrupted(f"supervisor:{result['reason']}")
                elif ledger.state["status"] == "ready":
                    ledger.fail_before_unit(f"supervisor:{result['reason']}")
                raise ValueError(f"Final unit failed: {run['run_id']} {result['reason']}")
            after = ledger.state
            if after["cursor"] != state["cursor"] + 1 or after["pending"] is not None:
                raise ValueError("Final worker did not accept exactly one policy")
            unit_seconds.append(result["wall_seconds"])
        outcome = ledger.state["status"]
        if outcome == "completed":
            _close_final(ledger, roster=roster)
            outcome = "passed"
    except BaseException as exc:
        if ledger.state["status"] == "running":
            ledger.mark_interrupted(f"session:{type(exc).__name__}:{exc}")
        elif ledger.state["status"] == "ready":
            ledger.fail_before_unit(f"session:{type(exc).__name__}:{exc}")
        raise
    journal.end(token, now=time.time(), monotonic=time.monotonic(), status="ready")
    return {"status": outcome, "accepted": ledger.state["cursor"],
            "session_elapsed_seconds": time.monotonic() - began,
            "final_contrast_sha256": (sha(CAMPAIGN / "final-contrast.json")
                                       if outcome == "passed" else None)}


def _require_live_resources() -> None:
    blockers = host_blockers(inspect_host())
    if blockers:
        raise ValueError("Resources lost during final unit: " + ", ".join(blockers))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", nargs="?", choices=("source-preflight", "fetch-final",
                                                "final-preflight", "run-final"))
    parser.add_argument("--worker", metavar="RUN_ID")
    parser.add_argument("--session-token", help=argparse.SUPPRESS)
    parser.add_argument("--parent-pid", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker, session_token=args.session_token, parent_pid=args.parent_pid)
        return
    if args.mode == "source-preflight":
        result = final_source_preflight()
    elif args.mode == "fetch-final":
        result = acquire_final_source()
    elif args.mode == "final-preflight":
        prerequisites = final_preflight()
        result = host_budget()
        result["runs"] = prerequisites["verified"]["complete_runs"]
        result["approval_sha256"] = sha(
            ROOT / "docs/protocols/OOS-v1-2-final-2024-2025-approval.json")
    elif args.mode == "run-final":
        result = run_final()
    else:
        parser.error("mode required")
    print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)
    if result["status"] not in {"ready", "exported", "passed", "completed"}:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
