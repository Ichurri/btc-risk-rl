"""ADR-002 Q/A/B schedule; execution is restricted to small synthetic tests."""

from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256

import numpy as np
import torch

from btc_risk_rl.agents.collector import Collector, immutable
from btc_risk_rl.agents.models import Actor, Critic, FrozenPolicy, clipped_objective, fingerprint
from btc_risk_rl.agents.risk import dual_update, empirical_tail, monte_carlo, variational
from btc_risk_rl.agents.synthetic import SyntheticSettings


def fixed_digest(fixed):
    h = sha256()
    for key, value in fixed.items():
        h.update(key.encode())
        h.update(value.tobytes() if isinstance(value, np.ndarray) else repr(value).encode())
    return h.hexdigest()


def tensor(x):
    return torch.tensor(np.array(x, copy=True), dtype=torch.float64)


class RunAbort(RuntimeError):
    def __init__(self, diagnostic):
        self.diagnostic = diagnostic
        super().__init__(f"Synthetic run invalidated: {diagnostic}")


class SyntheticExperiment:
    def __init__(self, source, settings, *, condition, risk_enabled=True, run_id):
        if type(settings) is not SyntheticSettings or condition not in {"C0", "C5", "C10"}:
            raise ValueError("Explicit synthetic settings and known condition required")
        self.collector = Collector(source, seed=settings.seed, run_id=run_id)
        self.settings, self.condition = settings, condition
        self.enabled = condition != "C0" and risk_enabled
        self.alpha = 0.1 if condition == "C10" else 0.05  # C0 diagnostics only
        self.actor = Actor(hidden=settings.hidden, seed=settings.seed)
        self.critic = Critic(hidden=settings.hidden, seed=settings.seed + 1)
        self.actor_optimizer = torch.optim.Adam(
            self.actor.parameters(),
            lr=settings.actor_lr,
            betas=(0.9, 0.999),
            eps=1e-8,
            weight_decay=0,
        )
        self.critic_optimizer = torch.optim.Adam(
            self.critic.parameters(),
            lr=settings.critic_lr,
            betas=(0.9, 0.999),
            eps=1e-8,
            weight_decay=0,
        )
        self.multiplier = 0.0
        self.eta = None
        self.started = self.failed = False
        self.batches, self.fixed, self.events, self.audits = [], [], [], []
        self.phase = "not_started"
        self.actor_updates = self.critic_updates = 0

    def _collect(self, policy, role, iteration, count):
        self.phase = role
        batch = self.collector.collect(
            policy,
            role=role,
            iteration=iteration,
            count=count,
            fragment_steps=self.settings.fragment_steps,
        )
        self.batches.append(batch)
        self.events.append(
            dict(
                event=role,
                iteration=iteration,
                policy_version=policy.version,
                realizations=[t.realization for t in batch],
                route_ids=[t.route_id for t in batch],
                count=count,
            )
        )
        return batch

    @staticmethod
    def _losses(batch):
        return -monte_carlo(np.stack([t.rewards for t in batch]))[:, 0]

    def _targets(self, batch, baseline):
        obs = np.stack([t.observations[:-1] for t in batch])
        g = monte_carlo(np.stack([t.rewards for t in batch]))
        with torch.no_grad():
            values = baseline(tensor(obs)).numpy()
        advantage = g - values
        # Copy exactly in risk-off mode: do not even operate on shortfalls.
        d = advantage.copy()
        if self.enabled and self.multiplier != 0:
            d -= self.multiplier / self.alpha * np.maximum(-g[:, 0] - self.eta, 0)[:, None]
        fixed = dict(
            observations=obs,
            actions=np.stack([t.actions for t in batch]),
            old_logp=np.stack([t.log_probs for t in batch]),
            returns=g,
            old_values=values,
            advantages=advantage,
            coefficients=d,
        )
        fixed = {k: immutable(v) for k, v in fixed.items()}
        fixed.update(
            eta=self.eta, multiplier=self.multiplier, alpha=self.alpha, bound=self.settings.bound
        )
        self.fixed.append(fixed)
        return fixed

    def _minibatches(self, n, epochs, iteration, phase):
        rng = np.random.default_rng(
            np.random.SeedSequence([self.settings.seed, 100, iteration, phase])
        )
        for _ in range(epochs):
            order = rng.permutation(n)
            for start in range(0, n, self.settings.minibatch):
                yield order[start : start + self.settings.minibatch]

    @staticmethod
    def _optimizer_step(loss, model, optimizer):
        if not torch.isfinite(loss):
            raise ValueError("Nonfinite loss")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        if any(p.grad is None or not torch.isfinite(p.grad).all() for p in model.parameters()):
            raise ValueError("Nonfinite/missing gradient")
        optimizer.step()
        if any(not torch.isfinite(p).all() for p in model.parameters()):
            raise ValueError("Nonfinite updated parameters")

    def _update(self, fixed, iteration):
        s = self.settings
        before = fixed_digest(fixed)
        critic_before = fingerprint(self.critic)
        actor_before = fingerprint(self.actor)
        self.phase = "actor"
        for ids in self._minibatches(len(fixed["returns"]), s.actor_epochs, iteration, 0):
            lp = self.actor.log_prob(
                tensor(fixed["observations"][ids]), tensor(fixed["actions"][ids])
            )
            loss = -clipped_objective(
                lp, tensor(fixed["old_logp"][ids]), tensor(fixed["coefficients"][ids]), s.clip
            )
            self._optimizer_step(loss, self.actor, self.actor_optimizer)
            self.actor_updates += 1
        if fingerprint(self.critic) != critic_before or fixed_digest(fixed) != before:
            raise ValueError("Actor update altered critic or frozen coefficients")
        self.events.append(
            dict(
                event="actor",
                iteration=iteration,
                eta_used=fixed["eta"],
                lambda_used=fixed["multiplier"],
                alpha=fixed["alpha"],
                bound=fixed["bound"],
                actor_before=actor_before,
                actor_after=fingerprint(self.actor),
                critic_before=critic_before,
                critic_after=fingerprint(self.critic),
                fixed_before=before,
                fixed_after=fixed_digest(fixed),
            )
        )
        # Policy is frozen BEFORE critic updates. No shared parameters.
        policy = FrozenPolicy(self.actor, generation=iteration + 1)
        actor_before = fingerprint(self.actor)
        self.phase = "critic"
        for ids in self._minibatches(len(fixed["returns"]), s.critic_epochs, iteration, 1):
            prediction = self.critic(tensor(fixed["observations"][ids]))
            loss = ((prediction - tensor(fixed["returns"][ids])) ** 2).mean()
            self._optimizer_step(loss, self.critic, self.critic_optimizer)
            self.critic_updates += 1
        if fingerprint(self.actor) != actor_before or fixed_digest(fixed) != before:
            raise ValueError("Critic update altered actor or frozen targets")
        policy.check()
        self.events.append(
            dict(
                event="critic",
                iteration=iteration,
                actor_before=actor_before,
                actor_after=fingerprint(self.actor),
                critic_after=fingerprint(self.critic),
                fixed_after=fixed_digest(fixed),
            )
        )
        return policy

    def run(self):
        if self.started:
            raise ValueError("Run already started; replay/retry not allowed")
        self.started = True
        s = self.settings
        iteration = 0
        try:
            policy = FrozenPolicy(self.actor, generation=0)
            q = self._collect(policy, "Q", 0, s.n_q)
            initial_q_tail = empirical_tail(self._losses(q), self.alpha)
            self.eta = initial_q_tail["eta"]
            for iteration in range(s.iterations):
                baseline = deepcopy(self.critic).eval().requires_grad_(False)
                a = self._collect(policy, "A", iteration, s.n_a)
                fixed = self._targets(a, baseline)
                policy = self._update(fixed, iteration)
                q = self._collect(policy, "Q", iteration + 1, s.n_q)
                tail_q = empirical_tail(self._losses(q), self.alpha)
                self.eta = tail_q["eta"]
                b = self._collect(policy, "B", iteration + 1, s.n_b)
                losses = self._losses(b)
                tail_b = empirical_tail(losses, self.alpha)
                f_b = variational(losses, self.alpha, self.eta)
                previous = self.multiplier
                self.phase = "dual"
                self.multiplier = dual_update(
                    previous, f_b, s.bound, s.dual_lr, enabled=self.enabled
                )
                audit = dict(
                    iteration=iteration + 1,
                    policy_version=policy.version,
                    eta=self.eta,
                    f_b=f_b,
                    rho_b=tail_b["rho"],
                    rho_q=tail_q["rho"],
                    f_violation=f_b - s.bound,
                    empirical_violation=tail_b["rho"] - s.bound,
                    lambda_before=previous,
                    lambda_after=self.multiplier,
                    q_tail=tail_q,
                    b_tail=tail_b,
                    interpretation="empirical_diagnostic_not_population_certificate",
                )
                self.audits.append(audit)
                self.events.append(
                    dict(
                        event="dual",
                        iteration=iteration + 1,
                        lambda_before=previous,
                        lambda_after=self.multiplier,
                    )
                )
        except Exception as exc:
            self.failed = True
            self.collector.failed = True
            raise RunAbort(
                dict(
                    phase=self.phase,
                    iteration=iteration,
                    error=f"{type(exc).__name__}: {exc}",
                    batch=getattr(exc, "diagnostic", None),
                    transitions_consumed=self.collector.transitions,
                    action="discard_failed_run_no_selective_retry",
                )
            ) from exc
        expected = s.n_q + s.iterations * (s.n_a + s.n_q + s.n_b)
        if self.collector.trajectories != expected or self.collector.transitions != 180 * expected:
            self.failed = True
            raise RunAbort({"error": "Resource accounting mismatch"})
        return dict(
            status="passed",
            purpose=s.purpose,
            condition=self.condition,
            risk_enabled=self.enabled,
            initial_q_tail=initial_q_tail,
            settings=asdict(s),
            events=self.events,
            audits=self.audits,
            trajectories=self.collector.trajectories,
            transitions=self.collector.transitions,
            actor_updates=self.actor_updates,
            critic_updates=self.critic_updates,
            actor_sha256=fingerprint(self.actor),
            critic_sha256=fingerprint(self.critic),
            market_training_executed=False,
            final_test_accessed=False,
        )
