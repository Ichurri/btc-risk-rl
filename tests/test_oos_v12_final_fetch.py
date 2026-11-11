"""Invented transport only; final market bytes are never requested here."""

import hashlib
import json
from urllib.parse import parse_qs, urlparse

import numpy as np
import pandas as pd
import pytest

from btc_risk_rl.config import STEP_MS
from btc_risk_rl.evaluation.historical_path import PERIODS


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows():
    start, _, steps = PERIODS["final_2024_2025"]
    times = start - 43 * STEP_MS + np.arange(steps + 43, dtype=np.int64) * STEP_MS
    return [[int(t), "100", "101", "99", "100.5", "5",
             int(t + STEP_MS - 1), "0", 1, "0", "0", "0"] for t in times]


def _context(rows):
    rows = rows[:43]
    return pd.DataFrame({
        "open_time_ms": [row[0] for row in rows],
        "close_time_ms": [row[6] for row in rows],
        "open": [float(row[1]) for row in rows],
        "high": [float(row[2]) for row in rows],
        "low": [float(row[3]) for row in rows],
        "close": [float(row[4]) for row in rows],
        "volume": [float(row[5]) for row in rows],
    })


def test_invented_pages_are_saved_once_and_match_h1_context(tmp_path):
    from btc_risk_rl.evaluation.final_fetch import fetch_final_pages
    from btc_risk_rl.evaluation.source_final import load_final_binance_bars

    rows = _rows()
    calls = []

    def transport(url):
        query = parse_qs(urlparse(url).query)
        start = int(query["startTime"][0])
        index = (start - rows[0][0]) // STEP_MS
        calls.append(start)
        return json.dumps(rows[index:index + 1000]).encode()

    root = tmp_path / "invented-final"
    result = fetch_final_pages(root, endpoint="https://example.invalid/api/v3/klines",
                               transport=transport)
    assert result["status"] == "download_complete_not_accepted"
    assert len(result["pages"]) == 5
    assert len(calls) == 5
    assert sum(page["rows"] for page in result["pages"]) == 4429
    bars, provenance = load_final_binance_bars(
        root, expected_manifest_sha256=_sha(root / "manifest.json"),
        expected_h1_context=_context(rows),
    )
    assert len(bars) == 4429
    assert provenance["h1_context_rows_matched"] == 43
    with pytest.raises(FileExistsError):
        fetch_final_pages(root, endpoint="https://example.invalid/api/v3/klines",
                          transport=transport)


def test_invented_gap_fails_and_preserves_partial_manifest(tmp_path):
    from btc_risk_rl.evaluation.final_fetch import fetch_final_pages

    rows = _rows()

    def transport(url):
        start = int(parse_qs(urlparse(url).query)["startTime"][0])
        index = (start - rows[0][0]) // STEP_MS
        page = rows[index:index + 1000]
        if index == 1000:
            page = page[1:]
        return json.dumps(page).encode()

    root = tmp_path / "invented-final"
    with pytest.raises(ValueError, match="contiguous"):
        fetch_final_pages(root, endpoint="https://example.invalid/api/v3/klines",
                          transport=transport)
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["status"] == "failed"
    assert (root / "page-0000.json").exists()
    assert (root / "page-0001.json").exists()
