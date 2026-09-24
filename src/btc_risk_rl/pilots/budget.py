"""Single-writer append-only campaign ledger and shared La Paz daily deadlines."""

import fcntl
import json
import math
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

LA_PAZ = ZoneInfo("America/La_Paz")
CAPS = {"q0": 1800, "iteration": 2700}


def utc(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat()


class CampaignLedger:
    def __init__(self, root, *, now, identity, external_seconds=0.0):
        if not math.isfinite(external_seconds) or external_seconds < 0:
            raise ValueError("Invalid external daily debit")
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = (self.root / "campaign.lock").open("a")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self.lock.close()
            raise ValueError("Campaign already active") from exc
        self.path = self.root / "ledger.jsonl"
        try:
            if self.path.exists():
                lines = self.path.read_text().splitlines()
                self.state = json.loads(lines[-1])
                if self.state["identity"] != identity:
                    raise ValueError("Campaign identity mismatch")
                if now < self.state["updated_epoch"]:
                    raise ValueError("UTC clock moved backwards")
                if self.state["status"] == "running":
                    self.fail(now, "interrupted_supervisor_or_unit")
                    raise ValueError("Campaign interrupted; failed permanently")
                if self.state["status"] in {"failed", "incomplete"}:
                    raise ValueError("Campaign failed/incomplete; no selective retry")
            else:
                self.state = dict(
                    identity=identity,
                    status="ready",
                    days={},
                    runs={},
                    measurements={},
                    resources={},
                    units=[],
                    cursor=0,
                )
            self.day_key = datetime.fromtimestamp(now, LA_PAZ).date().isoformat()
            if self.day_key not in self.state["days"]:
                date = datetime.fromtimestamp(now, LA_PAZ).date()
                midnight = datetime.combine(
                    date + timedelta(days=1), datetime.min.time(), LA_PAZ
                ).timestamp()
                hard = min(now + max(0, 10800 - external_seconds), midnight)
                self.state["days"][self.day_key] = dict(
                    started_utc_epoch=now,
                    started_utc=utc(now),
                    hard_deadline=hard,
                    work_deadline=min(now + 9000, hard - 1800),
                    preflight_done=False,
                    active_seconds=0.0,
                    external_seconds=external_seconds,
                )
            self.day = self.state["days"][self.day_key]
            extra = max(0, external_seconds - self.day.get("external_seconds", 0.0))
            if extra:
                self.day["hard_deadline"] -= extra
                self.day["work_deadline"] = min(
                    self.day["work_deadline"], self.day["hard_deadline"] - 1800
                )
                self.day["external_seconds"] = external_seconds
            self.persist(now)
        except BaseException:
            self.lock.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.lock.close()

    def persist(self, now):
        if now < self.state.get("updated_epoch", now):
            raise ValueError("UTC clock moved backwards")
        self.state.update(updated_epoch=now, updated_utc=utc(now))
        with self.path.open("a") as f:
            f.write(json.dumps(self.state, sort_keys=True, allow_nan=False) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def preflight_done(self, now):
        if not self.day["preflight_done"]:
            if now - self.day["started_utc_epoch"] > 900:
                self.fail(now, "preflight_timeout")
                raise ValueError("Preflight exceeded 15 minutes")
            self.day["work_deadline"] = min(self.day["work_deadline"], now + 8100)
            self.day["preflight_done"] = True
        self.persist(now)

    def required(self, condition, kind):
        samples = self.state["measurements"].get(f"{condition}/{kind}", [])
        value = 1.5 * max(samples) if samples else CAPS[kind]
        if value > CAPS[kind]:
            raise ValueError("Measured conservative estimate exceeds approved cap")
        return value

    def admit(self, condition, kind, now):
        if self.state["status"] != "ready":
            raise ValueError("Campaign not ready")
        if not self.day["preflight_done"]:
            raise ValueError("Preflight required")
        return (
            "start"
            if self.day["work_deadline"] - now >= self.required(condition, kind)
            else "pause"
        )

    def begin(self, run_id, kind, now):
        if self.state["status"] != "ready":
            raise ValueError("Campaign not ready")
        run = self.state["runs"].setdefault(run_id, {"days": [], "resources": {}})
        if self.day_key not in run["days"]:
            if (
                len(run["days"]) >= 3
                or sum(len(r["days"]) for r in self.state["runs"].values()) >= 27
            ):
                self.state["status"] = "incomplete"
                self.persist(now)
                raise ValueError("Approved sessions exhausted")
            run["days"].append(self.day_key)
        self.state.update(status="running", pending=dict(run_id=run_id, kind=kind, start=now))
        self.persist(now)

    def finish(self, now, *, resources, condition, **evidence):
        if self.state["status"] != "running":
            raise ValueError("No active unit")
        pending = self.state["pending"]
        elapsed = now - pending["start"]
        work_seconds = evidence.get("work_seconds", elapsed)
        work_ended = evidence.get("work_ended", now)
        if (
            elapsed <= 0
            or not 0 < work_seconds <= CAPS[pending["kind"]]
            or work_ended > self.day["work_deadline"]
            or now > self.day["hard_deadline"]
        ):
            self.fail(now, "unit_time_limit")
            raise ValueError("Unit time limit exceeded")
        self.state["measurements"].setdefault(f"{condition}/{pending['kind']}", []).append(
            work_seconds
        )
        run = self.state["runs"][pending["run_id"]]
        for key, value in resources.items():
            if value < 0:
                raise ValueError("Invalid resource delta")
            for totals in (run["resources"], self.state["resources"]):
                totals[key] = totals.get(key, 0) + value
        if "checkpoint" in evidence:
            run.update(checkpoint=evidence["checkpoint"], next_unit=pending["unit"] + 1)
            if pending["unit"] == 2:
                self.state["cursor"] += 1
        self.state["units"].append(
            dict(
                **pending,
                end=now,
                end_utc=utc(now),
                seconds=elapsed,
                resources=resources,
                **evidence,
            )
        )
        self.state.update(status="ready", pending=None)
        self.persist(now)

    def fail(self, now, reason, **evidence):
        self.state.update(status="failed", failure=dict(reason=reason, utc=utc(now), **evidence))
        self.persist(now)
