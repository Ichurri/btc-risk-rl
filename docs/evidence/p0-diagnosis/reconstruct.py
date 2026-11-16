"""Audit original P0 A batches at fixed checkpoints. Never construct/step an optimizer."""

import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from btc_risk_rl.agents.collector import Collector, immutable
from btc_risk_rl.agents.market_source import TrainingMarket
from btc_risk_rl.agents.models import Actor, Critic, FrozenPolicy, clipped_objective, fingerprint
from btc_risk_rl.agents.risk import monte_carlo
from btc_risk_rl.agents.trainer import fixed_digest, tensor
from btc_risk_rl.config import load_config

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CAMPAIGN = ROOT / "artifacts/p0-approved-v1"


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def snapshot():
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(CAMPAIGN.rglob("*")) if p.is_file()}


def stats(x):
    x = np.asarray(x)
    return dict(
        mean=float(x.mean()),
        std=float(x.std()),
        min=float(x.min()),
        max=float(x.max()),
        second_moment=float(np.mean(x * x)),
    )


def vector(model):
    return torch.cat([p.detach().flatten() for p in model.parameters()])


def gradient(actor, obs, actions, lp, coeff, clip):
    loss = -clipped_objective(
        actor.log_prob(tensor(obs), tensor(actions)), tensor(lp), tensor(coeff), clip
    )
    g = torch.cat([x.flatten() for x in torch.autograd.grad(loss, tuple(actor.parameters()))])
    return g.detach(), float(loss.detach())


def denied(*args, **kwargs):
    raise AssertionError("Optimizer steps forbidden in diagnosis")


