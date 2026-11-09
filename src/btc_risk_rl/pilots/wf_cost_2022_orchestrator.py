"""Metered attempts for the separately permitted 2022-only WF study.

This module accounts for checks and unit admission. It contains no market
loader or unit runner; the historical entry requires a pinned permit.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from btc_risk_rl.pilots.budget import LA_PAZ
from btc_risk_rl.pilots.protocol import ROOT
from btc_risk_rl.pilots.wf_cost_session import (
    DAY_LIMIT,
    WFCostSessionJournal,
    _split_days,
)

CAMPAIGN_NAME = "oos-v12-wf-cost-only-2022-02"
CAMPAIGN = ROOT / "artifacts" / CAMPAIGN_NAME
APPROVAL = ROOT / "docs/protocols/OOS-v1-2-wf-cost-2022-only-02-approval.json"
PROPOSAL = ROOT / "docs/proposals/OOS-v1-2-costo-2022-reemplazo-02-v1.md"
JOURNAL_NAME = "wf-2022-only-02-attempts.jsonl"
CHECKS_NAME = "wf-2022-only-02-checks.jsonl"
ATTEMPT_PROFILES = (
    ("oos-v12-wf-cost-only-2022-01", "wf-2022-only-01-attempts.jsonl"),
    (CAMPAIGN_NAME, JOURNAL_NAME),
)
MARKET_EXECUTION_ENABLED = True
REGISTRATION_SHA256 = "940d5da7088b6b93901f7747dd1201f013ede7eabd9ddc43f4afa3ffd1be051f"
OWN_DAILY = 3600
OWN_CUMULATIVE = 4800
OWN_CLOSE_RESERVE = 600
GLOBAL_CLOSE_RESERVE = 2700
ACTIVE_DAYS_MAX = 2
UNIT_CAPS = (120,) + (180,) * 10


class PreflightBlocked(Exception):
    """A measured guard failure before a unit, eligible for later recheck."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_code_gate() -> None:
    """Check the compile-time permission before any filesystem side effect."""
    if not MARKET_EXECUTION_ENABLED or REGISTRATION_SHA256 is None:
        raise PermissionError("WF 2022 market cost study NOT AUTHORIZED")


def require_campaign() -> dict:
    """Fail before creating a journal, root, request, or market trajectory."""
    require_code_gate()
    if not APPROVAL.is_file() or _sha256(APPROVAL) != REGISTRATION_SHA256:
        raise PermissionError("WF 2022 approval hash mismatch")
    registration = json.loads(APPROVAL.read_text())
    if (registration.get("active") is not True
            or registration.get("campaign") != CAMPAIGN_NAME
            or registration.get("scope") != "2022_training_cut_cost_only"
            or registration.get("protocol_sha256") != _sha256(PROPOSAL)
            or registration.get("seed") != 498614892
            or registration.get("condition") != "C10"
            or registration.get("units") != 11):
        raise PermissionError("WF 2022 approval identity mismatch")
    return registration


@dataclass(frozen=True)
class Charges:
    own_by_day: dict[str, float]
    active_days: frozenset[str]
    blocked: bool


def _union_length(intervals: list[tuple[float, float]]) -> float:
    cursor = None
    total = 0.0
    for start, stop in sorted(intervals):
        if not math.isfinite(start) or not math.isfinite(stop) or stop < start:
            raise ValueError("Invalid WF budget interval")
        if cursor is None or start > cursor:
            total += stop - start
            cursor = stop
        elif stop > cursor:
            total += stop - cursor
            cursor = stop
    return total


