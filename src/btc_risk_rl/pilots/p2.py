"""P2 diagnostic D for synthetic fixtures and guarded accepted training."""

import json
import os
import random
import time
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import ClassVar

import numpy as np
import torch

from btc_risk_rl.agents.collector import (
    ARRAYS,
    Collector,
    assemble,
    load_trajectory,
    save_trajectory,
)
from btc_risk_rl.agents.models import clipped_objective, fingerprint
from btc_risk_rl.agents.risk import monte_carlo
from btc_risk_rl.agents.synthetic import SyntheticMarket, SyntheticSettings
from btc_risk_rl.pilots.p2_metrics import full_metric, overlap, warning_rates


@dataclass(frozen=True)
class P2SyntheticSettings(SyntheticSettings):
    purpose: str = "p2_synthetic_tests_only"
    expected_purpose: ClassVar[str] = "p2_synthetic_tests_only"
    max_iterations: ClassVar[int] = 10
    critic_epochs: int = 4
    bound: float = 0.10536051565782628


def file_hash(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def tree_hash(value):
    h = sha256()

    def visit(x):
        if isinstance(x, torch.Tensor):
            x = x.detach().cpu().numpy()
        if isinstance(x, np.ndarray):
            h.update(str((x.dtype.str, x.shape)).encode())
            h.update(x.tobytes())
        elif isinstance(x, dict):
            for k in sorted(x, key=str):
                visit(k)
                visit(x[k])
        elif isinstance(x, (tuple, list)):
            for v in x:
                visit(v)
        else:
            h.update(repr(x).encode())

    visit(value)
    return h.hexdigest()


def learning_hash(run):
    return tree_hash(
        [
            run.actor.state_dict(),
            run.critic.state_dict(),
            run.actor_optimizer.state_dict(),
            run.critic_optimizer.state_dict(),
            [p.grad for m in (run.actor, run.critic) for p in m.parameters()],
            run.eta,
            run.multiplier,
            run.events,
            run.audits,
            sorted(run.collector.used),
            run.collector.trajectories,
            run.collector.transitions,
            torch.random.get_rng_state(),
            np.random.get_state(),
            random.getstate(),
        ]
    )


def risk_snapshot(policy, fixed, clip):
    """Full A gradients at pi_k, on a detached copy; never an optimizer step."""
    from btc_risk_rl.agents.trainer import tensor

    actor = deepcopy(policy._actor).requires_grad_(True)
    gradients = []
    for coeff in (fixed["coefficients"], fixed["advantages"]):
        loss = -clipped_objective(
            actor.log_prob(tensor(fixed["observations"]), tensor(fixed["actions"])),
            tensor(fixed["old_logp"]),
            tensor(coeff),
            clip,
        )
        gradients.append(
            torch.cat([g.flatten() for g in torch.autograd.grad(loss, tuple(actor.parameters()))])
        )
    total = float(torch.linalg.vector_norm(gradients[0]))
    risk = float(torch.linalg.vector_norm(gradients[0] - gradients[1]))
    if not np.isfinite([total, risk]).all():
        raise ValueError("Nonfinite full A gradient diagnostic")
    shortfall = np.maximum(-fixed["returns"][:, 0] - fixed["eta"], 0)
    changed = np.any(fixed["coefficients"] != fixed["advantages"], axis=1)
    return dict(
        eta_used=fixed["eta"],
        lambda_used=fixed["multiplier"],
        initial_total_gradient_norm=total,
        initial_risk_gradient_norm=risk,
        shortfalls=dict(numerator=int(np.count_nonzero(shortfall)), denominator=len(shortfall)),
        altered_coefficients=dict(
            numerator=int(np.count_nonzero(changed)), denominator=len(changed)
        ),
        shortfall_max=float(shortfall.max()),
        shortfall_mean=float(shortfall.mean()),
    )


def footprints(batch):
    # UTC transition start uniquely identifies a time within disjoint H1 segments.
    # No interval is filled: only observed starts from fully assembled trajectories.
    return [
        dict(start=str(int(t.times[0])), times=[str(int(x)) for x in t.times[:-1]]) for t in batch
    ]


class Diagnostic:
    def __init__(self, root, *, n=64):
        if type(n) is not int or not 1 <= n <= 64:
            raise ValueError("Diagnostic size must be 1..64 (small fixtures are synthetic only)")
        self.root = Path(root).resolve()
        self.n = n
        self.records, self.learning, self.d_footprints = [], [], []
        self.collector = None
        self.a = []

    def bind(self, source, seed, run_id, permit=None):
        from btc_risk_rl.agents.market_source import TrainingMarket
        if type(source) is SyntheticMarket:
            if permit is not None:
                raise PermissionError("Synthetic diagnostic does not use a market permit")
        elif type(source) is TrainingMarket:
            from btc_risk_rl.pilots.p2_market import P2MarketPermit
            from btc_risk_rl.pilots.p2r_market import P2RMarketPermit
            from btc_risk_rl.pilots.p3_market import P3MarketPermit
            if type(permit) not in {P2MarketPermit, P2RMarketPermit, P3MarketPermit}:
                raise PermissionError("P2 market diagnostic requires registered permit")
            permit.validate_d(source, seed, run_id)
        else:
            raise PermissionError("Unknown P2 diagnostic source")
        self.collector = Collector(source, seed=seed, run_id=run_id,
                                   diagnostic_permit=permit)

    def observe(self, batch, role, iteration):
        entry = dict(role=role, iteration=iteration, paths=footprints(batch))
        self.learning.append(entry)
        if role == "A":
            self.a = entry["paths"]

    def finish(self, run, policy, baseline, fixed, iteration):
        from btc_risk_rl.agents.trainer import tensor

        if iteration != len(self.records):
            raise ValueError("Diagnostic replay or missing prior D")
        before = learning_hash(run)
        policy.check()
        pre_hash, post_hash = fingerprint(baseline), fingerprint(run.critic)
        started = time.monotonic()

        def phase(name):
            marker = getattr(self, "phase_marker", None)
            if marker is not None:
                temp = marker.with_suffix(".tmp")
                temp.write_text(json.dumps(dict(phase=name, started_monotonic=started)))
                os.replace(temp, marker)

        phase("D")
        with run.telemetry.measure("D", iteration, self.collector, run):
            run.phase = "D"

            def deadline():
                if getattr(self, "progress", None):
                    self.progress()
                if time.monotonic() - started > 900:
                    raise TimeoutError("P2 diagnostic subcap exceeded")

            self.collector.progress = deadline
            fragments = self.root / "fragments"
            fragments.mkdir(parents=True, exist_ok=True)

            def persist(path, arrays, metadata):
                with path.open("xb") as stream:
                    np.savez(
                        stream,
                        metadata=np.frombuffer(json.dumps(metadata).encode(), dtype=np.uint8),
                        **{k: np.asarray(v) for k, v in arrays.items()},
                    )
                    stream.flush()
                    os.fsync(stream.fileno())

            def fragment_sink(f):
                replica = f.realization.rsplit("/", 1)[1]
                persist(
                    fragments / f"{iteration}-{replica}-{f.start}.npz",
                    {k: getattr(f, k) for k in ARRAYS},
                    dict(
                        realization=f.realization,
                        route_id=f.route_id,
                        policy_version=f.policy_version,
                        start=f.start,
                        status="diagnostic_fragment_not_resume_checkpoint",
                    ),
                )

            def failure_sink(arrays, replica, step, error):
                persist(
                    self.root / f"failed-{iteration}.npz",
                    arrays,
                    dict(
                        replica=replica,
                        step=step,
                        error=error,
                        status="unvalidated_partial_not_resumable",
                    ),
                )

            self.collector.fragment_sink = fragment_sink
            self.collector.failure_sink = failure_sink
            batch = self.collector.collect(
                policy,
                role="D",
                iteration=iteration,
                count=self.n,
                fragment_steps=run.settings.fragment_steps,
            )
            if len(batch) != self.n:
                raise ValueError("Incomplete diagnostic batch")
            for t in batch:
                assemble([t])
                if t.policy_version != policy.version:
                    raise ValueError("Diagnostic policy mismatch")
            obs = np.stack([t.observations[:-1] for t in batch])
            targets = monte_carlo(np.stack([t.rewards for t in batch]))
            with torch.no_grad():
                metrics = {}
                for label, x, g in (
                    ("A", fixed["observations"], fixed["returns"]),
                    ("D", obs, targets),
                ):
                    pre = full_metric(baseline(tensor(x)).numpy(), g)
                    post = full_metric(run.critic(tensor(x)).numpy(), g)
                    metrics[label] = dict(
                        pre=pre,
                        post=post,
                        reduction=1 - post["mse"] / pre["mse"] if pre["mse"] > 0 else None,
                    )
            paths = footprints(batch)
            self.root.mkdir(parents=True, exist_ok=True)
            archives = []
            for i, trajectory in enumerate(batch):
                path = self.root / f"D-{iteration:02d}-{i:03d}.npz"
                save_trajectory(path, trajectory)
                archives.append(
                    dict(
                        path=str(path),
                        sha256=file_hash(path),
                        realization=trajectory.realization,
                        route_id=trajectory.route_id,
                    )
                )
            risk = risk_snapshot(policy, fixed, run.settings.clip)
            deadline()
            policy.check()
            if (
                learning_hash(run) != before
                or fingerprint(baseline) != pre_hash
                or fingerprint(run.critic) != post_hash
            ):
                raise ValueError("Diagnostic mutated learning state or gradients/RNG")
            self.records.append(
                dict(
                    iteration=iteration,
                    policy_version=policy.version,
                    critic_pre=pre_hash,
                    critic_post=post_hash,
                    **metrics,
                    targets_sha256=tree_hash(targets),
                    risk=risk,
                    gap=metrics["D"]["post"]["relative_mse"] - metrics["A"]["post"]["relative_mse"],
                    overlap=overlap(paths, self.a, [p for e in self.learning for p in e["paths"]]),
                    archives=archives,
                    bytes=sum(Path(a["path"]).stat().st_size for a in archives),
                )
            )
            self.d_footprints.append(paths)
            phase("complete")

    def state(self):
        return dict(
            root=str(self.root),
            n=self.n,
            records=deepcopy(self.records),
            learning=deepcopy(self.learning),
            d_footprints=deepcopy(self.d_footprints),
            used=sorted(self.collector.used),
            trajectories=self.collector.trajectories,
            transitions=self.collector.transitions,
            diagnostics=self.collector.diagnostics,
        )

    @classmethod
    def restore(cls, state, source, seed, run_id, permit=None):
        obj = cls(state["root"], n=state["n"])
        obj.bind(source, seed, run_id, permit=permit)
        for k in ("records", "learning", "d_footprints"):
            setattr(obj, k, state[k])
        obj.collector.used = {tuple(x) for x in state["used"]}
        for k in ("trajectories", "transitions", "diagnostics"):
            setattr(obj.collector, k, state[k])
        return obj

    def validate(self, run):
        n = run.next_iteration
        if (
            self.collector.failed
            or len(self.records) != n
            or len(self.d_footprints) != n
            or self.collector.used != {(k, "D") for k in range(n)}
            or self.collector.trajectories != n * self.n
            or self.collector.transitions != n * self.n * 180
            or len(self.learning) != 1 + 3 * n
        ):
            raise ValueError("Incomplete diagnostic checkpoint")
        for k, record in enumerate(self.records):
            actor = [e for e in run.events if e["event"] == "actor"][k]
            critic = [e for e in run.events if e["event"] == "critic"][k]
            if (
                record["iteration"] != k
                or len(record["archives"]) != self.n
                or record["policy_version"] != f"policy-{k}:{actor['actor_before']}"
                or record["critic_pre"] != actor["critic_before"]
                or record["critic_post"] != critic["critic_after"]
            ):
                raise ValueError("Diagnostic policy/critic identity mismatch")
            restored = []
            for i, archive in enumerate(record["archives"]):
                path = self.root / f"D-{k:02d}-{i:03d}.npz"
                if str(path) != archive["path"] or file_hash(path) != archive["sha256"]:
                    raise ValueError("Diagnostic archive hash mismatch")
                t = load_trajectory(path)
                if (
                    t.policy_version != record["policy_version"]
                    or t.realization != f"{run.collector.run_id}/{k}/D/{i}"
                    or t.route_id != archive["route_id"]
                ):
                    raise ValueError("Diagnostic trajectory identity mismatch")
                restored.append(t)
            targets = monte_carlo(np.stack([t.rewards for t in restored]))
            if (
                tree_hash(targets) != record["targets_sha256"]
                or footprints(restored) != self.d_footprints[k]
            ):
                raise ValueError("Diagnostic targets/footprints mismatch")

    def report(self):
        learning = [p for e in self.learning for p in e["paths"]]
        return dict(
            records=self.records,
            trajectories=self.collector.trajectories,
            transitions=self.collector.transitions,
            warnings=warning_rates(self.records),
            retrospective_overlap=[overlap(d, [], learning) for d in self.d_footprints],
        )


def entrypoint(*, profile, output, config, protocol=None):
    # Before config, directories, source constructors or trajectory collection.
    if profile == "market":
        from btc_risk_rl.pilots.p2_runner import run_market
        return run_market(protocol)
    if profile != "synthetic":
        raise PermissionError("P2 market/unknown profile NOT AUTHORIZED")
    from btc_risk_rl.pilots.p2_runner import run_synthetic
    return run_synthetic(output, config)
