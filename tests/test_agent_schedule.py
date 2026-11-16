"""Small real optimizer updates on generated synthetic H3 paths only."""

from dataclasses import replace

import numpy as np
import pytest
import torch


def make(config, condition="C5", risk_enabled=True, **overrides):
    from btc_risk_rl.agents.synthetic import SyntheticMarket, SyntheticSettings
    from btc_risk_rl.agents.trainer import SyntheticExperiment

    settings = replace(SyntheticSettings(), **overrides)
    return SyntheticExperiment(
        SyntheticMarket(config),
        settings,
        condition=condition,
        risk_enabled=risk_enabled,
        run_id=f"test-{condition}",
    )


def test_exact_QAB_order_policy_versions_and_budget(config):
    from btc_risk_rl.agents.risk import dual_update, variational

    run = make(config)
    result = run.run()
    assert [e["event"] for e in result["events"]] == [
        "Q",
        "A",
        "actor",
        "critic",
        "Q",
        "B",
        "dual",
        "A",
        "actor",
        "critic",
        "Q",
        "B",
        "dual",
    ]
    assert result["trajectories"] == 3 + 2 * (2 + 3 + 3)
    assert result["transitions"] == 180 * result["trajectories"]
    q0, a0, q1, b1, a1, q2, b2 = run.batches
    assert q0[0].policy_version == a0[0].policy_version
    assert q1[0].policy_version == b1[0].policy_version == a1[0].policy_version
    assert q2[0].policy_version == b2[0].policy_version
    assert q0[0].policy_version != q1[0].policy_version
    identities = [t.realization for batch in run.batches for t in batch]
    assert len(set(identities)) == len(identities)
    previous = 0.0
    for i, audit in enumerate(result["audits"]):
        batch = (b1, b2)[i]
        losses = [-t.rewards.sum() for t in batch]
        assert audit["f_b"] == pytest.approx(variational(losses, 0.05, audit["eta"]))
        assert audit["lambda_before"] == previous
        assert audit["lambda_after"] == dual_update(
            previous, audit["f_b"], run.settings.bound, run.settings.dual_lr, enabled=True
        )
        assert audit["rho_b"] <= audit["f_b"] + 1e-14
        previous = audit["lambda_after"]
    assert previous > 0
    with pytest.raises(ValueError):
        run.run()


def test_fixed_coefficients_old_baseline_and_separate_critic(config):
    from btc_risk_rl.agents.models import fingerprint

    run = make(config, iterations=1)
    before = fingerprint(run.critic)
    result = run.run()
    fixed = run.fixed[0]
    a = run.batches[1]
    np.testing.assert_array_equal(fixed["old_logp"], np.stack([x.log_probs for x in a]))
    np.testing.assert_allclose(fixed["advantages"], fixed["returns"] - fixed["old_values"])
    np.testing.assert_array_equal(fixed["coefficients"], fixed["advantages"])  # lambda_0=0
    assert not fixed["returns"].flags.writeable
    events = result["events"]
    actor_event, critic_event = events[2], events[3]
    assert actor_event["critic_before"] == actor_event["critic_after"] == before
    assert critic_event["actor_before"] == critic_event["actor_after"]
    assert critic_event["critic_after"] != before
    assert actor_event["fixed_before"] == actor_event["fixed_after"] == critic_event["fixed_after"]


@pytest.mark.parametrize("condition", ["C5", "C10"])
def test_risk_off_reproduces_C0_parameters_and_optimizer_exactly(config, condition):
    baseline, off = make(config, "C0"), make(config, condition, risk_enabled=False)
    baseline.run()
    off.run()
    for left, right in [(baseline.actor, off.actor), (baseline.critic, off.critic)]:
        for x, y in zip(left.parameters(), right.parameters()):
            assert torch.equal(x, y)
    for opt_a, opt_b in [
        (baseline.actor_optimizer, off.actor_optimizer),
        (baseline.critic_optimizer, off.critic_optimizer),
    ]:
        sa, sb = opt_a.state_dict(), opt_b.state_dict()
        assert sa["param_groups"] == sb["param_groups"]
        for k in sa["state"]:
            for field in sa["state"][k]:
                assert torch.equal(sa["state"][k][field], sb["state"][k][field])
    assert baseline.multiplier == off.multiplier == 0


def test_C0_auxiliary_counts_do_not_change_learning_or_stopping(config):
    a = make(config, "C0")
    b = make(config, "C0", n_q=5, n_b=4)
    ra, rb = a.run(), b.run()
    for x, y in zip(a.actor.parameters(), b.actor.parameters()):
        assert torch.equal(x, y)
    for x, y in zip(a.critic.parameters(), b.critic.parameters()):
        assert torch.equal(x, y)
    assert len(ra["audits"]) == len(rb["audits"]) == 2
    assert ra["transitions"] != rb["transitions"]  # resources still counted


def test_failed_audit_invalidates_run_and_cannot_retry(config, monkeypatch):
    from btc_risk_rl.agents.trainer import RunAbort

    run = make(config, iterations=1)
    original = run.collector.collect

    def broken(policy, **kwargs):
        if kwargs["role"] == "B":
            raise ValueError("synthetic B failure")
        return original(policy, **kwargs)

    monkeypatch.setattr(run.collector, "collect", broken)
    with pytest.raises(RunAbort) as exc:
        run.run()
    assert run.failed and run.multiplier == 0
    assert exc.value.diagnostic["phase"] == "B"
    with pytest.raises(ValueError):
        run.run()


def test_second_actor_uses_previous_dual_and_eta_with_full_trajectory_loss(config):
    run = make(config, "C10")
    result = run.run()
    fixed = run.fixed[1]
    prior = result["audits"][0]
    assert fixed["multiplier"] == prior["lambda_after"] > 0
    assert fixed["eta"] == prior["eta"]
    # Independent forward sums rather than production reverse-cumsum helper.
    trajectories = run.batches[4]
    losses = np.array([-sum(t.rewards.tolist()) for t in trajectories])
    shortfall = np.array([max(loss - fixed["eta"], 0) for loss in losses])
    expected = fixed["advantages"] - prior["lambda_after"] / 0.1 * shortfall[:, None]
    np.testing.assert_allclose(fixed["coefficients"], expected, rtol=1e-13, atol=1e-14)