def reconcile(
    attempts: WFCostSessionJournal | None,
    sessions: WFCostSessionJournal | None,
    ledger_state: dict,
    *,
    now: float,
    active_token: str | None = None,
    active_session_token: str | None = None,
) -> Charges:
    """Union attempts, services and ledger coverage by La Paz date once."""
    if not math.isfinite(now):
        raise ValueError("Invalid WF budget clock")
    intervals: dict[str, list[tuple[float, float]]] = {}
    active_days: set[str] = set()
    monotonic_excess: dict[str, float] = {}
    orphan_days: set[str] = set()
    blocked = ledger_state.get("status") in {"failed", "incomplete", "running"}

    def add_interval(start: float, stop: float) -> None:
        if not math.isfinite(start) or not math.isfinite(stop) or stop < start:
            raise ValueError("Invalid WF budget interval")
        if start == stop:
            active_days.add(datetime.fromtimestamp(start, LA_PAZ).date().isoformat())
        for day, left, right in _split_days(start, stop):
            active_days.add(day)
            intervals.setdefault(day, []).append((left, right))

    for row in ledger_state.get("days", {}).values():
        start = row["started_utc_epoch"]
        charged = row.get("charged_wall_seconds", 0.0)
        if not isinstance(charged, (int, float)) or not math.isfinite(charged) or charged < 0:
            raise ValueError("Invalid WF ledger charge")
        add_interval(start, start + charged)

    for journal, live_token in ((attempts, active_token), (sessions, active_session_token)):
        if journal is None:
            continue
        for item in journal.sessions:
            start_row, end_row = item["start"], item["end"]
            start = start_row["epoch"]
            stop = now if end_row is None else end_row["epoch"]
            add_interval(start, stop)
            if end_row is None and start_row["token"] != live_token:
                blocked = True
                if start == stop:
                    orphan_days.add(datetime.fromtimestamp(start, LA_PAZ).date().isoformat())
                orphan_days.update(day for day, _, _ in _split_days(start, stop))
            if end_row is not None:
                blocked |= end_row["status"] == "failed"
                excess = end_row["elapsed_seconds"] - end_row["wall_seconds"]
                if excess > 0:
                    day = datetime.fromtimestamp(stop, LA_PAZ).date().isoformat()
                    monotonic_excess[day] = max(monotonic_excess.get(day, 0.0), excess)

    own = {day: _union_length(intervals.get(day, [])) + monotonic_excess.get(day, 0.0)
           for day in active_days}
    for day in orphan_days:
        own[day] = DAY_LIMIT
    return Charges(own, frozenset(active_days), blocked)


def shared_attempt_debit(artifacts: Path, *, now: float, day: str,
                         campaign_name: str = CAMPAIGN_NAME,
                         journal_name: str = JOURNAL_NAME) -> float:
    """Additional global charge for one pinned attempt journal beyond WF sources."""
    if (campaign_name, journal_name) not in ATTEMPT_PROFILES:
        raise ValueError("Unknown WF 2022 attempt profile")
    artifacts = Path(artifacts)
    journal_path = artifacts / "shared-pilot-budget" / journal_name
    if not journal_path.exists():
        return 0.0
    campaign = artifacts / campaign_name
    ledger_path = campaign / "ledger.jsonl"
    sessions_path = campaign / "sessions.jsonl"
    ledger = json.loads(ledger_path.read_text().splitlines()[-1]) if ledger_path.exists() else {}
    with WFCostSessionJournal(journal_path, campaign=campaign_name, read_only=True) as attempts:
        if sessions_path.exists():
            with WFCostSessionJournal(sessions_path, campaign=campaign_name,
                                      read_only=True) as sessions:
                base = reconcile(None, sessions, ledger, now=now)
                merged = reconcile(attempts, sessions, ledger, now=now)
        else:
            base = reconcile(None, None, ledger, now=now)
            merged = reconcile(attempts, None, ledger, now=now)
    if day not in merged.active_days:
        return 0.0
    if merged.blocked:
        return max(0.0, DAY_LIMIT - base.own_by_day.get(day, 0.0))
    return max(0.0, merged.own_by_day.get(day, 0.0) - base.own_by_day.get(day, 0.0))


class _RealClock:
    now = staticmethod(time.time)
    monotonic = staticmethod(time.monotonic)


