"""Read-only, cutoff-specific accepted-training source for the two cost folds."""

import hashlib
import json
from io import StringIO

import numpy as np
import pandas as pd

from btc_risk_rl.agents.market_source import TrainingMarket
from btc_risk_rl.config import load_config
from btc_risk_rl.data.segmentation import build_tables
from btc_risk_rl.env.market import AcceptedMarket
from btc_risk_rl.features.market import FEATURES, TrainScaler
from btc_risk_rl.pilots.wf_cost import CONFIG, EXPECTED, SHARD_MANIFEST_SHA256, TRAIN_SHARD, digest

CUTOFF = {"2021": "2020-12-02T00:00:00Z", "2022": "2021-12-02T00:00:00Z"}


def _csv_hash(frame):
    stream = StringIO()
    frame.to_csv(stream, index=False)
    return hashlib.sha256(stream.getvalue().encode()).hexdigest()


def build_fold_source(year):
    """Reconstruct H1 tables strictly below cutoff; never collect a path."""
    if year not in EXPECTED:
        raise ValueError("Unknown cost-study fold")
    if digest(TRAIN_SHARD / "manifest.json") != SHARD_MANIFEST_SHA256:
        raise ValueError("Training-only shard changed")
    parent = json.loads((TRAIN_SHARD / "manifest.json").read_text())
    for name, expected in parent["files"].items():
        if digest(TRAIN_SHARD / name) != expected:
            raise ValueError(f"Training-only shard product changed: {name}")
    config = load_config(CONFIG)
    cutoff = int(pd.Timestamp(CUTOFF[year]).timestamp() * 1000)
    frame = pd.read_csv(TRAIN_SHARD / "bars.csv", float_precision="round_trip")
    if (set(frame.partition) - {"warmup", "train"}
            or (frame.open_time >= 1672531200000).any()):
        raise ValueError("Training-only shard contains protected rows")
    frame = frame.loc[frame.open_time < cutoff].copy()
    if frame.empty or (frame.open_time >= cutoff).any():
        raise ValueError("Fold cutoff invalid")
    mask = frame[["open_time", "segment_id", "partition"]].copy()
    mask["reason"] = "retained"
    bars = frame.drop(columns=["segment_id", "partition"])
    tables = build_tables(bars, mask, config)
    features = tables["features.csv"]
    indexed = features.set_index(pd.to_datetime(features.open_time, unit="ms", utc=True))
    scaler = TrainScaler.fit(indexed[FEATURES], pd.Timestamp(config.data.train_start),
                             pd.Timestamp(CUTOFF[year]))
    observations = features.copy()
    observations.loc[:, FEATURES] = scaler.transform(indexed[FEATURES]).to_numpy()
    episodes = tables["episodes.csv"]
    if (len(episodes), scaler.fit_count) != EXPECTED[year]:
        raise ValueError("Fold route/scaler count differs from indexed calibration")
    if (episodes.last_target_ms >= cutoff).any() or not (episodes.transitions == 180).all():
        raise ValueError("Fold episodes escape cutoff/horizon")
    selected = {"bars.csv": tables["bars.csv"], "features.csv": features,
                "observations.csv": observations, "episodes.csv": episodes,
                "transitions.csv": tables["transitions.csv"]}
    hashes = {name: _csv_hash(value) for name, value in selected.items()}
    hashes["scaler.json"] = hashlib.sha256(
        (json.dumps(scaler.to_dict(), sort_keys=True) + "\n").encode()
    ).hexdigest()
    view = AcceptedMarket.__new__(AcceptedMarket)
    view._config = config
    view._training_only = True
    view.manifest_sha256 = parent["parent_h1_manifest_sha256"]
    view._bars = selected["bars.csv"].set_index("open_time")
    view._observations = observations.set_index("open_time")
    view._episodes = episodes.set_index("episode_id")
    view._transitions = selected["transitions.csv"]
    view.episode_ids = tuple(int(x) for x in view._episodes.index)
    view._target_keys = {(r.partition, int(r.segment_id), int(r.target_ms))
                         for r in view._transitions.itertuples()}
    view.audit = dict(status="passed", mode="read_only_H1_training_fold",
                      normalizer_refitted=False, fold_refit_at_preparation=True,
                      fit_count=scaler.fit_count, train_episodes=len(episodes),
                      validation_observations_loaded=False, product_hashes=hashes,
                      parent_product_hashes=parent["files"])
    source = TrainingMarket.__new__(TrainingMarket)
    source.config = config
    source._view = view
    source.route_ids = view.episode_ids
    source.audit = view.audit
    source._identity = dict(profile=source.profile,
                            manifest_sha256=view.manifest_sha256,
                            training_shard_manifest_sha256=SHARD_MANIFEST_SHA256,
                            fold=year, cutoff_exclusive_ms=cutoff,
                            scaler_sha256=hashes["scaler.json"], files=hashes,
                            parent_h1_files=parent["parent_h1_file_sha256"])
    if not np.isfinite(observations[FEATURES].to_numpy()).all():
        raise ValueError("Nonfinite fold observations")
    return source


def inspect_fold(year):
    source = build_fold_source(year)
    view = source._view
    return dict(fold=year, cutoff_ms=source.identity()["cutoff_exclusive_ms"],
                episodes=len(source.route_ids), fit_rows=source.audit["fit_count"],
                latest_target_ms=int(view._episodes.last_target_ms.max()),
                source_profile=source.profile, scaler_sha256=source.identity()["scaler_sha256"],
                product_sha256=source.identity()["files"],
                training_shard_manifest_sha256=SHARD_MANIFEST_SHA256,
                validation_observations_loaded=False, trajectories_generated=0,
                warmup_bars=int((view._bars.partition == "warmup").sum()),
                transition_count=len(view._transitions))
