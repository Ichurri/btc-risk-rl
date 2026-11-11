"""Read the fixed K10 OOS actor without loading a training market or optimizer."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import torch

from btc_risk_rl.agents.models import Actor, fingerprint


def load_oos_final_actor(checkpoint: Path, *, expected_state_sha256: str,
                         expected_run_id: str, expected_seed: int,
                         expected_condition: str, expected_settings: dict,
                         expected_source_identity: dict,
                         expected_actor_updates: int,
                         expected_critic_updates: int) -> tuple[Actor, dict]:
    """Verify accepted checkpoint identity and complete boundary before use.

    The caller must first verify the frozen roster and ledger hash chain;
    `expected_state_sha256` is the accepted unit's hash in that ledger.
    """
    checkpoint = Path(checkpoint)
    if (checkpoint.name != "checkpoint-10" or checkpoint.is_symlink()
            or (checkpoint / "manifest.json").is_symlink()
            or (checkpoint / "state.pt").is_symlink()):
        raise ValueError("OOS final checkpoint path or symlink invalid")
    raw_manifest = (checkpoint / "manifest.json").read_bytes()
    manifest = json.loads(raw_manifest)
    if (type(manifest) is not dict
            or manifest.get("schema_version") != "p2_complete_boundary_v1"
            or manifest.get("profile") != "oos_v12_train_only"
            or manifest.get("boundary") != "after_dual_and_D"
            or manifest.get("run_id") != expected_run_id
            or manifest.get("condition") != expected_condition
            or manifest.get("risk_enabled") is not (expected_condition != "C0")
            or manifest.get("settings") != expected_settings
            or expected_settings.get("seed") != expected_seed
            or expected_settings.get("critic_beta") != 0
            or expected_settings.get("iterations") != 10
            or manifest.get("provenance", {}).get("data") != expected_source_identity):
        raise ValueError("OOS final checkpoint identity mismatch")
    raw_state = (checkpoint / "state.pt").read_bytes()
    state_sha = hashlib.sha256(raw_state).hexdigest()
    if state_sha != expected_state_sha256 or manifest.get("state_sha256") != state_sha:
        raise ValueError("OOS final checkpoint state hash mismatch")
    state = torch.load(io.BytesIO(raw_state), map_location="cpu", weights_only=True)
    if type(state) is not dict or state.get("diagnostic") is None:
        raise ValueError("OOS final checkpoint complete diagnostic missing")
    attrs = state.get("attrs", {})
    if (attrs.get("next_iteration") != 10 or attrs.get("generation") != 10
            or attrs.get("boundary") != "after_dual_and_D"
            or attrs.get("actor_updates") != expected_actor_updates
            or attrs.get("critic_updates") != expected_critic_updates
            or expected_actor_updates <= 0 or expected_critic_updates <= 0):
        raise ValueError("OOS final checkpoint incomplete or counters disagree")
    weights = state.get("actor")
    if not isinstance(weights, dict) or "net.0.weight" not in weights:
        raise ValueError("OOS final checkpoint actor missing")
    hidden = expected_settings.get("hidden")
    if (type(hidden) is not int or hidden <= 0
            or weights["net.0.weight"].shape[0] != hidden):
        raise ValueError("OOS final checkpoint actor shape mismatch")
    actor = Actor(hidden=hidden, seed=0).eval().requires_grad_(False)
    actor.load_state_dict(weights, strict=True)
    if any(not torch.isfinite(tensor).all() for tensor in actor.state_dict().values()):
        raise ValueError("OOS final checkpoint actor nonfinite")
    return actor, {
        "run_id": expected_run_id, "condition": expected_condition,
        "seed": expected_seed, "generation": 10,
        "boundary": "after_dual_and_D", "state_sha256": state_sha,
        "manifest_sha256": hashlib.sha256(raw_manifest).hexdigest(),
        "actor_fingerprint": fingerprint(actor),
    }
