"""Synthetic checks for the read-only P3 cross-diagnostic calculator."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import torch

SCRIPT = Path(__file__).resolve().parents[1] / "docs/evidence/p3-cross-diagnostic/analyze.py"


def analyzer():
    spec = importlib.util.spec_from_file_location("p3_cross_diagnostic", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_metrics_use_same_targets_for_both_critics():
    module = analyzer()
    targets = np.array([1.0, 2.0])
    control = module.metrics(np.array([0.0, 1.0]), targets)
    treatment = module.metrics(np.array([1.0, 3.0]), targets)
    assert control["count"] == treatment["count"] == 2
    assert control["mse"] == 1.0
    assert treatment["mse"] == 0.5
    assert control["zero_mse"] == treatment["zero_mse"] == 2.5
    assert control["bias"] == -1.0
    assert treatment["bias"] == 0.5


def test_pool_weights_observations_not_iteration_ratios():
    module = analyzer()
    first = module.metrics(np.array([2.0]), np.array([1.0]))
    second = module.metrics(np.array([0.0, 0.0, 0.0]), np.array([2.0, 2.0, 2.0]))
    pooled = module.pool([first, second])
    assert pooled["count"] == 4
    assert pooled["mse"] == 13 / 4
    assert pooled["zero_mse"] == 13 / 4
    assert pooled["bias"] == -5 / 4


def test_archive_rejects_tampered_hash_and_nontraining_route(tmp_path):
    module = analyzer()
    run = tmp_path / "run-00-C0-b0"
    d = run / "D"
    d.mkdir(parents=True)
    path = d / "D-07-000.npz"
    meta = {
        "schema_version": "h4_trajectory_v1",
        "realization": "run-00-C0-b0/7/D/0",
        "route_id": "accepted-train:5:synthetic",
        "policy_version": "policy-7:synthetic",
        "end_reason": "collection_window",
    }
    x = np.zeros((181, 13))
    x[:, 12] = (180 - np.arange(181)) / 180
    np.savez(
        path,
        metadata=np.frombuffer(json.dumps(meta).encode(), dtype=np.uint8),
        observations=x,
        rewards=np.ones(180),
        times=np.arange(181, dtype=np.int64) * 14_400_000,
        terminated=np.array([False] * 179 + [True]),
        truncated=np.zeros(180, dtype=bool),
    )
    archive = {
        "path": str(path),
        "sha256": module.sha256(path),
        "realization": meta["realization"],
        "route_id": meta["route_id"],
    }
    module.load_archive(run, archive, 7, 0, meta["policy_version"])
    with pytest.raises(ValueError, match="SHA-256"):
        module.load_archive(run, {**archive, "sha256": "0" * 64}, 7, 0,
                            meta["policy_version"])
    wrong = {**meta, "route_id": "validation:5:synthetic"}
    np.savez(
        path,
        metadata=np.frombuffer(json.dumps(wrong).encode(), dtype=np.uint8),
        observations=x,
        rewards=np.ones(180),
        times=np.arange(181, dtype=np.int64) * 14_400_000,
        terminated=np.array([False] * 179 + [True]),
        truncated=np.zeros(180, dtype=bool),
    )
    with pytest.raises(ValueError, match="training route"):
        module.load_archive(run, {**archive, "sha256": module.sha256(path)}, 7, 0,
                            meta["policy_version"])


def test_checkpoint_rejects_wrong_hash_and_source(tmp_path):
    module = analyzer()
    run = tmp_path / "run-00-C0-b0"
    checkpoint = run / "checkpoint-8"
    checkpoint.mkdir(parents=True)
    actor = module.Actor(hidden=4, seed=710031)
    critic = module.Critic(hidden=4, seed=710031)
    state = {
        "actor": actor.state_dict(), "critic": critic.state_dict(),
        "attrs": {"next_iteration": 8, "generation": 8,
                  "boundary": "after_dual_and_D"},
    }
    torch.save(state, checkpoint / "state.pt")
    digest = module.sha256(checkpoint / "state.pt")
    manifest = {
        "state_sha256": digest, "run_id": run.name, "condition": "C0",
        "settings": {"critic_beta": 0, "seed": 710031, "hidden": 4},
        "provenance": {"data": {"profile": "accepted_train_collection_only"}},
        "profile": "authorized_p3_only",
    }
    (checkpoint / "manifest.json").write_text(json.dumps(manifest))
    accepted = {"checkpoint": str(checkpoint), "checkpoint_sha256": digest,
                "run_id": run.name}
    module.load_checkpoint(run, accepted, 8, 710031, "C0", 0)
    with pytest.raises(ValueError, match="checkpoint SHA-256"):
        module.load_checkpoint(run, {**accepted, "checkpoint_sha256": "0" * 64},
                               8, 710031, "C0", 0)
    manifest["provenance"]["data"]["profile"] = "validation"
    (checkpoint / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="checkpoint source"):
        module.load_checkpoint(run, accepted, 8, 710031, "C0", 0)


def test_matrix_keeps_critic_and_d_policy_axes_separate():
    module = analyzer()

    class ConstantCritic:
        def __init__(self, value):
            self.value = value

        def __call__(self, observations):
            return torch.full(observations.shape[:-1], self.value, dtype=torch.float64)

    runs, accepted = {}, {}
    for seed in module.SEEDS:
        for condition in module.CONDITIONS:
            accepted[f"{seed}/{condition}"] = {
                "control": {"D_post_late": {"m": 1.0, "z": 1.0, "r0": 1.0}},
                "treatment": {"D_post_late": {"m": 1.0, "z": 4.0, "r0": 0.25}},
            }
            for beta in (0, 1):
                target = np.full((64, 180), 1.0 + beta)
                source = module.metrics(np.full((64, 180), float(beta)), target)
                records = [{} for _ in range(10)]
                for k in module.ITERATIONS:
                    records[k] = {"D": {"post": source}}
                runs[seed, condition, beta] = {
                    "run_id": f"synthetic-{seed}-{condition}-{beta}",
                    "report_sha256": "synthetic",
                    "batches": {k: (np.zeros((64, 180, 13)), target)
                                for k in module.ITERATIONS},
                    "critics": {k: ConstantCritic(float(beta)) for k in module.ITERATIONS},
                    "records": records,
                    "routes": {k: [f"accepted-train:{i}" for i in range(64)]
                               for k in module.ITERATIONS},
                }
    result = module.evaluate({"assessment": {"pairs": accepted}}, runs, 3456)
    pair = result["pairs"][0]
    cells = pair["cells"]
    assert cells["critic_b0_on_D_b0"]["mse"] == 1.0
    assert cells["critic_b1_on_D_b0"]["mse"] == 0.0
    assert cells["critic_b0_on_D_b1"]["mse"] == 4.0
    assert cells["critic_b1_on_D_b1"]["mse"] == 1.0
    assert cells["critic_b0_on_D_b1"]["zero_mse"] == 4.0
    assert cells["critic_b1_on_D_b0"]["bias"] == 0.0
    assert pair["coverage"]["D_b0"]["observations_evaluated"] == 34_560
    assert len(result["seed_blocks"]) == 3
