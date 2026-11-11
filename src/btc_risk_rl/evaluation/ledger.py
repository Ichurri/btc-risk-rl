"""Durable internal ledger for complete, separately permitted evaluation units.

This component is not an access gate or a public evaluator. A future caller
must verify the 108-run frozen roster and the partition permit first.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path


def _digest(value: object) -> bool:
    return (type(value) is str and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def _hash(state: dict) -> str:
    raw = json.dumps({key: value for key, value in state.items()
                      if key != "state_hash"}, sort_keys=True,
                     separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


class EvaluationLedger:
    """Append only states; one policy may be active and only complete units advance."""

    def __init__(self, root: Path, identity: dict):
        self.root = Path(root)
        self.identity = json.loads(json.dumps(identity, sort_keys=True, allow_nan=False))
        self.path = self.root / "ledger.jsonl"
        self.lock = self.root / "ledger.lock"

    @classmethod
    def create(cls, root: Path, identity: dict) -> EvaluationLedger:
        ledger = cls(root, identity)
        if (type(identity) is not dict or identity.get("partition")
                not in {"technical_2023", "final_2024_2025"}
                or not isinstance(identity.get("roster"), list)
                or not identity["roster"]):
            raise ValueError("Evaluation ledger identity invalid")
        for name in ("approval_sha256", "training_ledger_sha256",
                     "export_manifest_sha256"):
            if not _digest(identity.get(name)):
                raise ValueError("Evaluation ledger identity hash invalid")
        ledger.root.mkdir(parents=True, exist_ok=False)
        with ledger.lock.open("x", encoding="utf-8"):
            pass
        state = {
            "schema": "oos_v12_evaluation_ledger_v1", "identity": ledger.identity,
            "status": "ready", "cursor": 0, "pending": None, "accepted": [],
            "failure": None, "updated_utc": _utc(), "previous_hash": None,
        }
        state["state_hash"] = _hash(state)
        with ledger.path.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(state, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        return ledger

    @classmethod
    def open(cls, root: Path, identity: dict) -> EvaluationLedger:
        ledger = cls(root, identity)
        _ = ledger.state
        return ledger

    def _read_unlocked(self) -> dict:
        if self.root.is_symlink() or self.path.is_symlink() or self.lock.is_symlink():
            raise ValueError("Evaluation ledger symlink invalid")
        previous = None
        lines = self.path.read_bytes().splitlines()
        if not lines:
            raise ValueError("Evaluation ledger chain empty")
        for raw in lines:
            state = json.loads(raw)
            if (state.get("previous_hash") != previous
                    or state.get("state_hash") != _hash(state)):
                raise ValueError("Evaluation ledger chain invalid")
            previous = state["state_hash"]
        if state.get("schema") != "oos_v12_evaluation_ledger_v1":
            raise ValueError("Evaluation ledger schema invalid")
        if state.get("identity") != self.identity:
            raise ValueError("Evaluation ledger identity mismatch")
        cursor, accepted, pending = state.get("cursor"), state.get("accepted"), state.get("pending")
        roster = self.identity["roster"]
        if (type(cursor) is not int or not 0 <= cursor <= len(roster)
                or type(accepted) is not list or len(accepted) != cursor
                or any(row.get("run") != roster[index]
                       for index, row in enumerate(accepted))):
            raise ValueError("Evaluation ledger accepted roster invalid")
        status = state.get("status")
        if (status not in {"ready", "running", "completed", "failed"}
                or (status == "ready" and (pending is not None or cursor == len(roster)))
                or (status == "running" and (type(pending) is not dict
                                               or pending.get("run") != roster[cursor]))
                or (status == "completed" and (pending is not None
                                                 or cursor != len(roster)))):
            raise ValueError("Evaluation ledger status invalid")
        return state

    @property
    def state(self) -> dict:
        with self.lock.open("r", encoding="utf-8") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_SH)
            return self._read_unlocked()

    def _append(self, current: dict, changed: dict) -> None:
        changed["previous_hash"] = current["state_hash"]
        changed["updated_utc"] = _utc()
        changed["state_hash"] = _hash(changed)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(changed, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def begin(self, run: dict, *, token: str) -> None:
        with self.lock.open("r", encoding="utf-8") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            current = self._read_unlocked()
            if current["status"] == "failed":
                raise ValueError("Evaluation ledger failed; no restart")
            if (current["status"] != "ready" or current["pending"] is not None
                    or run != self.identity["roster"][current["cursor"]]):
                raise ValueError("Evaluation roster or complete boundary mismatch")
            if not isinstance(token, str) or not token:
                raise ValueError("Evaluation unit token invalid")
            changed = dict(current, status="running",
                           pending={"run": run, "token": token, "started_utc": _utc()})
            self._append(current, changed)

    def accept(self, run: dict, *, token: str, report_sha256: str,
               trace_sha256: str, seconds: float) -> None:
        with self.lock.open("r", encoding="utf-8") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            current = self._read_unlocked()
            pending = current.get("pending")
            if (current["status"] != "running" or pending.get("token") != token
                    or pending.get("run") != run):
                raise ValueError("Evaluation unit token or pending identity mismatch")
            if (not _digest(report_sha256) or not _digest(trace_sha256)
                    or not math.isfinite(seconds) or seconds <= 0):
                raise ValueError("Evaluation accepted evidence invalid")
            accepted = [*current["accepted"], {
                "run": run, "report_sha256": report_sha256,
                "trace_sha256": trace_sha256, "seconds": seconds,
                "ended_utc": _utc(),
            }]
            cursor = current["cursor"] + 1
            status = "completed" if cursor == len(self.identity["roster"]) else "ready"
            changed = dict(current, status=status, cursor=cursor,
                           pending=None, accepted=accepted)
            self._append(current, changed)

    def mark_interrupted(self, reason: str) -> None:
        with self.lock.open("r", encoding="utf-8") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            current = self._read_unlocked()
            if current["status"] != "running" or not reason:
                raise ValueError("Evaluation interruption requires active unit")
            changed = dict(current, status="failed", failure=reason)
            self._append(current, changed)
