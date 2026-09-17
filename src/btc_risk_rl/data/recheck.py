"""Re-query anomalous development bars without rewriting the original dataset."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd

from btc_risk_rl.config import STEP_MS, Config, guard_development, utc_ms
from btc_risk_rl.data.binance import read_raw, request_bytes, sha256
from btc_risk_rl.data.quality import validate_rows


def recheck_anomalies(config: Config, raw: Path, output: Path, transport=request_bytes):
    rows, _ = read_raw(raw)
    start, end = utc_ms(config.data.warmup_start), utc_ms(config.data.test_start)
    _, report = validate_rows(rows, start, end, utc_ms(datetime.now(timezone.utc)))
    missing = {int(pd.Timestamp(t).timestamp() * 1000) for t in report["missing_open_times_utc"]}
    targets = sorted(missing | set(report.get("invalid_open_times_ms", [])))
    original = {int(r[0]): r for r in rows}
    output.mkdir(parents=True, exist_ok=False)

    def query(t):
        guard_development(t, t + STEP_MS)
        params = dict(
            symbol="BTCUSDT",
            interval="4h",
            startTime=t,
            endTime=t + STEP_MS - 1,
            limit=1000,
            timeZone="0",
        )
        entry = {"open_time_ms": t, "originally_missing": t in missing, "query": params}
        try:
            payload = transport(config.data.endpoint + "?" + urlencode(params))
            file = output / f"bar-{t}.json"
            file.write_bytes(payload)
            found = json.loads(payload)
            if not isinstance(found, list):
                raise ValueError("Invalid response")
            if any(int(r[0]) != t for r in found):
                raise ValueError("Response outside exact requested bar")
            match = [r for r in found if int(r[0]) == t]
            entry.update(file=file.name, sha256=sha256(file), returned_rows=len(found))
            if not match:
                entry["status"] = "still_missing"
            elif len(match) != 1:
                entry["status"] = "ambiguous_response"
            else:
                r = match[0]
                entry["status"] = "unchanged" if original.get(t) == r else "changed"
                entry["close_time_ms"] = int(r[6])
                entry["standard_close"] = int(r[6]) == t + STEP_MS - 1
        except Exception as exc:
            entry.update(status="request_failed", error=f"{type(exc).__name__}: {exc}")
        return entry

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(query, targets))
    audit = {
        "performed_at_utc": datetime.now(timezone.utc).isoformat(),
        "raw_manifest_sha256": sha256(raw / "manifest.json"),
        "final_test_accessed": False,
        "original_data_modified": False,
        "counts": {
            state: sum(r["status"] == state for r in results)
            for state in sorted({r["status"] for r in results})
        },
        "results": results,
    }
    (output / "recheck.json").write_text(json.dumps(audit, indent=2) + "\n")
    return audit
