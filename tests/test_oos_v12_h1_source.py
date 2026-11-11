"""The future H1 source adapter is tested with invented development rows."""

import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from btc_risk_rl.config import STEP_MS
from btc_risk_rl.evaluation.historical_path import PERIODS


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source(tmp_path):
    start, _, steps = PERIODS["technical_2023"]
    n = steps + 43
    times = start - 43 * STEP_MS + np.arange(n, dtype=np.int64) * STEP_MS
    prices = 100 + np.arange(n) * 0.001
    source = tmp_path / "invented-h1"
    source.mkdir()
    pd.DataFrame({
        "open_time": times, "open": prices, "high": prices + 0.3,
        "low": prices - 0.3, "close": prices + 0.1,
        "volume": np.full(n, 5.0), "close_time": times + STEP_MS - 1,
        "segment_id": np.full(n, 10),
        "partition": ["train"] * 43 + ["validation"] * steps,
    }).to_csv(source / "bars.csv", index=False, float_format="%.17g")
    (source / "manifest.json").write_text(json.dumps({
        "status": "accepted", "policy": "B_ADR_004",
        "acceptance_scope": "development_data_under_policy_B_not_training_authorization",
        "files": {"bars.csv": _sha(source / "bars.csv")},
        "final_test_accessed": False,
        "sources": {"raw_manifest_sha256": "a" * 64},
    }))
    return source


def test_invented_h1_source_yields_exact_technical_export_rows(tmp_path):
    from btc_risk_rl.evaluation.source_h1 import load_h1_technical_bars

    source = _source(tmp_path)
    bars, provenance = load_h1_technical_bars(
        source, expected_h1_manifest_sha256=_sha(source / "manifest.json"),
        expected_raw_manifest_sha256="a" * 64,
    )
    assert list(bars) == ["open_time_ms", "close_time_ms", "open", "high",
                          "low", "close", "volume"]
    assert len(bars) == 2233
    assert provenance["h1_bars_sha256"] == _sha(source / "bars.csv")
    assert provenance["source_manifest_sha256"] == _sha(source / "manifest.json")


def test_wrong_h1_manifest_rejected_before_bars_open(tmp_path, monkeypatch):
    from btc_risk_rl.evaluation.source_h1 import load_h1_technical_bars

    source = _source(tmp_path)
    opened = []
    original = pd.read_csv

    def watched(path, *args, **kwargs):
        opened.append(str(path))
        return original(path, *args, **kwargs)

    monkeypatch.setattr(pd, "read_csv", watched)
    with pytest.raises(ValueError, match="manifest hash"):
        load_h1_technical_bars(source, expected_h1_manifest_sha256="b" * 64,
                               expected_raw_manifest_sha256="a" * 64)
    assert opened == []


def test_h1_partition_tampering_fails_even_with_rehashed_csv(tmp_path):
    from btc_risk_rl.evaluation.source_h1 import load_h1_technical_bars

    source = _source(tmp_path)
    bars = pd.read_csv(source / "bars.csv")
    bars.loc[100, "partition"] = "train"
    bars.to_csv(source / "bars.csv", index=False)
    manifest = json.loads((source / "manifest.json").read_text())
    manifest["files"]["bars.csv"] = _sha(source / "bars.csv")
    (source / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="partition"):
        load_h1_technical_bars(source,
                               expected_h1_manifest_sha256=_sha(source / "manifest.json"),
                               expected_raw_manifest_sha256="a" * 64)
