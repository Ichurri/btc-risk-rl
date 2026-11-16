"""Read-only P2 closure from completed ledgers and existing artifacts; no environment or optimizer."""

import argparse
import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path

from btc_risk_rl.pilots.p2_budget import state_hash
from btc_risk_rl.pilots.p2_market import (
    ACCEPTED_MANIFEST_SHA,
    MARKET_CAMPAIGN,
    PROTOCOL_SHA,
    REGISTRY_SHA,
    P2MarketSettings,
    roster,
)
from btc_risk_rl.pilots.p2_metrics import campaign_gate


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def chain(path):
    previous = None
    entries = 0
    for line in path.read_text().splitlines():
        state = json.loads(line)
        if state.get("previous_hash") != previous or state.get("state_hash") != state_hash(state):
            raise ValueError("P2 ledger chain mismatch")
        previous = state["state_hash"]
        entries += 1
    if entries == 0:
        raise ValueError("Empty P2 ledger")
    return state, entries


def verified_unit(root, unit, settings, condition):
    index = unit["unit"]
    payload_path = root / f"unit-{index}.json"
    payload = json.loads(payload_path.read_text())
    report = payload["report"]
    expected = asdict(settings)
    if (payload["unit"] != index or report["settings"] != expected
            or report["condition"] != condition or report["purpose"] != "authorized_p2_only"
            or report["final_test_accessed"]):
        raise ValueError("P2 completed unit profile mismatch")
    n_a, n_q, n_b = settings.n_a, settings.n_q, settings.n_b
    updates = math.ceil(n_a / settings.minibatch)
    resources = dict(
        trajectories=n_q if index == 0 else n_a + n_q + n_b,
        transitions=180 * (n_q if index == 0 else n_a + n_q + n_b),
        diagnostic_trajectories=0 if index == 0 else 64,
        diagnostic_transitions=0 if index == 0 else 64 * 180,
        actor_updates=0 if index == 0 else settings.actor_epochs * updates,
        critic_updates=0 if index == 0 else settings.critic_epochs * updates,
    )
    if payload["resources"] != resources or unit["resources"] != resources:
        raise ValueError("P2 completed unit resource mismatch")
    manifest_path = root / f"checkpoint-{index}/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    state_path = manifest_path.parent / "state.pt"
    boundary = "after_q0" if index == 0 else "after_dual_and_D"
    source = manifest["provenance"]["data"]
    if (manifest["schema_version"] != "p2_complete_boundary_v1"
            or manifest["boundary"] != boundary
            or manifest["profile"] != "authorized_p2_only"
            or manifest["settings"] != expected
            or manifest["state_sha256"] != sha(state_path)
            or source["manifest_sha256"] != ACCEPTED_MANIFEST_SHA
            or source["scaler_sha256"] != source["files"]["scaler.json"]
            or unit["checkpoint_sha256"] != manifest["state_sha256"]):
        raise ValueError("P2 checkpoint identity/hash mismatch")
    records = report["diagnostic"]["records"]
    if len(records) != index or report["diagnostic"]["trajectories"] != 64 * index:
        raise ValueError("P2 D count mismatch")
    archive_count = 0
    for record in records:
        if len(record["archives"]) != 64:
            raise ValueError("P2 D archive count mismatch")
        for archive in record["archives"]:
            path = Path(archive["path"])
            if not path.is_relative_to(MARKET_CAMPAIGN) or sha(path) != archive["sha256"]:
                raise ValueError("P2 D archive hash mismatch")
            archive_count += 1
    return dict(
        unit=index,
        resources=resources,
        work_seconds=unit["work_seconds"],
        wall_seconds=unit["seconds"],
        rss_peak_bytes=unit["supervisor"]["rss_peak_bytes"],
        algorithm_seconds=payload["algorithm_seconds"],
        save_seconds=payload["save_seconds"],
        checkpoint_sha256=manifest["state_sha256"],
        payload_sha256=sha(payload_path),
        manifest_sha256=sha(manifest_path),
        d_archives_checked=archive_count,
        legacy_market_training_executed_flag=report["market_training_executed"],
    ), report, payload


def brief_metric(metric):
    """Keep reproducible scalar summaries in Git; full reports remain local."""
    keys = ("count", "mse", "z", "relative_mse", "bias", "normalized_bias")
    return {key: metric[key] for key in keys}


