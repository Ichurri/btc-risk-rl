"""Accepted training integration tested first with a synthetic H1 product."""

import json

import numpy as np
import pytest
from test_simulator import accepted_synthetic as accepted_fixture

accepted_synthetic = accepted_fixture


def test_training_view_has_only_training_and_keeps_all_indices(accepted_synthetic):
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.config import utc_ms
    from btc_risk_rl.data.binance import sha256

    c, _, out, _ = accepted_synthetic
    source = TrainingMarket(c, out, expected_manifest=sha256(out / "manifest.json"))
    assert len(source.route_ids) == 7048
    assert not hasattr(source, "validation_path")
    for index in source.route_ids:
        path = source.environment(index).path
        assert path.partition == "train" and len(path.times) == 181
        assert path.times[-1] < utc_ms(c.data.validation_start)
    assert source.identity()["scaler_sha256"] == sha256(out / "scaler.json")
    assert source.audit["normalizer_refitted"] is False
    with pytest.raises(ValueError):
        source.environment("validation")


def test_market_collection_uniform_frozen_and_optimizer_blocked(accepted_synthetic):
    from btc_risk_rl.agents.collector import Collector
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.agents.models import Actor, FrozenPolicy, fingerprint
    from btc_risk_rl.agents.synthetic import SyntheticSettings
    from btc_risk_rl.agents.trainer import SyntheticExperiment
    from btc_risk_rl.data.binance import sha256

    c, _, out, _ = accepted_synthetic
    source = TrainingMarket(c, out, expected_manifest=sha256(out / "manifest.json"))
    actor = Actor(hidden=4, seed=8)
    before = fingerprint(actor)
    col = Collector(source, seed=41, run_id="test-integration")
    batch = col.collect(FrozenPolicy(actor, generation=0), role="A", iteration=0, count=3)
    expected = np.random.default_rng(np.random.SeedSequence([41, 1, 0, 0])).choice(
        source.route_ids, 3
    )
    assert [int(t.route_id.split(":")[1]) for t in batch] == list(expected)
    assert fingerprint(actor) == before
    with pytest.raises(PermissionError, match="Market"):
        SyntheticExperiment(source, SyntheticSettings(), condition="C0", run_id="blocked")


def test_manifest_anchor_and_file_corruption_rejected(accepted_synthetic, tmp_path):
    import shutil

    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.data.binance import sha256

    c, _, out, _ = accepted_synthetic
    with pytest.raises(ValueError, match="manifest"):
        TrainingMarket(c, out, expected_manifest="wrong")
    damaged = tmp_path / "damaged"
    shutil.copytree(out, damaged)
    with (damaged / "observations.csv").open("a") as f:
        f.write("corruption")
    with pytest.raises(ValueError, match="hash"):
        TrainingMarket(c, damaged, expected_manifest=sha256(out / "manifest.json"))


def test_pilot_command_cannot_be_authorized_by_input_file(tmp_path):
    import subprocess
    import sys

    p = tmp_path / "protocol.json"
    p.write_text(json.dumps({"authorized": True}))
    result = subprocess.run(
        [sys.executable, "scripts/run_pilot.py", "--protocol", str(p)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2 and "blocked" in result.stdout
