import json
from urllib.parse import parse_qs, urlparse

import pandas as pd
import pytest
from conftest import synthetic_rows

from btc_risk_rl.config import STEP_MS, utc_ms
from btc_risk_rl.data.binance import fetch_development, read_raw
from btc_risk_rl.data.pipeline import prepare_development
from btc_risk_rl.data.quality import validate_rows

START = int(pd.Timestamp("2022-01-01", tz="UTC").timestamp() * 1000)


def check(rows, n=10):
    return validate_rows(rows, START, START + n * STEP_MS, START + (n + 1) * STEP_MS)


def test_valid_and_identical_duplicate():
    rows = synthetic_rows(START, 10)
    frame, report = check(rows + [rows[2]])
    assert report["status"] == "passed"
    assert report["duplicates_removed"] == 1
    assert len(frame) == 10


def test_conflicting_duplicate_fails():
    rows = synthetic_rows(START, 10)
    changed = rows[2].copy()
    changed[4] = "101"
    _, report = check(rows + [changed])
    assert report["status"] == "failed"


def test_gap_is_not_imputed():
    rows = synthetic_rows(START, 10)
    rows.pop(3)
    frame, report = check(rows)
    assert len(frame) == 9
    assert report["status"] == "failed"
    assert len(report["missing_open_times_utc"]) == 1


@pytest.mark.parametrize(
    "column,value", [(1, "0"), (2, "1"), (3, "1000"), (4, "nan"), (5, "-1"), (6, 123)]
)
def test_invalid_market_data_rejected(column, value):
    rows = synthetic_rows(START, 10)
    rows[3][column] = value
    _, report = check(rows)
    assert report["status"] == "failed"


def test_incomplete_excluded_and_gate_fails():
    rows = synthetic_rows(START, 10)
    frame, report = validate_rows(rows, START, START + 10 * STEP_MS, START + 9 * STEP_MS)
    assert len(frame) == 9
    assert report["incomplete_removed"] == 1
    assert report["status"] == "failed"


def test_zero_volume_recorded_not_dropped():
    rows = synthetic_rows(START, 10)
    rows[3][5] = "0"
    frame, report = check(rows)
    assert len(frame) == 10 and report["zero_volume_bars"] == 1
    assert report["status"] == "passed"


def test_final_rows_blocked():
    boundary = int(pd.Timestamp("2024-01-01", tz="UTC").timestamp() * 1000)
    with pytest.raises(ValueError):
        validate_rows(
            synthetic_rows(boundary, 10), boundary, boundary + STEP_MS * 10, boundary + STEP_MS * 11
        )


def make_transport(config, remove=None):
    start, end = utc_ms(config.data.warmup_start), utc_ms(config.data.test_start)
    all_rows = synthetic_rows(start, (end - start) // STEP_MS)
    if remove is not None:
        all_rows.pop(remove)
    calls = []

    def transport(url):
        q = parse_qs(urlparse(url).query)
        lo, hi = int(q["startTime"][0]), int(q["endTime"][0])
        assert hi < end
        calls.append((lo, hi))
        return json.dumps([r for r in all_rows if lo <= r[0] <= hi][:1000]).encode()

    return transport, calls


def test_download_prepare_manifest_and_partitions(config, tmp_path):
    transport, calls = make_transport(config)
    raw, processed = tmp_path / "raw", tmp_path / "processed"
    manifest = fetch_development(config, raw, transport)
    assert len(calls) > 1 and manifest["final_test_accessed"] is False
    prepared = prepare_development(config, raw, processed)
    assert prepared["status"] == "accepted"
    train = pd.read_csv(processed / "train.csv")
    val = pd.read_csv(processed / "validation.csv")
    assert len(train) == 10957 and len(val) == 2191
    assert train.iloc[-1].open_time < utc_ms(config.data.validation_start)
    assert val.iloc[1].open_time == utc_ms(config.data.validation_start)
    assert val.iloc[-1].open_time < utc_ms(config.data.test_start)
    scaler = json.loads((processed / "scaler.json").read_text())
    assert scaler["fit_count"] == 10956
    assert scaler["fit_end_exclusive"].startswith("2023-01-01")
    assert not (processed / "test.csv").exists()


def test_hash_tampering_rejected(config, tmp_path):
    transport, _ = make_transport(config)
    raw = tmp_path / "raw"
    fetch_development(config, raw, transport)
    (raw / "page-0000.json").write_text("[]")
    with pytest.raises(ValueError, match="hash"):
        read_raw(raw)


def test_quality_failure_cannot_emit_features(config, tmp_path):
    transport, _ = make_transport(config, remove=300)
    raw, output = tmp_path / "raw", tmp_path / "processed"
    fetch_development(config, raw, transport)
    with pytest.raises(ValueError, match="quality gate"):
        prepare_development(config, raw, output)
    assert (output / "quality.json").exists()
    assert not (output / "train.csv").exists()


def test_pagination_no_progress_fails(config, tmp_path):
    row = synthetic_rows(utc_ms(config.data.warmup_start), 1)
    with pytest.raises(ValueError, match="no progress"):
        fetch_development(config, tmp_path / "raw", lambda _: json.dumps(row).encode())
    assert json.loads((tmp_path / "raw/manifest.json").read_text())["status"] == "failed"
