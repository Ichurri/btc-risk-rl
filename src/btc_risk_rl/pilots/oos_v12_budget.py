"""Read-only union of OOS precheck and unit-ledger time by La Paz date."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from pathlib import Path

from btc_risk_rl.pilots.budget import LA_PAZ
from btc_risk_rl.pilots.p2_budget import state_hash
from btc_risk_rl.pilots.protocol import ROOT
from btc_risk_rl.pilots.wf_cost_session import (
    WFCostSessionJournal,
    _split_days,
)

AMENDMENT = ROOT / "docs/protocols/OOS-v1-2-training-budget-amendment-20261111.json"
AMENDMENT_SHA256 = "ebd4856b3658fac31f10baeb1688a58dbab61ac80e3655f99f8228604a16c036"


def amended_budget():
    raw = AMENDMENT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != AMENDMENT_SHA256:
        raise ValueError("OOS budget amendment hash mismatch")
    data = json.loads(raw)
    if (data.get("status") != "authorized_training_only"
            or data.get("daily_global_seconds") != 50400
            or data.get("daily_closure_reserve_seconds") != 2700
            or data.get("active_days_max") != 20):
        raise ValueError("OOS budget amendment identity mismatch")
    return data

PREP_CAMPAIGN = "oos-v12-training-v1"
PREP_NAME = "oos-v12-training-preflight.jsonl"
RECOVERY_POLICY_PATH = ROOT / "docs/protocols/OOS-v1-2-preunit-timeout-recovery-20261114.json"
RECOVERY_POLICY_SHA256 = "2ba512e67d7a2f2d84492c4d285338928abf7e5f0a44c19d27c726183c17d722"
CHECKS_NAME = "oos-v12-training-checks.jsonl"
MIGRATION_POLICY_PATH = ROOT / "docs/protocols/OOS-v1-2-code-transition-20261114.json"
MIGRATION_POLICY_SHA256 = "b5851eadf2eefadbf90ccc5ad47e71173f56cd5b980e5053ab64b2f0cf38b4ad"
EXPECTED_OPERATIONAL_CODE_PATHS = frozenset({
    "src/btc_risk_rl/pilots/oos_v12_budget.py",
    "src/btc_risk_rl/pilots/oos_v12_launch.py",
    "src/btc_risk_rl/pilots/oos_v12_training.py",
    "src/btc_risk_rl/pilots/wf_cost_session.py",
})
CAMPAIGN_NAMES = (
    "oos-v12-training-wf-2021-01",
    "oos-v12-training-wf-2022-01",
    "oos-v12-training-main-01",
)


def recovery_policy():
    if not RECOVERY_POLICY_PATH.is_file():
        raise ValueError("OOS recovery policy absent")
    raw = RECOVERY_POLICY_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != RECOVERY_POLICY_SHA256:
        raise ValueError("OOS recovery policy hash mismatch")
    policy = json.loads(raw)
    if (policy.get("schema") != "oos_preunit_timeout_recovery_v1"
            or policy.get("reason") != "OOS formal preparation exceeded 900 seconds"
            or policy.get("preparation_seconds_max") != 1200):
        raise ValueError("OOS recovery policy identity mismatch")
    return policy


def migration_policy():
    if not MIGRATION_POLICY_PATH.is_file():
        raise ValueError("OOS migration policy absent")
    raw = MIGRATION_POLICY_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MIGRATION_POLICY_SHA256:
        raise ValueError("OOS migration policy hash mismatch")
    policy = json.loads(raw)
    if (policy.get("schema") != "oos_preunit_code_transition_v1"
            or policy.get("reason") != "Campaign identity mismatch"
            or set(policy.get("allowed_changed_code_paths", []))
            != EXPECTED_OPERATIONAL_CODE_PATHS
            or policy.get("cursor_at_transition") != 103
            or policy.get("accepted_units_at_transition") != 1133):
        raise ValueError("OOS migration policy identity mismatch")
    return policy


def recoverable_precheck_timeout(session, artifacts):
    """Recognize only pinned, fully passing preunit failures."""
    end = session["end"]
    if end is None or end.get("status") != "failed":
        return False
    digest = hashlib.sha256(json.dumps(end, sort_keys=True,
                                       allow_nan=False).encode()).hexdigest()
    policies = (recovery_policy(), migration_policy())
    policy = next((p for p in policies if digest == p["failed_end_sha256"]
                   and end.get("token") == p["token"]
                   and end.get("reason") == p["reason"]), None)
    if policy is None:
        return False
    path = Path(artifacts) / "shared-pilot-budget" / CHECKS_NAME
    if not path.is_file():
        return False
    previous, completed = None, []
    for line in path.read_text().splitlines():
        row = json.loads(line)
        digest = row.pop("sha256")
        if (row.get("previous") != previous
                or hashlib.sha256(json.dumps(row, sort_keys=True,
                                             allow_nan=False).encode()).hexdigest()
                != digest):
            raise ValueError("OOS precheck chain corrupt")
        previous = digest
        if row.get("event") == "check_end" and row.get("token") == policy["token"]:
            completed.append((row, digest))
    expected = ["suite", "ruff", "main-2018-2022"]
    return (len(completed) == 3
            and [row["name"] for row, _ in completed] == expected
            and all(row["status"] == "ready" for row, _ in completed)
            and completed[-1][1] == policy["checks_end_sha256"])


def _union(intervals):
    total = 0.0
    cursor = None
    for start, end in sorted(intervals):
        if not all(math.isfinite(v) for v in (start, end)) or end < start:
            raise ValueError("Invalid OOS budget interval")
        if cursor is None or start > cursor:
            total += end - start
            cursor = end
        elif end > cursor:
            total += end - cursor
            cursor = end
    return total


def inspect_oos_debit(artifacts, *, now, active_prep_token=None,
                      prior_day_adjustment_seconds=None):
    """Merge all accepted OOS intervals; open or failed preparation blocks reentry."""
    artifacts = Path(artifacts)
    budget = amended_budget()
    day_limit = budget["daily_global_seconds"]
    if prior_day_adjustment_seconds is None:
        prior_day_adjustment_seconds = (
            budget["prior_day"]["conservative_extra_debit_seconds"]
            if artifacts.resolve() == (ROOT / "artifacts").resolve() else 0.0
        )
    if (not math.isfinite(prior_day_adjustment_seconds)
            or prior_day_adjustment_seconds < 0):
        raise ValueError("Invalid OOS prior-day adjustment")
    intervals = {}
    forced_days = set()
    observed_days = set()
    ledger_by_campaign = {}
    blocked = False
    observed_failed_hashes = set()

    def add(start, end):
        if end < start:
            raise ValueError("OOS budget clock moved backwards")
        if end == start:
            observed_days.add(datetime.fromtimestamp(start, LA_PAZ).date().isoformat())
        for day, left, right in _split_days(start, end):
            observed_days.add(day)
            intervals.setdefault(day, []).append((left, right))

    for name in CAMPAIGN_NAMES:
        path = artifacts / name / "ledger.jsonl"
        if not path.exists():
            continue
        previous = None
        for line in path.read_text().splitlines():
            state = json.loads(line)
            if (state.get("state_hash") != state_hash(state)
                    or state.get("previous_hash") != previous):
                raise ValueError("OOS ledger hash chain corrupt")
            previous = state["state_hash"]
        blocked |= state["status"] == "running"
        charges = {}
        for day, row in state["days"].items():
            observed_days.add(day)
            start = row["started_utc_epoch"]
            seconds = row.get("charged_wall_seconds", 0.0)
            if not math.isfinite(seconds) or seconds < 0:
                raise ValueError("OOS ledger charge invalid")
            if (state["status"] in {"failed", "incomplete"}
                    and state.get("pending") and day == max(state["days"])):
                forced_days.add(day)
            add(start, start + seconds)
            charges[day] = seconds
        ledger_by_campaign[name] = charges

    path = artifacts / "shared-pilot-budget" / PREP_NAME
    if path.exists():
        with WFCostSessionJournal(path, campaign=PREP_CAMPAIGN, read_only=True) as journal:
            for item in journal.sessions:
                start, end = item["start"], item["end"]
                if end is not None and end["status"] == "failed":
                    observed_failed_hashes.add(hashlib.sha256(json.dumps(
                        end, sort_keys=True, allow_nan=False).encode()).hexdigest())
                orphan = end is None and start["token"] != active_prep_token
                failed = (end is not None and end["status"] == "failed"
                          and not recoverable_precheck_timeout(item, artifacts))
                blocked |= orphan or failed
                stop = now if end is None else end["epoch"]
                add(start["epoch"], stop)
                if orphan or failed:
                    for day, _, _ in _split_days(start["epoch"], stop):
                        forced_days.add(day)
                if end is not None:
                    excess = end["elapsed_seconds"] - end["wall_seconds"]
                    if excess > 0:
                        day = datetime.fromtimestamp(stop, LA_PAZ).date().isoformat()
                        intervals.setdefault(day, []).append((stop, stop + excess))

    if artifacts.resolve() == (ROOT / "artifacts").resolve():
        for policy in (recovery_policy(), migration_policy()):
            debit = policy.get("diagnostic_debit")
            if debit is not None and policy["failed_end_sha256"] in observed_failed_hashes:
                add(debit["start_epoch"], debit["end_epoch"])

    by_day = {day: min(day_limit, _union(values)) for day, values in intervals.items()}
    prior_day = budget["prior_day"]["day_la_paz"]
    if prior_day in observed_days and prior_day_adjustment_seconds:
        by_day[prior_day] = min(day_limit, by_day[prior_day] + prior_day_adjustment_seconds)
    for day in forced_days:
        by_day[day] = day_limit
    return dict(by_day=by_day, blocked=blocked,
                ledger_by_campaign=ledger_by_campaign,
                active_days=sorted(observed_days | forced_days))
