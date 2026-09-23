"""Analytical, synthetic-only H4 checks."""

import math

import numpy as np
import pytest


def test_mc_is_full_undiscounted_and_rejects_fragment():
    from btc_risk_rl.agents.risk import monte_carlo

    r = np.zeros((2, 180))
    r[0, :3] = [1, -2, 3]
    r[0, -1] = 4
    g = monte_carlo(r)
    np.testing.assert_array_equal(g[0, :4], [6, 5, 7, 4])
    assert g[0, -1] == 4 and not g[1].any()
    with pytest.raises(ValueError):
        monte_carlo(r[:, :60])


def test_fractional_tied_tail_and_fixed_eta_are_distinct():
    from btc_risk_rl.agents.risk import empirical_tail, variational

    x = np.array([0.0, 1.0, 1.0, 3.0])
    tail = empirical_tail(x, 0.5)
    assert tail["eta"] == 1 and tail["rho"] == 2 and tail["ties"] == 2
    np.testing.assert_array_equal(tail["weights"], [0, 0.5, 0.5, 1])
    assert variational(x, 0.5, tail["eta"]) == tail["rho"]
    assert variational(x, 0.5, 0) == 2.5
    small = empirical_tail(x, 0.1)
    assert small["rho"] == pytest.approx(3) and small["mass"] == 0.4
    assert sum(small["weights"]) == pytest.approx(0.4)


def test_quantile_uses_lower_endpoint_and_no_rounded_ties():
    from btc_risk_rl.agents.risk import empirical_tail

    t = empirical_tail(np.arange(20.0), 0.05)
    assert t["eta"] == 18 and t["rho"] == 19
    x = np.array([1.0, np.nextafter(1.0, 2.0), 2.0])
    assert empirical_tail(x, 0.5)["ties"] == 1


def test_dual_projection_and_sign():
    from btc_risk_rl.agents.risk import dual_update

    assert dual_update(0.2, 0.5, 0.1, 0.3, enabled=True) == pytest.approx(0.32)
    assert dual_update(0.1, -0.5, 0.1, 0.3, enabled=True) == 0
    assert dual_update(0.2, 0.5, 0.1, 0.3, enabled=False) == 0


def test_logistic_normal_density_and_gradient():
    import torch

    from btc_risk_rl.agents.models import Actor

    actor = Actor(hidden=4, seed=1)
    with torch.no_grad():
        for p in actor.parameters():
            p.zero_()
        actor.net[-1].bias[1] = math.log(math.expm1(1 - 1e-6))
    x = torch.zeros((3, 13), dtype=torch.float64)
    a = torch.tensor([0.2, 0.5, 0.8], dtype=torch.float64)
    lp = actor.log_prob(x, a)
    z = np.log(a.numpy() / (1 - a.numpy()))
    expected = -0.5 * z * z - 0.5 * math.log(2 * math.pi) - np.log(a.numpy() * (1 - a.numpy()))
    np.testing.assert_allclose(lp.detach(), expected, rtol=1e-14)
    lp.sum().backward()
    assert all(torch.isfinite(p.grad).all() for p in actor.parameters())
    rng = np.random.default_rng(7)
    action, logp = actor.sample(np.zeros(13), rng)
    assert 0 < action < 1
    assert (
        logp
        == actor.log_prob(
            torch.zeros(13, dtype=torch.float64), torch.tensor(action, dtype=torch.float64)
        ).item()
    )
    for a_bad in [0.0, 1.0, float("nan")]:
        with pytest.raises(ValueError):
            actor.log_prob(x[0], torch.tensor(a_bad, dtype=torch.float64))


def test_snapshot_and_initialization_do_not_change_global_rng():
    import torch

    from btc_risk_rl.agents.models import Actor, Critic, FrozenPolicy, fingerprint

    state = torch.random.get_rng_state().clone()
    a, c = Actor(hidden=4, seed=1), Critic(hidden=4, seed=2)
    assert torch.equal(state, torch.random.get_rng_state())
    assert not ({p.data_ptr() for p in a.parameters()} & {p.data_ptr() for p in c.parameters()})
    frozen = FrozenPolicy(a, generation=0)
    before = frozen.version
    with torch.no_grad():
        next(a.parameters()).add_(1)
    assert frozen.version == before and frozen.digest != fingerprint(a)
    frozen.check()


def test_ppo_surrogate_uses_trajectory_mean_and_temporal_sum():
    import torch

    from btc_risk_rl.agents.models import clipped_objective

    old = torch.zeros((2, 180), dtype=torch.float64)
    ratios = torch.ones_like(old)
    ratios[:, :2] = torch.tensor([1.5, 0.5])
    coeff = torch.zeros_like(old)
    coeff[:, :2] = torch.tensor([2.0, -3.0])
    # min(1.5*2,1.2*2) + min(.5*-3,.8*-3) = 0
    assert clipped_objective(ratios.log(), old, coeff, 0.2).item() == pytest.approx(0)
    coeff[:] = 1
    assert clipped_objective(old, old, coeff, 0.2).item() == 180


def test_saturated_actions_abort_without_clipping_or_resampling():
    import torch

    from btc_risk_rl.agents.models import Actor

    actor = Actor(hidden=2, seed=2)
    with torch.no_grad():
        for p in actor.parameters():
            p.zero_()
        actor.net[-1].bias[0] = 1000
    rng = np.random.default_rng(1)
    with pytest.raises(ValueError, match="strictly inside"):
        actor.sample(np.zeros(13), rng)


def test_log_density_score_matches_independent_finite_difference():
    import torch

    from btc_risk_rl.agents.models import Actor

    actor = Actor(hidden=2, seed=9)
    with torch.no_grad():
        for p in actor.parameters():
            p.zero_()
    x = torch.zeros(13, dtype=torch.float64)
    a = torch.tensor(0.7, dtype=torch.float64)
    actor.log_prob(x, a).backward()
    sigma = math.log(2) + 1e-6
    z = math.log(0.7 / 0.3)

    def oracle(mu):
        return (
            -0.5 * ((z - mu) / sigma) ** 2
            - math.log(sigma * math.sqrt(2 * math.pi))
            - math.log(0.7 * 0.3)
        )

    numerical = (oracle(1e-5) - oracle(-1e-5)) / 2e-5
    assert actor.net[-1].bias.grad[0].item() == pytest.approx(numerical, rel=1e-9)


@pytest.mark.parametrize("losses,alpha", [([], 0.1), ([float("nan")], 0.1), ([1], 0), ([1], 1)])
def test_invalid_tail_inputs_are_not_silently_repaired(losses, alpha):
    from btc_risk_rl.agents.risk import empirical_tail

    with pytest.raises(ValueError):
        empirical_tail(losses, alpha)
