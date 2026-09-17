import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from btc_risk_rl.config import Config, utc_ms
from btc_risk_rl.data.binance import read_raw, sha256
from btc_risk_rl.data.quality import validate_rows
from btc_risk_rl.features.market import TrainScaler, market_features


def prepare_development(config: Config, raw: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    rows, manifest = read_raw(raw)
    start, end = utc_ms(config.data.warmup_start), utc_ms(config.data.test_start)
    if (manifest["start_inclusive_ms"], manifest["end_exclusive_ms"]) != (start, end):
        raise ValueError("Raw manifest does not match configured coverage")
    frame, quality = validate_rows(rows, start, end, utc_ms(datetime.now(timezone.utc)))
    (output / "quality.json").write_text(json.dumps(quality, indent=2) + "\n")
    if quality["status"] != "passed":
        raise ValueError("Dataset failed quality gate; see quality.json. No features accepted.")
    features = market_features(frame)
    train_start = pd.Timestamp(config.data.train_start)
    val_start = pd.Timestamp(config.data.validation_start)
    test_start = pd.Timestamp(config.data.test_start)
    # Fit on the explicitly bounded training subset, never full development.
    scaler = TrainScaler.fit(features, train_start, val_start)
    scaled = scaler.transform(features)
    (output / "scaler.json").write_text(json.dumps(scaler.to_dict(), indent=2) + "\n")
    partitions = {}
    for name, lo, hi in (("train", train_start, val_start), ("validation", val_start, test_start)):
        # One previous bar supplies the initial observation. Its return is NOT scored.
        mask = (frame.index >= lo.to_pydatetime() - timedelta(hours=4)) & (frame.index < hi)
        joined = frame.loc[mask].join(scaled.loc[mask])
        if not np.isfinite(joined.to_numpy()).all():
            raise ValueError("Nonfinite prepared observations")
        target = output / f"{name}.csv"
        joined.to_csv(target, index=False, float_format="%.17g")
        partitions[name] = {
            "file": target.name,
            "sha256": sha256(target),
            "scored_start": lo.isoformat(),
            "end_exclusive": hi.isoformat(),
            "bars_including_context": len(joined),
            "scored_transitions": len(joined) - 1,
        }
    prepared = {
        "status": "accepted",
        "final_test_accessed": False,
        "config": config.model_dump(mode="json"),
        "partitions": partitions,
        "raw_manifest_sha256": sha256(raw / "manifest.json"),
        "scaler_sha256": sha256(output / "scaler.json"),
        "quality_sha256": sha256(output / "quality.json"),
        "secondary_source_verified": False,
    }
    (output / "manifest.json").write_text(json.dumps(prepared, indent=2) + "\n")
    return prepared
