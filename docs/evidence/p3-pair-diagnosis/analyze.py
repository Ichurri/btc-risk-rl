"""Read-only P3 pair audit from accepted reports, D archives and checkpoints."""

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import torch

from btc_risk_rl.agents.models import Critic, fingerprint
from btc_risk_rl.pilots.p2 import tree_hash

REPO = Path(__file__).resolve().parents[3]
CAMPAIGN = REPO / "artifacts/p3-approved-v1"
CLOSURE = REPO / "docs/evidence/p3-market-2026-10-13/final-closure.json"
LEDGER_SHA256 = "86b111b5365cda1760441d2f73d42e0463a4b4b2a7ddbc6e0e41f2a78751fcfe"
CLOSURE_SHA256 = "1d96dd5ed2cb4af27a0f3993501ea7c40ece67ccc5862fe0f9d7b0049c033c6d"
EPS = 1e-12


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(actual, expected):
    assert math.isclose(actual, expected, rel_tol=2e-11, abs_tol=2e-12), (actual, expected)


def pool(rows):
    n = sum(row["count"] for row in rows)
    sse = math.fsum(row["sse"] for row in rows)
    q = math.fsum(row["target_sq"] for row in rows)
    error = math.fsum(row["error_sum"] for row in rows)
    assert n > 0 and q > EPS * n and math.isfinite(sse + q + error)
    return dict(n=n, m=sse / n, z=q / n, r0=sse / q,
                bias=error / n, b0=(error / n) / math.sqrt(q / n))


def checkpoint_model(run, iteration, seed, beta, condition):
    path = run / f"checkpoint-{iteration}"
    manifest = json.loads((path / "manifest.json").read_text())
    assert manifest["run_id"] == run.name
    assert manifest["condition"] == condition
    assert manifest["settings"]["critic_beta"] == beta
    assert manifest["state_sha256"] == sha256(path / "state.pt")
    state = torch.load(path / "state.pt", map_location="cpu", weights_only=False)
    assert state["attrs"]["next_iteration"] == iteration
    assert state["attrs"]["boundary"] == ("after_q0" if iteration == 0 else "after_dual_and_D")
    model = Critic(hidden=manifest["settings"]["hidden"], seed=seed)
    model.load_state_dict(state["critic"])
    return model.eval()


def verify_raw_d(run, record, k, seed, beta, condition):
    assert len(record["archives"]) == 64
    observations, rewards = [], []
    for i, archive in enumerate(record["archives"]):
        path = Path(archive["path"])
        assert path.resolve().is_relative_to((run / "D").resolve())
        assert path == run / "D" / f"D-{k:02d}-{i:03d}.npz"
        assert sha256(path) == archive["sha256"]
        with np.load(path, allow_pickle=False) as data:
            meta = json.loads(data["metadata"].tobytes())
            assert meta["policy_version"] == record["policy_version"]
            assert meta["realization"] == f"{run.name}/{k}/D/{i}"
            assert meta["route_id"] == archive["route_id"]
            assert meta["route_id"].startswith("accepted-train:")
            assert meta["end_reason"] in {
                "collection_window", "segment_boundary", "partition_boundary"
            }
            x, r = data["observations"], data["rewards"]
            assert x.shape == (181, 13) and r.shape == (180,)
            assert np.isfinite(x).all() and np.isfinite(r).all()
            assert np.array_equal(x[:, 12], (180 - np.arange(181)) / 180)
            assert np.array_equal(np.diff(data["times"]), np.full(180, 14_400_000))
            assert data["terminated"][-1] and not data["terminated"][:-1].any()
            assert not data["truncated"].any()
            observations.append(x[:-1].copy())
            rewards.append(r.copy())
    x = np.stack(observations)
    rewards = np.stack(rewards)
    targets = np.cumsum(rewards[:, ::-1], axis=1)[:, ::-1].copy()
    assert tree_hash(targets) == record["targets_sha256"]
    metrics = {}
    for stage, index, expected_hash in (
        ("pre", k, record["critic_pre"]),
        ("post", k + 1, record["critic_post"]),
    ):
        model = checkpoint_model(run, index, seed, beta, condition)
        assert fingerprint(model) == expected_hash
        with torch.no_grad():
            predictions = model(torch.as_tensor(x, dtype=torch.float64)).numpy()
        error = predictions - targets
        reported = record["D"][stage]
        actual = dict(
            count=int(targets.size), sse=float(np.sum(error**2)),
            target_sq=float(np.sum(targets**2)), error_sum=float(np.sum(error)),
        )
        assert actual["count"] == reported["count"] == 64 * 180
        for name in ("sse", "target_sq", "error_sum"):
            close(actual[name], reported[name])
        close(float(predictions.mean()), reported["prediction_stats"]["mean"])
        close(float(targets.mean()), reported["target_stats"]["mean"])
        for third in range(3):
            part = slice(third * 60, (third + 1) * 60)
            row = reported["thirds"][third]
            close(float(np.sum(error[:, part] ** 2)), row["sse"])
            close(float(np.sum(targets[:, part] ** 2)), row["target_sq"])
        metrics[stage] = actual
    return metrics


