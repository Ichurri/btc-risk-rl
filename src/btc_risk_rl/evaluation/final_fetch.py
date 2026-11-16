"""Internal paged final-source acquisition for a future separate permit.

There is no public entry point. An authorized supervisor must check the
final partition gate before calling this function. Tests inject a transport
that returns invented rows and make no network requests.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse

from btc_risk_rl.config import STEP_MS
from btc_risk_rl.data.binance import request_bytes
from btc_risk_rl.evaluation.historical_path import PERIODS


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _persist(path: Path, manifest: dict) -> None:
    temp = path.with_suffix(".json.tmp")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(manifest, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def fetch_final_pages(destination: Path, *, endpoint: str,
                      transport=request_bytes) -> dict:
    """Write an immutable, paged candidate; reject missing or altered bars."""
    destination = Path(destination)
    parsed = urlparse(endpoint)
    if (parsed.scheme != "https" or parsed.netloc != "api.binance.com"
            or parsed.path != "/api/v3/klines" or parsed.query or parsed.fragment):
        raise ValueError("Final source endpoint invalid")
    start, end, steps = PERIODS["final_2024_2025"]
    cursor = start - 43 * STEP_MS
    destination.mkdir(parents=True, exist_ok=False)
    manifest_path = destination / "manifest.json"
    manifest = {
        "schema": "oos_v12_final_raw_v1", "status": "downloading",
        "source": "Binance spot API", "symbol": "BTCUSDT", "interval": "4h",
        "start_inclusive_ms": cursor, "end_exclusive_ms": end,
        "started_utc": _utc(), "pages": [],
    }
    _persist(manifest_path, manifest)
    try:
        while cursor < end:
            params = {
                "symbol": "BTCUSDT", "interval": "4h", "startTime": cursor,
                "endTime": end - 1, "limit": 1000, "timeZone": "0",
            }
            raw = transport(endpoint + "?" + urlencode(params))
            if type(raw) is not bytes:
                raise ValueError("Final source response must be bytes")
            name = f"page-{len(manifest['pages']):04d}.json"
            page_path = destination / name
            with page_path.open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            rows = json.loads(raw)
            if (type(rows) is not list or not 1 <= len(rows) <= 1000
                    or any(type(row) is not list or len(row) != 12
                           or type(row[0]) is not int or type(row[6]) is not int
                           for row in rows)):
                raise ValueError("Final source page schema invalid")
            times = [row[0] for row in rows]
            if (times[0] != cursor or times[-1] >= end
                    or any(right - left != STEP_MS
                           for left, right in zip(times, times[1:]))
                    or any(row[6] != row[0] + STEP_MS - 1 for row in rows)):
                raise ValueError("Final source page is not contiguous complete candles")
            manifest["pages"].append({
                "file": name, "sha256": hashlib.sha256(raw).hexdigest(),
                "rows": len(rows), "query": params,
            })
            _persist(manifest_path, manifest)
            cursor = times[-1] + STEP_MS
        if sum(page["rows"] for page in manifest["pages"]) != steps + 43:
            raise ValueError("Final source total coverage invalid")
        manifest["status"] = "download_complete_not_accepted"
        manifest["completed_utc"] = _utc()
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["error"] = f"{type(exc).__name__}: {exc}"
        _persist(manifest_path, manifest)
        raise
    _persist(manifest_path, manifest)
    return manifest
