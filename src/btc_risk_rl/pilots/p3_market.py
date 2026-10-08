"""P3 historical contract and inactive, independent campaign authorization."""

import hashlib
import json
import os
import shutil
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from btc_risk_rl.agents.market_source import TrainingMarket
from btc_risk_rl.config import load_config
from btc_risk_rl.pilots.p2_budget import state_hash
from btc_risk_rl.pilots.protocol import ROOT, P0Settings

PROTOCOL = ROOT / "docs/proposals/P3-protocolo-v1-1.md"
ADOPTION = ROOT / "docs/protocols/P3-adopcion-metodologica-v1-1.md"
DESIGN = ROOT / "docs/protocols/P3-executor-infrastructure-v1.json"
BASE_DESIGN = ROOT / "docs/protocols/P2-infrastructure-v1.json"
MANIFEST = ROOT / "docs/evidence/segmented-h1/manifest.json"
CONFIG = ROOT / "configs/initial.toml"
ENTRYPOINT = ROOT / "scripts/run_p3_market.py"
TRAIN_SHARD = ROOT / "data/processed/p2r-training-h1"
PREPARED = ROOT / "data/processed/segmented-B-h1"
CAMPAIGN = ROOT / "artifacts/p3-approved-v1"
REGISTRATION = ROOT / "docs/protocols/P3-market-approval.json"

ANCHORS = {
    PROTOCOL: "24bfc835650353dc6709db0de36de246b83045541d7103b11361a14ecd73ce21",
    ADOPTION: "53755060b93faaa8f8646b7efdea87df407572c41686824a340ea178aa75ebc9",
    DESIGN: "4f2c0861609e096966632734adc28a6e75092295e65d9d9ec464b9a61f0962a7",
    BASE_DESIGN: "d5fa2f2726cd6458df3c290e7b58c591f11310c7a9b645c47a5fb6bd419e5238",
    MANIFEST: "d7cd59b7cda003a0f69883a83a0bacf06a65c37f3653a2f466c249ddf41a6998",
    CONFIG: "1a6b5b401f20c9e4a11835cf4575b70c73d72bb4e844aca7552e3f934d911269",
}
TRAIN_SHARD_MANIFEST_SHA256 = "62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9"

# A future approval must be registered separately and pinned in reviewed code.
MARKET_EXECUTION_ENABLED = False
REGISTRATION_SHA256 = None


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def design():
    for path, expected in ANCHORS.items():
        if digest(path) != expected:
            raise ValueError(f"P3 frozen input changed: {path.name}")
    data = json.loads(DESIGN.read_text())
    if data["protocol_id"] != "P3-executor-infrastructure-v1" or data["market_execution_authorized"]:
        raise ValueError("P3 infrastructure design cannot authorize a campaign")
    return data


def roster():
    rows = [
        (block["seed"], condition["name"], beta)
        for block in design()["blocks"]
        for condition in block["conditions"]
        for beta in condition["arms"]
    ]
    if len(rows) != 18 or len(set(rows)) != 18:
        raise ValueError("P3 requires eighteen distinct run identities")
    return rows


@dataclass(frozen=True)
class P3MarketSettings(P0Settings):
    purpose: str = "authorized_p3_only"
    seed: int = 710031
    iterations: int = 10
    critic_epochs: int = 4
    critic_beta: int = 0

    def __post_init__(self):
        p = design()
        candidate = json.loads(BASE_DESIGN.read_text())["training_candidate"]
        expected = dict(
            purpose="authorized_p3_only", hidden=candidate["hidden"],
            iterations=p["iterations"], n_a=candidate["n_a"],
            n_q=candidate["n_q"], n_b=candidate["n_b"],
            actor_epochs=candidate["actor_epochs"], critic_epochs=p["critic_epochs"],
            minibatch=candidate["minibatch_trajectories"],
            actor_lr=candidate["actor_lr"], critic_lr=candidate["critic_lr"],
            dual_lr=candidate["dual_lr"], clip=candidate["clip"],
            bound=p["risk_bound"], seed=self.seed,
            fragment_steps=candidate["fragment_steps"], critic_beta=self.critic_beta,
        )
        if (type(self.critic_beta) is not int or self.critic_beta not in {0, 1}
                or asdict(self) != expected
                or self.seed not in {seed for seed, _, _ in roster()}):
            raise ValueError("P3 settings differ from adopted design")


