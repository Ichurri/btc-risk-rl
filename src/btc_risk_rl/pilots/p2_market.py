"""P2 accepted-training profile and read-only preflight; campaign registration is inactive."""

import hashlib
import importlib.metadata
import json
import math
import os
import platform
import shutil
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from btc_risk_rl.agents.market_source import TrainingMarket
from btc_risk_rl.config import utc_ms
from btc_risk_rl.pilots.budget import LA_PAZ, utc
from btc_risk_rl.pilots.protocol import ROOT, P0Settings

PROTOCOL = ROOT / "docs/protocols/P2-infrastructure-v1.json"
PROTOCOL_SHA = "d5fa2f2726cd6458df3c290e7b58c591f11310c7a9b645c47a5fb6bd419e5238"
REGISTRY = ROOT / "docs/protocols/P2-market-registration-v1.json"
REGISTRY_SHA = "2052c549132bfb3df3819a17454d28f6e0690d93dfb9bc4eaa621926ba03c1c3"
ACCEPTED_MANIFEST = ROOT / "docs/evidence/segmented-h1/manifest.json"
ACCEPTED_MANIFEST_SHA = "d7cd59b7cda003a0f69883a83a0bacf06a65c37f3653a2f466c249ddf41a6998"
PREPARED = ROOT / "data/processed/segmented-B-h1"
CONFIG = ROOT / "configs/initial.toml"
CONFIG_SHA = "1a6b5b401f20c9e4a11835cf4575b70c73d72bb4e844aca7552e3f934d911269"
MARKET_CAMPAIGN = ROOT / "artifacts/p2-approved-v1"
MARKET_ACTIVATED = False  # Requires a later explicit user authorization and reviewed commit.


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def design(path=PROTOCOL):
    path = Path(path)
    if path.resolve() != PROTOCOL.resolve() or digest(path) != PROTOCOL_SHA:
        raise ValueError("Unregistered or edited P2 design")
    value = json.loads(path.read_text())
    if (value["protocol_id"] != "P2-infrastructure-v1"
            or value["market_execution_authorized"] is not False):
        raise ValueError("P2 market profile remains inactive")
    return value


def roster():
    return [(b["seed"], c) for b in design()["blocks"] for c in b["order"]]


@dataclass(frozen=True)
class P2MarketSettings(P0Settings):
    purpose: str = "authorized_p2_only"
    seed: int = 610031
    iterations: int = 10
    critic_epochs: int = 4

    def __post_init__(self):
        p = design()
        t = p["training_candidate"]
        expected = dict(
            purpose="authorized_p2_only", hidden=t["hidden"], iterations=t["iterations"],
            n_a=t["n_a"], n_q=t["n_q"], n_b=t["n_b"],
            actor_epochs=t["actor_epochs"], critic_epochs=t["critic_epochs"],
            minibatch=t["minibatch_trajectories"], actor_lr=t["actor_lr"],
            critic_lr=t["critic_lr"], dual_lr=t["dual_lr"], clip=t["clip"],
            bound=p["risk"]["bound_selected"], seed=self.seed,
            fragment_steps=t["fragment_steps"],
        )
        if asdict(self) != expected or self.seed not in {s for s, _ in roster()}:
            raise ValueError("P2 settings differ from accepted design")


class P2MarketPermit:
    """Worker lease: fail closed until a separate registration is reviewed and activated."""

    def __init__(self, token):
        self.token = token
        self.settings = self.condition = self.run_id = None

    @staticmethod
    def require_registration(path=PROTOCOL):
        design(PROTOCOL if path is None else path)
        if digest(CONFIG) != CONFIG_SHA:
            raise PermissionError("P2 market configuration identity changed")
        if digest(REGISTRY) != REGISTRY_SHA:
            raise PermissionError("P2 registration changed without reviewed code")
        entry = json.loads(REGISTRY.read_text())
        if (entry.get("protocol_sha256") != PROTOCOL_SHA
                or entry.get("accepted_manifest_sha256") != ACCEPTED_MANIFEST_SHA
                or not MARKET_ACTIVATED or entry.get("active") is not True
                or not entry.get("approval_record") or not entry.get("campaign_permit")):
            raise PermissionError("P2 market campaign NOT AUTHORIZED")
        return entry

    def validate(self, settings, condition, run_id):
        self.require_registration()
        if type(settings) is not P2MarketSettings:
            raise PermissionError("P2 market settings required")
        rows = roster()
        state = json.loads((MARKET_CAMPAIGN / "ledger.jsonl").read_text().splitlines()[-1])
        pending = state.get("pending") or {}
        index = state["cursor"]
        if (state["status"] != "running" or not 0 <= index < len(rows)
                or pending.get("token") != self.token
                or pending.get("supervisor_pid") != os.getppid()
                or pending.get("run_id") != run_id
                or rows[index] != (settings.seed, condition)
                or run_id != f"run-{index:02d}-{condition}"):
            raise PermissionError("No active registered P2 supervisor lease")
        self.settings, self.condition, self.run_id = settings, condition, run_id

    def validate_d(self, source, seed, run_id):
        if type(source) is not TrainingMarket or seed != getattr(self.settings, "seed", None):
            raise PermissionError("P2 diagnostic source/seed mismatch")
        self.validate(self.settings, self.condition, run_id)
        if (run_id != self.run_id or len(source.route_ids) != 7048
                or source.identity()["manifest_sha256"] != ACCEPTED_MANIFEST_SHA
                or source.audit["normalizer_refitted"]
                or source.audit["validation_observations_loaded"]):
            raise PermissionError("P2 diagnostic training identity mismatch")


