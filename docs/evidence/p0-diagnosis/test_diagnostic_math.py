"""Analytical diagnostic checks, no optimizer and no market input."""

import numpy as np
import torch

from btc_risk_rl.agents.models import clipped_objective


def test_positive_dual_without_shortfall_has_identical_coefficients_and_gradient():
    advantages = torch.ones((2, 180), dtype=torch.float64)
    loss = torch.tensor([0.1, 0.2], dtype=torch.float64)
    eta, multiplier, alpha = 0.25, 0.3, 0.05
    penalty = multiplier / alpha * torch.clamp(loss - eta, min=0)
    assert torch.equal(penalty, torch.zeros_like(penalty))
    x = torch.zeros_like(advantages, requires_grad=True)
    off = -clipped_objective(x, torch.zeros_like(x), advantages, 0.2)
    on = -clipped_objective(x, torch.zeros_like(x), advantages - penalty[:, None], 0.2)
    assert torch.equal(torch.autograd.grad(off, x)[0], torch.autograd.grad(on, x)[0])


def test_risk_gradient_sign_and_temporal_sum_analytical():
    # At ratio=1, loss derivative changes by +lambda/alpha*shortfall/N per step.
    advantages = torch.ones((2, 180), dtype=torch.float64)
    penalty = torch.tensor([0.0, 0.6], dtype=torch.float64)
    x = torch.zeros_like(advantages, requires_grad=True)
    off = -clipped_objective(x, torch.zeros_like(x), advantages, 0.2)
    on = -clipped_objective(x, torch.zeros_like(x), advantages - penalty[:, None], 0.2)
    difference = torch.autograd.grad(on, x)[0] - torch.autograd.grad(off, x)[0]
    torch.testing.assert_close(difference, penalty[:, None].expand_as(x) / 2, rtol=0, atol=1e-16)
    assert np.isclose(difference.sum().item(), 54)


def test_ratio_can_warn_despite_absolute_mse_improving():
    target = np.array([0.1, -0.1])
    before, after = np.array([0.4, 0.4]), np.array([0.2, 0.2])
    denominator = np.mean(target**2) + 1e-12
    mse_before = np.mean((target - before) ** 2)
    mse_after = np.mean((target - after) ** 2)
    assert mse_after < mse_before and mse_after / denominator > 1
