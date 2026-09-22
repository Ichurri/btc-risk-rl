"""Offline deterministic accounting probe, NOT training or a strategy-selection run."""

import argparse
import csv
import importlib.metadata
import json
import math
import platform
import subprocess
import sys
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path

import numpy as np

from btc_risk_rl.config import load_config
from btc_risk_rl.data.binance import sha256
from btc_risk_rl.env.market import AcceptedMarket
from btc_risk_rl.env.trading import TradingEnv

WEIGHTS = (0.0, 0.25, 0.75, 1.0, 0.5, 0.9)
LEDGER_FIELDS = [
    "probe",
    "step",
    "execution_open_time_ms",
    "target_weight",
    "delta_btc",
    "reference_price",
    "execution_price",
    "commission",
    "slippage_cost",
    "cash",
    "btc",
    "equity_previous_close",
    "equity_open_before",
    "equity_open_after",
    "equity",
    "reward",
    "terminated",
    "truncated",
    "objective_terminal",
    "cvar_eligible",
    "bootstrap_mask",
    "trace_mask",
    "clock",
    "end_reason",
]


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def close(actual, expected, label):
    check(math.isclose(actual, expected, rel_tol=2e-12, abs_tol=1e-9), label)


def audit_rollout(path, config, writer, label):
    env = TradingEnv(path, config)
    observation, initial = env.reset(seed=20260921)
    check(initial["cash"] == config.environment.initial_cash and initial["btc"] == 0, "reset")
    previous = initial
    rewards, errors = [], []
    commissions, slippage = [], []
    for i in range(len(path.times) - 1):
        check(np.array_equal(observation[:10], path.features[i]), "current observation")
        target = WEIGHTS[(i // 13 + 1) % len(WEIGHTS)]  # fixed before seeing prices
        observation, reward, terminated, truncated, info = env.step(target)
        p = float(path.opens[i + 1])
        delta = info["delta_btc"]
        with localcontext() as ctx:
            ctx.prec = 50

            def dec(x):
                return Decimal(str(x))

            execution = dec(p) * (
                1 + dec(config.environment.slippage)
                if delta > 0
                else 1 - dec(config.environment.slippage)
                if delta < 0
                else 1
            )
            fee = abs(dec(delta)) * execution * dec(config.environment.commission)
            slip = abs(dec(delta)) * dec(p) * dec(config.environment.slippage)
            expected_cash = dec(previous["cash"]) - dec(delta) * execution - fee
            expected_btc = dec(previous["btc"]) + dec(delta)
            equity = expected_cash + expected_btc * dec(path.closes[i + 1])
        close(info["execution_price"], float(execution), "execution price")
        close(info["commission"], float(fee), "commission")
        close(info["slippage_cost"], float(slip), "slippage")
        close(info["cash"], float(expected_cash), "cashflow")
        close(info["btc"], float(expected_btc), "BTC conservation")
        close(info["equity"], float(equity), "close equity")
        close(info["equity_open_before"], previous["cash"] + previous["btc"] * p, "gap equity")
        close(info["equity_open_after"], info["cash"] + info["btc"] * p, "open equity")
        close(info["btc"] * p / info["equity_open_after"], target, "post-cost target")
        close(reward, math.log(float(equity) / previous["equity"]), "net log reward")
        close(
            observation[10], info["btc"] * path.closes[i + 1] / info["equity"], "portfolio weight"
        )
        close(observation[11], math.log(info["equity"] / initial["equity"]), "log equity state")
        check(info["execution_open_time_ms"] == int(path.times[i + 1]), "execution time")
        last = i == len(path.times) - 2
        training = path.partition == "train"
        check(terminated == (last and training), "objective terminality")
        check(truncated == (last and not training), "collection/data truncation")
        check(info["objective_terminal"] == terminated, "objective flag")
        check(
            info["cvar_eligible"] == info["trajectory_complete"] == terminated, "risk completeness"
        )
        mask = int(not last) if training else None
        check(info["bootstrap_mask"] == info["trace_mask"] == mask, "learning masks")
        expected_clock = (180 - i - 1) / 180 if training else 1.0
        check(observation[12] == expected_clock, "horizon clock")
        check(info["cash"] >= 0 and info["btc"] >= 0, "nonnegative holdings")
        errors.append(abs(info["cash"] - float(expected_cash)))
        rewards.append(reward)
        commissions.append(info["commission"])
        slippage.append(info["slippage_cost"])
        if writer is not None:
            writer.writerow(
                {
                    **{key: info[key] for key in LEDGER_FIELDS if key in info},
                    "probe": label,
                    "reward": reward,
                    "truncated": truncated,
                    "terminated": terminated,
                    "clock": float(observation[12]),
                }
            )
        previous = info
    expected_sum = math.log(previous["equity"] / initial["equity"])
    check(abs(math.fsum(rewards) - expected_sum) < 1e-10, "telescoping reward")
    check(previous["end_reason"] == path.end_reason, "end reason")
    return dict(
        probe=label,
        partition=path.partition,
        segment_id=path.segment_id,
        steps=len(rewards),
        first_target_ms=int(path.times[1]),
        last_target_ms=int(path.times[-1]),
        end_reason=path.end_reason,
        terminated=terminated,
        truncated=truncated,
        final_clock=float(observation[12]),
        cvar_eligible=previous["cvar_eligible"],
        final_cash=previous["cash"],
        final_btc=previous["btc"],
        final_equity=previous["equity"],
        net_log_reward_sum=math.fsum(rewards),
        telescoping_error=abs(math.fsum(rewards) - expected_sum),
        max_cashflow_error=max(errors),
        commission_total=math.fsum(commissions),
        slippage_total=math.fsum(slippage),
        forced_liquidation=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/initial.toml"))
    parser.add_argument("--raw", type=Path, default=Path("data/raw/development"))
    parser.add_argument("--prepared", type=Path, default=Path("data/processed/segmented-B-h1"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--context", choices=["local", "remote"], required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    args.output.mkdir(parents=True, exist_ok=False)
    # This loader guards source ranges before product audit or market page access.
    data = AcceptedMarket(config, args.raw, args.prepared)
    raw_manifest = json.loads((args.raw / "manifest.json").read_text())
    prepared_manifest = json.loads((args.prepared / "manifest.json").read_text())
    protected = [args.raw / "manifest.json", args.prepared / "manifest.json"]
    protected += [args.raw / page["file"] for page in raw_manifest["pages"]]
    protected += [args.prepared / name for name in prepared_manifest["files"]]
    before = {str(p): sha256(p) for p in protected}
    boundaries = {}
    for episode_id in data.episode_ids:
        path = data.training_path(episode_id)
        if path.segment_id not in boundaries:
            boundaries[path.segment_id] = [episode_id, episode_id]
        boundaries[path.segment_id][1] = episode_id
    probes = []
    with (args.output / "ledger.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LEDGER_FIELDS)
        writer.writeheader()
        for episode_id in sorted({i for pair in boundaries.values() for i in pair}):
            probes.append(
                audit_rollout(
                    data.training_path(episode_id), config, writer, f"train-index-{episode_id}"
                )
            )
        probes.append(
            audit_rollout(data.validation_path(), config, writer, "validation-continuous")
        )
    after = {str(p): sha256(p) for p in protected}
    check(before == after, "Inputs or scaler changed")
    code = sorted(Path("src/btc_risk_rl/env").glob("*.py")) + [
        Path(__file__),
        Path("tests/test_simulator.py"),
        Path("tests/test_temporal_contract.py"),
        Path("src/btc_risk_rl/config.py"),
        Path("configs/initial.toml"),
        Path("src/btc_risk_rl/data/config_compatibility.py"),
        Path("src/btc_risk_rl/data/segmented_audit.py"),
    ]
    result = dict(
        status="passed",
        purpose="deterministic_accounting_probe_not_strategy_evaluation",
        context=args.context,
        time_utc=datetime.now(timezone.utc).isoformat(),
        platform=platform.platform(),
        python=sys.version,
        packages={
            name: importlib.metadata.version(name)
            for name in ["numpy", "pandas", "gymnasium", "pytest", "ruff"]
        },
        command=[sys.executable, *sys.argv],
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        git_status=subprocess.check_output(["git", "status", "--short"], text=True),
        indexed_episodes_verified=len(data.episode_ids),
        eligible_segments=len(boundaries),
        paths_executed=len(probes),
        steps_executed=sum(p["steps"] for p in probes),
        validation_resets=1,
        action_rule="WEIGHTS[(step_index // 13 + 1) % 6]",
        weights=WEIGHTS,
        source_hashes_before=before,
        source_hashes_after=after,
        source_and_scaler_unchanged=True,
        code_hashes={str(p.resolve().relative_to(Path.cwd())): sha256(p) for p in code},
        ledger_sha256=sha256(args.output / "ledger.csv"),
        probes=probes,
        adr_002="adopted_v2_1",
        contract_version=config.environment.contract_version,
        observation_version=config.environment.observation_version,
        gamma=config.environment.gamma,
        config_compatibility=data.audit["config_compatibility"],
        data_audit=data.audit,
        training_executed=False,
        final_test_accessed=False,
    )
    (args.output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: result[key]
                for key in [
                    "status",
                    "indexed_episodes_verified",
                    "paths_executed",
                    "steps_executed",
                    "source_and_scaler_unchanged",
                    "training_executed",
                    "final_test_accessed",
                ]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
