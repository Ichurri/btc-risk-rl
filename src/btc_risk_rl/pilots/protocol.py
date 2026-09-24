"""Frozen, user-approved P0 settings; caller JSON cannot self-authorize."""

import hashlib
import json
import math
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from btc_risk_rl.agents.synthetic import SyntheticSettings

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL = ROOT / "docs/protocols/P0-approved-v1.json"
PROTOCOL_SHA = "3beec41bffa5e019b43b01e4af1f16165cdb260c0554516ba3b095ea7c1ddf33"
CAMPAIGN = ROOT / "artifacts/p0-approved-v1"


def approved(path=PROTOCOL):
    path = Path(path)
    if (
        path.resolve() != PROTOCOL.resolve()
        or hashlib.sha256(path.read_bytes()).hexdigest() != PROTOCOL_SHA
    ):
        raise ValueError("Unregistered or modified P0 protocol")
    return json.loads(path.read_text())


def roster():
    return [(b["seed"], c) for b in approved()["blocks"] for c in b["order"]]


@dataclass(frozen=True)
class P0Settings(SyntheticSettings):
    purpose: str = "authorized_p0_only"
    hidden: int = 32
    n_a: int = 64
    n_q: int = 400
    n_b: int = 400
    minibatch: int = 16
    bound: float = -math.log(0.90)
    seed: int = 410031

    def __post_init__(self):
        p = approved()
        expected = dict(
            purpose="authorized_p0_only",
            hidden=32,
            iterations=2,
            n_a=64,
            n_q=400,
            n_b=400,
            actor_epochs=2,
            critic_epochs=2,
            minibatch=16,
            actor_lr=1e-4,
            critic_lr=1e-3,
            dual_lr=0.1,
            clip=0.2,
            bound=p["risk"]["bound_selected"],
            seed=self.seed,
            fragment_steps=60,
        )
        if asdict(self) != expected or self.seed not in {b["seed"] for b in p["blocks"]}:
            raise ValueError("P0 settings differ from approved frozen configuration")


class Permit:
    """Worker-only lease bound to canonical campaign's pending unit and parent."""

    def __init__(self, token):
        self.token = token

    def validate(self, settings, condition, run_id):
        approved()
        state = json.loads((CAMPAIGN / "ledger.jsonl").read_text().splitlines()[-1])
        pending = state.get("pending") or {}
        if (
            state["status"] != "running"
            or pending.get("token") != self.token
            or pending.get("supervisor_pid") != os.getppid()
            or pending["run_id"] != run_id
        ):
            raise PermissionError("No active supervisor P0 lease")
        index = state["cursor"]
        if (
            roster()[index] != (settings.seed, condition)
            or run_id != f"run-{index:02d}-{condition}"
        ):
            raise PermissionError("P0 roster/order mismatch")