def run_id_for(index, row):
    seed, condition, beta = row
    if type(index) is not int or index < 0 or (seed, condition, beta) != roster()[index]:
        raise ValueError("P3 run identity disagrees with fixed order")
    return f"run-{index:02d}-{condition}-b{beta}"


class P3MarketPermit:
    """Worker lease tied to the future P3-only hashed ledger and parent PID."""

    def __init__(self, token):
        self.token = token
        self.settings = self.condition = self.run_id = None

    @staticmethod
    def require_campaign():
        # An edited JSON or command cannot cross this code-level gate.
        if not MARKET_EXECUTION_ENABLED or REGISTRATION_SHA256 is None:
            raise PermissionError("P3 market campaign NOT AUTHORIZED")
        if digest(REGISTRATION) != REGISTRATION_SHA256:
            raise PermissionError("P3 market approval hash mismatch")
        entry = json.loads(REGISTRATION.read_text())
        if (entry.get("active") is not True
                or entry.get("scope") != "accepted_training_2018_2022_only"
                or entry.get("campaign") != CAMPAIGN.name
                or entry.get("protocol_sha256") != ANCHORS[PROTOCOL]
                or entry.get("adoption_sha256") != ANCHORS[ADOPTION]
                or entry.get("design_sha256") != ANCHORS[DESIGN]
                or entry.get("training_shard_manifest_sha256") != TRAIN_SHARD_MANIFEST_SHA256):
            raise PermissionError("P3 market campaign NOT AUTHORIZED")
        design()
        return entry

    def validate(self, settings, condition, run_id):
        self.require_campaign()
        if type(settings) is not P3MarketSettings:
            raise PermissionError("P3 market settings required")
        state = json.loads((CAMPAIGN / "ledger.jsonl").read_text().splitlines()[-1])
        pending = state.get("pending") or {}
        index = state.get("cursor")
        if (state.get("state_hash") != state_hash(state)
                or state.get("status") != "running"
                or type(index) is not int or not 0 <= index < 18
                or pending.get("token") != self.token
                or pending.get("supervisor_pid") != os.getppid()
                or pending.get("run_id") != run_id
                or roster()[index] != (settings.seed, condition, settings.critic_beta)
                or run_id != run_id_for(index, roster()[index])):
            raise PermissionError("No active P3 supervisor lease")
        self.settings, self.condition, self.run_id = settings, condition, run_id

    def validate_d(self, source, seed, run_id):
        if type(source) is not TrainingMarket or seed != getattr(self.settings, "seed", None):
            raise PermissionError("P3 diagnostic source/seed mismatch")
        self.validate(self.settings, self.condition, run_id)
        identity = source.identity()
        if (run_id != self.run_id or len(source.route_ids) != 7048
                or identity["manifest_sha256"] != ANCHORS[MANIFEST]
                or identity.get("training_shard_manifest_sha256")
                != TRAIN_SHARD_MANIFEST_SHA256
                or source.audit["normalizer_refitted"]
                or source.audit["validation_observations_loaded"]):
            raise PermissionError("P3 diagnostic training identity mismatch")

    def validate_request(self, request_path, request):
        self.require_campaign()
        state = json.loads((CAMPAIGN / "ledger.jsonl").read_text().splitlines()[-1])
        pending = state.get("pending") or {}
        run_id, unit = pending.get("run_id"), pending.get("unit")
        root = CAMPAIGN / str(run_id)
        previous = state["runs"].get(run_id, {}).get("checkpoint")
        index = state.get("cursor")
        row = roster()[index] if type(index) is int and 0 <= index < 18 else None
        if (state.get("state_hash") != state_hash(state)
                or state.get("status") != "running" or row is None
                or pending.get("token") != self.token
                or pending.get("supervisor_pid") != os.getppid()
                or type(unit) is not int
                or Path(request_path).resolve() != (root / f"request-{unit}.json").resolve()
                or pending.get("request_sha256") != digest(request_path)
                or request.get("root") != str(root)
                or request.get("run_id") != run_id
                or run_id != run_id_for(index, row)
                or request.get("condition") != row[1]
                or type(request.get("beta")) is not int
                or request["beta"] != row[2]
                or request.get("settings") != asdict(P3MarketSettings(seed=row[0], critic_beta=row[2]))
                or request.get("unit") != unit
                or request.get("previous") != previous
                or request.get("token") != self.token
                or request.get("atomic_checkpoint") is not True
                or request.get("config") != str(CONFIG)):
            raise PermissionError("P3 worker request does not match pending unit")


