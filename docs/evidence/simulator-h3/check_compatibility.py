"""New H3 regression runs. Synthetic H2 comparison plus historical ledger comparison."""

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

from btc_risk_rl.config import STEP_MS, load_config, utc_ms
from btc_risk_rl.env.market import MarketPath
from btc_risk_rl.env.trading import TradingEnv

H2 = "cc913b629694641543e2b54375dbda5d55130544"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def git_blob(path):
    return subprocess.check_output(["git", "show", f"{H2}:{path}"])


def synthetic_regression(config):
    # Trusted versioned H2 source executed only in this explicit regression.
    source = git_blob("src/btc_risk_rl/env/trading.py")
    namespace = {}
    exec(compile(source, f"git:{H2}/trading.py", "exec"), namespace)
    old_env = namespace["TradingEnv"]
    fixed = {}
    for name in ["env/accounting.py", "env/market.py", "features/market.py"]:
        path = Path("src/btc_risk_rl") / name
        check(path.read_bytes() == git_blob(str(path)), f"H2 invariant changed: {path}")
        fixed[str(path)] = digest(path)
    rows = []
    for partition, n, start in [
        ("train", 180, config.data.train_start),
        ("validation", 2190, config.data.validation_start),
    ]:
        j = np.arange(n + 1)
        times = utc_ms(start) + (j - 1) * STEP_MS
        opens = 100 + 0.03 * j + 2 * np.sin(j / 11)
        closes = opens + 0.5 * np.cos(j / 7)
        features = np.sin(j[:, None] / 17 + np.arange(10)[None, :])
        path = MarketPath(
            times,
            opens,
            closes,
            features,
            partition,
            0,
            "collection_window" if partition == "train" else "partition_boundary",
            "synthetic_h3_regression_not_market",
        )
        a, b = old_env(path, config), TradingEnv(path, config)
        old, new = a.reset(), b.reset()
        check(np.array_equal(old[0], new[0][:12]), "reset observation")
        for i in range(n):
            action = (i % 11) / 10
            old, new = a.step(action), b.step(action)
            check(np.array_equal(old[0], new[0][:12]), "H2 observation prefix")
            check(old[1] == new[1], "net log reward")
            for key in old[-1]:
                if key != "adr_002_status":
                    check(old[-1][key] == new[-1][key], f"cashflow/metadata {key}")
            check(old[2] is False and old[3] == (i == n - 1), "historical flags")
        check(new[2] == (partition == "train"), "new terminal")
        check(new[3] == (partition == "validation"), "new truncation")
        rows.append(
            {
                "partition": partition,
                "transitions": n,
                "observations_12_and_rewards_and_accounting": "exactly_equal",
            }
        )
    return {
        "kind": "fresh_synthetic_execution_of_both_versions",
        "h2_source_commit": H2,
        "h2_trading_sha256": hashlib.sha256(source).hexdigest(),
        "unchanged_modules": fixed,
        "runs": rows,
    }


def ledger_regression(new_summary, new_ledger, old_ledger):
    old = json.loads(Path("docs/evidence/simulator-h2/simulation-summary.json").read_text())
    new = json.loads(new_summary.read_text())
    check(digest(old_ledger) == old["ledger_sha256"], "unverified historical H2 ledger")
    check(digest(new_ledger) == new["ledger_sha256"], "unverified new H3 ledger")
    check(old["source_hashes_before"] == new["source_hashes_before"], "different inputs")
    check(
        old["weights"] == new["weights"] and old["action_rule"] == new["action_rule"],
        "different action schedule",
    )
    with old_ledger.open() as a, new_ledger.open() as b:
        old_rows, new_rows = list(csv.DictReader(a)), list(csv.DictReader(b))
    check(len(old_rows) == len(new_rows) == 7590, "row count")
    columns = [key for key in old_rows[0] if key != "truncated"]
    for old_row, new_row in zip(old_rows, new_rows):
        check(all(old_row[k] == new_row[k] for k in columns), "H2 ledger regression")
    return {
        "kind": "new_H3_development_run_compared_to_historical_H2_ledger",
        "historical_results_not_claimed_as_new": True,
        "rows_exactly_equal": len(new_rows),
        "compared_columns": columns,
        "old_ledger_sha256": digest(old_ledger),
        "new_ledger_sha256": digest(new_ledger),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--new-summary", type=Path, required=True)
    parser.add_argument("--new-ledger", type=Path, required=True)
    parser.add_argument("--old-ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    check(not args.output.exists(), "Output exists")
    result = {
        "status": "passed",
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "script_sha256": digest(Path(__file__)),
        "synthetic": synthetic_regression(load_config(Path("configs/initial.toml"))),
        "development": ledger_regression(args.new_summary, args.new_ledger, args.old_ledger),
        "training_executed": False,
        "final_test_accessed": False,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
