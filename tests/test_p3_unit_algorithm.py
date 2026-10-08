"""P3 worker algorithm uses fabricated routes only; no historical learning."""

import json

import torch

from btc_risk_rl.agents.synthetic import SyntheticMarket
from btc_risk_rl.pilots.p2 import P2SyntheticSettings, tree_hash
from btc_risk_rl.pilots.p2_runner import complete_unit
from btc_risk_rl.pilots.p3_critic import P3SyntheticSettings


def settings(beta):
    return P3SyntheticSettings(
        critic_beta=beta, seed=710031, iterations=1, hidden=4,
        n_a=2, n_q=2, n_b=2, actor_epochs=1, critic_epochs=4, minibatch=1,
    )


def test_q0_and_qabd_d_are_distinct_complete_p3_synthetic_units(config, tmp_path):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    source = SyntheticMarket(config)
    run_root = tmp_path / "run-00-C5-b1"
    q0 = complete_unit(source, settings(1), root=run_root,
                       condition="C5", run_id=run_root.name, unit=0,
                       atomic_checkpoint=True)
    assert q0["resources"]["actor_updates"] == q0["resources"]["critic_updates"] == 0
    assert q0["report"]["market_training_executed"] is False
    assert json.loads((run_root / "checkpoint-0/manifest.json").read_text())["boundary"] == "after_q0"
    after = complete_unit(source, settings(1), root=run_root,
                          condition="C5", run_id=run_root.name, unit=1,
                          previous=q0["checkpoint"], atomic_checkpoint=True)
    assert after["resources"] == dict(
        trajectories=6, transitions=1080, diagnostic_trajectories=2,
        diagnostic_transitions=360, actor_updates=2, critic_updates=8,
    )
    assert after["report"]["market_training_executed"] is False
    manifest = json.loads((run_root / "checkpoint-1/manifest.json").read_text())
    assert manifest["profile"] == "p3_synthetic_tests_only"
    assert manifest["settings"]["critic_beta"] == 1
    assert manifest["boundary"] == "after_dual_and_D"
    assert after["report"]["diagnostic"]["records"][0]["policy_version"].startswith("policy-0:")


def test_beta_zero_unit_matches_legacy_p2_learning_state(config, tmp_path):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    source = SyntheticMarket(config)
    p3 = tmp_path / "p3"
    old = tmp_path / "old"
    p3_q0 = complete_unit(source, settings(0), root=p3, condition="C5",
                          run_id="paired-fixture", unit=0, atomic_checkpoint=True)
    old_settings = P2SyntheticSettings(
        seed=710031, iterations=1, hidden=4, n_a=2, n_q=2, n_b=2,
        actor_epochs=1, critic_epochs=4, minibatch=1,
    )
    old_q0 = complete_unit(source, old_settings, root=old, condition="C5",
                           run_id="paired-fixture", unit=0, atomic_checkpoint=True)
    p3_a = complete_unit(source, settings(0), root=p3, condition="C5",
                         run_id="paired-fixture", unit=1,
                         previous=p3_q0["checkpoint"], atomic_checkpoint=True)
    old_a = complete_unit(source, old_settings, root=old, condition="C5",
                          run_id="paired-fixture", unit=1,
                          previous=old_q0["checkpoint"], atomic_checkpoint=True)
    p3_state = torch.load(p3_a["checkpoint"] + "/state.pt", map_location="cpu", weights_only=True)
    old_state = torch.load(old_a["checkpoint"] + "/state.pt", map_location="cpu", weights_only=True)
    for key in ("actor", "critic", "actor_optimizer", "critic_optimizer"):
        assert tree_hash(p3_state[key]) == tree_hash(old_state[key]), key
    assert p3_a["resources"] == old_a["resources"]
