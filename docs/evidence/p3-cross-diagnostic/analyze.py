"""Read-only cross-evaluation of accepted P3 critics on accepted late D batches."""

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import torch

from btc_risk_rl.agents.models import Actor, Critic, fingerprint
from btc_risk_rl.pilots.p2 import tree_hash

ROOT = Path(__file__).resolve().parents[3]
CAMPAIGN = ROOT / "artifacts/p3-approved-v1"
CLOSURE = ROOT / "docs/evidence/p3-market-2026-10-13/final-closure.json"
LEDGER_SHA256 = "86b111b5365cda1760441d2f73d42e0463a4b4b2a7ddbc6e0e41f2a78751fcfe"
CLOSURE_SHA256 = "1d96dd5ed2cb4af27a0f3993501ea7c40ece67ccc5862fe0f9d7b0049c033c6d"
SEEDS = (710031, 710047, 710081)
CONDITIONS = ("C0", "C5", "C10")
ITERATIONS = (7, 8, 9)
TRAJECTORIES = 64
HORIZON = 180


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(actual, expected):
    require(math.isclose(actual, expected, rel_tol=2e-11, abs_tol=2e-12),
            f"recomputed metric differs: {actual} != {expected}")


def metric_sums(count, sse, target_sq, error_sum):
    require(count > 0 and target_sq > 1e-12 * count, "undefined target signal")
    mse, zero = sse / count, target_sq / count
    bias = error_sum / count
    return {
        "count": count, "sse": sse, "target_sq": target_sq,
        "error_sum": error_sum, "mse": mse, "zero_mse": zero,
        "ratio_to_zero": sse / target_sq, "bias": bias,
        "normalized_bias": bias / math.sqrt(zero),
    }


def metrics(predictions, targets):
    predictions = np.asarray(predictions, dtype=np.float64)
    targets = np.asarray(targets, dtype=np.float64)
    require(predictions.shape == targets.shape and predictions.size > 0,
            "prediction/target coverage mismatch")
    require(np.isfinite(predictions).all() and np.isfinite(targets).all(),
            "nonfinite prediction or target")
    error = predictions - targets
    return metric_sums(
        int(targets.size), float(np.sum(error**2)),
        float(np.sum(targets**2)), float(np.sum(error)),
    )


def pool(rows):
    require(bool(rows), "no metric rows")
    return metric_sums(
        sum(row["count"] for row in rows),
        math.fsum(row["sse"] for row in rows),
        math.fsum(row["target_sq"] for row in rows),
        math.fsum(row["error_sum"] for row in rows),
    )


def load_archive(run, archive, k, index, policy_version):
    """Verify path, hash, training source and H180 before returning observations."""
    path = Path(archive["path"])
    expected = run / "D" / f"D-{k:02d}-{index:03d}.npz"
    require(path == expected and path.resolve().is_relative_to((run / "D").resolve()),
            "archive path outside accepted D")
    require(sha256(path) == archive["sha256"], "archive SHA-256 mismatch")
    with np.load(path, allow_pickle=False) as data:
        meta = json.loads(data["metadata"].tobytes())
        route = meta["route_id"]
        realization = f"{run.name}/{k}/D/{index}"
        require(route.startswith("accepted-train:"), "non-training route")
        require(meta["schema_version"] == "h4_trajectory_v1", "archive schema mismatch")
        require(meta["realization"] == archive["realization"] == realization,
                "realization mismatch")
        require(route == archive["route_id"], "route mismatch")
        require(meta["policy_version"] == policy_version, "D policy mismatch")
        require(meta["end_reason"] in {
            "collection_window", "segment_boundary", "partition_boundary"
        }, "unexpected end reason")
        x, rewards = data["observations"], data["rewards"]
        require(x.shape == (HORIZON + 1, 13) and rewards.shape == (HORIZON,),
                "incomplete D horizon")
        require(np.isfinite(x).all() and np.isfinite(rewards).all(), "nonfinite D archive")
        require(np.array_equal(x[:, 12], (HORIZON - np.arange(HORIZON + 1)) / HORIZON),
                "D clock mismatch")
        require(np.array_equal(np.diff(data["times"]), np.full(HORIZON, 14_400_000)),
                "D time continuity mismatch")
        require(bool(data["terminated"][-1]) and not data["terminated"][:-1].any()
                and not data["truncated"].any(), "incomplete D terminality")
        return x[:-1].copy(), rewards.copy(), route


