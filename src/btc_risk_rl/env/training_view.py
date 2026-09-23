"""Training-only view of cryptographically anchored, already accepted H1 products."""

import io
import json

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


def load_training_view(cls, config, prepared, expected_manifest):
    manifest_path = prepared / "manifest.json"
    if sha256(manifest_path) != expected_manifest:
        raise ValueError("Accepted manifest anchor mismatch")
    manifest = json.loads(manifest_path.read_text())
    if manifest["status"] != "accepted" or manifest["policy"] != "B_ADR_004":
        raise ValueError("Requires accepted policy B")
    compatibility = audit_config_compatibility(manifest["config"], config)
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
    lo, hi = utc_ms(config.data.train_start), utc_ms(config.data.validation_start)
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
        product_hashes=manifest["files"],
    )
    return obj