def brief_record(record):
    return dict(
        iteration=record["iteration"],
        policy_version=record["policy_version"],
        A={stage: brief_metric(record["A"][stage]) for stage in ("pre", "post")},
        D={stage: brief_metric(record["D"][stage]) for stage in ("pre", "post")},
        gap=record["gap"],
        risk=record["risk"],
        overlap=record["overlap"],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ledger = MARKET_CAMPAIGN / "ledger.jsonl"
    state, ledger_entries = chain(ledger)
    if state["status"] == "running":
        raise ValueError("P2 still running; closure must wait for a complete boundary")
    rows, checked_units, checked_archives = [], 0, 0
    for position, (seed, condition) in enumerate(roster()):
        run_id = f"run-{position:02d}-{condition}"
        run = state["runs"].get(run_id, {})
        count = run.get("next_unit", 0)
        units = [u for u in state["units"] if u["run_id"] == run_id]
        if [u["unit"] for u in units] != list(range(count)):
            raise ValueError("P2 completed unit sequence mismatch")
        settings = P2MarketSettings(seed=seed)
        verified, report, payload = [], None, None
        for unit in units:
            item, report, payload = verified_unit(MARKET_CAMPAIGN / run_id, unit,
                                                  settings, condition)
            verified.append(item)
            checked_units += 1
            checked_archives += item["d_archives_checked"] - (
                verified[-2]["d_archives_checked"] if len(verified) > 1 else 0
            )
        status = "completed" if count == 11 else "paused" if count else "not_started"
        if state["status"] in {"failed", "incomplete"} and position == state["cursor"]:
            status = state["status"]
        row = dict(run_id=run_id, seed=seed, condition=condition, status=status,
                   complete_iterations=max(0, count - 1),
                   resources=run.get("resources", {}), days=run.get("days", []),
                   sessions=len(run.get("sessions", [])), units=verified)
        if report is not None:
            records = report["diagnostic"]["records"]
            row.update(
                actor_sha256=report["actor_sha256"],
                critic_sha256=report["critic_sha256"],
                audits=[{k: a[k] for k in ("iteration", "eta", "lambda_before",
                                               "lambda_after", "f_b")}
                        for a in report["audits"]],
                diagnostic=[brief_record(r) for r in records],
                d_phase_seconds=[t["wall_seconds"] for t in report["telemetry"]
                                 if t["phase"] == "D"],
                warnings_count=len(payload["warnings"]),
                warning_rates=payload["learning_rates"],
                diagnostic_warning_rates=report["diagnostic"]["warnings"],
            )
        rows.append(row)
    resource_sum = {}
    for row in rows:
        for key, value in row["resources"].items():
            resource_sum[key] = resource_sum.get(key, 0) + value
    if resource_sum != state["resources"]:
        raise ValueError("P2 campaign resource sum mismatch")
    gates = ([dict(seed=r["seed"], condition=r["condition"], status="passed",
                   records=r["diagnostic"]) for r in rows]
             if state["status"] == "completed" else [])
    assessment = campaign_gate(gates) if gates else dict(
        decision="not_evaluated_until_nine_complete_runs")
    result = dict(
        status=state["status"], cursor=state["cursor"],
        pending=state.get("pending"), updated_utc=state["updated_utc"],
        protocol_sha256=PROTOCOL_SHA, registry_sha256=REGISTRY_SHA,
        identity=state["identity"], resources=state["resources"],
        days=state["days"], measurements=state["measurements"],
        failure=state.get("failure"), runs=rows, assessment=assessment,
        ledger_sha256=sha(ledger), ledger_entries_checked=ledger_entries,
        completed_units_checked=checked_units, d_archives_checked=checked_archives,
        validation_accessed=False, final_accessed=False,
        reporting_warning=("Frozen trainer metadata only marks P0/P1 as market training; "
                           "P2 reports market_training_executed=false despite verified "
                           "P2 profile, optimizer counters and accepted source"),
        interpretation="Development diagnostic on 2018–2022 training only; no temporal generalization, financial superiority or population CVaR claim",
    )
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "results.json").open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(status=result["status"], cursor=result["cursor"],
                          resources=result["resources"], output=str(args.output))))


if __name__ == "__main__":
    main()
