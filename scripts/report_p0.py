"""Export small P0 evidence from campaign logs only; no OHLC, optimizer or evaluation."""

import argparse
import hashlib
import json
from pathlib import Path

from btc_risk_rl.pilots.protocol import CAMPAIGN, PROTOCOL_SHA, roster


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    ledger = CAMPAIGN / "ledger.jsonl"
    state = json.loads(ledger.read_text().splitlines()[-1])
    rows = []
    manifests = []
    for index, (seed, condition) in enumerate(roster()):
        run_id = f"run-{index:02d}-{condition}"
        run = state["runs"].get(run_id, {})
        count = run.get("next_unit", 0)
        root = CAMPAIGN / run_id
        row = dict(
            run_id=run_id,
            seed=seed,
            condition=condition,
            complete_units=count,
            complete_iterations=max(0, count - 1),
            resources=run.get("resources", {}),
            days=run.get("days", []),
            status="completed" if count == 3 else "pending",
        )
        if state["status"] in {"failed", "incomplete"} and index == state["cursor"]:
            row["status"] = state["status"]
        elif count and count < 3:
            row["status"] = "paused"
        units = [u for u in state["units"] if u["run_id"] == run_id]
        row["measured_units"] = [
            {
                k: u[k]
                for k in (
                    "kind",
                    "unit",
                    "seconds",
                    "resources",
                    "supervisor",
                    "algorithm_seconds",
                    "save_seconds",
                )
            }
            for u in units
        ]
        if count:
            path = root / f"unit-{count - 1}.json"
            data = json.loads(path.read_text())
            report = data["report"]
            row.update(
                actor_sha256=report["actor_sha256"],
                critic_sha256=report["critic_sha256"],
                settings=report["settings"],
                warnings=data["warnings"],
                telemetry=report["telemetry"],
                stability=report["stability"],
                collection_diagnostics=report["collection_diagnostics"],
            )
            row["audits"] = [
                {k: v for k, v in a.items() if k not in {"q_tail", "b_tail"}}
                | {
                    "q_tail": {k: v for k, v in a["q_tail"].items() if k != "weights"},
                    "b_tail": {k: v for k, v in a["b_tail"].items() if k != "weights"},
                }
                for a in report["audits"]
            ]
            manifests.append(
                dict(
                    path=str(path.relative_to(CAMPAIGN)),
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                )
            )
            for unit in range(count):
                point = root / f"checkpoint-{unit}/manifest.json"
                meta = json.loads(point.read_text())
                manifests.append(
                    dict(
                        path=str(point.relative_to(CAMPAIGN)),
                        sha256=hashlib.sha256(point.read_bytes()).hexdigest(),
                        state_sha256=meta["state_sha256"],
                        commit=meta["git_commit"],
                    )
                )
        rows.append(row)
    result = dict(
        status=state["status"],
        pause_reason=state.get("pause_reason"),
        protocol_sha256=PROTOCOL_SHA,
        identity=state["identity"],
        resources=state["resources"],
        days=state["days"],
        measurements=state["measurements"],
        failure=state.get("failure"),
        updated_utc=state["updated_utc"],
        runs=rows,
        artifacts=manifests,
        ledger_sha256=hashlib.sha256(ledger.read_bytes()).hexdigest(),
        interpretation="P0 technical pilot only; two iterations do not show convergence or population CVaR compliance",
        validation_accessed=False,
        final_accessed=False,
    )
    with (args.output / "results.json").open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print(
        json.dumps(
            dict(status=result["status"], resources=result["resources"], output=str(args.output))
        )
    )


if __name__ == "__main__":
    main()