def main():
    if (OUT / "results.json").exists():
        raise FileExistsError("Preserve prior diagnostic evidence")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.optim.Adam.step = denied
    torch.optim.SGD.step = denied
    original = json.loads(
        (ROOT / "docs/evidence/p0-execution/campaign-results/results.json").read_text()
    )
    before = snapshot()
    for file, sha in original["identity"]["code"].items():
        assert digest(ROOT / file) == sha
    for item in original["artifacts"]:
        assert digest(CAMPAIGN / item["path"]) == item["sha256"]
        if "state_sha256" in item:
            assert digest((CAMPAIGN / item["path"]).parent / "state.pt") == item["state_sha256"]
    manifest_hash = digest(ROOT / "docs/evidence/segmented-h1/manifest.json")
    source = TrainingMarket(
        load_config(ROOT / "configs/initial.toml"),
        ROOT / "data/processed/segmented-B-h1",
        expected_manifest=manifest_hash,
    )
    assert len(source.route_ids) == 7048
    records = []
    states_by_run = {}
    for r in original["runs"]:
        rid, seed, settings = r["run_id"], r["seed"], r["settings"]
        states = []
        for n in range(3):
            base = CAMPAIGN / rid / f"checkpoint-{n}"
            m = json.loads((base / "manifest.json").read_text())
            assert digest(base / "state.pt") == m["state_sha256"]
            assert m["provenance"]["data"] == source.identity()
            states.append(torch.load(base / "state.pt", map_location="cpu", weights_only=True))
        states_by_run[rid] = states
        for iteration in range(2):
            pre, post = states[iteration], states[iteration + 1]
            actor = Actor(hidden=settings["hidden"], seed=seed)
            critic = Critic(hidden=settings["hidden"], seed=seed + 1)
            actor.load_state_dict(pre["actor"])
            critic.load_state_dict(pre["critic"])
            actor.eval()
            critic.eval().requires_grad_(False)
            actor_vec = vector(actor).clone()
            policy = FrozenPolicy(actor, generation=iteration)
            collector = Collector(source, seed=seed, run_id=rid)
            batch = collector.collect(
                policy, role="A", iteration=iteration, count=64, fragment_steps=60
            )
            events = post["attrs"]["events"]
            ev = next(e for e in events if e["event"] == "A" and e["iteration"] == iteration)
            assert [t.route_id for t in batch] == ev["route_ids"]
            assert [t.realization for t in batch] == ev["realizations"]
            assert all(t.policy_version == ev["policy_version"] for t in batch)
            observed_diag = next(
                d
                for d in post["collector"]["diagnostics"]
                if d["role"] == "A" and d["iteration"] == iteration
            )
            assert collector.diagnostics[0] == observed_diag
            obs = np.stack([t.observations[:-1] for t in batch])
            actions = np.stack([t.actions for t in batch])
            lp = np.stack([t.log_probs for t in batch])
            g = monte_carlo(np.stack([t.rewards for t in batch]))
            with torch.no_grad():
                values = critic(tensor(obs)).numpy()
            advantage = g - values
            eta, lam = pre["attrs"]["eta"], pre["attrs"]["multiplier"]
            alpha = 0.1 if r["condition"] == "C10" else 0.05
            shortfall = np.maximum(-g[:, 0] - eta, 0)
            penalty = lam / alpha * shortfall if r["condition"] != "C0" else np.zeros(64)
            coeff = advantage - penalty[:, None]
            fixed = {
                k: immutable(v)
                for k, v in dict(
                    observations=obs,
                    actions=actions,
                    old_logp=lp,
                    returns=g,
                    old_values=values,
                    advantages=advantage,
                    coefficients=coeff,
                ).items()
            }
            fixed.update(eta=eta, multiplier=lam, alpha=alpha, bound=settings["bound"])
            actor_event = next(
                e for e in events if e["event"] == "actor" and e["iteration"] == iteration
            )
            assert fixed_digest(fixed) == actor_event["fixed_before"] == actor_event["fixed_after"]
            assert lam == actor_event["lambda_used"] and eta == actor_event["eta_used"]
            stability = [s for s in post["telemetry"]["stability"] if s["iteration"] == iteration]
            target_log = next(s for s in stability if s["phase"] == "targets")
            before_mse = float(np.mean((g - values) ** 2))
            denom = float(np.mean(g * g) + 1e-12)
            assert before_mse == target_log["critic_mc_mse_before"]
            assert before_mse / denom == target_log["critic_relative_mse"]
            critic_logs = [s for s in stability if s["phase"] == "critic"]
            rng = np.random.default_rng(np.random.SeedSequence([seed, 100, iteration, 1]))
            minibatches = []
            for epoch in range(2):
                order = rng.permutation(64)
                for start in range(0, 64, 16):
                    ids = order[start : start + 16]
                    log = critic_logs[len(minibatches)]
                    denominator = float(np.mean(g[ids] ** 2) + 1e-12)
                    assert log["mc_mse"] / denominator == log["relative_mc_mse"]
                    minibatches.append(
                        dict(
                            epoch=epoch,
                            step=len(minibatches),
                            ids=ids.tolist(),
                            target=stats(g[ids]),
                            denominator=denominator,
                            original=log,
                            measurement="pre_step_on_this_minibatch_recorded_after_step",
                        )
                    )
            ids = np.random.default_rng(
                np.random.SeedSequence([seed, 100, iteration, 0])
            ).permutation(64)[:16]
            grad, loss = gradient(
                actor, obs[ids], actions[ids], lp[ids], coeff[ids], settings["clip"]
            )
            logged_actor = [s for s in stability if s["phase"] == "actor"]
            assert np.isclose(
                float(torch.linalg.vector_norm(grad)),
                logged_actor[0]["gradient_norm"],
                rtol=1e-12,
                atol=1e-12,
            )
            assert loss == logged_actor[0]["loss"]
            grad_all, _ = gradient(actor, obs, actions, lp, coeff, settings["clip"])
            grad_off, _ = gradient(actor, obs, actions, lp, advantage, settings["clip"])
            risk_grad = grad_all - grad_off
            assert torch.equal(vector(actor), actor_vec)
            actor_post = Actor(hidden=settings["hidden"], seed=seed)
            actor_post.load_state_dict(post["actor"])
            assert fingerprint(actor) == actor_event["actor_before"]
            assert fingerprint(actor_post) == actor_event["actor_after"]
            critic.load_state_dict(post["critic"])
            with torch.no_grad():
                after_values = critic(tensor(obs)).numpy()
            after_mse = float(np.mean((g - after_values) ** 2))
            records.append(
                dict(
                    run_id=rid,
                    seed=seed,
                    condition=r["condition"],
                    iteration=iteration,
                    warning_count=9,
                    correspondence=dict(
                        routes=True,
                        realizations=True,
                        policy=True,
                        collection_diagnostics_exact=True,
                        fixed_digest=fixed_digest(fixed),
                        first_actor_loss_exact=True,
                        first_actor_gradient_matches=True,
                    ),
                    critic=dict(
                        target=stats(g),
                        prediction_before=stats(values),
                        prediction_after=stats(after_values),
                        denominator=denom,
                        mse_before=before_mse,
                        mse_after=after_mse,
                        relative_before=before_mse / denom,
                        relative_after=after_mse / denom,
                        minibatches=minibatches,
                    ),
                    risk=dict(
                        eta=eta,
                        lambda_used=lam,
                        alpha=alpha,
                        losses=stats(-g[:, 0]),
                        shortfall_count=int((shortfall > 0).sum()),
                        shortfall_sum=float(shortfall.sum()),
                        shortfalls=shortfall.tolist(),
                        penalty_max=float(penalty.max()),
                        penalty_nonzero_trajectories=int((penalty != 0).sum()),
                        coefficient_delta_max=float(np.max(np.abs(coeff - advantage))),
                        initial_full_gradient_norm=float(torch.linalg.vector_norm(grad_all)),
                        initial_risk_gradient_delta_norm=float(torch.linalg.vector_norm(risk_grad)),
                        first_minibatch_ids=ids.tolist(),
                        original_actor_steps=logged_actor,
                        first_gradient_sha256=hashlib.sha256(grad.numpy().tobytes()).hexdigest(),
                    ),
                    parameters=dict(
                        actor_before=fingerprint(actor),
                        actor_after=fingerprint(actor_post),
                        actor_change_l2=float(
                            torch.linalg.vector_norm(vector(actor_post) - actor_vec)
                        ),
                    ),
                )
            )
            print(
                rid,
                iteration,
                "shortfalls",
                int((shortfall > 0).sum()),
                "risk_grad",
                float(torch.linalg.vector_norm(risk_grad)),
                "mse",
                before_mse,
                after_mse,
                flush=True,
            )
    # Exact C0/C5 paired checkpoint parameters, optimizer moments and logged actor steps.
    pairs = []
    for seed in (410031, 410047, 410081):
        names = {r["condition"]: r["run_id"] for r in original["runs"] if r["seed"] == seed}
        a, b = states_by_run[names["C0"]], states_by_run[names["C5"]]

        def equal(x, y):
            if isinstance(x, torch.Tensor):
                return torch.equal(x, y)
            if isinstance(x, dict):
                return x.keys() == y.keys() and all(equal(x[k], y[k]) for k in x)
            if isinstance(x, (list, tuple)):
                return len(x) == len(y) and all(equal(u, v) for u, v in zip(x, y, strict=True))
            return x == y

        pairs.append(
            dict(
                seed=seed,
                checkpoint_actor_equal=[
                    equal(x["actor"], y["actor"]) for x, y in zip(a, b, strict=True)
                ],
                checkpoint_actor_adam_equal=[
                    equal(x["actor_optimizer"], y["actor_optimizer"])
                    for x, y in zip(a, b, strict=True)
                ],
                all_logged_actor_steps_equal=equal(
                    [s for s in a[2]["telemetry"]["stability"] if s["phase"] == "actor"],
                    [s for s in b[2]["telemetry"]["stability"] if s["phase"] == "actor"],
                ),
            )
        )
    assert before == snapshot()
    assert len(records) == 18 and sum(r["warning_count"] for r in records) == 162
    result = dict(
        scope="frozen_original_A_reconstruction_no_optimizer_steps_no_validation_final",
        base="e0a2dfc",
        original_campaign_unchanged=True,
        original_files_sha256=before,
        source_identity=source.identity(),
        records=records,
        pairs=pairs,
        limitations="No intermediate minibatch weights saved: only first actor gradient reconstructed and matched; remaining original gradient norms retained, not full gradient vectors. End critic compared on same A is reconstructed in-sample.",
    )
    with (OUT / "results.json").open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
    print(
        "PASS: 18 exact fixed digests; 162 metrics; originals unchanged; zero optimizer steps",
        flush=True,
    )


if __name__ == "__main__":
    main()
