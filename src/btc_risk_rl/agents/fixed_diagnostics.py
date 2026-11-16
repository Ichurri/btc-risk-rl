"""Observational full-A metrics; no optimizer/RNG changes, fixed targets throughout."""

from hashlib import sha256

import numpy as np
import torch

from btc_risk_rl.agents.models import clipped_objective, fingerprint


def stats(x):
    if not np.isfinite(x).all():
        raise ValueError("Nonfinite fixed-A diagnostic")
    result = dict(
        mean=float(np.mean(x)),
        std=float(np.std(x)),
        min=float(np.min(x)),
        max=float(np.max(x)),
        second_moment=float(np.mean(x * x)),
    )
    if not all(np.isfinite(v) for v in result.values()):
        raise ValueError("Nonfinite fixed-A summary")
    return result


def fixed_diagnostic(run, fixed, iteration, measurement):
    from btc_risk_rl.agents.trainer import tensor

    g = fixed["returns"]
    obs = fixed["observations"]
    with torch.no_grad():
        v = run.critic(tensor(obs)).numpy()
    mse = float(np.mean((g - v) ** 2))
    denominator = float(np.mean(g * g) + 1e-12)
    shortfall = np.maximum(-g[:, 0] - fixed["eta"], 0)
    penalty = fixed["advantages"] - fixed["coefficients"]
    h = sha256()
    for name in ("observations", "actions", "old_logp", "returns"):
        h.update(name.encode())
        h.update(fixed[name].tobytes())
    grad_norm = None
    if measurement == "before_actor":
        grad_norm = 0.0
        if np.any(penalty):
            grads = []
            for coeff in (fixed["coefficients"], fixed["advantages"]):
                loss = -clipped_objective(
                    run.actor.log_prob(tensor(obs), tensor(fixed["actions"])),
                    tensor(fixed["old_logp"]),
                    tensor(coeff),
                    run.settings.clip,
                )
                grads.append(
                    torch.cat(
                        [
                            t.flatten()
                            for t in torch.autograd.grad(loss, tuple(run.actor.parameters()))
                        ]
                    )
                )
            grad_norm = float(torch.linalg.vector_norm(grads[0] - grads[1]))
            if not np.isfinite(grad_norm):
                raise ValueError("Nonfinite risk gradient diagnostic")
    return dict(
        phase="fixed_A",
        iteration=iteration,
        measurement=measurement,
        scope="full_A_fixed_targets",
        batch_sha256=h.hexdigest(),
        actor_sha256=fingerprint(run.actor),
        critic_sha256=fingerprint(run.critic),
        mse=mse,
        denominator=denominator,
        relative_mse=mse / denominator,
        target=stats(g),
        prediction=stats(v),
        eta=fixed["eta"],
        lambda_used=fixed["multiplier"],
        alpha=fixed["alpha"],
        shortfall_count=int(np.count_nonzero(shortfall)),
        shortfall_max=float(shortfall.max()),
        risk_penalty_nonzero=int(np.count_nonzero(np.any(penalty != 0, axis=1))),
        coefficient_delta_max=float(np.max(np.abs(penalty))),
        initial_risk_gradient_norm=grad_norm,
    )
