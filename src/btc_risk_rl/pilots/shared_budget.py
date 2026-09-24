"""Global lock and read-only debits from other registered campaign ledgers."""

import fcntl
import hashlib
import json
import math
import time
from datetime import datetime
from pathlib import Path

from btc_risk_rl.pilots.budget import LA_PAZ, utc


class SharedBudget:
    def __init__(self, artifacts, campaign_name, *, now):
        self.root = Path(artifacts)
        self.root.mkdir(parents=True, exist_ok=True)
        self.audit = self.root / "shared-pilot-budget"
        self.audit.mkdir(exist_ok=True)
        self.lock = (self.audit / "global.lock").open("a")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self.lock.close()
            raise ValueError("Another pilot holds the global daily budget") from exc
        self.external_seconds = 0.0
        self.sources = []
        self.day = datetime.fromtimestamp(now, LA_PAZ).date().isoformat()
        self.name = campaign_name
        try:
            for path in sorted(self.root.glob("p*-approved-v*/ledger.jsonl")):
                if path.parent.name == campaign_name:
                    continue
                state = json.loads(path.read_text().splitlines()[-1])
                if state["status"] == "running":
                    raise ValueError("Another campaign is running or interrupted")
                day = state["days"].get(self.day, {})
                spent = day.get("charged_wall_seconds", day.get("active_seconds", 0.0))
                if not math.isfinite(spent) or spent < 0:
                    raise ValueError("Invalid external daily consumption")
                self.external_seconds += spent
                self.sources.append(
                    dict(
                        path=str(path),
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        day=self.day,
                        seconds=spent,
                    )
                )
            self.record(now, "entered")
        except BaseException:
            self.lock.close()
            raise

    def record(self, now, status):
        with (self.audit / "events.jsonl").open("a") as f:
            f.write(
                json.dumps(
                    dict(
                        utc=utc(now),
                        day=self.day,
                        campaign=self.name,
                        status=status,
                        external_seconds=self.external_seconds,
                        sources=self.sources,
                    )
                )
                + "\n"
            )
            f.flush()
            __import__("os").fsync(f.fileno())

    def __enter__(self):
        return self

    def __exit__(self, *_):
        try:
            self.record(time.time(), "exited")
        finally:
            self.lock.close()
