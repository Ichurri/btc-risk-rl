"""Read-only integrity and resource snapshot after the first P3 session."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ROOT = REPO / "artifacts/p3-approved-v1"
SERVICE = "p3-market-v1-session-01.service"
INVOCATION = "8b3d6b175bd34b78a655010d46cccf3d"
LEDGER_PREFIX_BYTES = 30_414_121
JOURNAL_PREFIX_BYTES = 1_698_157


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    return digest(path.read_bytes())


def chain_snapshot(path, kind, prefix_bytes):
    with path.open("rb") as stream:
        data = stream.read(prefix_bytes)
    assert len(data) == prefix_bytes and data.endswith(b"\n")
    previous = None
    last = None
    count = 0
    events = Counter()
    for line in data.splitlines():
        row = json.loads(line)
        if kind == "ledger":
            actual = digest(json.dumps(
                {key: value for key, value in row.items() if key != "state_hash"},
                sort_keys=True, allow_nan=False,
            ).encode())
            assert row["previous_hash"] == previous
            assert row["state_hash"] == actual
        else:
            actual = row.pop("sha256")
            assert row["campaign"] == "p3-approved-v1"
            assert row["previous"] == previous
            assert actual == digest(json.dumps(row, sort_keys=True, allow_nan=False).encode())
            events[row["event"]] += 1
            row["sha256"] = actual
        previous = actual
        last = row
        count += 1
    assert last is not None
    return dict(
        sha256_at_session_close=digest(data), bytes_at_session_close=len(data),
        records=count, chain_head=previous, events=dict(sorted(events.items())),
    ), last


def main():
    ledger, state = chain_snapshot(ROOT / "ledger.jsonl", "ledger", LEDGER_PREFIX_BYTES)
    journal, last_event = chain_snapshot(
        ROOT / "supervisor.jsonl", "journal", JOURNAL_PREFIX_BYTES
    )
    assert state["status"] == "ready" and state["pending"] is None
    assert state["cursor"] == 10 and len(state["units"]) == 116
    assert last_event["event"] == "supervisor_exit"
    assert last_event["status"] == "ready"
    assert last_event["invocation_id"] == INVOCATION

    by_run = defaultdict(list)
    totals = Counter()
    for unit in state["units"]:
        by_run[unit["run_id"]].append(unit)
        totals.update(unit["resources"])
        work = ROOT / unit["run_id"]
        report = work / f"unit-{unit['unit']}.json"
        payload = json.loads(report.read_text())
        assert Path(unit["checkpoint"]).resolve().is_relative_to(ROOT.resolve())
        assert file_digest(report) == unit["report_sha256"]
        assert payload["checkpoint_sha256"] == unit["checkpoint_sha256"]
        assert file_digest(Path(unit["checkpoint"]) / "state.pt") == unit["checkpoint_sha256"]
        assert payload["status"] == "passed"
        assert payload["report"]["market_training_executed"] is (unit["unit"] > 0)
        assert payload["report"]["final_test_accessed"] is False
        assert unit["supervisor"]["status"] == "passed"
    assert dict(totals) == state["resources"]

    runs = []
    for index, (seed, condition, beta) in enumerate(state["identity"]["roster"][:11]):
        run_id = f"run-{index:02d}-{condition}-b{beta}"
        units = by_run[run_id]
        last = units[-1]
        assert [unit["unit"] for unit in units] == list(range(len(units)))
        payload = json.loads((ROOT / run_id / f"unit-{last['unit']}.json").read_text())
        d_rows = [row for row in payload["report"]["telemetry"] if row["phase"] == "D"]
        assert len(d_rows) == last["unit"]
        assert sorted(row["iteration"] for row in d_rows) == list(range(last["unit"]))
        runs.append(dict(
            run_id=run_id, seed=seed, condition=condition, beta=beta,
            complete=last["unit"] == 10, accepted_units=len(units),
            next_unit=state["runs"][run_id]["next_unit"],
            ledger_wall_seconds=sum(unit["seconds"] for unit in units),
            D_wall_seconds=sum(row["wall_seconds"] for row in d_rows),
            worker_rss_peak_bytes=max(unit["supervisor"]["rss_peak_bytes"] for unit in units),
            resources=state["runs"][run_id]["resources"],
            latest_checkpoint_sha256=last["checkpoint_sha256"],
            latest_report_sha256=last["report_sha256"],
            cumulative_warning_count=len(payload["warnings"]),
        ))
    assert sum(run["complete"] for run in runs) == state["cursor"]
    assert sum(run["accepted_units"] for run in runs) == len(state["units"])
    day = state["days"]["2026-10-08"]
    result = dict(
        scope="session_01_integrity_and_cost_only_no_P3_outcome_decision",
        service=SERVICE, invocation_id=INVOCATION,
        closed_utc=state["updated_utc"], campaign_status=state["status"],
        completed_runs=state["cursor"], planned_runs=len(state["identity"]["roster"]),
        accepted_units=len(state["units"]), planned_units=198,
        next_run_id="run-10-C0-b1", next_unit=6,
        ledger=ledger, supervisor_journal=journal,
        day=dict(active_seconds=day["active_seconds"],
                 charged_wall_seconds=day["charged_wall_seconds"],
                 external_seconds=day["external_seconds"],
                 work_deadline_epoch=day["work_deadline"],
                 hard_deadline_epoch=day["hard_deadline"]),
        resources=state["resources"], runs=runs,
        latest_journal_event=dict(event=last_event["event"], status=last_event["status"],
                                  utc=last_event["utc"], sha256=last_event["sha256"]),
    )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