def inspect_training_source(config, prepared, *, expected_manifest):
    """Read accepted training prefix and hashes; never request an episode path."""
    if (utc_ms(config.data.train_start) != 1514764800000
            or utc_ms(config.data.validation_start) != 1672531200000):
        raise ValueError("P2 preflight accepts only training 2018–2022")
    source = TrainingMarket(config, Path(prepared), expected_manifest=expected_manifest)
    view = source._view
    if len(source.route_ids) != 7048 or len(set(source.route_ids)) != 7048:
        raise ValueError("P2 accepted start count mismatch")
    episodes = view._episodes
    lo = int(episodes.first_target_ms.min())
    hi = int(episodes.last_target_ms.max())
    if (not (episodes.partition == "train").all() or lo < utc_ms(config.data.train_start)
            or hi >= utc_ms(config.data.validation_start)
            or source.audit["normalizer_refitted"]
            or source.audit["validation_observations_loaded"]):
        raise ValueError("P2 source escaped training partition or refitted scaler")
    identity = source.identity()
    return dict(profile=source.profile, accepted_starts=len(source.route_ids),
                first_target_ms=lo, last_target_ms=hi,
                manifest_sha256=identity["manifest_sha256"],
                scaler_sha256=identity["scaler_sha256"],
                config_sha256=identity["config_sha256"],
                product_hashes=identity["files"],
                validation_observations_loaded=False, normalizer_refitted=False,
                fit_count=source.audit["fit_count"],
                config_compatibility=source.audit["config_compatibility"],
                trajectories_generated=0)


def inspect_shared_budget(artifacts, *, now):
    """Read-only snapshot; runtime admission will take SharedBudget's global lock."""
    root = Path(artifacts)
    local_day = datetime.fromtimestamp(now, LA_PAZ).date().isoformat()
    spent = 0.0
    sources = []
    for path in sorted(root.glob("p*-approved-v*/ledger.jsonl")):
        state = json.loads(path.read_text().splitlines()[-1])
        if state["status"] == "running":
            raise ValueError("Another campaign is running/interrupted")
        day = state["days"].get(local_day, {})
        seconds = day.get("charged_wall_seconds", day.get("active_seconds", 0.0))
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Invalid external campaign seconds")
        spent += seconds
        sources.append(dict(path=str(path), sha256=digest(path), seconds=seconds))
    return dict(day_local=local_day, sampled_utc=utc(now),
                external_seconds=spent, remaining_seconds=max(0.0, 10800-spent),
                sources=sources, lock_acquired=False)


def inspect_preflight(*, now=None):
    """Development-only read. No permission activation, optimizer or path generation."""
    from btc_risk_rl.config import load_config

    now = time.time() if now is None else now
    p = design()
    if digest(CONFIG) != CONFIG_SHA:
        raise ValueError("P2 market configuration identity changed")
    if digest(REGISTRY) != REGISTRY_SHA:
        raise ValueError("P2 registration identity changed")
    registry = json.loads(REGISTRY.read_text())
    if (registry.get("active") is not False or registry.get("approval_record") is not None
            or registry.get("campaign_permit") is not None):
        raise ValueError("P2 preflight requires inactive registration")
    if digest(ACCEPTED_MANIFEST) != ACCEPTED_MANIFEST_SHA:
        raise ValueError("Accepted H1 manifest anchor changed")
    source = inspect_training_source(load_config(CONFIG), PREPARED,
                                     expected_manifest=ACCEPTED_MANIFEST_SHA)
    if source["manifest_sha256"] != ACCEPTED_MANIFEST_SHA:
        raise ValueError("Unexpected accepted market source")
    files = sorted((ROOT / "src/btc_risk_rl").rglob("*.py")) + [
        ROOT / "scripts/run_p2.py", ROOT / "scripts/preflight_p2.py",
        ROOT / "configs/initial.toml", ROOT / "uv.lock", ROOT / "pyproject.toml",
    ]
    hashes = {str(f.relative_to(ROOT)): digest(f) for f in files}
    mem = next(int(row.split()[1])*1024 for row in Path("/proc/meminfo").read_text().splitlines()
               if row.startswith("MemAvailable:"))
    disk = shutil.disk_usage(ROOT / "artifacts").free
    if (mem < p["budget_proposal"]["min_available_memory_bytes"]
            or disk < p["budget_proposal"]["min_free_disk_bytes"]):
        raise ValueError("Insufficient preflight memory/disk")
    runtime = dict(python=platform.python_version(), machine=platform.machine(),
                   packages={name: importlib.metadata.version(name)
                             for name in ("torch", "numpy", "pandas", "gymnasium")})
    return dict(status="ready_for_review_not_execution", design_sha256=PROTOCOL_SHA,
                registry_sha256=digest(REGISTRY), registry_active=False,
                market_command_enabled=False, training_source=source,
                code_config_lock_hashes=hashes, shared_budget=inspect_shared_budget(
                    ROOT / "artifacts", now=now), resources=dict(
                        available_memory_bytes=mem, free_disk_bytes=disk),
                runtime=runtime, learning_trajectories_if_authorized=81360,
                diagnostic_trajectories_if_authorized=5760,
                p1_learning_only_proxy_seconds=5512.723,
                p2_d_cost_seconds_measured=None,
                validation_accessed=False, final_accessed=False,
                market_trajectories_generated=0, optimizer_updates=0)
