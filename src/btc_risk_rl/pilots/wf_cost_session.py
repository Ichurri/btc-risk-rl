"""Durable WF session time outside the unit ledger, with exact overlap debit."""

from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path

from btc_risk_rl.pilots.budget import LA_PAZ, utc

DAY_LIMIT = 10800


def _hash(row):
    return hashlib.sha256(json.dumps(row, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _day_bounds(day):
    date = datetime.strptime(day, "%Y-%m-%d").date()
    return (datetime.combine(date, time.min, LA_PAZ).timestamp(),
            datetime.combine(date + timedelta(days=1), time.min, LA_PAZ).timestamp())


def _split_days(start, end):
    """Yield half-open wall-clock pieces in America/La_Paz."""
    while start < end:
        day = datetime.fromtimestamp(start, LA_PAZ).date().isoformat()
        _, next_midnight = _day_bounds(day)
        stop = min(end, next_midnight)
        yield day, start, stop
        start = stop


def _uncovered(start, end, coverage):
    """Length of one interval outside the union of ledger intervals."""
    clipped = sorted((max(start, a), min(end, b)) for a, b in coverage if a < end and b > start)
    cursor, result = start, 0.0
    for a, b in clipped:
        if a > cursor:
            result += a - cursor
        cursor = max(cursor, b)
    return result + max(0.0, end - cursor)


@dataclass(frozen=True)
class SessionCharges:
    extra_by_day: dict[str, float]
    session_days: frozenset[str]
    blocked: bool


class WFCostSessionJournal:
    """Single-writer, fsynced hash chain; an orphan or failed session blocks reentry."""

    def __init__(self, path, *, campaign, read_only=False):
        self.path = Path(path)
        self.campaign = campaign
        if self.path.is_symlink():
            raise ValueError("WF session journal may not be a symlink")
        self.lock = None
        if read_only:
            if not self.path.is_file():
                raise ValueError("WF session journal absent")
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            lock_path = self.path.with_suffix(".lock")
            if lock_path.is_symlink():
                raise ValueError("WF session lock may not be a symlink")
            self.lock = lock_path.open("a")
        try:
            if self.lock is not None:
                fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.sessions = []
            self.previous = None
            if self.path.exists():
                for line in self.path.read_text().splitlines():
                    row = json.loads(line)
                    digest = row.pop("sha256")
                    if (row.get("campaign") != campaign or row.get("previous") != self.previous
                            or _hash(row) != digest):
                        raise ValueError("WF session journal hash chain corrupt")
                    if row.get("schema_version") != "wf_cost_session_v1":
                        raise ValueError("WF session journal schema invalid")
                    if (type(row.get("epoch")) not in {int, float}
                            or type(row.get("monotonic")) not in {int, float}
                            or not math.isfinite(row["epoch"])
                            or not math.isfinite(row["monotonic"])
                            or type(row.get("token")) is not str):
                        raise ValueError("WF session journal clock or token invalid")
                    self.previous = digest
                    if row.get("event") == "start":
                        if self.sessions and self.sessions[-1]["end"] is None:
                            raise ValueError("WF session journal overlapping starts")
                        self.sessions.append(dict(start=row, end=None))
                    elif row.get("event") == "end":
                        if (not self.sessions or self.sessions[-1]["end"] is not None
                                or row.get("token") != self.sessions[-1]["start"].get("token")):
                            raise ValueError("WF session journal unmatched end")
                        start = self.sessions[-1]["start"]
                        if (row.get("status") not in {"ready", "failed"}
                                or row["epoch"] < start["epoch"]
                                or row["monotonic"] < start["monotonic"]
                                or row.get("wall_seconds") != row["epoch"] - start["epoch"]
                                or row.get("elapsed_seconds") != max(
                                    row["wall_seconds"], row["monotonic"] - start["monotonic"])):
                            raise ValueError("WF session journal end invalid")
                        self.sessions[-1]["end"] = row
                    else:
                        raise ValueError("WF session journal event invalid")
        except BaseException:
            if self.lock is not None:
                self.lock.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self.lock is not None:
            self.lock.close()

    def _append(self, row):
        if self.lock is None:
            raise ValueError("WF read-only session journal cannot append")
        row = dict(schema_version="wf_cost_session_v1", campaign=self.campaign,
                   previous=self.previous, **row)
        digest = _hash(row)
        created = not self.path.exists()
        with self.path.open("a") as stream:
            stream.write(json.dumps({**row, "sha256": digest}, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        if created:
            directory = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        self.previous = digest
        return row

    def start(self, *, now, monotonic, invocation_id):
        if not all(math.isfinite(value) for value in (now, monotonic)):
            raise ValueError("WF session clock invalid")
        if self.sessions:
            last = self.sessions[-1]
            if last["end"] is None:
                raise ValueError("WF unclosed session blocks reentry")
            if last["end"]["status"] != "ready":
                raise ValueError("WF failed session blocks reentry")
            if now < last["end"]["epoch"]:
                raise ValueError("WF session UTC clock moved backwards")
        token = uuid.uuid4().hex
        row = self._append(dict(event="start", token=token, epoch=now, utc=utc(now),
                                monotonic=monotonic, invocation_id=invocation_id,
                                day_la_paz=datetime.fromtimestamp(now, LA_PAZ).date().isoformat()))
        self.sessions.append(dict(start=row, end=None))
        return token

    def end(self, token, *, now, monotonic, status, reason=None):
        if (not self.sessions or self.sessions[-1]["end"] is not None
                or token != self.sessions[-1]["start"]["token"]):
            raise ValueError("WF session end does not match active start")
        start = self.sessions[-1]["start"]
        if (status not in {"ready", "failed"} or not math.isfinite(now)
                or not math.isfinite(monotonic) or now < start["epoch"]
                or monotonic < start["monotonic"]):
            raise ValueError("WF session end invalid")
        row = self._append(dict(event="end", token=token, epoch=now, utc=utc(now),
                                monotonic=monotonic, status=status, reason=reason,
                                wall_seconds=now - start["epoch"],
                                elapsed_seconds=max(now - start["epoch"],
                                                    monotonic - start["monotonic"])))
        self.sessions[-1]["end"] = row

    def charges(self, ledger_state, *, now, active_token=None):
        """Charge only session time not already covered by the ledger's day span."""
        if not math.isfinite(now):
            raise ValueError("WF session clock invalid")
        coverage = {}
        for day, row in ledger_state.get("days", {}).items():
            started = row["started_utc_epoch"]
            charged = row.get("charged_wall_seconds", 0)
            if not math.isfinite(started) or not math.isfinite(charged) or charged < 0:
                raise ValueError("WF ledger charge invalid")
            stop = started + charged
            if active_token is not None and day == datetime.fromtimestamp(now, LA_PAZ).date().isoformat():
                stop = max(stop, now)
            for covered_day, a, b in _split_days(started, stop):
                coverage.setdefault(covered_day, []).append((a, b))
        extra, days, blocked = {}, set(), False
        for session in self.sessions:
            start, end = session["start"], session["end"]
            stop = now if end is None else end["epoch"]
            if stop < start["epoch"]:
                raise ValueError("WF session clock moved backwards")
            orphan = end is None and start["token"] != active_token
            blocked |= orphan or (end is not None and end["status"] == "failed")
            if stop == start["epoch"]:
                day = datetime.fromtimestamp(stop, LA_PAZ).date().isoformat()
                days.add(day)
                if orphan:
                    extra[day] = DAY_LIMIT
            for day, a, b in _split_days(start["epoch"], stop):
                days.add(day)
                if orphan:
                    extra[day] = DAY_LIMIT
                elif extra.get(day) != DAY_LIMIT:
                    extra[day] = extra.get(day, 0.0) + _uncovered(a, b, coverage.get(day, []))
            if end is not None:
                excess = end["elapsed_seconds"] - end["wall_seconds"]
                if excess > 0:
                    day = datetime.fromtimestamp(end["epoch"], LA_PAZ).date().isoformat()
                    days.add(day)
                    if extra.get(day) != DAY_LIMIT:
                        extra[day] = extra.get(day, 0.0) + excess
        return SessionCharges(extra, frozenset(days), blocked)