def load_checkpoint(run, accepted, index, seed, condition, beta):
    path = run / f"checkpoint-{index}"
    require(Path(accepted["checkpoint"]) == path and accepted["run_id"] == run.name,
            "unaccepted checkpoint path")
    state_path = path / "state.pt"
    state_hash = sha256(state_path)
    require(state_hash == accepted["checkpoint_sha256"], "checkpoint SHA-256 mismatch")
    manifest = json.loads((path / "manifest.json").read_text())
    require(manifest["state_sha256"] == state_hash, "checkpoint manifest mismatch")
    require(manifest["run_id"] == run.name and manifest["condition"] == condition,
            "checkpoint identity mismatch")
    require(manifest["settings"]["critic_beta"] == beta
            and manifest["settings"]["seed"] == seed, "checkpoint settings mismatch")
    require(manifest["provenance"]["data"]["profile"] == "accepted_train_collection_only",
            "checkpoint source mismatch")
    require(manifest["profile"] == "authorized_p3_only", "checkpoint profile mismatch")
    state = torch.load(state_path, map_location="cpu", weights_only=False)
    require(state["attrs"]["next_iteration"] == index
            and state["attrs"]["generation"] == index
            and state["attrs"]["boundary"] == "after_dual_and_D",
            "checkpoint not a completed P3 boundary")
    hidden = manifest["settings"]["hidden"]
    actor = Actor(hidden=hidden, seed=seed)
    actor.load_state_dict(state["actor"])
    critic = Critic(hidden=hidden, seed=seed)
    critic.load_state_dict(state["critic"])
    actor.eval().requires_grad_(False)
    critic.eval().requires_grad_(False)
    return actor, critic


def audited_inputs():
    """Finish all provenance checks before calculating cross-MSE."""
    require(sha256(CAMPAIGN / "ledger.jsonl") == LEDGER_SHA256, "ledger SHA-256 mismatch")
    require(sha256(CLOSURE) == CLOSURE_SHA256, "closure SHA-256 mismatch")
    ledger = json.loads((CAMPAIGN / "ledger.jsonl").read_text().splitlines()[-1])
    closure = json.loads(CLOSURE.read_text())
    require(ledger["status"] == "completed" and ledger["pending"] is None
            and ledger["cursor"] == 18 and len(ledger["units"]) == 198,
            "P3 campaign is not fully accepted")
    require(ledger["assessment"]["decision"] == "review"
            and closure["campaign_status"] == "completed"
            and closure["accepted_units"] == 198, "closure decision mismatch")
    runs = {}
    archive_count = 0
    for position, (seed, condition, beta) in enumerate(ledger["identity"]["roster"]):
        require(seed in SEEDS and condition in CONDITIONS and beta in (0, 1),
                "unexpected roster entry")
        run = CAMPAIGN / f"run-{position:02d}-{condition}-b{beta}"
        accepted = ledger["units"][11 * position:11 * (position + 1)]
        require([unit["unit"] for unit in accepted] == list(range(11))
                and all(unit["run_id"] == run.name for unit in accepted),
                "incomplete run units")
        report_path = run / "unit-10.json"
        require(sha256(report_path) == accepted[10]["report_sha256"],
                "final report SHA-256 mismatch")
        payload = json.loads(report_path.read_text())
        require(payload["status"] == "passed" and payload["beta"] == beta,
                "unaccepted run report")
        report = payload["report"]
        require(report["market_training_executed"] is True
                and report["final_test_accessed"] is False,
                "run report provenance mismatch")
        records = report["diagnostic"]["records"]
        require([r["iteration"] for r in records] == list(range(10)),
                "incomplete diagnostic records")
        batches, critics, routes = {}, {}, {}
        for k in ITERATIONS:
            record = records[k]
            actor_before, critic_before = load_checkpoint(
                run, accepted[k], k, seed, condition, beta
            )
            require(record["policy_version"] == f"policy-{k}:{fingerprint(actor_before)}",
                    "D generator policy does not match checkpoint")
            require(record["critic_pre"] == fingerprint(critic_before),
                    "D pre critic does not match checkpoint")
            _, critic_after = load_checkpoint(
                run, accepted[k + 1], k + 1, seed, condition, beta
            )
            require(record["critic_post"] == fingerprint(critic_after),
                    "D post critic does not match checkpoint")
            require(len(record["archives"]) == TRAJECTORIES, "incomplete D archive list")
            observations, rewards, route_ids = [], [], []
            for index, archive in enumerate(record["archives"]):
                x, r, route = load_archive(run, archive, k, index, record["policy_version"])
                observations.append(x)
                rewards.append(r)
                route_ids.append(route)
                archive_count += 1
            x = np.stack(observations)
            targets = np.cumsum(np.stack(rewards)[:, ::-1], axis=1)[:, ::-1].copy()
            require(tree_hash(targets) == record["targets_sha256"], "D target hash mismatch")
            batches[k] = (x, targets)
            critics[k] = critic_after
            routes[k] = route_ids
        runs[(seed, condition, beta)] = {
            "run_id": run.name, "report_sha256": accepted[10]["report_sha256"],
            "batches": batches, "critics": critics, "records": records, "routes": routes,
        }
    require(set(runs) == {(s, c, b) for s in SEEDS for c in CONDITIONS for b in (0, 1)},
            "missing or duplicate P3 arm")
    require(archive_count == 18 * 3 * TRAJECTORIES, "D archive coverage mismatch")
    return ledger, runs, archive_count


