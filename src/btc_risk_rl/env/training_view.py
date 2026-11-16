"""Training-only view of cryptographically anchored, already accepted H1 products."""

import io
import json
from pathlib import Path

import numpy as np
import pandas as pd

from btc_risk_rl.config import STEP_MS, utc_ms
from btc_risk_rl.data.binance import sha256
from btc_risk_rl.data.config_compatibility import audit_config_compatibility
from btc_risk_rl.features.market import FEATURES, TrainScaler


def prefix(path, time_column, end):
    """Hash verification occurs first. Parse no numerical values at/after end."""
    with path.open() as f:
        header = f.readline()
        index = header.strip().split(",").index(time_column)
        lines = [header]
        for line in f:
            # The boundary envelope is read, not its OHLC/features.
            if int(line.split(",")[index]) >= end:
                break
            lines.append(line)
    return pd.read_csv(io.StringIO("".join(lines)), float_precision="round_trip")


def _accepted_h1_manifest(config, prepared, expected_manifest):
    manifest_path = prepared / "manifest.json"
    if sha256(manifest_path) != expected_manifest:
        raise ValueError("Accepted manifest anchor mismatch")
    manifest = json.loads(manifest_path.read_text())
    if manifest["status"] != "accepted" or manifest["policy"] != "B_ADR_004":
        raise ValueError("Requires accepted policy B")
    compatibility = audit_config_compatibility(manifest["config"], config)
    return manifest, compatibility


def load_training_view(cls, config, prepared, expected_manifest):
    manifest, compatibility = _accepted_h1_manifest(config, prepared, expected_manifest)
    for name, digest in manifest["files"].items():
        if "/" in name or name in {".", ".."} or sha256(prepared / name) != digest:
            raise ValueError(f"Accepted product hash mismatch: {name}")
    audit = json.loads((prepared / "audit.json").read_text())
    if (
        audit["status"] != "passed"
        or audit["normalizer_refitted"]
        or audit["train_episodes"] != 7048
    ):
        raise ValueError("Accepted audit mismatch")
    hi = utc_ms(config.data.validation_start)
    if config.data.train_start.year != 2018 or config.data.validation_start.year != 2023:
        raise ValueError("Training range must remain 2018–2022")
    tables = {}
    for name, column in [
        ("bars", "open_time"),
        ("observations", "open_time"),
        ("features", "open_time"),
        ("episodes", "last_target_ms"),
        ("transitions", "target_ms"),
    ]:
        tables[name] = prefix(prepared / f"{name}.csv", column, hi)
    return _assemble_training_view(
        cls, config, prepared, expected_manifest, manifest["files"], compatibility,
        audit, tables,
    )


def load_training_shard_view(cls, config, prepared, expected_manifest, shard,
                             expected_shard_manifest):
    """Use only H1 metadata and a separately pinned training-exclusive product."""
    if expected_shard_manifest is None:
        raise ValueError("P2R training-only shard is not registered")
    prepared, shard = Path(prepared), Path(shard)
    if shard.is_symlink() or shard.resolve() == prepared.resolve():
        raise ValueError("P2R training shard linked shared product")
    shard = shard.resolve()
    manifest, compatibility = _accepted_h1_manifest(config, prepared, expected_manifest)
    path = shard / "manifest.json"
    if sha256(path) != expected_shard_manifest:
        raise ValueError("P2R training shard manifest hash mismatch")
    product = json.loads(path.read_text())
    required = {
        "bars.csv", "observations.csv", "features.csv", "episodes.csv",
        "transitions.csv", "scaler.json", "audit.json",
    }
    lo, hi = utc_ms(config.data.train_start), utc_ms(config.data.validation_start)
    if (product.get("schema_version") != "p2r_training_shard_v1"
            or product.get("status") != "accepted_for_p2r_training_only"
            or product.get("parent_h1_manifest_sha256") != expected_manifest
            or product.get("parent_h1_file_sha256") != manifest["files"]
            or product.get("train_start_ms") != lo
            or product.get("train_end_exclusive_ms") != hi
            or set(product.get("files", {})) != required):
        raise ValueError("P2R training shard provenance/scope mismatch")
    for name, expected in product["files"].items():
        candidate = shard / name
        if candidate.is_symlink() or (
            name in {"bars.csv", "observations.csv", "features.csv", "episodes.csv",
                     "transitions.csv"}
            and candidate.stat().st_dev == (prepared / name).stat().st_dev
            and candidate.stat().st_ino == (prepared / name).stat().st_ino
        ):
            raise ValueError("P2R training shard linked shared product")
        if sha256(candidate) != expected:
            raise ValueError(f"P2R training shard hash mismatch: {name}")
    if (product["files"]["scaler.json"] != manifest["files"]["scaler.json"]
            or product["files"]["audit.json"] != manifest["files"]["audit.json"]):
        raise ValueError("P2R scaler/audit differs from accepted H1")
    audit = json.loads((shard / "audit.json").read_text())
    tables = {}
    for name, column in [
        ("bars", "open_time"), ("observations", "open_time"),
        ("features", "open_time"), ("episodes", "last_target_ms"),
        ("transitions", "target_ms"),
    ]:
        frame = pd.read_csv(shard / f"{name}.csv", float_precision="round_trip")
        if (column not in frame or frame.empty or
                not frame[column].between(lo, hi - 1).all()):
            # The warmup observation may predate training; it is handled below.
            if name not in {"bars", "observations", "features"} or frame.empty:
                raise ValueError("P2R training shard escaped training partition")
            if column not in frame or (frame[column] >= hi).any():
                raise ValueError("P2R training shard escaped training partition")
        tables[name] = frame
    view = _assemble_training_view(
        cls, config, shard, expected_manifest, product["files"], compatibility,
        audit, tables,
    )
    view.audit["mode"] = "anchored_H1_p2r_training_shard"
    view.audit["parent_product_hashes"] = manifest["files"]
    view.audit["training_shard_manifest_sha256"] = expected_shard_manifest
    return view


