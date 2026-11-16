"""Read-only closure audit of the approved P2R development campaign.

This script reads existing ledger, journal, checkpoints, and D archives. It
never invokes a collector, optimizer, market source, or validation dataset.
"""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from btc_risk_rl.pilots.p2_budget import state_hash
from btc_risk_rl.pilots.p2_metrics import campaign_gate
from btc_risk_rl.pilots.p2r_market import PRIOR_LEDGERS, ROOT, roster

CAMPAIGN = ROOT / "artifacts/p2r-approved-v2"


def digest(path):
    hash_ = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hash_.update(chunk)
    return hash_.hexdigest()


def read_chain(path, hash_key, previous_key):
    previous = None
    rows = []
    for line in Path(path).read_text().splitlines():
        row = json.loads(line)
        assert row[previous_key] == previous
        expected = state_hash(row) if hash_key == "state_hash" else hashlib.sha256(
            json.dumps({k: v for k, v in row.items() if k != hash_key},
                       sort_keys=True, allow_nan=False).encode()
        ).hexdigest()
        assert row[hash_key] == expected
        previous = expected
        rows.append(row)
    assert rows
    return rows


def compact_metric(metric):
    return {key: metric[key] for key in (
        "count", "mse", "z", "relative_mse", "bias", "normalized_bias",
        "prediction_stats", "target_stats",
    )} | {
        "thirds_relative_mse": [third["relative_mse"] for third in metric["thirds"]]
    }


