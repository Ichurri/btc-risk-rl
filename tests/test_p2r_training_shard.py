"""P2R training-only product contract, exercised with fabricated H1 data."""

import hashlib
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest
from test_simulator import accepted_synthetic as accepted_fixture

accepted_synthetic = accepted_fixture
TABLES = {
    "bars.csv": "open_time",
    "observations.csv": "open_time",
    "features.csv": "open_time",
    "episodes.csv": "last_target_ms",
    "transitions.csv": "target_ms",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@contextmanager
def opened_paths_forbidden(forbidden):
    opened = []
    active = [True]

    def audit(event, args):
        if not active[0] or event != "open" or not isinstance(args[0], (str, bytes)):
            return
        path = Path(args[0]).resolve()
        opened.append(str(path))
        if path in forbidden:
            raise AssertionError(f"Shared validation-containing product opened: {path}")

    sys.addaudithook(audit)
    try:
        yield opened
    finally:
        active[0] = False


def synthetic_shard(config, prepared, shard):
    from btc_risk_rl.config import utc_ms

    shard.mkdir()
    end = utc_ms(config.data.validation_start)
    for name, column in TABLES.items():
        lines = (prepared / name).read_text().splitlines(keepends=True)
        index = lines[0].strip().split(",").index(column)
        retained = [lines[0]]
        for line in lines[1:]:
            if int(line.split(",")[index]) >= end:
                break
            retained.append(line)
        (shard / name).write_text("".join(retained))
    for name in ("scaler.json", "audit.json"):
        (shard / name).write_bytes((prepared / name).read_bytes())
    parent = json.loads((prepared / "manifest.json").read_text())
    manifest = {
        "schema_version": "p2r_training_shard_v1",
        "status": "accepted_for_p2r_training_only",
        "parent_h1_manifest_sha256": digest(prepared / "manifest.json"),
        "parent_h1_file_sha256": parent["files"],
        "train_start_ms": utc_ms(config.data.train_start),
        "train_end_exclusive_ms": end,
        "files": {name: digest(shard / name) for name in [*TABLES, "scaler.json", "audit.json"]},
        "derivation": "synthetic_fixture_prefix_only",
    }
    (shard / "manifest.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")
    return digest(shard / "manifest.json")


def test_preflight_requires_registered_training_shard_without_opening_h1_tables(monkeypatch):
    from btc_risk_rl.pilots import p2r_market

    monkeypatch.setattr(p2r_market, "TRAIN_SHARD_MANIFEST_SHA256", None)
    forbidden = {p2r_market.PREPARED / name for name in TABLES}
    with opened_paths_forbidden(forbidden) as opened:
        with pytest.raises(ValueError, match="training-only shard.*registered"):
            p2r_market.inspect_preflight()
    assert not forbidden.intersection(map(Path, opened))
    print(json.dumps({"case": "real_preflight_unregistered", "opened_h1_data_files": [
        p for p in sorted(set(opened)) if p.startswith(str(p2r_market.PREPARED))
    ]}))


def test_synthetic_training_shard_loads_without_opening_shared_tables(
    accepted_synthetic, tmp_path,
):
    from btc_risk_rl.agents.market_source import TrainingMarket

    config, _, prepared, _ = accepted_synthetic
    shard = tmp_path / "training-shard"
    shard_sha = synthetic_shard(config, prepared, shard)
    forbidden = {prepared / name for name in TABLES}
    with opened_paths_forbidden(forbidden) as opened:
        source = TrainingMarket(
            config, prepared, expected_manifest=digest(prepared / "manifest.json"),
            training_shard=shard, expected_shard_manifest=shard_sha,
        )
        path = source.environment(source.route_ids[0]).path
    assert len(source.route_ids) == 7048
    assert path.partition == "train" and len(path.times) == 181
    assert source.identity()["training_shard_manifest_sha256"] == shard_sha
    assert str((prepared / "manifest.json").resolve()) in opened
    assert {str((shard / name).resolve()) for name in [*TABLES, "scaler.json", "audit.json"]}
    assert not forbidden.intersection(map(Path, opened))

    (shard / "bars.csv").write_text((shard / "bars.csv").read_text() + "tampered\n")
    with pytest.raises(ValueError, match="training shard hash"):
        TrainingMarket(config, prepared, expected_manifest=digest(prepared / "manifest.json"),
                       training_shard=shard, expected_shard_manifest=shard_sha)


def test_shard_link_to_shared_table_is_rejected_before_open(accepted_synthetic, tmp_path):
    from btc_risk_rl.agents.market_source import TrainingMarket

    config, _, prepared, _ = accepted_synthetic
    shard = tmp_path / "linked-shard"
    synthetic_shard(config, prepared, shard)
    (shard / "bars.csv").unlink()
    (shard / "bars.csv").symlink_to(prepared / "bars.csv")
    manifest = json.loads((shard / "manifest.json").read_text())
    manifest["files"]["bars.csv"] = digest(prepared / "bars.csv")
    (shard / "manifest.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")
    with opened_paths_forbidden({prepared / "bars.csv"}):
        with pytest.raises(ValueError, match="linked shared product"):
            TrainingMarket(config, prepared, expected_manifest=digest(prepared / "manifest.json"),
                           training_shard=shard,
                           expected_shard_manifest=digest(shard / "manifest.json"))


def test_hardlink_to_shared_table_is_rejected_before_open(accepted_synthetic, tmp_path):
    from btc_risk_rl.agents.market_source import TrainingMarket

    config, _, prepared, _ = accepted_synthetic
    shard = tmp_path / "hardlinked-shard"
    synthetic_shard(config, prepared, shard)
    (shard / "bars.csv").unlink()
    os.link(prepared / "bars.csv", shard / "bars.csv")
    manifest = json.loads((shard / "manifest.json").read_text())
    manifest["files"]["bars.csv"] = digest(prepared / "bars.csv")
    (shard / "manifest.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")
    with opened_paths_forbidden({prepared / "bars.csv"}):
        with pytest.raises(ValueError, match="linked shared product"):
            TrainingMarket(config, prepared, expected_manifest=digest(prepared / "manifest.json"),
                           training_shard=shard,
                           expected_shard_manifest=digest(shard / "manifest.json"))


def test_registered_synthetic_preflight_opens_only_metadata_and_shard(
    accepted_synthetic, tmp_path, monkeypatch,
):
    from btc_risk_rl.pilots import p2r_market

    config, _, prepared, _ = accepted_synthetic
    shard = tmp_path / "preflight-shard"
    shard_sha = synthetic_shard(config, prepared, shard)
    monkeypatch.setattr(p2r_market, "TRAIN_SHARD", shard)
    monkeypatch.setattr(p2r_market, "TRAIN_SHARD_MANIFEST_SHA256", shard_sha)
    monkeypatch.delitem(p2r_market.ANCHORS, p2r_market.MANIFEST)
    monkeypatch.setattr(p2r_market, "MANIFEST", prepared / "manifest.json")
    monkeypatch.setitem(p2r_market.ANCHORS, p2r_market.MANIFEST,
                        digest(prepared / "manifest.json"))
    forbidden = {prepared / name for name in TABLES}
    with opened_paths_forbidden(forbidden) as opened:
        report = p2r_market.inspect_preflight(prepared=prepared)
    assert report["source"]["accepted_starts"] == 7048
    assert report["training_shard_manifest_sha256"] == shard_sha
    assert str((prepared / "manifest.json").resolve()) in opened
    assert not forbidden.intersection(map(Path, opened))
    print(json.dumps({"case": "synthetic_registered_preflight", "opened_source_files": [
        p for p in sorted(set(opened))
        if p.startswith(str(prepared.resolve())) or p.startswith(str(shard.resolve()))
    ]}))
