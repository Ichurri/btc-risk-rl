"""Read-only audit of persisted B products, including exhaustive temporal checks."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from btc_risk_rl.config import STEP_MS, Config, utc_ms
from btc_risk_rl.data.binance import sha256
from btc_risk_rl.data.segmentation import (
    EPISODE_COLUMNS,
    HISTORY,
    HORIZON,
    META,
    TRANSITION_COLUMNS,
    coverage,
    partition_bounds,
)
from btc_risk_rl.data.segmented_pipeline import (
    DIAGNOSIS,
    FIT_RULE,
    compare_diagnosis,
    load_policy_sources,
)
from btc_risk_rl.features.market import FEATURES, TrainScaler, market_features


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same_table(actual: pd.DataFrame, expected: pd.DataFrame, name: str):
    actual, expected = actual.copy(), expected.copy()
    if "close_time" in actual and "close_time" in expected:
        actual["close_time"] = actual.close_time.astype("Int64")
        expected["close_time"] = expected.close_time.astype("Int64")
    try:
        pd.testing.assert_frame_equal(
            actual.reset_index(drop=True),
            expected.reset_index(drop=True),
            check_dtype=False,
            check_exact=True,
        )
    except AssertionError as exc:
        raise ValueError(f"Persisted table mismatch: {name}") from exc


def verify_segmented(config: Config, raw: Path, output: Path, diagnosis: Path = DIAGNOSIS) -> dict:
    manifest = json.loads((output / "manifest.json").read_text())
    require(manifest["status"] in {"pending_verification", "accepted"}, "Dataset not verifiable")
    require(manifest["config"] == config.model_dump(mode="json"), "Configuration mismatch")
    require(
        manifest["policy"] == "B_ADR_004" and manifest["fit_rule"] == FIT_RULE, "Policy mismatch"
    )
    require(
        manifest["training_executed"] is False and manifest["final_test_accessed"] is False,
        "Protected protocol flags changed",
    )
    require(
        manifest["validation_mode"] == "one_continuous_path_no_forced_liquidation",
        "Validation mode mismatch",
    )
    required = {
        "mask.csv",
        "bars.csv",
        "features.csv",
        "fit_observations.csv",
        "transitions.csv",
        "episodes.csv",
        "observations.csv",
        "scaler.json",
        "coverage.json",
        "diagnosis_comparison.json",
        "quality-original.json",
    }
    require(
        set(manifest["files"]) in (required, required | {"audit.json"}), "Artifact set mismatch"
    )
    if manifest["status"] == "accepted":
        require("audit.json" in manifest["files"], "Accepted product lacks audit")
    for name, expected_hash in manifest["files"].items():
        require(Path(name).name == name, "Invalid artifact path")
        require(sha256(output / name) == expected_hash, f"Artifact hash mismatch: {name}")
    frame, mask, quality, impact, sources = load_policy_sources(config, raw, diagnosis)
    require(manifest["sources"] == sources, "Source hashes changed")
    require(
        json.loads((output / "quality-original.json").read_text()) == quality,
        "Original quality report mismatch",
    )
    tables = {
        name: pd.read_csv(output / name, float_precision="round_trip")
        for name in sorted(required)
        if name.endswith(".csv")
    }
    same_table(tables["mask.csv"], mask, "mask")
    expected_bars = frame.reset_index(drop=True).merge(
        mask.loc[mask.reason == "retained", META], on="open_time", validate="one_to_one"
    )
    bars, features = tables["bars.csv"], tables["features.csv"]
    same_table(bars, expected_bars, "bars")
    require(not bars.open_time.duplicated().any(), "Duplicate bar")
    require((bars.open_time < utc_ms(config.data.test_start)).all(), "Final test boundary")
    expected_features = []
    for sid, group in bars.groupby("segment_id", sort=True):
        require((np.diff(group.open_time) == STEP_MS).all(), "Noncontiguous segment")
        group = group.set_index(pd.to_datetime(group.open_time, unit="ms", utc=True))
        values = market_features(group).iloc[HISTORY:]
        meta = group.iloc[HISTORY:][META].reset_index(drop=True)
        expected_features.append(pd.concat([meta, values.reset_index(drop=True)], axis=1))
    same_table(features, pd.concat(expected_features, ignore_index=True), "features")
    require(np.isfinite(features[FEATURES].to_numpy()).all(), "Nonfinite features")
    require(not features.open_time.duplicated().any(), "Duplicate observation")

    # Independent exhaustive transition enumeration from timestamps and membership,
    # rather than the preparation loop over adjacent observations.
    observed = dict(zip(features.open_time, features.segment_id))
    expected_trans = []
    for row in bars.itertuples():
        if (
            row.partition != "warmup"
            and observed.get(row.open_time) == row.segment_id
            and observed.get(row.open_time - STEP_MS) == row.segment_id
        ):
            expected_trans.append(
                (row.segment_id, row.partition, row.open_time - STEP_MS, row.open_time)
            )
    same_table(
        tables["transitions.csv"],
        pd.DataFrame(expected_trans, columns=TRANSITION_COLUMNS),
        "transitions",
    )
    trans = tables["transitions.csv"]
    val_lo, val_hi = partition_bounds(config)[-1][1:]
    val = trans.loc[trans.partition == "validation"]
    require(
        val.target_ms.tolist() == list(range(val_lo, val_hi, STEP_MS)),
        "Validation is not a complete continuous path",
    )
    require(val.segment_id.nunique() == 1, "Validation crosses segments")

    # Enumerate every possible window algebraically from independent segment bounds.
    train_lo, train_hi = partition_bounds(config)[1][1:]
    expected_episodes = []
    for sid, group in bars.groupby("segment_id", sort=True):
        first = max(int(group.open_time.min()) + (HISTORY + 1) * STEP_MS, train_lo)
        stop = min(int(group.open_time.max()) + STEP_MS, train_hi)
        for t in range(first, stop - (HORIZON - 1) * STEP_MS, STEP_MS):
            expected_episodes.append(
                (
                    len(expected_episodes),
                    sid,
                    "train",
                    t - STEP_MS,
                    t,
                    t + (HORIZON - 1) * STEP_MS,
                    HORIZON,
                )
            )
    episodes = tables["episodes.csv"]
    same_table(episodes, pd.DataFrame(expected_episodes, columns=EPISODE_COLUMNS), "episodes")
    require(len(episodes) > 0, "No eligible training episodes")
    targets = {(r.segment_id, r.target_ms) for r in trans.itertuples() if r.partition == "train"}
    # Check every transition in every indexed window, not merely the endpoints.
    for row in episodes.itertuples():
        require(
            all(
                (row.segment_id, t) in targets
                for t in range(row.first_target_ms, row.last_target_ms + STEP_MS, STEP_MS)
            ),
            "Episode crosses exclusion or partition",
        )

    eligible = features.loc[features.partition == "train"]
    same_table(tables["fit_observations.csv"], eligible[META], "fit sample")
    scaler_dict = json.loads((output / "scaler.json").read_text())
    scaler = TrainScaler(**scaler_dict)
    require(scaler.columns == FEATURES and scaler.fit_count == len(eligible), "Scaler schema/count")
    require(
        scaler.fit_start == config.data.train_start.isoformat()
        and scaler.fit_end_exclusive == config.data.validation_start.isoformat(),
        "Scaler fitting boundaries",
    )
    # Verify saved moments directly; do not call fit, including during validation auditing.
    expected_mean = eligible[FEATURES].mean().to_numpy()
    expected_scale = eligible[FEATURES].std(ddof=0).to_numpy()
    expected_scale[expected_scale == 0] = 1.0
    require(np.allclose(scaler.mean, expected_mean, rtol=1e-13, atol=1e-15), "Scaler mean mismatch")
    require(
        np.allclose(scaler.scale, expected_scale, rtol=1e-13, atol=1e-15), "Scaler scale mismatch"
    )
    indexed = features.set_index(pd.to_datetime(features.open_time, unit="ms", utc=True))
    z = scaler.transform(indexed[FEATURES]).reset_index(drop=True)
    require(np.isfinite(z.to_numpy()).all(), "Nonfinite normalized values")
    same_table(tables["observations.csv"], pd.concat([features[META], z], axis=1), "observations")
    report = coverage(tables, config)
    require(json.loads((output / "coverage.json").read_text()) == report, "Coverage mismatch")
    comparison = compare_diagnosis(report, impact)
    require(
        json.loads((output / "diagnosis_comparison.json").read_text()) == comparison,
        "Diagnostic comparison mismatch",
    )
    return {
        "status": "passed",
        "policy": "B_ADR_004",
        "source_hashes_verified": sources,
        "persisted_tables_verified": sorted(tables),
        "normalizer_refitted": False,
        "fit_count": scaler.fit_count,
        "train_episodes": len(episodes),
        "validation_transitions": len(val),
        "diagnosis_comparison": comparison,
        "training_executed": False,
        "final_test_accessed": False,
    }