class BudgetAttempt:
    """Hold the shared lock and meter checks before any unit ledger exists."""

    def __init__(self, artifacts: Path, *, clock=None,
                 gate: Callable[[], object] = require_code_gate,
                 authorize: Callable[[], object] = require_campaign,
                 external_spent: Callable[[float], float] | None = None,
                 night_window: bool = False):
        self.artifacts = Path(artifacts)
        self.clock = clock if clock is not None else _RealClock()
        self.gate = gate
        self.authorize = authorize
        self.external_spent = external_spent
        self.night_window = night_window
        self.journal_path = self.artifacts / "shared-pilot-budget" / JOURNAL_NAME
        self.checks_path = self.artifacts / "shared-pilot-budget" / CHECKS_NAME
        self.checks = []
        self.check_previous = None
        self.journal = None
        self.token = None
        self.lock = None

    def __enter__(self):
        self.gate()
        audit = self.artifacts / "shared-pilot-budget"
        audit.mkdir(parents=True, exist_ok=True)
        self.lock = (audit / "global.lock").open("a")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.journal = WFCostSessionJournal(self.journal_path, campaign=CAMPAIGN_NAME)
            self.token = self.journal.start(now=self.clock.now(),
                                            monotonic=self.clock.monotonic(),
                                            invocation_id=os.environ.get("INVOCATION_ID"))
            self.authorize()
            if self.checks_path.exists():
                for line in self.checks_path.read_text().splitlines():
                    row = json.loads(line)
                    digest = row.pop("sha256")
                    if (row.get("campaign") != CAMPAIGN_NAME
                            or row.get("previous") != self.check_previous
                            or hashlib.sha256(json.dumps(row, sort_keys=True,
                                                         allow_nan=False).encode()).hexdigest()
                            != digest):
                        raise ValueError("WF 2022 check journal corrupt")
                    self.check_previous = digest
        except BaseException:
            if self.journal is not None:
                if self.token is not None:
                    self.journal.end(self.token, now=self.clock.now(),
                                     monotonic=self.clock.monotonic(), status="failed",
                                     reason="check journal or attempt start failure")
                self.journal.__exit__(None, None, None)
            self.lock.close()
            raise
        return self

    def __exit__(self, exc_type, exc, _traceback):
        try:
            self.journal.end(self.token, now=self.clock.now(),
                             monotonic=self.clock.monotonic(),
                             status="failed" if exc_type and not issubclass(
                                 exc_type, PreflightBlocked) else "ready",
                             reason=str(exc) if exc is not None else None)
        finally:
            self.journal.__exit__(None, None, None)
            self.lock.close()
            self.token = None

    def _append_check(self, **fields) -> None:
        row = dict(campaign=CAMPAIGN_NAME, previous=self.check_previous,
                   token=self.token, **fields)
        digest = hashlib.sha256(json.dumps(row, sort_keys=True, allow_nan=False).encode()).hexdigest()
        created = not self.checks_path.exists()
        with self.checks_path.open("a") as stream:
            stream.write(json.dumps({**row, "sha256": digest}, sort_keys=True,
                                    allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        if created:
            directory = os.open(self.checks_path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        self.check_previous = digest

    def run_check(self, name: str, operation: Callable[[], object]):
        """Run a check only after the durable start; retain its elapsed time."""
        if not self.token or not isinstance(name, str) or not name:
            raise ValueError("WF check requires an active metered attempt")
        start = self.clock.now()
        start_mono = self.clock.monotonic()
        self._append_check(event="check_start", name=name, epoch=start,
                           monotonic=start_mono)
        status = "ready"
        try:
            return operation()
        except PreflightBlocked:
            status = "blocked"
            raise
        except BaseException:
            status = "failed"
            raise
        finally:
            end = self.clock.now()
            elapsed = max(end - start, self.clock.monotonic() - start_mono)
            self._append_check(event="check_end", name=name, epoch=end,
                               monotonic=self.clock.monotonic(), status=status,
                               elapsed_seconds=elapsed)
            self.checks.append(dict(name=name, start_epoch=start,
                                    end_epoch=end, status=status))

    def snapshot(self, ledger_state: dict, *, sessions=None,
                 session_token: str | None = None) -> Charges:
        if self.token is None:
            raise ValueError("WF attempt not active")
        return reconcile(self.journal, sessions, ledger_state, now=self.clock.now(),
                         active_token=self.token, active_session_token=session_token)

    def admit(self, ledger_state: dict, *, unit: int, sessions=None,
              session_token: str | None = None) -> str:
        """Admit a full unit cap only when all reserves and days still fit."""
        if type(unit) is not int or not 0 <= unit < len(UNIT_CAPS):
            raise ValueError("WF 2022 unit out of roster")
        if ledger_state:
            if (ledger_state.get("status") != "ready" or ledger_state.get("pending") is not None
                    or len(ledger_state.get("units", [])) != unit):
                raise ValueError("WF 2022 requires a complete expected frontier")
        snap = self.snapshot(ledger_state, sessions=sessions, session_token=session_token)
        if snap.blocked:
            raise ValueError("WF 2022 failed or unclosed state blocks admission")
        if len(snap.active_days) > ACTIVE_DAYS_MAX:
            return "incomplete"
        now = self.clock.now()
        day = datetime.fromtimestamp(now, LA_PAZ).date().isoformat()
        cap = UNIT_CAPS[unit]
        daily = snap.own_by_day.get(day, 0.0)
        cumulative = sum(snap.own_by_day.values())
        if cumulative + cap + (OWN_CLOSE_RESERVE if len(snap.active_days) == 2
                               else 2 * OWN_CLOSE_RESERVE) > OWN_CUMULATIVE:
            return "incomplete"
        if self.external_spent is None:
            from btc_risk_rl.pilots.wf_cost import inspect_budget

            budget = inspect_budget(now=now, campaign=self.artifacts / CAMPAIGN_NAME)
            if not budget["ok"]:
                raise ValueError("Another campaign is active")
            external = budget["global_spent"]
        else:
            external = self.external_spent(now)
        if not isinstance(external, (int, float)) or not math.isfinite(external) or external < 0:
            raise ValueError("Invalid WF external budget debit")
        midnight = datetime.combine(datetime.fromtimestamp(now, LA_PAZ).date()
                                    + timedelta(days=1), datetime.min.time(), LA_PAZ).timestamp()
        window_end = midnight
        window_reserve = OWN_CLOSE_RESERVE
        if self.night_window:
            local = datetime.fromtimestamp(now, LA_PAZ)
            if not 1 <= local.hour < 9:
                return "pause"
            window_end = local.replace(hour=9, minute=0, second=0,
                                       microsecond=0).timestamp()
        if (daily + cap + OWN_CLOSE_RESERVE > OWN_DAILY
                or external + daily + cap + GLOBAL_CLOSE_RESERVE > DAY_LIMIT
                or min(midnight, window_end) - now < cap + window_reserve):
            return "pause"
        return "start"

    def run_unit(self, ledger_state: dict, *, unit: int, operation: Callable[[], object],
                 sessions=None, session_token: str | None = None):
        """Never call the unit callback when its full cap and reserves cannot fit."""
        decision = self.admit(ledger_state, unit=unit, sessions=sessions,
                              session_token=session_token)
        if decision != "start":
            return decision
        start_wall = self.clock.now()
        start_mono = self.clock.monotonic()
        try:
            result = self.run_check(f"unit-{unit}", operation)
        except PreflightBlocked as exc:
            raise ValueError("WF 2022 resource guard failed during unit") from exc
        elapsed = max(self.clock.now() - start_wall,
                      self.clock.monotonic() - start_mono)
        if elapsed > UNIT_CAPS[unit]:
            raise ValueError("WF 2022 unit cap exceeded")
        return result
