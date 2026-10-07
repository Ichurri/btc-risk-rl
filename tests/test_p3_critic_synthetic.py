"""P3 critic intervention on fabricated routes only; no historical worker."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import torch

from btc_risk_rl.agents.checkpoint import load_checkpoint, save_checkpoint
from btc_risk_rl.agents.critic_objective import critic_objective
from btc_risk_rl.agents.synthetic import SyntheticMarket
from btc_risk_rl.agents.trainer import SyntheticExperiment, fixed_digest
from btc_risk_rl.pilots.p2 import Diagnostic, tree_hash
from btc_risk_rl.pilots.p3_critic import P3SyntheticSettings


def test_independent_loss_and_gradients_on_one_minibatch():
    prediction = torch.tensor([1.0, 2.0], dtype=torch.float64, requires_grad=True)
    targets = torch.tensor([0.0, 1.0], dtype=torch.float64)
    total0, mse0, penalty0 = critic_objective(prediction, targets, beta=0)
    assert total0 is mse0
    assert total0.item() == 1.0 and penalty0.item() == 0.0
    grad0 = torch.autograd.grad(total0, prediction)[0]
    torch.testing.assert_close(grad0, torch.tensor([1.0, 1.0], dtype=torch.float64))
    total1, mse1, penalty1 = critic_objective(prediction, targets, beta=1)
    assert (mse1.item(), penalty1.item(), total1.item()) == (1.0, 2.5, 3.5)
    grad1 = torch.autograd.grad(total1, prediction)[0]
    torch.testing.assert_close(grad1, torch.tensor([2.0, 3.0], dtype=torch.float64))
    assert targets.grad is None
    with pytest.raises(ValueError, match="same shape"):
        critic_objective(prediction, targets[:1], beta=1)


@pytest.mark.parametrize("bad_beta", [-1, 2, True, 0.5])
def test_only_adopted_binary_synthetic_arms_are_allowed(bad_beta):
    with pytest.raises(ValueError, match="critic_beta"):
        P3SyntheticSettings(critic_beta=bad_beta)


def test_beta_zero_matches_prechange_actor_critic_and_both_optimizers(tmp_path):
    output = tmp_path / "beta0-after.json"
    command = [
        sys.executable,
        "docs/evidence/p3-critic-synthetic/beta0_probe.py",
        "--profile",
        "p3_beta0",
        "--output",
        str(output),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    actual = json.loads(output.read_text())
    baseline = json.loads(Path("docs/evidence/p3-critic-synthetic/beta0-before.json").read_text())
    for key in (
        "actor",
        "critic",
        "actor_optimizer",
        "critic_optimizer",
        "fixed",
        "route_ids",
        "policy_versions",
        "actor_updates",
        "critic_updates",
        "trajectories",
        "diagnostic_trajectories",
    ):
        assert actual[key] == baseline[key], key


def make_run(config, root, beta):
    settings = P3SyntheticSettings(
        critic_beta=beta,
        seed=710047,
        iterations=1,
        hidden=4,
        n_a=2,
        n_q=2,
        n_b=2,
        actor_epochs=1,
        critic_epochs=4,
        minibatch=1,
    )
    run = SyntheticExperiment(
        SyntheticMarket(config),
        settings,
        condition="C5",
        run_id=f"p3-synthetic-beta-{beta}",
        journal=root / "journal",
        diagnostic=Diagnostic(root / "D", n=2),
    )
    return run


def test_first_actor_and_frozen_a_match_while_only_critic_changes(config, tmp_path):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    control = make_run(config, tmp_path / "control", 0)
    treatment = make_run(config, tmp_path / "treatment", 1)
    report0, report1 = control.run(), treatment.run()
    assert report0["status"] == report1["status"] == "passed"
    assert fixed_digest(control.fixed[0]) == fixed_digest(treatment.fixed[0])
    assert [row["route_ids"] for row in control.events if "route_ids" in row] == [
        row["route_ids"] for row in treatment.events if "route_ids" in row
    ]
    assert control.batches[1][0].realization != treatment.batches[1][0].realization
    assert control.batches[1][0].route_id == treatment.batches[1][0].route_id
    actor0 = next(row for row in control.events if row["event"] == "actor")
    actor1 = next(row for row in treatment.events if row["event"] == "actor")
    assert actor0["actor_after"] == actor1["actor_after"]
    assert actor0["critic_before"] == actor1["critic_before"]
    assert report0["actor_sha256"] == report1["actor_sha256"]
    assert report0["critic_sha256"] != report1["critic_sha256"]
    assert (
        control.diagnostic.records[0]["policy_version"]
        == (treatment.diagnostic.records[0]["policy_version"])
    )
    assert (
        control.diagnostic.records[0]["targets_sha256"]
        == (treatment.diagnostic.records[0]["targets_sha256"])
    )
    control_steps = [r for r in control.telemetry.stability if r["phase"] == "critic"]
    treated_steps = [r for r in treatment.telemetry.stability if r["phase"] == "critic"]
    assert len(control_steps) == len(treated_steps) == 8
    assert all("critic_penalty" not in row for row in control_steps)
    assert all(
        row["critic_objective"] == pytest.approx(row["mc_mse"] + row["critic_penalty"])
        for row in treated_steps
    )
    for run in (control, treatment):
        assert run.actor_updates == 2 and run.critic_updates == 8
        assert run.collector.trajectories == 8
        assert run.collector.transitions == 8 * 180
        assert run.diagnostic.collector.trajectories == 2
        assert run.diagnostic.collector.transitions == 2 * 180
        assert run.next_iteration == run.generation == 1
        assert run.boundary == "after_dual_and_D"
    assert control.collector.run_id != treatment.collector.run_id


def test_synthetic_beta_one_checkpoint_keeps_arm_identity_and_counters(config, tmp_path):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    settings = P3SyntheticSettings(
        critic_beta=1,
        seed=710081,
        iterations=2,
        hidden=4,
        n_a=2,
        n_q=2,
        n_b=2,
        actor_epochs=1,
        critic_epochs=4,
        minibatch=1,
    )
    source = SyntheticMarket(config)
    run = SyntheticExperiment(
        source,
        settings,
        condition="C10",
        run_id="p3-beta-one-checkpoint",
        journal=tmp_path / "journal",
        diagnostic=Diagnostic(tmp_path / "D", n=2),
    )
    assert run.run(pause_after=1)["boundary"] == "after_dual_and_D"
    manifest = save_checkpoint(run, tmp_path / "checkpoint")
    assert manifest["profile"] == "p3_synthetic_tests_only"
    assert manifest["settings"]["critic_beta"] == 1
    restored = load_checkpoint(tmp_path / "checkpoint", source, journal=tmp_path / "journal")
    assert restored.settings.critic_beta == 1
    assert restored.next_iteration == restored.generation == 1
    assert restored.actor_updates == 2 and restored.critic_updates == 8
    assert tree_hash(restored.actor_optimizer.state_dict()) == tree_hash(
        run.actor_optimizer.state_dict()
    )
    assert tree_hash(restored.critic_optimizer.state_dict()) == tree_hash(
        run.critic_optimizer.state_dict()
    )
    assert restored.run()["status"] == "passed"
    assert restored.actor_updates == 4 and restored.critic_updates == 16
