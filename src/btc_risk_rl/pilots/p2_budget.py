"""P2 ledger: ten iterations, three active days, immutable chained evidence."""

import hashlib
import json
import uuid
from pathlib import Path

from btc_risk_rl.pilots.budget import CampaignLedger


def state_hash(state):
    return hashlib.sha256(
        json.dumps(
            {k: v for k, v in state.items() if k != "state_hash"}, sort_keys=True, allow_nan=False
        ).encode()
    ).hexdigest()


class P2Ledger(CampaignLedger):
    iterations = 10
    preserve_completed = True

    def __init__(self, root, *, now, identity, external_seconds=0):
        self.session_id = uuid.uuid4().hex
        path = Path(root) / "ledger.jsonl"
        self.previous_hash = None
        if path.exists():
            for line in path.read_text().splitlines():
                state = json.loads(line)
                if state.get("previous_hash") != self.previous_hash or state.get(
                    "state_hash"
                ) != state_hash(state):
                    raise ValueError("P2 ledger hash chain corrupt")
                self.previous_hash = state["state_hash"]
        super().__init__(
            root,
            now=now,
            identity=dict(profile="p2_synthetic_only", **identity),
            external_seconds=external_seconds,
        )
        if self.state["status"] == "completed":
            return
        if len(self.state["days"]) > 3:
            self.state["status"] = "incomplete"
            self.persist(now)
            self.lock.close()
            raise ValueError("P2 three active days exhausted")

    def begin(self, run_id, kind, now):
        if self.state["status"] != "ready":
            raise ValueError("Campaign not ready")
        run = self.state["runs"].setdefault(run_id, {"days": [], "resources": {}})
        sessions = run.setdefault("sessions", [])
        if self.session_id not in sessions:
            if (
                len(sessions) >= 3
                or sum(len(r.get("sessions", [])) for r in self.state["runs"].values()) >= 27
            ):
                self.state["status"] = "incomplete"
                self.persist(now)
                raise ValueError("Approved P2 sessions exhausted")
            sessions.append(self.session_id)
        super().begin(run_id, kind, now)

    def persist(self, now):
        from btc_risk_rl.pilots.budget import utc

        if now < self.state.get("updated_epoch", now):
            raise ValueError("UTC clock moved backwards")
        self.state.update(updated_epoch=now, updated_utc=utc(now), previous_hash=self.previous_hash)
        self.state["state_hash"] = state_hash(self.state)
        super().persist(now)
        self.previous_hash = self.state["state_hash"]