def main():
    assert CAMPAIGN.name == "p2r-approved-v2"
    ledger_path = CAMPAIGN / "ledger.jsonl"
    journal_path = CAMPAIGN / "supervisor.jsonl"
    ledger_rows = read_chain(ledger_path, "state_hash", "previous_hash")
    journal_rows = read_chain(journal_path, "sha256", "previous")
    state = ledger_rows[-1]
    expected_roster = roster()
    assert state["status"] == "completed" and state["cursor"] == 9
    assert state["pending"] is None and len(state["units"]) == 99
    assert len(state["days"]) == 1
    assert journal_rows[-1]["event"] == "supervisor_exit"
    assert journal_rows[-1]["status"] == "completed"
    assert not list(CAMPAIGN.rglob("checkpoint-*.partial-*"))

    for name, expected in PRIOR_LEDGERS.items():
        assert digest(ROOT / "artifacts" / name / "ledger.jsonl") == expected

    heartbeat = defaultdict(list)
    event_counts = Counter()
    invocations = []
    for row in journal_rows:
        event_counts[row["event"]] += 1
        if row["event"] == "supervisor_started":
            invocations.append(row["invocation_id"])
        if row["event"] == "heartbeat":
            heartbeat[(row["invocation_id"], row["run_id"], row["unit"])].append(
                row["monotonic"]
            )
    gaps = [b - a for times in heartbeat.values() for a, b in zip(times, times[1:])]
    assert gaps and all(0 <= gap <= 5 for gap in gaps)
    assert event_counts["unit_completed"] == 99
    assert event_counts["unit_failed"] == 0
    assert event_counts["availability_lost"] == 2
    assert event_counts["paused"] == 2
    assert len(invocations) == 3 and len(set(invocations)) == 3

    expected_units = [
        (f"run-{i:02d}-{condition}", unit)
        for i, (_seed, condition) in enumerate(expected_roster)
        for unit in range(11)
    ]
    assert [(u["run_id"], u["unit"]) for u in state["units"]] == expected_units

    runs = []
    run_summaries = []
    source_hashes = set()
    git_commits = Counter()
    d_archives = 0
    d_seconds = 0.0
    d_peak_rss = 0
    overlap_totals = defaultdict(lambda: dict(numerator=0, denominator=0))
    d_warning_total = 0
    final_hashes = {}
    iteration_metrics = {}
    market_flags = Counter()
    final_access_flags = Counter()
    for i, (seed, condition) in enumerate(expected_roster):
        run_id = f"run-{i:02d}-{condition}"
        units = state["units"][11 * i:11 * (i + 1)]
        run_root = CAMPAIGN / run_id
        run = state["runs"][run_id]
        assert run["next_unit"] == 11
        assert run["checkpoint"] == str(run_root / "checkpoint-10")
        run_d_seconds = 0.0
        for unit, entry in enumerate(units):
            assert entry["kind"] == ("q0" if unit == 0 else "iteration")
            assert entry["checkpoint"] == str(run_root / f"checkpoint-{unit}")
            assert entry["work_ended"] <= state["days"]["2026-10-07"]["work_deadline"]
            assert entry["end"] <= state["days"]["2026-10-07"]["hard_deadline"]
            assert 0 < entry["work_seconds"] <= (1800 if unit == 0 else 2700)
            expected_resources = dict(
                trajectories=400 if unit == 0 else 864,
                transitions=180 * (400 if unit == 0 else 864),
                diagnostic_trajectories=0 if unit == 0 else 64,
                diagnostic_transitions=0 if unit == 0 else 11520,
                actor_updates=0 if unit == 0 else 8,
                critic_updates=0 if unit == 0 else 16,
            )
            assert entry["resources"] == expected_resources
            point = run_root / f"checkpoint-{unit}"
            manifest = json.loads((point / "manifest.json").read_text())
            assert manifest["state_sha256"] == entry["checkpoint_sha256"]
            assert digest(point / "state.pt") == entry["checkpoint_sha256"]
            assert manifest["boundary"] == (
                "after_q0" if unit == 0 else "after_dual_and_D"
            )
            assert manifest["profile"] == "authorized_p2r_only"
            assert manifest["run_id"] == run_id and manifest["condition"] == condition
            assert manifest["provenance"]["data"]["training_shard_manifest_sha256"] == (
                "62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9"
            )
            source_hashes.add(json.dumps(manifest["provenance"]["code"], sort_keys=True))
            git_commits[manifest["git_commit"]] += 1
            payload = json.loads((run_root / f"unit-{unit}.json").read_text())
            assert payload["status"] == "passed"
            assert payload["checkpoint_sha256"] == entry["checkpoint_sha256"]
            assert payload["resources"] == expected_resources
            market_flags[str(payload["report"]["market_training_executed"])] += 1
            final_access_flags[str(payload["report"]["final_test_accessed"])] += 1
            if unit:
                phases = [row for row in payload["report"]["telemetry"]
                          if row["phase"] == "D" and row["iteration"] == unit - 1]
                assert len(phases) == 1 and phases[0]["status"] == "complete"
                assert phases[0]["trajectories"] == 64
                assert phases[0]["transitions"] == 11520
                assert 0 < phases[0]["wall_seconds"] <= 900
                run_d_seconds += phases[0]["wall_seconds"]
                d_peak_rss = max(d_peak_rss, phases[0]["rss_peak_bytes"])

        final = json.loads((run_root / "unit-10.json").read_text())
        report = final["report"]
        assert report["status"] == "passed" and report["next_iteration"] == 10
        assert report["boundary"] == "after_dual_and_D"
        assert report["condition"] == condition and report["settings"]["seed"] == seed
        assert report["final_test_accessed"] is False
        records = report["diagnostic"]["records"]
        assert [r["iteration"] for r in records] == list(range(10))
        audits = report["audits"]
        assert len(audits) == 10
        run_metrics = []
        for iteration, record in enumerate(records):
            label, policy_hash = record["policy_version"].split(":", 1)
            assert label == f"policy-{iteration}"
            assert len(policy_hash) == 64 and all(c in "0123456789abcdef" for c in policy_hash)
            assert len(record["archives"]) == 64
            for label, count in record["overlap"].items():
                overlap_totals[label]["numerator"] += count["numerator"]
                overlap_totals[label]["denominator"] += count["denominator"]
            audit = audits[iteration]
            assert audit["iteration"] == iteration + 1
            run_metrics.append(dict(
                iteration=iteration, policy_version=record["policy_version"],
                A={stage: compact_metric(record["A"][stage]) for stage in ("pre", "post")},
                D={stage: compact_metric(record["D"][stage]) for stage in ("pre", "post")},
                risk=record["risk"], overlap=record["overlap"],
                B={key: audit[key] for key in (
                    "eta", "f_b", "rho_b", "rho_q", "f_violation",
                    "empirical_violation", "lambda_before", "lambda_after",
                )},
            ))
            for archive in record["archives"]:
                path = Path(archive["path"])
                assert path.is_relative_to(run_root / "D")
                assert archive["route_id"].startswith("accepted-train:")
                assert digest(path) == archive["sha256"]
                d_archives += 1
        runs.append(dict(seed=seed, condition=condition, status="passed", records=records))
        iteration_metrics[run_id] = run_metrics
        d_seconds += run_d_seconds
        d_warning_total += report["diagnostic"]["warnings"]["D/post/relative_mse"]["numerator"]
        final_hashes[run_id] = units[-1]["checkpoint_sha256"]
        run_summaries.append(dict(
            run_id=run_id, seed=seed, condition=condition,
            wall_seconds=sum(u["seconds"] for u in units),
            D_seconds=run_d_seconds,
            sessions=len(run["sessions"]),
            actor_updates=run["resources"]["actor_updates"],
            critic_updates=run["resources"]["critic_updates"],
            diagnostic_trajectories=run["resources"]["diagnostic_trajectories"],
            D_post_relative_mse_warning=report["diagnostic"]["warnings"]["D/post/relative_mse"],
        ))
    assert len(source_hashes) == 1
    assert d_archives == 5760
    assert state["resources"] == dict(
        trajectories=81360, transitions=14644800,
        diagnostic_trajectories=5760, diagnostic_transitions=1036800,
        actor_updates=720, critic_updates=1440,
    )
    assert final_access_flags == {"False": 99}

    gate = campaign_gate(runs)
    gate_summary = {}
    for key, value in gate["gates"].items():
        gate_summary[key] = dict(
            advance=value["advance"], checks=value["checks"],
            Z_D_early=value["early"]["z"], Z_D_late=value["late"]["z"],
            Z_A_late=value["A_late"]["z"],
            R_D_early=value["early"]["relative_mse"],
            R_D_late=value["late"]["relative_mse"],
            R_A_late=value["A_late"]["relative_mse"],
            bias_D_late=value["late"]["normalized_bias"],
        )
    day = state["days"]["2026-10-07"]
    assert day["external_seconds"] == 0
    assert day["charged_wall_seconds"] <= 10800
    assert day["active_seconds"] <= day["charged_wall_seconds"]
    assert state["updated_epoch"] <= day["hard_deadline"]
    print(json.dumps(dict(
        status=state["status"], cursor=state["cursor"], units_accepted=len(state["units"]),
        registration_sha256=digest(ROOT / "docs/protocols/P2R-market-approval.json"),
        ledger_sha256=digest(ledger_path), journal_sha256=digest(journal_path),
        ledger_rows=len(ledger_rows), journal_rows=len(journal_rows),
        unit_events=event_counts["unit_completed"],
        availability_lost_events=event_counts["availability_lost"],
        pauses=event_counts["paused"], unit_failed_events=event_counts["unit_failed"],
        heartbeat_intervals=len(gaps), heartbeat_max_seconds=max(gaps),
        invocation_ids=invocations, one_code_hash_set=len(source_hashes) == 1,
        checkpoint_git_commits=dict(git_commits),
        checkpoints_verified=99, D_archives_verified=d_archives,
        D_wall_seconds=d_seconds, D_peak_rss_bytes=d_peak_rss,
        worker_rss_peak_bytes=max(u["supervisor"]["rss_peak_bytes"] for u in state["units"]),
        supervisor_rss_peak_bytes=max(row.get("rss_supervisor", 0) or 0
                                      for row in journal_rows),
        Q0_unit_wall_seconds=sum(u["seconds"] for u in state["units"] if u["unit"] == 0),
        iteration_unit_wall_seconds=sum(u["seconds"] for u in state["units"]
                                        if u["unit"] > 0),
        D_post_relative_mse_warnings=dict(numerator=d_warning_total, denominator=90),
        D_overlap={label: dict(count) for label, count in overlap_totals.items()},
        day_local="2026-10-07", started_utc=day["started_utc"],
        completed_utc=state["updated_utc"], active_seconds=day["active_seconds"],
        charged_wall_seconds=day["charged_wall_seconds"],
        daily_limit_seconds=10800,
        remaining_daily_seconds=10800 - day["charged_wall_seconds"],
        work_deadline_epoch=day["work_deadline"],
        hard_deadline_epoch=day["hard_deadline"],
        resources=state["resources"], runs=run_summaries,
        iteration_metrics=iteration_metrics,
        final_checkpoint_hashes=final_hashes,
        numerical_technical_decision=gate["decision"],
        technical_seeds_passing=gate["seeds_passing"],
        technical_gates=gate_summary,
        market_training_executed_report_counts=dict(market_flags),
        final_test_accessed_report_counts=dict(final_access_flags),
        formal_interpretation="pending_review_of_preflight_metadata_discrepancy",
    ), sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