def evaluate(ledger, runs, archive_count):
    pairs = []
    for seed in SEEDS:
        for condition in CONDITIONS:
            arms = {b: runs[(seed, condition, b)] for b in (0, 1)}
            per_iteration = {}
            for k in ITERATIONS:
                cells = {}
                for critic_beta in (0, 1):
                    model = arms[critic_beta]["critics"][k]
                    for d_beta in (0, 1):
                        x, target = arms[d_beta]["batches"][k]
                        with torch.inference_mode():
                            predicted = model(torch.as_tensor(x, dtype=torch.float64)).numpy()
                        result = metrics(predicted, target)
                        require(result["count"] == TRAJECTORIES * HORIZON,
                                "incomplete evaluated D batch")
                        key = f"critic_b{critic_beta}_on_D_b{d_beta}"
                        cells[key] = result
                        if critic_beta == d_beta:
                            original = arms[d_beta]["records"][k]["D"]["post"]
                            for name in ("sse", "target_sq", "error_sum"):
                                close(result[name], original[name])
                per_iteration[str(k)] = cells
            pooled = {key: pool([per_iteration[str(k)][key] for k in ITERATIONS])
                      for key in per_iteration["7"]}
            accepted = ledger["assessment"]["pairs"][f"{seed}/{condition}"]
            for b in (0, 1):
                on = pooled[f"critic_b{b}_on_D_b{b}"]
                expected = accepted["control" if b == 0 else "treatment"]["D_post_late"]
                close(on["mse"], expected["m"])
                close(on["zero_mse"], expected["z"])
                close(on["ratio_to_zero"], expected["r0"])
            route_sets = {b: set(sum(arms[b]["routes"].values(), [])) for b in (0, 1)}
            coverage = {
                f"D_b{b}": {
                    "run_id": arms[b]["run_id"],
                    "report_sha256": arms[b]["report_sha256"],
                    "iterations": list(ITERATIONS),
                    "trajectories_expected": 192, "trajectories_evaluated": 192,
                    "observations_expected": 34_560, "observations_evaluated": 34_560,
                    "unique_route_ids": len(route_sets[b]),
                } for b in (0, 1)
            }
            pairs.append({
                "seed": seed, "condition": condition, "coverage": coverage,
                "common_route_ids": len(route_sets[0] & route_sets[1]),
                "cells": pooled, "by_iteration": per_iteration,
            })
    blocks = []
    for seed in SEEDS:
        group = [p for p in pairs if p["seed"] == seed]
        blocks.append({
            "seed": seed, "conditions": list(CONDITIONS), "condition_count": 3,
            "independent_seed_blocks": 1,
            "cells": {key: pool([p["cells"][key] for p in group])
                      for key in group[0]["cells"]},
        })
    return {
        "scope": "post_critic_cross_D_existing_training_archives_only",
        "original_decision_unchanged": "review",
        "input_commit": "0142d4a1fda37c4d93ae49805090beb4f0decbfe",
        "source_hashes": {"ledger_sha256": LEDGER_SHA256,
                          "closure_sha256": CLOSURE_SHA256},
        "input_coverage": {"D_archives_verified": archive_count,
                           "post_critic_checkpoints_verified": 54,
                           "k": list(ITERATIONS), "pair_count": 9},
        "pairs": pairs, "seed_blocks": blocks,
    }


def main():
    torch.set_num_threads(1)
    ledger, runs, archive_count = audited_inputs()
    result = evaluate(ledger, runs, archive_count)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
