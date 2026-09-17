"""Inspect same-source 1h records around anomalies; do not replace 4h bars."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode

from btc_risk_rl.config import STEP_MS, guard_development
from btc_risk_rl.data.binance import read_raw, request_bytes, sha256

rows, _ = read_raw(Path("data/raw/development"))
original = {int(r[0]): r for r in rows}
q = json.loads(Path("docs/evidence/quality-real.json").read_text())
missing = {int(datetime.fromisoformat(t).timestamp() * 1000) for t in q["missing_open_times_utc"]}
early = set(q["invalid_open_times_ms"])
output = Path("data/diagnosis/hourly")
output.mkdir(parents=True, exist_ok=False)


def query(t):
    end = t + STEP_MS
    while end in missing:
        end += STEP_MS
    end += 2 * STEP_MS
    start = t - STEP_MS
    guard_development(start, end)
    params = dict(
        symbol="BTCUSDT", interval="1h", startTime=start, endTime=end - 1, limit=1000, timeZone="0"
    )
    result = {"event_start_ms": t, "query": params}
    try:
        payload = request_bytes("https://api.binance.com/api/v3/klines?" + urlencode(params))
        file = output / f"{t}.json"
        file.write_bytes(payload)
        hourly = json.loads(payload)
        if not isinstance(hourly, list) or any(not start <= int(r[0]) < end for r in hourly):
            raise ValueError("Unexpected response")
        sub = [r for r in hourly if t <= int(r[0]) < t + STEP_MS]
        aggregated = None
        if sub:
            aggregated = [
                Decimal(sub[0][1]),
                max(Decimal(r[2]) for r in sub),
                min(Decimal(r[3]) for r in sub),
                Decimal(sub[-1][4]),
                sum(Decimal(r[5]) for r in sub),
            ]
        result.update(
            status="checked",
            file=file.name,
            sha256=sha256(file),
            early_bar_hourly_ohlcv_matches=aggregated == [Decimal(x) for x in original[t][1:6]],
            hourly_bars_inside_early_bar=len(sub),
            missing_4h_with_hourly_records={
                str(m): sum(m <= int(r[0]) < m + STEP_MS for r in hourly)
                for m in sorted(missing)
                if t < m < end
            },
            hourly_open_close_ms=[[int(r[0]), int(r[6])] for r in hourly],
        )
    except Exception as exc:
        result.update(status="unavailable", error=str(exc))
    return result


with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(query, sorted(early)))
Path("docs/evidence/diagnosis/hourly-comparison.json").write_text(
    json.dumps(
        {
            "source": "Same Binance API, 1h for diagnosis only",
            "final_test_accessed": False,
            "results": results,
        },
        indent=2,
    )
    + "\n"
)
print(
    json.dumps(
        {
            "checked": sum(r["status"] == "checked" for r in results),
            "ohlcv_matches": sum(r.get("early_bar_hourly_ohlcv_matches", False) for r in results),
        },
        indent=2,
    )
)
