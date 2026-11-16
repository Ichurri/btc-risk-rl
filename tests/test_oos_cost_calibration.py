"""Synthetic checks for the unadopted OOS cost probe."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from btc_risk_rl.agents.models import Actor, fingerprint

spec = importlib.util.spec_from_file_location(
    "calibrate_oos_v12", Path(__file__).resolve().parents[1] / "scripts/calibrate_oos_v12.py"
)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_cost_probe_cannot_write_into_prior_campaign_or_data_roots():
    for path in (probe.ROOT / "artifacts/p3-approved-v1/new", probe.ROOT / "data/processed/new"):
        with pytest.raises(ValueError):
            probe.guard_output(path)
    probe.guard_output(probe.ROOT / "artifacts/oos-cost-v12-test/fold")


def test_synthetic_walk_is_deterministic_and_does_not_change_actor(monkeypatch, tmp_path):
    actor = Actor(hidden=4, seed=7)
    before = fingerprint(actor)
    monkeypatch.setattr(probe, "load_actor", lambda: (actor, {"fixed_synthetic_actor": True}))
    monkeypatch.setitem(probe.LENGTHS, "short-test", 8)
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    a = probe.synthetic_walk("short-test", first)
    b = probe.synthetic_walk("short-test", second)
    assert a["return_sha256"] == b["return_sha256"]
    assert a["action_sha256"] == b["action_sha256"]
    assert a["steps"] == 8 and a["one_continuous_portfolio"]
    assert fingerprint(actor) == before
    assert np.isfinite(np.load(first / "simple_returns.npy", allow_pickle=False)).all()


def test_audit_rejects_non_synthetic_manifest_before_loading_returns(tmp_path, monkeypatch):
    root = tmp_path / "artifacts" / "oos-cost-v12-test" / "synthetic"
    root.mkdir(parents=True)
    monkeypatch.setattr(probe, "ROOT", tmp_path)
    (root / "result.json").write_text(json.dumps({"phase": "historical", "synthetic_only": False}))
    with pytest.raises(ValueError, match="Only synthetic"):
        probe.audit(root)
