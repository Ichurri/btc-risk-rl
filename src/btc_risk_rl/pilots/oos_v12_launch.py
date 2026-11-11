"""Durable, metered preparation before an OOS v1.2 training ledger exists."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from btc_risk_rl.pilots.budget import LA_PAZ
from btc_risk_rl.pilots.oos_v12_budget import PREP_CAMPAIGN, PREP_NAME, inspect_oos_debit
from btc_risk_rl.pilots.oos_v12_training import (
    CAMPAIGNS,
    LEGACY_COMPLETED_ROOTS,
    PROFILES,
    read_budget,
    require_campaign,
    roster,
    run_historical_units,
    verified_legacy_completed_root,
    window_admissible,
)
from btc_risk_rl.pilots.p2_budget import state_hash
from btc_risk_rl.pilots.protocol import ROOT
from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal

CHECKS_NAME = "oos-v12-training-checks.jsonl"


class PreflightBlocked(Exception):
    """A resource or budget block before training, eligible for a fresh check."""


def _hash(row):
    return hashlib.sha256(json.dumps(row, sort_keys=True, allow_nan=False).encode()).hexdigest()


class OOSPrecheckAttempt:
    def __init__(self, artifacts, *, gate=None):
        self.artifacts = Path(artifacts)
        self.gate = require_campaign if gate is None else gate
        self.audit = self.artifacts / "shared-pilot-budget"
        self.journal_path = self.audit / PREP_NAME
        self.checks_path = self.audit / CHECKS_NAME
        self.lock = self.journal = self.token = None
        self.previous = None

    def __enter__(self):
        self.gate()
        self.audit.mkdir(parents=True, exist_ok=True)
        self.lock = (self.audit / "global.lock").open("a")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.journal = WFCostSessionJournal(self.journal_path,
                                                 campaign=PREP_CAMPAIGN)
            self.token = self.journal.start(now=time.time(), monotonic=time.monotonic(),
                                            invocation_id=os.environ.get("INVOCATION_ID"))
            if self.checks_path.exists():
                for line in self.checks_path.read_text().splitlines():
                    row = json.loads(line)
                    digest = row.pop("sha256")
                    if (row.get("previous") != self.previous
                            or row.get("campaign") != PREP_CAMPAIGN
                            or _hash(row) != digest):
                        raise ValueError("OOS precheck journal corrupt")
                    self.previous = digest
            return self
        except BaseException:
            if self.journal is not None:
                if self.token is not None:
                    self.journal.end(self.token, now=time.time(),
                                     monotonic=time.monotonic(), status="failed",
                                     reason="precheck start failure")
                self.journal.__exit__(None, None, None)
            if self.lock is not None:
                self.lock.close()
            raise

    def release_global_lock(self):
        """Keep the durable session open while the supervisor takes the lock."""
        if self.lock is None or self.journal is None or self.token is None:
            raise ValueError("OOS preparation lock is not active")
        self.lock.close()
        self.lock = None

    def __exit__(self, exc_type, exc, _traceback):
        try:
            self.journal.end(self.token, now=time.time(), monotonic=time.monotonic(),
                             status="ready" if exc_type is None or issubclass(
                                 exc_type, PreflightBlocked) else "failed",
                             reason=str(exc) if exc is not None else None)
        finally:
            self.journal.__exit__(None, None, None)
            if self.lock is not None:
                self.lock.close()

    def _append(self, **values):
        row = dict(campaign=PREP_CAMPAIGN, token=self.token, previous=self.previous,
                   invocation_id=os.environ.get("INVOCATION_ID"), **values)
        digest = _hash(row)
        with self.checks_path.open("a") as stream:
            stream.write(json.dumps({**row, "sha256": digest}, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        self.previous = digest

    def run_check(self, name, operation):
        start = time.time()
        self._append(event="check_start", name=name, epoch=start)
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
            self._append(event="check_end", name=name, epoch=time.time(),
                         elapsed_seconds=time.time() - start, status=status)


def require_recent_prepare(profile):
    """Public executor must follow a same-session suite, Ruff and watched preflight."""
    if profile not in PROFILES:
        raise ValueError("Unknown OOS training profile")
    path = ROOT / "artifacts/shared-pilot-budget" / CHECKS_NAME
    if not path.is_file():
        raise PermissionError("OOS recent formal prechecks absent")
    previous = None
    rows = []
    for line in path.read_text().splitlines():
        row = json.loads(line)
        digest = row.pop("sha256")
        if row.get("previous") != previous or row.get("campaign") != PREP_CAMPAIGN or _hash(row) != digest:
            raise PermissionError("OOS precheck chain invalid")
        previous = digest
        rows.append(row)
    completed = [r for r in rows if r.get("event") == "check_end"][-3:]
    now = time.time()
    if (len(completed) != 3 or [r["name"] for r in completed] != ["suite", "ruff", profile]
            or any(r["status"] != "ready" for r in completed)
            or len({r["token"] for r in completed}) != 1
            or len({r["invocation_id"] for r in completed}) != 1
            or completed[-1]["invocation_id"] != os.environ.get("INVOCATION_ID")
            or not 0 <= now - completed[-1]["epoch"] <= 900):
        raise PermissionError("OOS recent formal prechecks invalid or stale")


def _checked_command(args, *, timeout, output_tail=1200):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                            check=False, timeout=timeout)
    if result.returncode:
        raise ValueError(f"OOS formal command failed: {result.stderr[-2000:]}\n{result.stdout[-2000:]}")
    return dict(command=args, stdout=(result.stdout if output_tail is None
                                      else result.stdout[-output_tail:]),
                stderr=result.stderr[-1200:])


def select_next_profile(campaigns=None, *, legacy_completed=None, now=None):
    """Select the first unfinished frozen roster, never replaying a failed unit."""
    production_roots = campaigns is None
    campaigns = CAMPAIGNS if production_roots else campaigns
    legacy_completed = (LEGACY_COMPLETED_ROOTS if production_roots else {}) \
        if legacy_completed is None else legacy_completed
    now = time.time() if now is None else now
    candidate = None
    for profile in PROFILES:
        root = Path(campaigns[profile])
        legacy = legacy_completed.get(profile)
        if root.exists() and legacy is not None and Path(legacy["root"]).exists():
            raise ValueError("OOS canonical and legacy roots both exist")
        path = root / "ledger.jsonl"
        if not path.exists():
            if root.exists():
                raise ValueError("OOS root exists without a complete ledger")
            legacy_root = verified_legacy_completed_root(profile, legacy_completed)
            if legacy_root is None:
                candidate = profile
                break
            root = legacy_root
            path = root / "ledger.jsonl"
        previous = None
        for line in path.read_text().splitlines():
            state = json.loads(line)
            if (state.get("previous_hash") != previous
                    or state.get("state_hash") != state_hash(state)):
                raise ValueError("OOS nightly ledger chain corrupt")
            previous = state["state_hash"]
        if previous is None:
            raise ValueError("OOS nightly ledger empty")
        expected = len(roster(profile))
        if state["status"] == "completed":
            if (state.get("cursor") != expected or state.get("pending") is not None
                    or len(state.get("units", [])) != expected * 11):
                raise ValueError("OOS completed count disagrees with frozen roster")
            continue
        if (state["status"] != "ready" or state.get("pending") is not None
                or type(state.get("cursor")) is not int
                or not 0 <= state["cursor"] < expected):
            raise ValueError("OOS campaign not resumable")
        candidate = profile
        break
    debit = inspect_oos_debit(Path(campaigns[PROFILES[0]]).parent, now=now)
    if debit["blocked"]:
        raise ValueError("OOS campaign or precheck failed/open; no reentry")
    return candidate


def run_nightly():
    """Run frozen profiles in order; a valid budget pause ends this session."""
    require_campaign()
    while window_admissible(time.time()):
        profile = select_next_profile()
        if profile is None:
            return "completed"
        try:
            state = prepare_and_run(profile)
        except PreflightBlocked as exc:
            print(json.dumps(dict(status="blocked_before_unit", profile=profile,
                                  reason=str(exc))), flush=True)
            return "blocked_before_unit"
        if state["status"] == "completed":
            continue
        if state["status"] == "ready" and state.get("pending") is None:
            return "paused_at_complete_boundary"
        raise ValueError("OOS nightly unit failed or has an incomplete boundary")
    return "outside_authorized_period"


def session_deadline_epoch(now):
    from btc_risk_rl.pilots.oos_v12_budget import amended_budget

    local = datetime.fromtimestamp(now, LA_PAZ)
    midnight = datetime.combine(local.date() + timedelta(days=1),
                                datetime.min.time(), LA_PAZ).timestamp()
    cutoff = datetime.fromisoformat(amended_budget()["presentation_cutoff_local"]).timestamp()
    return min(midnight, cutoff)


def prepare_and_run(profile):
    """One systemd session, preparation journal first, training only after ready."""
    require_campaign()
    if profile not in PROFILES or not window_admissible(time.time()):
        raise PreflightBlocked("OOS profile or authorized period blocked")
    if profile != select_next_profile():
        raise PreflightBlocked("OOS profile is not the next unfinished frozen roster")
    with OOSPrecheckAttempt(ROOT / "artifacts") as attempt:
        now = time.time()
        preparation_started = now
        if len(inspect_oos_debit(ROOT / "artifacts", now=now,
                                 active_prep_token=attempt.token)["active_days"]) > 20:
            raise PreflightBlocked("OOS twenty active days exhausted")
        deadline = session_deadline_epoch(now)
        budget = read_budget(profile, now=now, active_prep_token=attempt.token)
        if (not budget["ok"] or budget["remaining_before_reserve"] < 900 + 1800
                or deadline - now < 900 + 1800 + 2700):
            raise PreflightBlocked("OOS suite/Q0/closing reserve does not fit")
        attempt.run_check("suite", lambda: _checked_command(
            [sys.executable, "-m", "pytest", "-q"], timeout=900))
        attempt.run_check("ruff", lambda: _checked_command(
            [sys.executable, "-m", "ruff", "check", str(ROOT)], timeout=120))

        def watched():
            result = _checked_command(
                [sys.executable, str(ROOT / "scripts/audit_oos_v12_training_preflight.py"),
                 profile], timeout=180, output_tail=None)
            payload = json.loads(result["stdout"])
            if payload["status"] != "ready" or payload["protected_or_shared_csv_opened"]:
                raise PreflightBlocked(f"OOS watched preflight blocked: {payload['blockers']}")
            return payload

        os.environ["OOS_PREP_TOKEN"] = attempt.token
        try:
            preflight = attempt.run_check(profile, watched)
        finally:
            os.environ.pop("OOS_PREP_TOKEN", None)
        if time.time() - preparation_started > 900:
            raise ValueError("OOS formal preparation exceeded 900 seconds")
        remaining = read_budget(profile, now=time.time(),
                                active_prep_token=attempt.token)
        if (not remaining["ok"] or remaining["remaining_before_reserve"] < 1800
                or session_deadline_epoch(time.time()) - time.time() < 1800 + 2700):
            raise PreflightBlocked("OOS Q0 plus closing reserve no longer fits")
        print(json.dumps(dict(stage="prepared", profile=profile,
                              preflight=preflight, token=attempt.token),
                         sort_keys=True), flush=True)
        attempt.release_global_lock()
        os.environ["OOS_PREP_TOKEN"] = attempt.token
        try:
            require_recent_prepare(profile)
            state = run_historical_units(profile)
            if state["status"] in {"failed", "incomplete"}:
                raise ValueError("OOS supervised unit failed or exhausted its limits")
            return state
        finally:
            os.environ.pop("OOS_PREP_TOKEN", None)