def main():
    torch.set_num_threads(1)
    assert sha256(CAMPAIGN / "ledger.jsonl") == LEDGER_SHA256
    assert sha256(CLOSURE) == CLOSURE_SHA256
    state = json.loads((CAMPAIGN / "ledger.jsonl").read_text().splitlines()[-1])
    closure = json.loads(CLOSURE.read_text())
    assert state["status"] == "completed" and state["pending"] is None
    assert state["cursor"] == 18 and len(state["units"]) == 198
    assert closure["campaign_status"] == "completed" and closure["accepted_units"] == 198
    assert state["assessment"]["decision"] == "review"

    runs = {}
    for index, (seed, condition, beta) in enumerate(state["identity"]["roster"]):
        run_id = f"run-{index:02d}-{condition}-b{beta}"
        run = CAMPAIGN / run_id
        report_path = run / "unit-10.json"
        accepted = state["units"][index * 11 : (index + 1) * 11]
        assert len(accepted) == 11 and accepted[-1]["run_id"] == run_id
        assert sha256(report_path) == accepted[-1]["report_sha256"]
        payload = json.loads(report_path.read_text())
        report = payload["report"]
        assert payload["status"] == "passed" and payload["beta"] == beta
        assert report["settings"]["critic_beta"] == beta
        assert report["market_training_executed"] is True
        assert report["final_test_accessed"] is False
        records = report["diagnostic"]["records"]
        assert [row["iteration"] for row in records] == list(range(10))
        assert report["diagnostic"]["trajectories"] == 640
        critic_steps = [row for row in report["stability"] if row.get("phase") == "critic"]
        assert len(critic_steps) == 160
        if beta == 1:
            assert all(row["critic_penalty"] > 0 for row in critic_steps)
            for row in critic_steps:
                close(row["critic_objective"], row["mc_mse"] + row["critic_penalty"])
        else:
            assert all("critic_penalty" not in row for row in critic_steps)
        first_actor = next(row["actor_after"] for row in report["events"]
                           if row["event"] == "actor" and row["iteration"] == 0)
        raw = [verify_raw_d(run, records[k], k, seed, beta, condition) for k in (7, 8, 9)]
        d_late = pool([r["D"]["post"] for r in records[7:10]])
        d_early = pool([r["D"]["post"] for r in records[0:3]])
        d_pre_late = pool([r["D"]["pre"] for r in records[7:10]])
        d_third3 = pool([r["D"]["post"]["thirds"][2] for r in records[7:10]])
        a_late = pool([r["A"]["post"] for r in records[7:10]])
        close(pool([r["D"]["post"] for r in records[7:10]])["m"],
              pool([row["post"] for row in raw])["m"])
        v2 = math.fsum(
            (r["D"]["post"]["prediction_stats"]["std"] ** 2
             + r["D"]["post"]["prediction_stats"]["mean"] ** 2) * r["D"]["post"]["count"]
            for r in records[7:10]
        ) / d_late["n"]
        vg = (v2 + d_late["z"] - d_late["m"]) / 2
        close(d_late["m"] - d_late["z"], v2 - 2 * vg)
        risk = [r["risk"] for r in records]
        runs[(seed, condition, beta)] = dict(
            run_id=run_id, final_report_sha256=accepted[-1]["report_sha256"],
            final_checkpoint_sha256=accepted[-1]["checkpoint_sha256"],
            D_early=d_early, D_pre_late=d_pre_late, D_late=d_late,
            D_late_third3=d_third3, A_late=a_late,
            decomposition=dict(e_v2=v2, e_vg=vg, mse_minus_z=d_late["m"] - d_late["z"]),
            risk=dict(lambda_max=max(r["lambda_used"] for r in risk),
                      risk_gradient_max=max(r["initial_risk_gradient_norm"] for r in risk),
                      shortfalls=sum(r["shortfalls"]["numerator"] for r in risk),
                      altered_coefficients=sum(r["altered_coefficients"]["numerator"] for r in risk)),
            policy_0=records[0]["policy_version"],
            policy_9=records[9]["policy_version"],
            actor_after_first=first_actor,
            critic_after_first=records[0]["critic_post"],
            critic_penalty_steps=160 if beta == 1 else 0,
            critic_penalty_mean=(math.fsum(row["critic_penalty"] for row in critic_steps) / 160
                                 if beta == 1 else 0.0),
            D_targets_0=records[0]["targets_sha256"],
            D_targets_9=records[9]["targets_sha256"],
        )

    pairs = []
    for seed in (710031, 710047, 710081):
        for condition in ("C0", "C5", "C10"):
            control, treatment = (runs[seed, condition, b] for b in (0, 1))
            d0, d1 = control["D_late"], treatment["D_late"]
            delta_d = d1["r0"] - d0["r0"]
            delta_d3 = treatment["D_late_third3"]["r0"] - control["D_late_third3"]["r0"]
            delta_a = treatment["A_late"]["r0"] - control["A_late"]["r0"]
            h1 = d1["r0"] - treatment["A_late"]["r0"]
            accepted = state["assessment"]["pairs"][f"{seed}/{condition}"]
            assert control["actor_after_first"] == treatment["actor_after_first"]
            assert control["D_targets_0"] == treatment["D_targets_0"]
            assert control["critic_after_first"] != treatment["critic_after_first"]
            for actual, expected in ((delta_d, accepted["delta_d"]),
                                     (delta_d3, accepted["delta_d3"]),
                                     (delta_a, accepted["delta_a"]),
                                     (h1, accepted["h1"]),
                                     (d0["r0"], accepted["control"]["D_post_late"]["r0"]),
                                     (d1["r0"], accepted["treatment"]["D_post_late"]["r0"])):
                close(actual, expected)
            checks = dict(zero_exact=d1["m"] <= 0.95 * d1["z"],
                          delta_d=delta_d <= -0.05, delta_d3=delta_d3 <= -0.10,
                          delta_a=delta_a <= 0.10, bias=abs(d1["b0"]) <= 0.25,
                          gap=h1 <= 0.5)
            assert checks == accepted["checks"] and accepted["informative"] is True
            pairs.append(dict(seed=seed, condition=condition,
                              beta0=control, beta1=treatment,
                              first_actor_equal=True, first_D_targets_equal=True,
                              first_critic_distinct=True,
                              treated_zero_predictor_mse=d1["z"],
                              treated_threshold=0.95 * d1["z"],
                              delta_d=delta_d, delta_d3=delta_d3,
                              delta_a=delta_a, h1=h1, checks=checks))
    cross_condition = []
    for seed in (710031, 710047, 710081):
        for beta in (0, 1):
            rows = [runs[seed, condition, beta] for condition in ("C0", "C5", "C10")]
            assert len({row["policy_0"] for row in rows}) == 1
            assert len({row["D_targets_0"] for row in rows}) == 1
            assert len({row["policy_9"] for row in rows}) == 3
            assert len({row["D_targets_9"] for row in rows}) == 3
            ratios = [row["D_late"]["r0"] for row in rows]
            cross_condition.append(dict(seed=seed, beta=beta,
                                        late_ratio_spread=max(ratios) - min(ratios),
                                        distinct_late_policies=3, distinct_late_targets=3))
    result = dict(
        scope="accepted_P3_training_only_read_only_pair_diagnosis",
        base_commit="0142d4a1fda37c4d93ae49805090beb4f0decbfe",
        sources=dict(ledger=str(CAMPAIGN / "ledger.jsonl"), ledger_sha256=LEDGER_SHA256,
                     closure=str(CLOSURE), closure_sha256=CLOSURE_SHA256),
        raw_D_archives_checked=18 * 3 * 64,
        D_pre_post_checkpoint_pairs_checked=18 * 3,
        cross_condition=cross_condition,
        pairs=pairs,
    )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
