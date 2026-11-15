"""Frozen OOS actor loading uses invented checkpoints only."""

import hashlib
import json

import pytest
import torch

from btc_risk_rl.agents.models import Actor


def _checkpoint(tmp_path):
    path = tmp_path / "checkpoint-10"
    path.mkdir()
    actor = Actor(hidden=8, seed=7)
    state = {"actor": actor.state_dict(),
             "attrs": {"next_iteration": 10, "generation": 10,
                       "boundary": "after_dual_and_D", "actor_updates": 80,
                       "critic_updates": 160}, "diagnostic": {"synthetic": True}}
    torch.save(state, path / "state.pt")
    digest = hashlib.sha256((path / "state.pt").read_bytes()).hexdigest()
    manifest = {"schema_version": "p2_complete_boundary_v1",
                "profile": "oos_v12_train_only", "condition": "C5",
                "run_id": "run-00-C5-b0", "risk_enabled": True,
                "boundary": "after_dual_and_D", "state_sha256": digest,
                "settings": {"seed": 101, "critic_beta": 0, "iterations": 10, "hidden": 8},
                "provenance": {"data": {"source": "invented"}}}
    (path / "manifest.json").write_text(json.dumps(manifest))
    return path, digest, manifest


def test_final_actor_loads_only_complete_matching_synthetic_checkpoint(tmp_path):
    from btc_risk_rl.evaluation.checkpoint_read import load_oos_final_actor

    path, digest, _ = _checkpoint(tmp_path)
    actor, metadata = load_oos_final_actor(
        path, expected_state_sha256=digest, expected_run_id="run-00-C5-b0",
        expected_seed=101, expected_condition="C5",
        expected_settings={"seed": 101, "critic_beta": 0,
                           "iterations": 10, "hidden": 8},
        expected_source_identity={"source": "invented"},
        expected_actor_updates=80, expected_critic_updates=160,
    )
    assert metadata["boundary"] == "after_dual_and_D"
    assert metadata["generation"] == 10
    assert not actor.training
    assert not any(parameter.requires_grad for parameter in actor.parameters())


def test_wrong_identity_rejected_before_torch_load(tmp_path, monkeypatch):
    from btc_risk_rl.evaluation.checkpoint_read import load_oos_final_actor

    path, digest, _ = _checkpoint(tmp_path)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("actor weights opened before manifest identity")

    monkeypatch.setattr(torch, "load", forbidden)
    with pytest.raises(ValueError, match="identity"):
        load_oos_final_actor(path, expected_state_sha256=digest,
                             expected_run_id="run-00-C10-b0", expected_seed=101,
                             expected_condition="C10",
                             expected_settings={"seed": 101, "critic_beta": 0,
                                                "iterations": 10, "hidden": 8},
                             expected_source_identity={"source": "invented"},
                             expected_actor_updates=80, expected_critic_updates=160)


def test_incomplete_state_and_tampered_hash_rejected(tmp_path):
    from btc_risk_rl.evaluation.checkpoint_read import load_oos_final_actor

    path, digest, _ = _checkpoint(tmp_path)
    with pytest.raises(ValueError, match="hash"):
        load_oos_final_actor(path, expected_state_sha256="0" * 64,
                             expected_run_id="run-00-C5-b0", expected_seed=101,
                             expected_condition="C5",
                             expected_settings={"seed": 101, "critic_beta": 0,
                                                "iterations": 10, "hidden": 8},
                             expected_source_identity={"source": "invented"},
                             expected_actor_updates=80, expected_critic_updates=160)
    state = torch.load(path / "state.pt", map_location="cpu", weights_only=True)
    state["attrs"]["next_iteration"] = 9
    torch.save(state, path / "state.pt")
    new_digest = hashlib.sha256((path / "state.pt").read_bytes()).hexdigest()
    manifest = json.loads((path / "manifest.json").read_text())
    manifest["state_sha256"] = new_digest
    (path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="complete"):
        load_oos_final_actor(path, expected_state_sha256=new_digest,
                             expected_run_id="run-00-C5-b0", expected_seed=101,
                             expected_condition="C5",
                             expected_settings={"seed": 101, "critic_beta": 0,
                                                "iterations": 10, "hidden": 8},
                             expected_source_identity={"source": "invented"},
                             expected_actor_updates=80, expected_critic_updates=160)
