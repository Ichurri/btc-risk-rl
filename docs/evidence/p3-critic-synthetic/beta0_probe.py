"""Small deterministic synthetic reference; never loads accepted market data."""

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import torch

from btc_risk_rl.agents.synthetic import SyntheticMarket
from btc_risk_rl.agents.trainer import SyntheticExperiment, fixed_digest
from btc_risk_rl.config import load_config
from btc_risk_rl.pilots.p2 import Diagnostic, P2SyntheticSettings, tree_hash


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("legacy", "p3_beta0"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    settings_type = P2SyntheticSettings
    if args.profile == "p3_beta0":
        from btc_risk_rl.pilots.p3_critic import P3SyntheticSettings

        settings_type = P3SyntheticSettings
    settings = settings_type(
        seed=710031,
        iterations=1,
        hidden=4,
        n_a=2,
        n_q=2,
        n_b=2,
        actor_epochs=1,
        critic_epochs=4,
        minibatch=1,
    )
    source = SyntheticMarket(load_config(Path("configs/initial.toml")))
    with TemporaryDirectory(prefix="p3-critic-fixture-") as temporary:
        root = Path(temporary)
        run = SyntheticExperiment(
            source,
            settings,
            condition="C5",
            run_id="p3-critic-paired-fixture",
            journal=root / "journal",
            diagnostic=Diagnostic(root / "D", n=2),
        )
        report = run.run()
        assert report["status"] == "passed"
        output = dict(
            scope="synthetic_only_no_market",
            profile=args.profile,
            seed=settings.seed,
            actor=tree_hash(run.actor.state_dict()),
            critic=tree_hash(run.critic.state_dict()),
            actor_optimizer=tree_hash(run.actor_optimizer.state_dict()),
            critic_optimizer=tree_hash(run.critic_optimizer.state_dict()),
            fixed=[fixed_digest(row) for row in run.fixed],
            route_ids=[row["route_ids"] for row in run.events if "route_ids" in row],
            policy_versions=[
                row["policy_version"] for row in run.events if "policy_version" in row
            ],
            actor_updates=run.actor_updates,
            critic_updates=run.critic_updates,
            trajectories=run.collector.trajectories,
            diagnostic_trajectories=run.diagnostic.collector.trajectories,
        )
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(f"{args.profile}: actor={output['actor'][:12]} critic={output['critic'][:12]}")


if __name__ == "__main__":
    main()
