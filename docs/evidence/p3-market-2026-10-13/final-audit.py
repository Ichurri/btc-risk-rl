"""Read-only P3 closure audit over all accepted reports and checkpoints."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from btc_risk_rl.pilots.p3_units import assess_completed_campaign

REPO = Path(__file__).resolve().parents[3]
ROOT = REPO / "artifacts/p3-approved-v1"
INVOCATION = "629b6812dc79470e876a5ec7670e801a"
LEDGER_PREFIX = (30_414_121, "cff406928d2ff5655599c5fb1c99465c3a13bbb8aeb505fa39e1291724c446ce")
JOURNAL_PREFIX = (1_698_157, "5b4e2a51bd11ba4d10d7e2a6f39ae1b575177890204d3dedb17d7c5aa611e85b")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_chain(path, kind, prefix):
    data = path.read_bytes()
    assert digest(data[:prefix[0]]) == prefix[1]
    assert data[:prefix[0]].endswith(b"\n")
    previous = None
    count = 0
    events = Counter()
    last = None
    for line in data.splitlines():
        row = json.loads(line)
        if kind == "ledger":
            actual = digest(json.dumps(
                {key: value for key, value in row.items() if key != "state_hash"},
                sort_keys=True, allow_nan=False,
            ).encode())
            assert row["previous_hash"] == previous and row["state_hash"] == actual
        else:
            actual = row.pop("sha256")
            assert row["campaign"] == "p3-approved-v1" and row["previous"] == previous
            assert actual == digest(json.dumps(row, sort_keys=True, allow_nan=False).encode())
            events[row["event"]] += 1
            row["sha256"] = actual
        previous = actual
        last = row
        count += 1
    assert last is not None
    return dict(sha256=digest(data), size_bytes=len(data), records=count,
                chain_head=previous, events=dict(sorted(events.items()))), last


def main():
    ledger, state = verify_chain(ROOT / "ledger.jsonl", "ledger", LEDGER_PREFIX)
    journal, last_event = verify_chain(ROOT / "supervisor.jsonl", "journal", JOURNAL_PREFIX)
    assert state["status"] == "completed" and state["pending"] is None
    assert state["cursor"] == 18 and len(state["units"]) == 198
    assert last_event["event"] == "supervisor_exit"
    assert last_event["status"] == "completed" and last_event["invocation_id"] == INVOCATION
    assert len(state["days"]) == 2 and set(state["days"]) == {"2026-10-08", "2026-10-13"}
    assert all(day["charged_wall_seconds"] <= 10800 for day in state["days"].values())

    by_run = defaultdict(list)
    resources = Counter()
    for unit in state["units"]:
        by_run[unit["run_id"]].append(unit)
        resources.update(unit["resources"])
        work = ROOT / unit["run_id"]
        report = work / f"unit-{unit['unit']}.json"
        checkpoint = Path(unit["checkpoint"])
        payload = json.loads(report.read_text())
        assert checkpoint.resolve().is_relative_to(ROOT.resolve())
        assert digest(report.read_bytes()) == unit["report_sha256"]
        assert digest((checkpoint / "state.pt").read_bytes()) == unit["checkpoint_sha256"]
        assert payload["checkpoint_sha256"] == unit["checkpoint_sha256"]
        assert payload["status"] == "passed" and unit["supervisor"]["status"] == "passed"
        assert payload["report"]["market_training_executed"] is (unit["unit"] > 0)
        assert payload["report"]["final_test_accessed"] is False
    assert dict(resources) == state["resources"]

    runs = []
    for index, (seed, condition, beta) in enumerate(state["identity"]["roster"]):
        run_id = f"run-{index:02d}-{condition}-b{beta}"
        units = by_run[run_id]
        assert [unit["unit"] for unit in units] == list(range(11))
        assert state["runs"][run_id]["next_unit"] == 11
        last = units[-1]
        payload = json.loads((ROOT / run_id / "unit-10.json").read_text())
        d_rows = [row for row in payload["report"]["telemetry"] if row["phase"] == "D"]
        assert sorted(row["iteration"] for row in d_rows) == list(range(10))
        runs.append(dict(
            run_id=run_id, seed=seed, condition=condition, beta=beta,
            accepted_units=11, ledger_wall_seconds=sum(unit["seconds"] for unit in units),
            D_wall_seconds=sum(row["wall_seconds"] for row in d_rows),
            worker_rss_peak_bytes=max(unit["supervisor"]["rss_peak_bytes"] for unit in units),
            cumulative_warning_count=len(payload["warnings"]),
            final_report_sha256=last["report_sha256"],
            final_checkpoint_sha256=last["checkpoint_sha256"],
        ))
    assert sum(run["accepted_units"] for run in runs) == 198
    recomputed = json.loads(json.dumps(assess_completed_campaign(ROOT, state)))
    assert recomputed == state["assessment"]
    decision = state["assessment"]
    pairs = {
        name: dict(
            advance=pair["advance"], informative=pair["informative"],
            missing_z_gates=pair["missing_z_gates"],
            delta_d=pair["delta_d"], delta_d3=pair["delta_d3"],
            delta_a=pair["delta_a"], h1=pair["h1"], checks=pair["checks"],
        )
        for name, pair in decision["pairs"].items()
    }
    result = dict(
        scope="P3_historical_development_diagnostic_closure_read_only",
        service="p3-market-v1-session-02.service", invocation_id=INVOCATION,
        closed_utc=state["updated_utc"], campaign_status=state["status"],
        completed_runs=state["cursor"], accepted_units=len(state["units"]),
        ledger=ledger, supervisor_journal=journal,
        latest_journal_event=dict(event=last_event["event"], status=last_event["status"],
                                  utc=last_event["utc"], sha256=last_event["sha256"]),
        days=state["days"], resources=state["resources"],
        total_ledger_unit_wall_seconds=sum(unit["seconds"] for unit in state["units"]),
        total_D_wall_seconds=sum(run["D_wall_seconds"] for run in runs),
        runs=runs, decision=dict(
            decision=decision["decision"], blocks=decision["blocks"],
            independent_seed_blocks=decision["independent_seed_blocks"],
            seed_blocks_passing=decision["seed_blocks_passing"], pairs=pairs,
            interpretation=decision["interpretation"],
        ),
    )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
