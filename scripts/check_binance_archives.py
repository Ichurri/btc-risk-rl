"""Same-publisher corroboration, not a new source or replacement dataset."""

import csv
import hashlib
import io
import json
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from btc_risk_rl.config import FINAL_START, STEP_MS, guard_development
from btc_risk_rl.data.binance import read_raw, request_bytes

rows, _ = read_raw(Path("data/raw/development"))
by_time = {int(r[0]): r for r in rows}
q = json.loads(Path("docs/evidence/quality-real.json").read_text())
targets = set(q["invalid_open_times_ms"]) | {
    int(datetime.fromisoformat(t).timestamp() * 1000) for t in q["missing_open_times_utc"]
}
months = sorted({datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m") for t in targets})
out = Path("data/diagnosis/archives")
out.mkdir(parents=True, exist_ok=False)


def check(month):
    lo = datetime.fromisoformat(month + "-01T00:00:00+00:00")
    assert lo < FINAL_START
    name = f"BTCUSDT-4h-{month}.zip"
    url = "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/4h/" + name
    result = {"month": month, "url": url}
    try:
        payload = request_bytes(url)
        (out / name).write_bytes(payload)
        checksum = request_bytes(url + ".CHECKSUM")
        (out / (name + ".CHECKSUM")).write_bytes(checksum)
        digest = hashlib.sha256(payload).hexdigest()
        if digest != checksum.decode().split()[0]:
            raise ValueError("Archive checksum failed")
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            entries = list(csv.reader(io.StringIO(z.read(z.namelist()[0]).decode())))
        data = {int(r[0]): r for r in entries}
        guard_development(min(data), max(data) + STEP_MS)
        observations = []
        for t in sorted(targets):
            if datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m") != month:
                continue
            r = data.get(t)
            api = by_time.get(t)
            observations.append(
                {
                    "open_ms": t,
                    "archive_present": r is not None,
                    "api_present": api is not None,
                    "field_differences": []
                    if r is None or api is None
                    else [
                        {"index": i, "api": str(api[i]), "archive": r[i]}
                        for i in range(11)
                        if Decimal(str(api[i])) != Decimal(r[i])
                    ],
                    "same_first_11_fields": None
                    if r is None or api is None
                    else all(Decimal(str(a)) == Decimal(str(b)) for a, b in zip(r[:11], api[:11])),
                }
            )
        result.update(status="verified_checksum", sha256=digest, observations=observations)
    except Exception as exc:
        result.update(status="unavailable", error=f"{type(exc).__name__}: {exc}")
    return result


with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(check, months))
report = {
    "source": "Binance archives, same publisher, derived from klines API; not independent confirmation",
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "final_test_accessed": False,
    "results": results,
}
Path("docs/evidence/diagnosis/archive-comparison.json").write_text(
    json.dumps(report, indent=2) + "\n"
)
print(json.dumps({r["month"]: r["status"] for r in results}, indent=2))
