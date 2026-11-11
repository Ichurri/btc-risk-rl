"""Internal final-source audit for immutable, separately authorized pages.

No network access or public command exists here. A future permitted fetcher
must write the page files and pin the manifest before this reader is called.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from btc_risk_rl.config import STEP_MS
from btc_risk_rl.evaluation.historical_path import PERIODS


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_final_binance_bars(source: Path, *, expected_manifest_sha256: str
                            ) -> tuple[pd.DataFrame, dict]:
    """Verify page hashes and exact 2024–2025 coverage including context."""
    source = Path(source)
    manifest_path = source / "manifest.json"
    if source.is_symlink() or manifest_path.is_symlink():
        raise ValueError("Final source symlink invalid")
    if _sha(manifest_path) != expected_manifest_sha256:
        raise ValueError("Final source manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    start, end, steps = PERIODS["final_2024_2025"]
    if (type(manifest) is not dict
            or manifest.get("schema") != "oos_v12_final_raw_v1"
            or manifest.get("status") != "download_complete_not_accepted"
            or manifest.get("source") != "Binance spot API"
            or manifest.get("symbol") != "BTCUSDT"
            or manifest.get("interval") != "4h"
            or manifest.get("start_inclusive_ms") != start - 43 * STEP_MS
            or manifest.get("end_exclusive_ms") != end
            or not isinstance(manifest.get("pages"), list)
            or not manifest["pages"]):
        raise ValueError("Final source manifest provenance or coverage invalid")
    rows = []
    for index, page in enumerate(manifest["pages"]):
        name = f"page-{index:04d}.json"
        path = source / name
        if (type(page) is not dict or page.get("file") != name
                or type(page.get("rows")) is not int
                or not 1 <= page["rows"] <= 1000
                or path.is_symlink() or _sha(path) != page.get("sha256")):
            raise ValueError(f"Final source page hash or identity mismatch: {name}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if (type(payload) is not list or len(payload) != page["rows"]
                or any(type(row) is not list or len(row) != 12 for row in payload)):
            raise ValueError(f"Final source page schema mismatch: {name}")
        rows.extend(payload)
    if len(rows) != steps + 43:
        raise ValueError("Final source bars count incomplete")
    try:
        times = np.asarray([int(row[0]) for row in rows], dtype=np.int64)
        close_times = np.asarray([int(row[6]) for row in rows], dtype=np.int64)
        prices = np.asarray([[float(row[j]) for j in (1, 2, 3, 4, 5)]
                             for row in rows], dtype=np.float64)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError("Final source numeric row invalid") from exc
    if (int(times[0]) != start - 43 * STEP_MS
            or int(times[-1]) != end - STEP_MS
            or not (np.diff(times) == STEP_MS).all()
            or not (close_times == times + STEP_MS - 1).all()):
        raise ValueError("Final source requires contiguous complete candles")
    if (not np.isfinite(prices).all() or (prices[:, :4] <= 0).any()
            or (prices[:, 4] < 0).any()
            or (prices[:, 1] < np.maximum(prices[:, 0], prices[:, 3])).any()
            or (prices[:, 2] > np.minimum(prices[:, 0], prices[:, 3])).any()):
        raise ValueError("Final source OHLCV invalid")
    bars = pd.DataFrame({
        "open_time_ms": times, "close_time_ms": close_times,
        "open": prices[:, 0], "high": prices[:, 1], "low": prices[:, 2],
        "close": prices[:, 3], "volume": prices[:, 4],
    })
    return bars, {
        "source_manifest_sha256": expected_manifest_sha256,
        "partition": "final_2024_2025", "page_count": len(manifest["pages"]),
        "bar_count": len(rows),
    }
