"""Registered P1 only: frozen roster, settings and worker lease."""

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from btc_risk_rl.pilots.protocol import ROOT, P0Settings

PROTOCOL = ROOT / "docs/protocols/P1-approved-v1.json"
PROTOCOL_SHA = "fe2e86ecc8891824a538b41ad900c30db9d24e74e8424ab8dd2cf0ed2cb40eb4"
CAMPAIGN = ROOT / "artifacts/p1-approved-v1"


def approved(path=PROTOCOL):
    path = Path(path)
    if (
        path.resolve() != PROTOCOL.resolve()
        or hashlib.sha256(path.read_bytes()).hexdigest() != PROTOCOL_SHA
    ):
        raise ValueError("Unregistered or modified P1 protocol")
    return json.loads(path.read_text())


def entries():
    result = []
    for b in approved()["blocks"]:
        for c in b["order"]:
            for epochs in b["critic_epochs_order"]:
                result.append(
                    dict(
                        seed=b["seed"],
                        condition=c,
                        epochs=epochs,
                        run_id=f"run-{len(result):02d}-{c}-e{epochs}",
                    )
                )
    return result


@dataclass(frozen=True)
class P1Settings(P0Settings):
    purpose: str = "authorized_p1_only"
    seed: int = 510031

    def __post_init__(self):
        p = approved()
        expected = asdict(P0Settings())
        expected.update(
            purpose="authorized_p1_only", seed=self.seed, critic_epochs=self.critic_epochs
        )
        if (
            asdict(self) != expected
            or self.seed not in {b["seed"] for b in p["blocks"]}
            or self.critic_epochs not in (2, 4)
        ):
            raise ValueError("P1 settings differ from approved configuration")


class P1Permit:
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
            or pending.get("run_id") != run_id
        ):
            raise PermissionError("No active P1 lease")
        row = entries()[state["cursor"]]
        if (row["seed"], row["condition"], row["epochs"], row["run_id"]) != (
            settings.seed,
            condition,
            settings.critic_epochs,
            run_id,
        ):
            raise PermissionError("P1 roster/order/arm mismatch")


def check_first_pair(campaign, result):
    """Integrity only; never test performance or select checkpoints during execution."""

    def signature(report):
        metrics = [
            s for s in report["stability"] if s["phase"] == "fixed_A" and s["iteration"] == 0
        ]
        first = next(s for s in metrics if s["measurement"] == "before_actor")
        actor = next(s for s in metrics if s["measurement"] == "after_actor_before_critic")
        return first["batch_sha256"], actor["actor_sha256"]

    target = signature(result["report"])
    seed = result["report"]["settings"]["seed"]
    for path in Path(campaign).glob("run-*/unit-1.json"):
        other = json.loads(path.read_text())["report"]
        if other["settings"]["seed"] == seed and signature(other) != target:
            raise ValueError("P1 initial A or first actor mismatch across arms/conditions")
