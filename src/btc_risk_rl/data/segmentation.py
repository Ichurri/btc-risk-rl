"""Policy B temporal tables. No price imputation, fitting, downloading or training."""

import numpy as np
import pandas as pd

from btc_risk_rl.config import STEP_MS, Config, guard_development, utc_ms
from btc_risk_rl.data.quality import validate_rows
from btc_risk_rl.features.market import market_features

HISTORY = 42
HORIZON = 180
META = ["open_time", "segment_id", "partition"]
TRANSITION_COLUMNS = ["segment_id", "partition", "observation_ms", "target_ms"]
EPISODE_COLUMNS = [
    "episode_id",
    "segment_id",
    "partition",
    "initial_observation_ms",
    "first_target_ms",
    "last_target_ms",
    "transitions",
]


def partition_bounds(config: Config):
    d = config.data
    return [
        ("warmup", utc_ms(d.warmup_start), utc_ms(d.train_start)),
        ("train", utc_ms(d.train_start), utc_ms(d.validation_start)),
        ("validation", utc_ms(d.validation_start), utc_ms(d.test_start)),
    ]


def build_mask(rows: list, config: Config, approved: dict[int, int | None]):
    """Require exact approved missing timestamps and early close values, then quarantine."""
    bounds = partition_bounds(config)
    start, end = bounds[0][1], bounds[-1][2]
    guard_development(start, end)
    train_lo, train_hi = bounds[1][1:]
    if any(not train_lo <= t < train_hi for t in approved):
        raise ValueError("Policy B exclusions must belong to training")
    # Do not silently truncate malformed closing timestamps in the strict validator.
    for row in rows:
        if not isinstance(row, list) or len(row) != 12:
            raise ValueError("Expected Binance kline schema with 12 fields")
        if int(row[6]) != float(row[6]) or not int(row[0]) <= int(row[6]) < int(row[0]) + STEP_MS:
            raise ValueError("Invalid closing timestamp")
    frame, quality = validate_rows(rows, start, end, end + STEP_MS)
    if (
        quality.get("invalid_ohlcv_or_open_time_count", 0)
        or quality["incomplete_removed"]
        or any(e.startswith("Conflicting duplicate") for e in quality["errors"])
    ):
        raise ValueError("Invalid source data beyond approved temporal anomalies")
    missing = {utc_ms(pd.Timestamp(t)) for t in quality["missing_open_times_utc"]}
    early = {
        int(r.open_time): int(r.close_time)
        for r in frame.itertuples()
        if r.close_time < r.open_time + STEP_MS - 1
    }
    if missing != {t for t, close in approved.items() if close is None} or early != {
        t: close for t, close in approved.items() if close is not None
    }:
        raise ValueError("Source anomalies do not exactly match approved inventory")
    excluded = set(approved)
    reopening = {t + STEP_MS for t in excluded if t + STEP_MS not in excluded}
    if any(not train_lo <= t < train_hi for t in reopening):
        raise ValueError("Policy B reopening must belong to training")
    observed = dict(zip(frame.open_time, frame.close_time))
    records, segment, block, previous_retained = [], -1, -1, False
    for t in range(start, end, STEP_MS):
        if t in excluded and t - STEP_MS not in excluded:
            block += 1
        reason = (
            "missing"
            if t in missing
            else "early_close"
            if t in early
            else "reopening"
            if t in reopening
            else "retained"
        )
        retained = reason == "retained"
        if retained and not previous_retained:
            segment += 1
        part = next(name for name, lo, hi in bounds if lo <= t < hi)
        records.append(
            {
                "open_time": t,
                "partition": part,
                "present": t in observed,
                "close_time": observed.get(t),
                "expected_close_time": t + STEP_MS - 1,
                "reason": reason,
                "block_id": -1 if retained else block,
                "segment_id": segment if retained else -1,
            }
        )
        previous_retained = retained
    mask = pd.DataFrame(records)
    mask["close_time"] = mask.close_time.astype("Int64")
    return frame, mask, quality


