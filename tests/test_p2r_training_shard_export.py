"""Export/audit contract exercised only with fabricated accepted H1 products."""

import hashlib
import json
import shutil

import pytest
from test_simulator import accepted_synthetic as accepted_fixture

from btc_risk_rl.config import utc_ms

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


def expected_prefix(path, column, end):
    lines = path.read_bytes().splitlines(keepends=True)
    index = lines[0].decode().strip().split(",").index(column)
    kept = [lines[0]]
    for line in lines[1:]:
        if int(line.decode().split(",")[index]) >= end:
            break
        kept.append(line)
    return b"".join(kept)


def test_export_preserves_byte_exact_h1_training_prefix_and_all_paths(
    accepted_synthetic, tmp_path,
):
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.data.training_shard_export import export_training_shard

    config, _, prepared, _ = accepted_synthetic
    shard = tmp_path / "p2r-training-h1"
    report = export_training_shard(
        config, prepared, shard, expected_manifest=digest(prepared / "manifest.json")
    )
    end = utc_ms(config.data.validation_start)
    for name, column in TABLES.items():
        assert (shard / name).read_bytes() == expected_prefix(prepared / name, column, end)
        assert report["files"][name]["prefix_equal_row_by_row"] is True
        assert report["files"][name]["last_included_ms"] < end
    for name in ("scaler.json", "audit.json"):
        assert (shard / name).read_bytes() == (prepared / name).read_bytes()
    assert report["accepted_starts"] == 7048
    assert report["validated_paths"] == 7048
    assert report["usable_segments"] == 15
    assert report["exclusions"] == {"missing": 16, "early_close": 20, "reopening": 20}
    assert report["normalizer_refitted"] is False
    assert report["validation_rows_exported"] == 0
    assert json.loads((shard / "export-audit.json").read_text()) == report
    source = TrainingMarket(
        config, prepared, expected_manifest=digest(prepared / "manifest.json"),
        training_shard=shard,
        expected_shard_manifest=digest(shard / "manifest.json"),
    )
    assert len(source.route_ids) == 7048
    with pytest.raises(ValueError, match="Validation is inaccessible"):
        source._view.validation_path()
    with pytest.raises(FileExistsError):
        export_training_shard(config, prepared, shard,
                              expected_manifest=digest(prepared / "manifest.json"))


def test_independent_reaudit_detects_changed_derived_row(accepted_synthetic, tmp_path):
    from btc_risk_rl.data.training_shard_export import (
        audit_training_shard,
        export_training_shard,
    )

    config, _, prepared, _ = accepted_synthetic
    shard = tmp_path / "audited-shard"
    report = export_training_shard(
        config, prepared, shard, expected_manifest=digest(prepared / "manifest.json")
    )
    checked = audit_training_shard(
        config, prepared, shard, expected_manifest=digest(prepared / "manifest.json"),
        expected_shard_manifest=report["training_shard_manifest_sha256"],
    )
    assert checked["validated_paths"] == 7048
    rows = (shard / "bars.csv").read_bytes().splitlines(keepends=True)
    rows[1] = rows[1].replace(b".", b"9", 1)
    (shard / "bars.csv").write_bytes(b"".join(rows))
    with pytest.raises(ValueError, match="training shard hash mismatch"):
        audit_training_shard(
            config, prepared, shard, expected_manifest=digest(prepared / "manifest.json"),
            expected_shard_manifest=report["training_shard_manifest_sha256"],
        )


def test_hash_mismatch_fails_without_accepted_shard(accepted_synthetic, tmp_path):
    from btc_risk_rl.data.training_shard_export import export_training_shard

    config, _, prepared, _ = accepted_synthetic
    copy = tmp_path / "altered-h1"
    shutil.copytree(prepared, copy)
    with (copy / "bars.csv").open("ab") as stream:
        stream.write(b"tampered\n")
    out = tmp_path / "blocked-shard"
    with pytest.raises(ValueError, match="H1 product hash mismatch: bars.csv"):
        export_training_shard(config, copy, out,
                              expected_manifest=digest(prepared / "manifest.json"))
    assert not out.exists()
    partial = list(tmp_path.glob("blocked-shard.partial-*"))
    assert len(partial) == 1
    assert json.loads((partial[0] / "failure.json").read_text())["status"] == "failed"
    assert not (partial[0] / "manifest.json").exists()