def inspect_preflight(*, prepared=PREPARED, now=None):
    """Read only the H1 training shard and identity; never collect a route."""
    from btc_risk_rl.agents.checkpoint import provenance
    from btc_risk_rl.pilots.p2r import check_resources, read_power
    from btc_risk_rl.pilots.p2r_market import PRIOR_LEDGERS, inspect_shared_budget

    design()
    for name, expected in PRIOR_LEDGERS.items():
        if digest(ROOT / "artifacts" / name / "ledger.jsonl") != expected:
            raise ValueError(f"Prior campaign ledger changed: {name}")
    p2r_ledger = ROOT / "artifacts/p2r-approved-v2/ledger.jsonl"
    if digest(p2r_ledger) != "fe443e5e32d26a7de075fa6e34771c8f20651bbe566f9097bfdb367d17d0b866":
        raise ValueError("P2R original ledger changed")
    if digest(TRAIN_SHARD / "manifest.json") != TRAIN_SHARD_MANIFEST_SHA256:
        raise ValueError("P3 training shard changed")
    market = TrainingMarket(
        load_config(CONFIG), prepared, expected_manifest=ANCHORS[MANIFEST],
        training_shard=TRAIN_SHARD,
        expected_shard_manifest=TRAIN_SHARD_MANIFEST_SHA256,
    )
    episodes = market._view._episodes
    if (len(market.route_ids) != 7048 or len(set(market.route_ids)) != 7048
            or not (episodes.partition == "train").all()
            or market.audit["normalizer_refitted"]
            or market.audit["validation_observations_loaded"]):
        raise ValueError("P3 training-only source identity mismatch")
    source = dict(
        profile=market.profile,
        accepted_starts=len(market.route_ids),
        manifest_sha256=ANCHORS[MANIFEST],
        training_shard_manifest_sha256=TRAIN_SHARD_MANIFEST_SHA256,
        scaler_sha256=market.identity()["files"]["scaler.json"],
        product_hashes=market.identity()["files"],
        validation_observations_loaded=False,
        normalizer_refitted=False,
        trajectories_generated=0,
    )
    memory = next(int(line.split()[1]) * 1024 for line in Path("/proc/meminfo").read_text().splitlines()
                  if line.startswith("MemAvailable:"))
    disk = shutil.disk_usage(ROOT / "artifacts").free
    resource_blocker = None
    try:
        check_resources(stage="preflight", disk_path=ROOT / "artifacts",
                        memory_available=memory, disk_free=disk)
    except ValueError as exc:
        resource_blocker = str(exc)
    return dict(
        status=("read_only_resources_blocked" if resource_blocker
                else "read_only_ready_campaign_disabled" if not MARKET_EXECUTION_ENABLED
                else "read_only_ready_campaign_enabled"),
        protocol_sha256=ANCHORS[PROTOCOL], adoption_sha256=ANCHORS[ADOPTION],
        design_sha256=ANCHORS[DESIGN], config_sha256=ANCHORS[CONFIG],
        source=source, provenance=provenance(market),
        prior_ledgers=PRIOR_LEDGERS | {"p2r-approved-v2": digest(p2r_ledger)},
        shared_budget=inspect_shared_budget(ROOT / "artifacts", now=time.time() if now is None else now),
        power=read_power(), resources=dict(memory_available_bytes=memory, disk_free_bytes=disk),
        resource_blocker=resource_blocker,
        entrypoint_sha256=digest(ENTRYPOINT),
        market_trajectories_generated=0, optimizer_updates=0,
        market_execution_enabled=MARKET_EXECUTION_ENABLED,
    )


def run_market_units():
    """Guard before data access, root creation, or importing the supervisor."""
    P3MarketPermit.require_campaign()
    from btc_risk_rl.pilots.p3_units import run_historical_units

    return run_historical_units()
