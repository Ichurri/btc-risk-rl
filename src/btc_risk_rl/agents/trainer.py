"""Single ADR-002 Q/A/B schedule for synthetic tests and supervised authorized P0."""

from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256

import numpy as np
import torch

from btc_risk_rl.agents.collector import Collector, immutable
from btc_risk_rl.agents.journal import RunJournal
from btc_risk_rl.agents.models import Actor, Critic, FrozenPolicy, clipped_objective, fingerprint
from btc_risk_rl.agents.risk import dual_update, empirical_tail, monte_carlo, variational
from btc_risk_rl.agents.synthetic import SyntheticMarket, SyntheticSettings
from btc_risk_rl.agents.telemetry import Telemetry


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
        super().__init__(f"Run invalidated: {diagnostic}")


class SyntheticExperiment:
    def __init__(
        self, source, settings, *, condition, risk_enabled=True, run_id, journal=None, permit=None
    ):
        from btc_risk_rl.agents.market_source import TrainingMarket
        from btc_risk_rl.pilots.protocol import P0Settings, Permit

        if condition not in {"C0", "C5", "C10"}:
            raise ValueError("Known condition required")
        if type(source) is TrainingMarket:
            if (
                type(settings) is not P0Settings
                or type(permit) is not Permit
                or (condition != "C0" and not risk_enabled)
            ):
                raise PermissionError("Market optimization requires authorized P0 supervisor lease")
            permit.validate(settings, condition, run_id)
        elif type(source) is not SyntheticMarket or type(settings) is not SyntheticSettings:
            raise ValueError("Explicit synthetic settings and known source required")
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
        self.next_iteration = self.generation = 0
        self.boundary = "before_q0"
        self.initial_q_tail = None
        self.status = "new"
        self.telemetry = Telemetry()
        self.budget = None
        self.journal = RunJournal(journal, create=True) if journal is not None else None

    def _collect(self, policy, role, iteration, count):
        self.phase = role
        with self.telemetry.measure(role, iteration, self.collector, self):
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
        with torch.no_grad():
            recomputed = self.actor.log_prob(
                tensor(obs), tensor(np.stack([t.actions for t in batch]))
            )
        error = float(np.max(np.abs(recomputed.numpy() - np.stack([t.log_probs for t in batch]))))
        if error > 1e-10:
            raise ValueError("Frozen log-probabilities inconsistent")
        self.telemetry.stability.append(
            dict(
                phase="targets",
                iteration=self.next_iteration,
                old_logprob_max_error=error,
                critic_mc_mse_before=float(np.mean((g - values) ** 2)),
                critic_relative_mse=float(np.mean((g - values) ** 2) / (np.mean(g**2) + 1e-12)),
            )
        )
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
        grad_norm = float(
            torch.sqrt(sum(torch.sum(p.grad.detach() ** 2) for p in model.parameters()))
        )
        optimizer.step()
        if any(not torch.isfinite(p).all() for p in model.parameters()):
            raise ValueError("Nonfinite updated parameters")
        return grad_norm

    def _update(self, fixed, iteration):
        s = self.settings
        before = fixed_digest(fixed)
        critic_before = fingerprint(self.critic)
        actor_before = fingerprint(self.actor)
        self.phase = "actor"
        with self.telemetry.measure("actor", iteration, self.collector, self):
            for ids in self._minibatches(len(fixed["returns"]), s.actor_epochs, iteration, 0):
                lp = self.actor.log_prob(
                    tensor(fixed["observations"][ids]), tensor(fixed["actions"][ids])
                )
                loss = -clipped_objective(
                    lp, tensor(fixed["old_logp"][ids]), tensor(fixed["coefficients"][ids]), s.clip
                )
                grad_norm = self._optimizer_step(loss, self.actor, self.actor_optimizer)
                ratio = torch.exp(lp.detach() - tensor(fixed["old_logp"][ids]))
                coeff = tensor(fixed["coefficients"][ids])
                active = ((ratio > 1 + s.clip) & (coeff > 0)) | ((ratio < 1 - s.clip) & (coeff < 0))
                self.telemetry.stability.append(
                    dict(
                        phase="actor",
                        iteration=iteration,
                        loss=float(loss.detach()),
                        gradient_norm=grad_norm,
                        ratio_min=float(ratio.min()),
                        ratio_max=float(ratio.max()),
                        ratio_clip_fraction=float(
                            ((ratio < 1 - s.clip) | (ratio > 1 + s.clip)).double().mean()
                        ),
                        surrogate_clip_fraction=float(active.double().mean()),
                    )
                )
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
        with self.telemetry.measure("critic", iteration, self.collector, self):
            for ids in self._minibatches(len(fixed["returns"]), s.critic_epochs, iteration, 1):
                prediction = self.critic(tensor(fixed["observations"][ids]))
                loss = ((prediction - tensor(fixed["returns"][ids])) ** 2).mean()
                grad_norm = self._optimizer_step(loss, self.critic, self.critic_optimizer)
                self.telemetry.stability.append(
                    dict(
                        phase="critic",
                        iteration=iteration,
                        mc_mse=float(loss.detach()),
                        relative_mc_mse=float(loss.detach())
                        / (float(np.mean(fixed["returns"][ids] ** 2)) + 1e-12),
                        gradient_norm=grad_norm,
                    )
                )
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

    def _journal(self, status):
        if self.journal is not None:
            self.journal.append(
                status=status,
                next_iteration=self.next_iteration,
                boundary=self.boundary,
                run_id=self.collector.run_id,
            )

    def run(self, *, pause_after=None, budget=None):
        if self.started or self.failed:
            raise ValueError("Run already started; replay/retry not allowed")
        if pause_after is not None and (
            type(pause_after) is not int
            or not self.next_iteration <= pause_after <= self.settings.iterations
        ):
            raise ValueError("Invalid planned pause boundary")
        if self.budget is not None and budget is not None and budget is not self.budget:
            raise ValueError("Cannot reset a restored budget")
        self.started = True
        self.budget = budget if budget is not None else self.budget
        s = self.settings
        iteration = self.next_iteration
        try:
            policy = FrozenPolicy(self.actor, generation=self.generation)
            if self.initial_q_tail is None:
                if self.budget and not self.budget.can_start("q0", self.collector.source.profile):
                    self.status = "paused"
                    return self._report()
                self.boundary = "in_unit"
                self._journal("running")
                q = self._collect(policy, "Q", 0, s.n_q)
                with self.telemetry.measure("eta", 0, self.collector, self):
                    self.initial_q_tail = empirical_tail(self._losses(q), self.alpha)
                    self.eta = self.initial_q_tail["eta"]
                if self.budget:
                    self.budget.check_reserve()
                self.boundary = "after_q0"
                self._journal("ready")
            for iteration in range(self.next_iteration, s.iterations):
                if pause_after == iteration or (
                    self.budget
                    and not self.budget.can_start("iteration", self.collector.source.profile)
                ):
                    self.status = "paused"
                    self._journal("ready")
                    return self._report()
                self.boundary = "in_unit"
                self._journal("running")
                baseline = deepcopy(self.critic).eval().requires_grad_(False)
                a = self._collect(policy, "A", iteration, s.n_a)
                fixed = self._targets(a, baseline)
                policy = self._update(fixed, iteration)
                q = self._collect(policy, "Q", iteration + 1, s.n_q)
                with self.telemetry.measure("eta", iteration + 1, self.collector, self):
                    tail_q = empirical_tail(self._losses(q), self.alpha)
                    self.eta = tail_q["eta"]
                b = self._collect(policy, "B", iteration + 1, s.n_b)
                with self.telemetry.measure("audit_dual", iteration + 1, self.collector, self):
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
                self.next_iteration = self.generation = iteration + 1
                if self.budget:
                    self.budget.check_reserve()
                self.boundary = "after_dual"
                self._journal("ready")
        except BaseException as exc:
            self.failed = True
            self.collector.failed = True
            self.status = "failed"
            self._journal("failed")
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
            self._journal("failed")
            raise RunAbort({"error": "Resource accounting mismatch"})
        self.status = "passed"
        self._journal("completed")
        return self._report()

    def _report(self):
        return dict(
            status=self.status,
            purpose=self.settings.purpose,
            condition=self.condition,
            risk_enabled=self.enabled,
            initial_q_tail=self.initial_q_tail,
            settings=asdict(self.settings),
            events=self.events,
            audits=self.audits,
            trajectories=self.collector.trajectories,
            transitions=self.collector.transitions,
            actor_updates=self.actor_updates,
            critic_updates=self.critic_updates,
            actor_sha256=fingerprint(self.actor),
            critic_sha256=fingerprint(self.critic),
            next_iteration=self.next_iteration,
            boundary=self.boundary,
            telemetry=self.telemetry.records,
            stability=self.telemetry.stability,
            collection_diagnostics=self.collector.diagnostics,
            budget=self.budget.snapshot() if self.budget else None,
            market_training_executed=self.settings.purpose == "authorized_p0_only",
            final_test_accessed=False,
        )
