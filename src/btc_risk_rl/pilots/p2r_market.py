"""P2R historical profile and read-only entrance audit; campaign remains disabled."""

import hashlib
import json
import math
import os
import shutil
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from btc_risk_rl.agents.market_source import TrainingMarket
from btc_risk_rl.config import load_config
from btc_risk_rl.pilots.budget import LA_PAZ, utc
from btc_risk_rl.pilots.p2_budget import state_hash
from btc_risk_rl.pilots.p2_market import inspect_training_source
from btc_risk_rl.pilots.p2r import DAY_LIMIT, EXCLUDED_DAY
from btc_risk_rl.pilots.protocol import ROOT, P0Settings

PROTOCOL = ROOT / "docs/proposals/P2R-protocolo-v2.md"
ADOPTION = ROOT / "docs/protocols/P2R-adopcion-metodologica-v2.md"
DESIGN = ROOT / "docs/protocols/P2-infrastructure-v1.json"
MANIFEST = ROOT / "docs/evidence/segmented-h1/manifest.json"
CONFIG = ROOT / "configs/initial.toml"
ENTRYPOINT = ROOT / "scripts/run_p2r_market.py"
PREPARED = ROOT / "data/processed/segmented-B-h1"
CAMPAIGN = ROOT / "artifacts/p2r-approved-v2"
REGISTRATION = ROOT / "docs/protocols/P2R-market-approval.json"

ANCHORS = {
    PROTOCOL: "3372045783747399290cf2baa1e48c82f59c3e917d49f1e9f6ef8e1d08677f79",
    ADOPTION: "7b420e180620d5512aac0f7cf696ec38b075b4d4a56ac2a33540b6debb3dfe0b",
    DESIGN: "d5fa2f2726cd6458df3c290e7b58c591f11310c7a9b645c47a5fb6bd419e5238",
    MANIFEST: "d7cd59b7cda003a0f69883a83a0bacf06a65c37f3653a2f466c249ddf41a6998",
    CONFIG: "1a6b5b401f20c9e4a11835cf4575b70c73d72bb4e844aca7552e3f934d911269",
}
PRIOR_LEDGERS = {
    "p0-approved-v1": "1d1ee72ca0ac49529f205b30942a68f381d86037e336091c490c624098339b8c",
    "p1-approved-v1": "926eab40bc764e1cae88a74e6718ba70b50e2df0626e8e34964078cc4ba55755",
    "p2-approved-v1": "e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8",
}

# This requires a later, explicit approval commit. A JSON or CLI flag cannot flip it.
MARKET_EXECUTION_ENABLED = False
REGISTRATION_SHA256 = None


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def design():
    for path, expected in ANCHORS.items():
        if digest(path) != expected:
            raise ValueError(f"P2R frozen input changed: {path.name}")
    p = json.loads(DESIGN.read_text())
    if p["protocol_id"] != "P2-infrastructure-v1" or p["market_execution_authorized"]:
        raise ValueError("P2R design anchor invalid")
    return p


def roster():
    return [(block["seed"], condition)
            for block in design()["blocks"] for condition in block["order"]]


def inspect_shared_budget(artifacts, *, now):
    """Read-only mirror of P2RSharedBudget's conservative external debit."""
    root = Path(artifacts)
    day = datetime.fromtimestamp(now, LA_PAZ).date().isoformat()
    sources = []
    spent = 0.0
    for path in sorted(root.glob("p*-approved-v*/ledger.jsonl")):
        state = json.loads(path.read_text().splitlines()[-1])
        if state["status"] == "running":
            raise ValueError("Another campaign running or interrupted")
        row = state["days"].get(day)
        if row is None:
            continue
        charged = row.get("charged_wall_seconds")
        incomplete = (charged is None or charged == 0 or
                      (state["status"] in {"failed", "incomplete"} and state.get("pending")))
        seconds = DAY_LIMIT if incomplete else charged
        if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Invalid external daily consumption")
        spent += seconds
        sources.append(dict(path=str(path), sha256=digest(path), seconds=seconds,
                            reason="incomplete_debit" if incomplete else "measured", day=day))
    if day == EXCLUDED_DAY:
        spent = DAY_LIMIT
    return dict(day_local=day, sampled_utc=utc(now), external_seconds=spent,
                remaining_seconds=max(0.0, DAY_LIMIT - spent), sources=sources,
                excluded_day=day == EXCLUDED_DAY, lock_acquired=False)


@dataclass(frozen=True)
class P2RMarketSettings(P0Settings):
    purpose: str = "authorized_p2r_only"
    seed: int = 610031
    iterations: int = 10
    critic_epochs: int = 4

    def __post_init__(self):
        protocol = design()
        t = protocol["training_candidate"]
        expected = dict(
            purpose="authorized_p2r_only", hidden=t["hidden"], iterations=t["iterations"],
            n_a=t["n_a"], n_q=t["n_q"], n_b=t["n_b"], actor_epochs=t["actor_epochs"],
            critic_epochs=t["critic_epochs"], minibatch=t["minibatch_trajectories"],
            actor_lr=t["actor_lr"], critic_lr=t["critic_lr"], dual_lr=t["dual_lr"],
            clip=t["clip"], bound=protocol["risk"]["bound_selected"], seed=self.seed,
            fragment_steps=t["fragment_steps"],
        )
        if asdict(self) != expected or self.seed not in {seed for seed, _ in roster()}:
            raise ValueError("P2R settings differ from adopted design")


