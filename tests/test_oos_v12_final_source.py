"""Invented Binance-shaped pages test a future final-source reader."""

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
    start, end, steps = PERIODS["final_2024_2025"]
    times = start - 43 * STEP_MS + np.arange(steps + 43, dtype=np.int64) * STEP_MS
    root = tmp_path / "invented-binance-final"
    root.mkdir()
    pages = []
    for number, left in enumerate(range(0, len(times), 1000)):
        page = root / f"page-{number:04d}.json"
        rows = [[int(t), "100", "101", "99", "100.5", "5",
                 int(t + STEP_MS - 1), "0", 1, "0", "0", "0"]
                for t in times[left:left + 1000]]
        page.write_text(json.dumps(rows))
        pages.append({
            "file": page.name, "sha256": _sha(page), "rows": len(rows),
            "query": {"symbol": "BTCUSDT", "interval": "4h",
                      "startTime": int(times[left]), "endTime": end - 1,
                      "limit": 1000, "timeZone": "0"},
        })
    (root / "manifest.json").write_text(json.dumps({
        "schema": "oos_v12_final_raw_v1", "status": "download_complete_not_accepted",
        "source": "Binance spot API", "symbol": "BTCUSDT", "interval": "4h",
        "start_inclusive_ms": int(times[0]), "end_exclusive_ms": end,
        "pages": pages,
    }, sort_keys=True))
    return root


def _accepted_context(root):
    rows = json.loads((root / "page-0000.json").read_text())[:43]
    return pd.DataFrame({
        "open_time_ms": [row[0] for row in rows],
        "close_time_ms": [row[6] for row in rows],
        "open": [float(row[1]) for row in rows],
        "high": [float(row[2]) for row in rows],
        "low": [float(row[3]) for row in rows],
        "close": [float(row[4]) for row in rows],
        "volume": [float(row[5]) for row in rows],
    })


def test_invented_final_pages_extract_exact_contiguous_bars(tmp_path):
    from btc_risk_rl.evaluation.source_final import load_final_binance_bars

    root = _source(tmp_path)
    bars, provenance = load_final_binance_bars(
        root, expected_manifest_sha256=_sha(root / "manifest.json"),
        expected_h1_context=_accepted_context(root),
    )
    assert len(bars) == 4429
    assert list(bars) == ["open_time_ms", "close_time_ms", "open", "high",
                          "low", "close", "volume"]
    assert provenance["source_manifest_sha256"] == _sha(root / "manifest.json")
    assert provenance["page_count"] == 5


def test_final_manifest_pin_rejects_before_page_open(tmp_path, monkeypatch):
    from btc_risk_rl.evaluation.source_final import load_final_binance_bars

    root = _source(tmp_path)
    opened = []
    original = type(root).read_bytes

    def watched(path):
        if path.name.startswith("page-"):
            opened.append(path.name)
        return original(path)

    monkeypatch.setattr(type(root), "read_bytes", watched)
    with pytest.raises(ValueError, match="manifest hash"):
        load_final_binance_bars(root, expected_manifest_sha256="a" * 64,
                                expected_h1_context=_accepted_context(root))
    assert opened == []


def test_final_missing_candle_rejected_even_with_rehashed_page(tmp_path):
    from btc_risk_rl.evaluation.source_final import load_final_binance_bars

    root = _source(tmp_path)
    path = root / "page-0002.json"
    rows = json.loads(path.read_text())
    rows[50][0] += STEP_MS
    rows[50][6] += STEP_MS
    path.write_text(json.dumps(rows))
    manifest = json.loads((root / "manifest.json").read_text())
    manifest["pages"][2]["sha256"] = _sha(path)
    (root / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="contiguous"):
        load_final_binance_bars(root,
                                expected_manifest_sha256=_sha(root / "manifest.json"),
                                expected_h1_context=_accepted_context(root))


@pytest.mark.parametrize("bad_time", [1703448000000.5, "1703448000000.5", True])
def test_final_rejects_noninteger_timestamp_even_if_page_is_rehashed(tmp_path, bad_time):
    from btc_risk_rl.evaluation.source_final import load_final_binance_bars

    root = _source(tmp_path)
    path = root / "page-0000.json"
    rows = json.loads(path.read_text())
    rows[0][0] = bad_time
    path.write_text(json.dumps(rows))
    manifest = json.loads((root / "manifest.json").read_text())
    manifest["pages"][0]["sha256"] = _sha(path)
    (root / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="numeric row"):
        load_final_binance_bars(root,
                                expected_manifest_sha256=_sha(root / "manifest.json"),
                                expected_h1_context=_accepted_context(root))


def test_final_prefix_must_match_accepted_h1_context_exactly(tmp_path):
    from btc_risk_rl.evaluation.source_final import load_final_binance_bars

    root = _source(tmp_path)
    context = _accepted_context(root)
    bars, provenance = load_final_binance_bars(
        root, expected_manifest_sha256=_sha(root / "manifest.json"),
        expected_h1_context=context,
    )
    assert len(bars) == 4429
    assert provenance["h1_context_rows_matched"] == 43
    context.loc[20, "volume"] += 1
    with pytest.raises(ValueError, match="H1 context"):
        load_final_binance_bars(root,
                                expected_manifest_sha256=_sha(root / "manifest.json"),
                                expected_h1_context=context)


def test_final_source_rejects_rehashed_manifest_with_wrong_page_query(tmp_path):
    from btc_risk_rl.evaluation.source_final import load_final_binance_bars

    root = _source(tmp_path)
    context = _accepted_context(root)
    manifest = json.loads((root / "manifest.json").read_text())
    manifest["pages"][2]["query"]["startTime"] += STEP_MS
    (root / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="query"):
        load_final_binance_bars(root,
                                expected_manifest_sha256=_sha(root / "manifest.json"),
                                expected_h1_context=context)
