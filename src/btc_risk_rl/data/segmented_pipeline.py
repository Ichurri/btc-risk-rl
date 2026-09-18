"""Offline preparation restricted to the historical inventory approved in ADR-004."""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from btc_risk_rl.config import Config, guard_development, utc_ms
from btc_risk_rl.data.binance import read_raw, sha256
from btc_risk_rl.data.segmentation import build_mask, build_tables, coverage
from btc_risk_rl.features.market import FEATURES, TrainScaler

DIAGNOSIS = Path("docs/evidence/diagnosis/inventory")
FIT_RULE = "all_finite_train_observations_once_including_short_segments_and_terminal_states"


def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def load_policy_sources(config: Config, raw: Path, diagnosis: Path):
    # Inspect declared bounds before hashing or reading a single data page.
    manifest = json.loads((raw / "manifest.json").read_text())
    guard_development(manifest["start_inclusive_ms"], manifest["end_exclusive_ms"])
    start, end = utc_ms(config.data.warmup_start), utc_ms(config.data.test_start)
    if (manifest["start_inclusive_ms"], manifest["end_exclusive_ms"]) != (start, end):
        raise ValueError("Raw manifest does not match configured coverage")
    if (manifest["symbol"], manifest["interval"]) != ("BTCUSDT", "4h"):
        raise ValueError("Raw instrument mismatch")
    impact = json.loads((diagnosis / "impact.json").read_text())
    if sha256(raw / "manifest.json") != impact["raw_manifest_sha256"]:
        raise ValueError("Raw manifest differs from approved diagnostic source")
    approved = {}
    with (diagnosis / "inventory.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            t = utc_ms(pd.Timestamp(r["open_utc"]))
            if (
                t in approved
                or r["partition"] != "train"
                or r["type"] not in {"missing", "early_close"}
            ):
                raise ValueError("Invalid approved inventory")
            approved[t] = None if r["type"] == "missing" else utc_ms(pd.Timestamp(r["close_utc"]))
    if len(approved) != 36 or sum(v is None for v in approved.values()) != 16:
        raise ValueError("ADR-004 requires the 16 missing and 20 early-close intervals")
    rows, _ = read_raw(raw)
    frame, mask, quality = build_mask(rows, config, approved)
    reopen = mask.loc[mask.reason == "reopening", "open_time"].tolist()
    if (
        reopen != [utc_ms(pd.Timestamp(t)) for t in impact["reopening_candidates"]]
        or len(reopen) != 20
    ):
        raise ValueError("Reopenings differ from approved diagnosis")
    sources = {
        "raw_manifest_sha256": sha256(raw / "manifest.json"),
        "inventory_sha256": sha256(diagnosis / "inventory.csv"),
        "impact_sha256": sha256(diagnosis / "impact.json"),
    }
    return frame, mask, quality, impact, sources


def compare_diagnosis(report: dict, impact: dict) -> dict:
    expected = impact["scenarios"]["B_quarantine_plus_reopening"]
    for part in ("train", "validation"):
        for key, value in expected[part].items():
            if report[part][key] != value:
                raise ValueError(f"Diagnostic coverage mismatch: {part}.{key}")
    for part, counts in impact["counts"].items():
        actual = report[part]
        if (
            actual["expected_bars"] != counts["expected"]
            or actual["received_bars"] != counts["received"]
            or actual["exclusions"]["missing"] != counts["missing"]
            or actual["exclusions"]["early_close"] != counts["early_close"]
        ):
            raise ValueError(f"Diagnostic count mismatch: {part}")
    return {
        "status": "matched",
        "differences": [],
        "validation_windows_180": "diagnostic_count_only_not_evaluation_episodes",
    }


def prepare_segmented(config: Config, raw: Path, output: Path, diagnosis: Path = DIAGNOSIS) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    try:
        frame, mask, quality, impact, sources = load_policy_sources(config, raw, diagnosis)
        tables = build_tables(frame, mask, config)
        report = coverage(tables, config)
        comparison = compare_diagnosis(report, impact)
        features = tables["features.csv"]
        indexed = features.set_index(pd.to_datetime(features.open_time, unit="ms", utc=True))
        scaler = TrainScaler.fit(
            indexed[FEATURES],
            pd.Timestamp(config.data.train_start),
            pd.Timestamp(config.data.validation_start),
        )
        if scaler.fit_count != len(tables["fit_observations.csv"]):
            raise ValueError("Scaler eligibility mismatch")
        write_json(output / "scaler.json", scaler.to_dict())
        # Production transformation also uses the persisted object, never a validation fit.
        restored = TrainScaler(**json.loads((output / "scaler.json").read_text()))
        normalized = restored.transform(indexed[FEATURES]).reset_index(drop=True)
        if not np.isfinite(normalized.to_numpy()).all():
            raise ValueError("Nonfinite normalized observations")
        tables["observations.csv"] = pd.concat(
            [features[["open_time", "segment_id", "partition"]], normalized], axis=1
        )
        for name, table in tables.items():
            table.to_csv(output / name, index=False, float_format="%.17g")
        write_json(output / "coverage.json", report)
        write_json(output / "diagnosis_comparison.json", comparison)
        write_json(output / "quality-original.json", quality)
        files = {p.name: sha256(p) for p in sorted(output.iterdir())}
        manifest = dict(
            schema_version=1,
            status="pending_verification",
            policy="B_ADR_004",
            acceptance_scope="development_data_under_policy_B_not_training_authorization",
            created_at_utc=datetime.now(timezone.utc).isoformat(),
            config=config.model_dump(mode="json"),
            sources=sources,
            files=files,
            fit_rule=FIT_RULE,
            training_executed=False,
            final_test_accessed=False,
            validation_mode="one_continuous_path_no_forced_liquidation",
            secondary_source_verified=False,
        )
        write_json(output / "manifest.json", manifest)
        from btc_risk_rl.data.segmented_audit import verify_segmented

        audit = verify_segmented(config, raw, output, diagnosis)
        write_json(output / "audit.json", audit)
        manifest["files"]["audit.json"] = sha256(output / "audit.json")
        manifest["status"] = "accepted"
        write_json(output / "manifest.json", manifest)
        return manifest
    except Exception as exc:
        # A partially written product is never mistaken for an accepted dataset.
        path = output / "manifest.json"
        if path.exists():
            failed = json.loads(path.read_text())
            failed["status"] = "failed"
            write_json(path, failed)
        write_json(output / "failure.json", {"status": "failed", "error": str(exc)})
        raise