class P2RMarketPermit:
    """Worker lease tied to P2R's own hashed ledger and supervisor parent."""

    def __init__(self, token):
        self.token = token
        self.settings = self.condition = self.run_id = None

    @staticmethod
    def require_campaign():
        if not MARKET_EXECUTION_ENABLED or REGISTRATION_SHA256 is None:
            raise PermissionError("P2R market campaign NOT AUTHORIZED")
        if digest(REGISTRATION) != REGISTRATION_SHA256:
            raise PermissionError("P2R market approval hash mismatch")
        entry = json.loads(REGISTRATION.read_text())
        if (entry.get("active") is not True
                or entry.get("scope") != "accepted_training_2018_2022_only"
                or entry.get("protocol_sha256") != ANCHORS[PROTOCOL]
                or entry.get("adoption_sha256") != ANCHORS[ADOPTION]
                or entry.get("campaign") != CAMPAIGN.name):
            raise PermissionError("P2R market campaign NOT AUTHORIZED")
        design()
        return entry

    def validate(self, settings, condition, run_id):
        self.require_campaign()
        if type(settings) is not P2RMarketSettings:
            raise PermissionError("P2R market settings required")
        rows = roster()
        lines = (CAMPAIGN / "ledger.jsonl").read_text().splitlines()
        state = json.loads(lines[-1])
        pending = state.get("pending") or {}
        index = state["cursor"]
        if (state.get("state_hash") != state_hash(state)
                or state["status"] != "running" or not 0 <= index < len(rows)
                or pending.get("token") != self.token
                or pending.get("supervisor_pid") != os.getppid()
                or pending.get("run_id") != run_id
                or rows[index] != (settings.seed, condition)
                or run_id != f"run-{index:02d}-{condition}"):
            raise PermissionError("No active P2R supervisor lease")
        self.settings, self.condition, self.run_id = settings, condition, run_id

    def validate_d(self, source, seed, run_id):
        if type(source) is not TrainingMarket or seed != getattr(self.settings, "seed", None):
            raise PermissionError("P2R diagnostic source/seed mismatch")
        self.validate(self.settings, self.condition, run_id)
        if (run_id != self.run_id or len(source.route_ids) != 7048
                or source.identity()["manifest_sha256"] != ANCHORS[MANIFEST]
                or source.audit["normalizer_refitted"]
                or source.audit["validation_observations_loaded"]):
            raise PermissionError("P2R diagnostic training identity mismatch")

    def validate_request(self, request_path, request):
        """Bind worker input to the pending, hashed unit in the canonical root."""
        self.require_campaign()
        state = json.loads((CAMPAIGN / "ledger.jsonl").read_text().splitlines()[-1])
        pending = state.get("pending") or {}
        run_id, unit = pending.get("run_id"), pending.get("unit")
        run_root = CAMPAIGN / str(run_id)
        previous = state["runs"].get(run_id, {}).get("checkpoint")
        if (state.get("state_hash") != state_hash(state)
                or pending.get("token") != self.token
                or not isinstance(unit, int)
                or Path(request_path).resolve() != (run_root / f"request-{unit}.json").resolve()
                or pending.get("request_sha256") != digest(request_path)
                or request.get("root") != str(run_root)
                or request.get("run_id") != run_id
                or request.get("unit") != unit
                or request.get("previous") != previous
                or request.get("token") != self.token
                or request.get("atomic_checkpoint") is not True
                or request.get("config") != str(CONFIG)):
            raise PermissionError("P2R worker request does not match pending unit")


def inspect_preflight(*, prepared=PREPARED, now=None):
    """Read-only accepted-training inspection; never generates a trajectory."""
    from btc_risk_rl.agents.checkpoint import provenance
    from btc_risk_rl.pilots.p2r import check_resources, read_power

    now = time.time() if now is None else now
    design()
    for name, expected in PRIOR_LEDGERS.items():
        if digest(ROOT / "artifacts" / name / "ledger.jsonl") != expected:
            raise ValueError(f"Prior campaign ledger changed: {name}")
    source = inspect_training_source(load_config(CONFIG), prepared,
                                     expected_manifest=ANCHORS[MANIFEST])
    if source["scaler_sha256"] != source["product_hashes"]["scaler.json"]:
        raise ValueError("P2R scaler identity mismatch")
    market = TrainingMarket(load_config(CONFIG), prepared, expected_manifest=ANCHORS[MANIFEST])
    memory = next(int(line.split()[1]) * 1024
                  for line in Path("/proc/meminfo").read_text().splitlines()
                  if line.startswith("MemAvailable:"))
    disk = shutil.disk_usage(ROOT / "artifacts").free
    if check_resources(stage="preflight", disk_path=ROOT / "artifacts",
                       memory_available=memory, disk_free=disk) != "ready":
        raise ValueError("P2R resources unavailable")
    return dict(
        status=("read_only_ready_campaign_enabled" if MARKET_EXECUTION_ENABLED
                else "read_only_ready_campaign_disabled"),
        protocol_sha256=ANCHORS[PROTOCOL], adoption_sha256=ANCHORS[ADOPTION],
        design_sha256=ANCHORS[DESIGN], config_sha256=ANCHORS[CONFIG],
        accepted_manifest_sha256=ANCHORS[MANIFEST], source=source,
        provenance=provenance(market), prior_ledgers=PRIOR_LEDGERS,
        shared_budget=inspect_shared_budget(ROOT / "artifacts", now=now),
        power=read_power(), resources=dict(memory_available_bytes=memory,
                                           disk_free_bytes=disk),
        entrypoint_sha256=digest(ENTRYPOINT),
        market_trajectories_generated=0, optimizer_updates=0,
        market_execution_enabled=MARKET_EXECUTION_ENABLED,
    )


def run_market_units():
    """Historical executor entrance, permanently blocked until separate approval."""
    P2RMarketPermit.require_campaign()  # Before data access or artifact creation.
    from btc_risk_rl.pilots.p2r_units import run_historical_units

    return run_historical_units()
