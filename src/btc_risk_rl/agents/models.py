"""CPU float64 networks and an explicit logistic-normal density on (0,1)."""

from copy import deepcopy
from hashlib import sha256

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


def network(hidden, outputs, seed):
    if type(hidden) is not int or hidden < 1:
        raise ValueError("Positive hidden width required")
    # nn.Linear initialization otherwise consumes the process-global stream.
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        net = nn.Sequential(
            nn.Linear(13, hidden, dtype=torch.float64),
            nn.Tanh(),
            nn.Linear(hidden, outputs, dtype=torch.float64),
        )
    return net


def observations(x):
    if x.shape[-1] != 13 or x.dtype != torch.float64 or x.device.type != "cpu":
        raise ValueError("H3 observation requires 13 CPU float64 components")
    if not torch.isfinite(x).all():
        raise ValueError("Nonfinite observation")


class Actor(nn.Module):
    def __init__(self, *, hidden, seed):
        super().__init__()
        self.net = network(hidden, 2, seed)

    def parameters_at(self, x):
        observations(x)
        raw = self.net(x)
        mu, sigma = raw[..., 0], F.softplus(raw[..., 1]) + 1e-6
        if not torch.isfinite(mu).all() or not torch.isfinite(sigma).all():
            raise ValueError("Nonfinite distribution")
        return mu, sigma

    def log_prob(self, x, actions):
        mu, sigma = self.parameters_at(x)
        if actions.shape != mu.shape or not torch.isfinite(actions).all():
            raise ValueError("Invalid action shape or value")
        if not ((actions > 0) & (actions < 1)).all():
            raise ValueError("Logistic-normal action must lie strictly inside (0,1)")
        z = torch.log(actions) - torch.log1p(-actions)
        result = torch.distributions.Normal(mu, sigma).log_prob(z)
        result = result - torch.log(actions) - torch.log1p(-actions)
        if not torch.isfinite(result).all():
            raise ValueError("Nonfinite log density")
        return result

    @torch.no_grad()
    def sample(self, observation, rng):
        x = torch.as_tensor(np.array(observation, copy=True), dtype=torch.float64)
        mu, sigma = self.parameters_at(x)
        z = rng.normal(float(mu), float(sigma))
        action = torch.sigmoid(torch.tensor(z, dtype=torch.float64))
        # No clipping or selective resampling: log_prob rejects saturation.
        return float(action), float(self.log_prob(x, action))


class Critic(nn.Module):
    def __init__(self, *, hidden, seed):
        super().__init__()
        self.net = network(hidden, 1, seed)

    def forward(self, x):
        observations(x)
        value = self.net(x).squeeze(-1)
        if not torch.isfinite(value).all():
            raise ValueError("Nonfinite critic")
        return value


def fingerprint(model):
    h = sha256()
    for name, value in model.state_dict().items():
        h.update(name.encode())
        h.update(value.detach().cpu().numpy().tobytes())
    return h.hexdigest()


class FrozenPolicy:
    def __init__(self, actor, *, generation):
        self._actor = deepcopy(actor).eval().requires_grad_(False)
        self.digest = fingerprint(self._actor)
        self.version = f"policy-{generation}:{self.digest}"

    def check(self):
        if fingerprint(self._actor) != self.digest:
            raise ValueError("Frozen policy changed")

    def sample(self, observation, rng):
        return self._actor.sample(observation, rng)


def clipped_objective(logp, old_logp, coefficients, clip):
    if logp.ndim != 2 or logp.shape[1] != 180:
        raise ValueError("Whole trajectories required")
    if old_logp.shape != logp.shape or coefficients.shape != logp.shape or not 0 < clip < 1:
        raise ValueError("Invalid surrogate inputs")
    ratio = torch.exp(logp - old_logp)
    objective = (
        torch.minimum(ratio * coefficients, torch.clamp(ratio, 1 - clip, 1 + clip) * coefficients)
        .sum(1)
        .mean()
    )
    if not torch.isfinite(objective):
        raise ValueError("Nonfinite PPO objective")
    return objective
