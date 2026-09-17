"""Download original Binance pages with bounds, hashes and fail-closed validation."""

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from btc_risk_rl.config import STEP_MS, Config, guard_development, utc_ms


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def request_bytes(url: str) -> bytes:
    for attempt in range(3):
        try:
            with urlopen(
                Request(url, headers={"User-Agent": "btc-risk-rl/0.1 research"}), timeout=20
            ) as response:
                return response.read()
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
            delay = min(float(exc.headers.get("Retry-After", 2**attempt)), 30)
            time.sleep(delay)
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("Request attempts exhausted")


def fetch_development(config: Config, destination: Path, transport=request_bytes) -> dict:
    start, end = utc_ms(config.data.warmup_start), utc_ms(config.data.test_start)
    guard_development(start, end)
    # Refuse to overwrite existing evidence. Interrupted downloads remain inspectable.
    destination.mkdir(parents=True, exist_ok=False)
    manifest = {
        "schema_version": 1,
        "status": "downloading",
        "source": "Binance spot API",
        "symbol": config.data.symbol,
        "interval": config.data.interval,
        "start_inclusive_ms": start,
        "end_exclusive_ms": end,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "final_test_accessed": False,
        "pages": [],
    }
    path = destination / "manifest.json"

    def save():
        path.write_text(json.dumps(manifest, indent=2) + "\n")

    save()
    cursor = start
    try:
        while cursor < end:
            params = dict(
                symbol=config.data.symbol,
                interval="4h",
                startTime=cursor,
                endTime=end - 1,
                limit=1000,
                timeZone="0",
            )
            payload = transport(config.data.endpoint + "?" + urlencode(params))
            page_path = destination / f"page-{len(manifest['pages']):04d}.json"
            page_path.write_bytes(payload)
            rows = json.loads(payload)
            if not isinstance(rows, list) or not rows:
                raise ValueError("Empty or invalid response before requested end")
            times = [int(row[0]) for row in rows]
            if min(times) < start or max(times) >= end:
                raise ValueError("Response outside development boundary")
            next_cursor = max(times) + STEP_MS
            if next_cursor <= cursor:
                raise ValueError("Pagination made no progress")
            manifest["pages"].append(
                {
                    "file": page_path.name,
                    "sha256": sha256(page_path),
                    "query": params,
                    "rows": len(rows),
                }
            )
            save()
            cursor = next_cursor
        manifest["status"] = "download_complete_not_quality_accepted"
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        save()
    return manifest


def read_raw(destination: Path) -> tuple[list, dict]:
    manifest = json.loads((destination / "manifest.json").read_text())
    guard_development(manifest["start_inclusive_ms"], manifest["end_exclusive_ms"])
    if manifest["status"] != "download_complete_not_quality_accepted":
        raise ValueError("Incomplete raw download")
    rows = []
    for page in manifest["pages"]:
        name = page["file"]
        if Path(name).name != name:
            raise ValueError("Invalid page path")
        path = destination / name
        if sha256(path) != page["sha256"]:
            raise ValueError("Raw data hash mismatch")
        rows.extend(json.loads(path.read_text()))
    return rows, manifest