def build_tables(frame: pd.DataFrame, mask: pd.DataFrame, config: Config) -> dict:
    """Create all finite observations and all possible training windows, once per start."""
    if config.environment.episode_steps != HORIZON:
        raise ValueError("ADR-004 preparation requires 180 transitions")
    retained = mask.loc[mask.reason == "retained", META].set_index("open_time")
    bars = frame.reset_index(drop=True).merge(retained, on="open_time", validate="one_to_one")
    feature_parts = []
    for _, group in bars.groupby("segment_id", sort=True):
        indexed = group.set_index(pd.to_datetime(group.open_time, unit="ms", utc=True))
        values = market_features(indexed)
        # Missing warmup is explicit; nonfinite values after warmup are errors, not dropped.
        valid = values.iloc[HISTORY:]
        if not np.isfinite(valid.to_numpy()).all():
            raise ValueError("Nonfinite features after segment warmup")
        part = group.iloc[HISTORY:][META].reset_index(drop=True)
        feature_parts.append(pd.concat([part, valid.reset_index(drop=True)], axis=1))
    features = pd.concat(feature_parts, ignore_index=True)
    fit = features.loc[features.partition == "train", META].reset_index(drop=True)
    transitions = []
    for sid, group in features.groupby("segment_id", sort=True):
        times = group.open_time.to_numpy(dtype=np.int64)
        for i in range(1, len(group)):
            part = group.iloc[i].partition
            if part != "warmup":
                transitions.append((sid, part, int(times[i - 1]), int(times[i])))
    trans = pd.DataFrame(transitions, columns=TRANSITION_COLUMNS)
    episodes = []
    for sid, group in trans.loc[trans.partition == "train"].groupby("segment_id", sort=True):
        targets = group.target_ms.to_numpy(dtype=np.int64)
        for i in range(len(targets) - HORIZON + 1):
            episodes.append(
                (
                    len(episodes),
                    sid,
                    "train",
                    int(targets[i] - STEP_MS),
                    int(targets[i]),
                    int(targets[i + HORIZON - 1]),
                    HORIZON,
                )
            )
    return {
        "mask.csv": mask,
        "bars.csv": bars,
        "features.csv": features,
        "fit_observations.csv": fit,
        "transitions.csv": trans,
        "episodes.csv": pd.DataFrame(episodes, columns=EPISODE_COLUMNS),
    }


def iso_ms(t: int) -> str:
    return pd.Timestamp(t, unit="ms", tz="UTC").isoformat(timespec="milliseconds")


def coverage(tables: dict, config: Config) -> dict:
    mask, bars = tables["mask.csv"], tables["bars.csv"]
    trans, episodes = tables["transitions.csv"], tables["episodes.csv"]
    result = {}
    for name, lo, hi in partition_bounds(config):
        selected = mask.loc[mask.partition == name]
        details = []
        for sid, group in bars.groupby("segment_id", sort=True):
            n = int(((group.open_time >= lo) & (group.open_time < hi)).sum())
            if not n:
                continue
            count = int(((trans.segment_id == sid) & (trans.partition == name)).sum())
            details.append(
                dict(
                    start_utc=iso_ms(int(group.open_time.min())),
                    end_exclusive_utc=iso_ms(int(group.open_time.max()) + STEP_MS),
                    raw_partition_bars=n,
                    usable_transitions=count,
                    candidate_starts_180=max(0, count - HORIZON + 1),
                    nonoverlapping_windows_180=count // HORIZON,
                )
            )
        full_segment_ids = set(episodes.segment_id)
        reachable = trans.loc[(trans.partition == name) & trans.segment_id.isin(full_segment_ids)]
        result[name] = dict(
            expected_bars=len(selected),
            received_bars=int(selected.present.sum()),
            exclusions={
                reason: int((selected.reason == reason).sum())
                for reason in ("missing", "early_close", "reopening")
            },
            segments=len(details),
            retained_partition_bars=sum(d["raw_partition_bars"] for d in details),
            usable_transitions=sum(d["usable_transitions"] for d in details),
            candidate_starts_180=sum(d["candidate_starts_180"] for d in details),
            nonoverlapping_windows_180=sum(d["nonoverlapping_windows_180"] for d in details),
            segments_with_180=sum(d["candidate_starts_180"] > 0 for d in details),
            episode_reachable_targets=len(reachable) if name == "train" else None,
            details=details,
        )
    return result