def _assemble_training_view(cls, config, prepared, expected_manifest, product_hashes,
                            compatibility, audit, tables):
    if (audit["status"] != "passed" or audit["normalizer_refitted"]
            or audit["train_episodes"] != 7048):
        raise ValueError("Accepted audit mismatch")
    lo = utc_ms(config.data.train_start)
    if config.data.train_start.year != 2018 or config.data.validation_start.year != 2023:
        raise ValueError("Training range must remain 2018–2022")
    episodes = tables["episodes"]
    if len(episodes) != 7048 or not (episodes.partition == "train").all():
        raise ValueError("Training index mismatch")
    if (episodes.first_target_ms < lo).any() or not (episodes.transitions == 180).all():
        raise ValueError("Training index boundary/horizon mismatch")
    if not (episodes.last_target_ms - episodes.initial_observation_ms == 180 * STEP_MS).all():
        raise ValueError("Training index temporal mismatch")
    if not (tables["transitions"].partition == "train").all():
        raise ValueError("Non-training transitions")
    scaler = TrainScaler(**json.loads((prepared / "scaler.json").read_text()))
    features = tables["features"]
    eligible = features.loc[features.open_time >= lo, FEATURES]
    if (
        scaler.fit_count != len(eligible)
        or scaler.fit_end_exclusive != config.data.validation_start.isoformat()
    ):
        raise ValueError("Training scaler scope mismatch")
    scale = eligible.std(ddof=0).replace(0, 1).to_numpy()
    if not np.allclose(eligible.mean(), scaler.mean, rtol=1e-13, atol=1e-15) or not np.allclose(
        scale, scaler.scale, rtol=1e-13, atol=1e-15
    ):
        raise ValueError("Training scaler moments mismatch")
    indexed = features.set_index(pd.to_datetime(features.open_time, unit="ms", utc=True))
    expected = scaler.transform(indexed[FEATURES]).to_numpy()
    if not np.allclose(expected, tables["observations"][FEATURES], rtol=1e-13, atol=1e-15):
        raise ValueError("Persisted training normalization mismatch")
    obj = cls.__new__(cls)
    obj._config = config
    obj._training_only = True
    obj.manifest_sha256 = expected_manifest
    obj._bars = tables["bars"].set_index("open_time")
    obj._observations = tables["observations"].set_index("open_time")
    obj._episodes = episodes.set_index("episode_id")
    obj._transitions = tables["transitions"]
    obj.episode_ids = tuple(int(i) for i in obj._episodes.index)
    if len(set(obj.episode_ids)) != 7048:
        raise ValueError("Duplicate episode IDs")
    obj._target_keys = {
        (r.partition, int(r.segment_id), int(r.target_ms)) for r in obj._transitions.itertuples()
    }
    obj.audit = dict(
        status="passed",
        mode="anchored_H1_training_only",
        normalizer_refitted=False,
        fit_count=scaler.fit_count,
        train_episodes=7048,
        validation_observations_loaded=False,
        config_compatibility=compatibility,
        product_hashes=product_hashes,
    )
    return obj
