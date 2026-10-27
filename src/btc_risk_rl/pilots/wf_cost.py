"""Isolated 22-unit walk-forward training-cost study contract.

This module offers a read-only preflight and pure admission rules. The public
execution boundary verifies a pinned, study-specific registration before
loading a market source or creating a campaign root.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from btc_risk_rl.agents.synthetic import SyntheticSettings
from btc_risk_rl.pilots.budget import LA_PAZ, utc
from btc_risk_rl.pilots.p2_budget import P2Ledger
from btc_risk_rl.pilots.protocol import ROOT

PROTOCOL = ROOT / "docs/proposals/OOS-v1-2-costo-entrenamiento-cortes-v1.md"
V12 = ROOT / "docs/proposals/cierre-pilotos-evaluacion-fuera-muestra-v1-2.md"
CONFIG = ROOT / "configs/initial.toml"
DESIGN = ROOT / "docs/protocols/OOS-v1-2-wf-cost-executor-v1.json"
TRAIN_SHARD = ROOT / "data/processed/p2r-training-h1"
CAMPAIGN = ROOT / "artifacts/oos-v12-wf-cost-only-01"
SHARD_MANIFEST_SHA256 = "62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9"
# Closed prospectively after the second service failed its identity guard
# before unit 1. Keep the historical registration hash for audit only.
MARKET_EXECUTION_ENABLED = False
REGISTRATION_SHA256 = "b36e32521f43af3f0b7b363f2555d1bee19fa5200c3cee30b5e8987068984369"
REGISTRATION = ROOT / "docs/protocols/OOS-v1-2-wf-cost-approval.json"
ROSTER = (("2021", 276696733, "C10"), ("2022", 498614892, "C10"))
EXPECTED = {"2021": (3639, 5764), "2022": (4678, 7703)}


@dataclass(frozen=True)
class WFCostSettings(SyntheticSettings):
    """Exact cost-study candidate, distinct from approved P3 settings."""

    purpose: str = "wf_cost_only"
    hidden: int = 32
    iterations: int = 10
    n_a: int = 64
    n_q: int = 400
    n_b: int = 400
    actor_epochs: int = 2
    critic_epochs: int = 4
    minibatch: int = 16
    bound: float = 0.10536051565782628
    seed: int = 276696733
    critic_beta: int = 0

    def __post_init__(self):
        from btc_risk_rl.pilots.p3_market import BASE_DESIGN

        candidate = json.loads(BASE_DESIGN.read_text())["training_candidate"]
        expected = dict(
            purpose="wf_cost_only", hidden=candidate["hidden"],
            iterations=10, n_a=candidate["n_a"], n_q=candidate["n_q"],
            n_b=candidate["n_b"], actor_epochs=candidate["actor_epochs"],
            critic_epochs=4, minibatch=candidate["minibatch_trajectories"],
            actor_lr=candidate["actor_lr"], critic_lr=candidate["critic_lr"],
            dual_lr=candidate["dual_lr"], clip=candidate["clip"],
            bound=0.10536051565782628, seed=self.seed,
            fragment_steps=candidate["fragment_steps"], critic_beta=0,
        )
        if (type(self.seed) is not int or self.seed not in {row[1] for row in ROSTER}
                or asdict(self) != expected):
            raise ValueError("WF cost settings differ from frozen 22-unit proposal")


class WFCostLedger(P2Ledger):
    """Dedicated chained ledger, exact 2×11 order and tighter unit caps."""

    iterations = 10

    def __init__(self, root, *, identity, now, external_seconds=0):
        if "roster" in identity:
            rows = identity["roster"]
            if not isinstance(rows, (tuple, list)):
                raise ValueError("WF cost roster identity has invalid shape")
            canonical = []
            for row in rows:
                if (not isinstance(row, (tuple, list)) or len(row) != 3
                        or type(row[0]) is not str or type(row[1]) is not int
                        or type(row[2]) is not str):
                    raise ValueError("WF cost roster identity has invalid shape")
                canonical.append(list(row))
            identity = {**identity, "roster": canonical}
        super().__init__(root, identity=identity, now=now,
                         external_seconds=external_seconds)
        if self.state["status"] == "completed":
            return
        if len(self.state["days"]) > 2:
            self.state["status"] = "incomplete"
            self.persist(now)
            self.lock.close()
            raise ValueError("WF cost two active days exhausted")
        self.day["work_deadline"] = min(self.day["work_deadline"],
                                         self.day["hard_deadline"] - 2700)
        self.persist(now)

    def _seconds(self, now):
        current = max(0.0, now - self.day["started_utc_epoch"])
        previous = sum(row.get("charged_wall_seconds", 0.0)
                       for day, row in self.state["days"].items() if day != self.day_key)
        return current, previous + current

    def admit_unit(self, fold, unit, now):
        if self.state["status"] != "ready" or not self.day["preflight_done"]:
            raise ValueError("WF cost preflight and ready boundary required")
        if (fold, unit) != units()[len(self.state["units"])]:
            raise ValueError("WF cost roster or unit order changed")
        current, cumulative = self._seconds(now)
        decision = admit(BudgetState(tuple(self.state["days"]), current, cumulative,
                                     self.day["external_seconds"] + current),
                         self.day_key, unit)
        if decision == "start" and self.day["work_deadline"] - now < unit_cap(unit):
            return "pause"
        return decision

    def begin_unit(self, fold, unit, now):
        if (fold, unit) != units()[len(self.state["units"])]:
            raise ValueError("WF cost roster or unit order changed")
        if self.state["status"] != "ready":
            raise ValueError("Campaign not ready")
        if self.admit_unit(fold, unit, now) != "start":
            raise ValueError("WF cost unit was not admitted")
        if len(self.state["days"]) > 2:
            raise ValueError("WF cost active-day limit")
        run_id = f"wf-{fold}"
        super().begin(run_id, "q0" if unit == 0 else "iteration", now)
        self.state["pending"]["unit"] = unit
        self.persist(now)

    def accept_unit(self, fold, unit, now, checkpoint, *, report, resources=None,
                    evidence=None):
        if self.state["status"] != "running":
            raise ValueError("No active WF cost unit")
        pending = self.state["pending"]
        try:
            if (pending.get("run_id") != f"wf-{fold}" or pending.get("unit") != unit
                    or (fold, unit) != units()[len(self.state["units"])]):
                raise ValueError("WF cost pending identity mismatch")
            expected_boundary = "after_q0" if unit == 0 else "after_dual_and_D"
            actor, critic = 8 * unit, 16 * unit
            marker = unit > 0
            if (report.get("boundary") != expected_boundary
                    or type(report.get("actor_updates")) is not int
                    or type(report.get("critic_updates")) is not int
                    or report["actor_updates"] != actor
                    or report["critic_updates"] != critic
                    or report.get("market_training_executed") is not marker):
                raise ValueError("WF cost marker/counters/boundary mismatch")
            if now - pending["start"] > unit_cap(unit):
                raise ValueError("WF cost unit cap exceeded")
            checkpoint = Path(checkpoint)
            canonical = self.root / f"wf-{fold}" / f"checkpoint-{unit}"
            if (checkpoint.resolve() != canonical.resolve()
                    or checkpoint.is_symlink() or not checkpoint.is_dir()):
                raise ValueError("WF cost complete checkpoint missing")
            manifest_path = checkpoint / "manifest.json"
            state_path = checkpoint / "state.pt"
            if not manifest_path.is_file() or not state_path.is_file():
                raise ValueError("WF cost complete checkpoint missing")
            sha = digest(state_path)
            manifest = json.loads(manifest_path.read_text())
            if (manifest.get("schema_version") != "p2_complete_boundary_v1"
                    or manifest.get("boundary") != expected_boundary
                    or manifest.get("profile") != "wf_cost_only"
                    or manifest.get("run_id") != f"wf-{fold}"
                    or manifest.get("condition") != "C10"
                    or manifest.get("state_sha256") != sha):
                raise ValueError("WF cost checkpoint manifest mismatch")
            expected_delta = {"actor_updates": 0 if unit == 0 else 8,
                              "critic_updates": 0 if unit == 0 else 16}
            if resources is not None and any(resources.get(key) != value
                                             for key, value in expected_delta.items()):
                raise ValueError("WF cost resource delta mismatch")
            super().finish(now, resources=resources or expected_delta,
                           condition="C10", checkpoint=str(checkpoint),
                           checkpoint_sha256=sha,
                           work_seconds=now - pending["start"], work_ended=now,
                           **(evidence or {}))
            if self.state["cursor"] == 2 and len(self.state["units"]) == 22:
                self.state["status"] = "completed"
                self.persist(now)
            return sha
        except (OSError, TypeError, ValueError) as exc:
            self.fail(now, str(exc))
            raise


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def roster() -> tuple[tuple[str, int, str], ...]:
    """Fixed order; cost seeds cannot enter the main or auxiliary trial."""
    return ROSTER


def units() -> tuple[tuple[str, int], ...]:
    return tuple((fold, unit) for fold, _, _ in roster() for unit in range(11))


def unit_cap(unit: int) -> int:
    if type(unit) is not int or not 0 <= unit <= 10:
        raise ValueError("Cost study has only Q0 and ten Q/A/B+D units")
    return 120 if unit == 0 else 180


@dataclass(frozen=True)
class BudgetState:
    active_days: tuple[str, ...]
    daily_own: float
    cumulative: float
    global_spent: float


def admit(state: BudgetState, day: str, unit: int) -> str:
    """Reserve the full cap before starting; never downgrade a partial unit."""
    cap = unit_cap(unit)
    if not all(math.isfinite(x) and x >= 0 for x in (
        state.daily_own, state.cumulative, state.global_spent
    )):
        raise ValueError("Invalid budget debit")
    if day not in state.active_days and len(state.active_days) >= 2:
        return "incomplete"
    own = state.daily_own if day in state.active_days else 0.0
    if state.cumulative + cap > 5400:
        return "incomplete"
    if own + cap > 3600 or state.global_spent + cap + 2700 > 10800:
        return "pause"
    return "start"


def guard_fold_path(path: Path) -> Path:
    """Allow only immutable fold product locations inside the isolated root."""
    path = Path(path)
    expected = (CAMPAIGN / "folds").resolve()
    if path.resolve() not in {expected / "wf-2021", expected / "wf-2022"}:
        raise ValueError("Fold path escapes isolated cost-study root")
    if path.is_symlink():
        raise ValueError("Fold path may not be a symlink")
    return path


def require_campaign() -> dict:
    """Code-level gate precedes request reads, shard loading and root creation."""
    if not MARKET_EXECUTION_ENABLED or REGISTRATION_SHA256 is None:
        raise PermissionError("WF cost market study NOT AUTHORIZED")
    if digest(REGISTRATION) != REGISTRATION_SHA256:
        raise PermissionError("WF cost registration hash mismatch")
    entry = json.loads(REGISTRATION.read_text())
    if (entry.get("active") is not True
            or entry.get("scope") != "cost_measurement_training_folds_only"
            or entry.get("campaign") != CAMPAIGN.name
            or entry.get("protocol_sha256") != digest(PROTOCOL)
            or entry.get("design_sha256") != digest(DESIGN)
            or entry.get("training_shard_manifest_sha256") != SHARD_MANIFEST_SHA256):
        raise PermissionError("WF cost registration inconsistent")
    return entry


class WFCostPermit:
    """Worker lease bound to one fold/unit, parent PID and chained ledger."""

    def __init__(self, token):
        self.token = token
        self.fold = None

    def _pending(self):
        from btc_risk_rl.pilots.p2_budget import state_hash

        require_campaign()
        state = json.loads((CAMPAIGN / "ledger.jsonl").read_text().splitlines()[-1])
        pending = state.get("pending") or {}
        if (state.get("state_hash") != state_hash(state)
                or state.get("status") != "running"
                or pending.get("token") != self.token
                or pending.get("supervisor_pid") != os.getppid()):
            raise PermissionError("No active WF cost supervisor lease")
        return state, pending

    def validate(self, settings, condition, run_id):
        state, pending = self._pending()
        index = state.get("cursor")
        if (type(settings) is not WFCostSettings
                or type(index) is not int or not 0 <= index < 2
                or (run_id, condition, settings.seed) !=
                (f"wf-{ROSTER[index][0]}", "C10", ROSTER[index][1])
                or pending.get("run_id") != run_id):
            raise PermissionError("WF cost run identity mismatch")
        self.fold = ROSTER[index][0]

    def validate_d(self, source, seed, run_id):
        from btc_risk_rl.agents.market_source import TrainingMarket

        state, _ = self._pending()
        fold, expected_seed, _ = ROSTER[state["cursor"]]
        identity = source.identity()
        fold_manifest = CAMPAIGN / "folds" / f"wf-{fold}" / "manifest.json"
        recorded = json.loads(fold_manifest.read_text())
        if (type(source) is not TrainingMarket or seed != expected_seed
                or run_id != f"wf-{fold}" or identity.get("fold") != fold
                or identity.get("training_shard_manifest_sha256") != SHARD_MANIFEST_SHA256
                or len(source.route_ids) != EXPECTED[fold][0]
                or recorded.get("source_identity") != identity
                or state["identity"]["source"].get(fold) != identity
                or source.audit["normalizer_refitted"]
                or source.audit["validation_observations_loaded"]):
            raise PermissionError("WF cost D escaped accepted fold")

    def validate_request(self, path, request):
        state, pending = self._pending()
        index = state["cursor"]
        fold, seed, condition = ROSTER[index]
        unit = pending.get("unit")
        root = CAMPAIGN / f"wf-{fold}"
        previous = state["runs"].get(f"wf-{fold}", {}).get("checkpoint")
        if (type(unit) is not int or not 0 <= unit <= 10
                or Path(path).resolve() != (root / f"request-{unit}.json").resolve()
                or pending.get("request_sha256") != digest(path)
                or request.get("root") != str(root)
                or request.get("run_id") != f"wf-{fold}"
                or request.get("fold") != fold
                or request.get("condition") != condition
                or request.get("unit") != unit
                or request.get("previous") != previous
                or request.get("token") != self.token
                or request.get("settings") != asdict(WFCostSettings(seed=seed))
                or request.get("config") != str(CONFIG)
                or request.get("atomic_checkpoint") is not True):
            raise PermissionError("WF cost worker request does not match pending unit")


def run_historical_units() -> None:
    require_campaign()
    from btc_risk_rl.pilots.wf_cost_units import run_units

    return run_units()


def _command_output(args: list[str]) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=10,
                                check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"unavailable: {exc}"
    return result.stdout.strip() or result.stderr.strip() or f"exit={result.returncode}"


def inspect_host() -> dict:
    """Read host state; do not change power, linger or the user manager."""
    from btc_risk_rl.pilots.p2r import read_power

    try:
        ac, battery = read_power()
        power = dict(ac=ac, battery_percent=battery)
    except (OSError, ValueError) as exc:
        power = dict(error=str(exc))
    available = next((int(line.split()[1]) * 1024
                      for line in Path("/proc/meminfo").read_text().splitlines()
                      if line.startswith("MemAvailable:")), None)
    return dict(
        power=power,
        memory_available_bytes=available,
        disk_free_bytes=shutil.disk_usage(ROOT / "artifacts").free,
        linger=_command_output(["loginctl", "show-user", str(os.getuid()),
                                "-p", "Linger", "--value"]),
        user_manager=_command_output(["systemctl", "--user", "is-system-running"]),
    )


def inspect_inputs() -> dict:
    """Hash only accepted training products and metadata; never open shared CSV."""
    opened = []
    hashes = {}
    for path in (PROTOCOL, V12, DESIGN, CONFIG, TRAIN_SHARD / "manifest.json"):
        hashes[str(path)] = digest(path)
        opened.append(str(path))
    if hashes[str(TRAIN_SHARD / "manifest.json")] != SHARD_MANIFEST_SHA256:
        raise ValueError("Training shard manifest changed")
    manifest = json.loads((TRAIN_SHARD / "manifest.json").read_text())
    for name, expected in manifest["files"].items():
        path = TRAIN_SHARD / name
        if path.is_symlink() or digest(path) != expected:
            raise ValueError(f"Training-only product changed: {name}")
        opened.append(str(path))
        hashes[str(path)] = expected
    if (manifest["status"] != "accepted_for_p2r_training_only"
            or manifest["train_end_exclusive_ms"] != 1672531200000):
        raise ValueError("Training shard scope changed")
    design = json.loads(DESIGN.read_text())
    if (design["status"] != "infrastructure_only_not_authorized"
            or design["total_units"] != 22
            or [tuple(x) for x in design["roster"]] != list(ROSTER)):
        raise ValueError("Cost-study design changed")
    missing_folds = []
    for fold in EXPECTED:
        location = guard_fold_path(CAMPAIGN / "folds" / f"wf-{fold}")
        if not (location / "manifest.json").is_file():
            missing_folds.append(str(location / "manifest.json"))
    return dict(ok=True, opened=opened, sha256=hashes,
                missing_fold_manifests=missing_folds,
                accepted_training_end_exclusive_ms=1672531200000)


def inspect_budget(*, now: float | None = None) -> dict:
    """Read prior campaign debits for the current La Paz day without locking."""
    from btc_risk_rl.pilots.p2_budget import state_hash

    now = time.time() if now is None else now
    day = datetime.fromtimestamp(now, LA_PAZ).date().isoformat()
    sources, spent, active = [], 0.0, []
    for path in sorted((ROOT / "artifacts").glob("p*-approved-v*/ledger.jsonl")):
        raw = path.read_bytes()
        state = json.loads(raw.splitlines()[-1])
        if state.get("state_hash") and state["state_hash"] != state_hash(state):
            raise ValueError(f"Corrupt campaign ledger: {path}")
        if state.get("status") == "running":
            active.append(str(path))
        debit = state.get("days", {}).get(day, {})
        charged = debit.get("charged_wall_seconds")
        incomplete = bool(debit) and (
            charged is None or charged == 0
            or (state.get("status") in {"failed", "incomplete"} and state.get("pending"))
        )
        seconds = 10800 if incomplete else (charged if charged is not None else 0.0)
        if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
            raise ValueError(f"Invalid campaign debit: {path}")
        spent += seconds
        sources.append(dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(),
                            status=state.get("status"), charged_today_seconds=seconds,
                            reason="incomplete_debit" if incomplete else "measured"))
    return dict(ok=not active, day_la_paz=day, global_spent=spent,
                remaining_before_reserve=max(0.0, 10800 - spent - 2700),
                active_campaigns=active, sources=sources)


def inspect_preflight() -> dict:
    """Read-only snapshot. An absent permission is always a launch blocker."""
    blockers = []
    host = inspect_host()
    power = host["power"]
    if power.get("ac") is not True:
        blockers.append("AC not connected" if "error" not in power else power["error"])
    if power.get("battery_percent", -1) < 50:
        blockers.append("Battery below 50 percent")
    if (host["memory_available_bytes"] is None
            or host["memory_available_bytes"] < 4 * 1024**3):
        blockers.append("Available memory below 4 GiB")
    if host["disk_free_bytes"] < 20 * 1024**3:
        blockers.append("Free disk below 20 GiB")
    if host["linger"] != "yes":
        blockers.append("Linger is not yes")
    if host["user_manager"] != "running":
        blockers.append("systemd --user manager is not running cleanly")
    try:
        inputs = inspect_inputs()
    except (OSError, KeyError, ValueError) as exc:
        inputs = dict(ok=False, error=str(exc), opened=[])
        blockers.append("Training input integrity: " + str(exc))
    try:
        budget = inspect_budget()
    except (OSError, KeyError, ValueError) as exc:
        budget = dict(ok=False, error=str(exc))
        blockers.append("Shared budget: " + str(exc))
    else:
        if not budget["ok"]:
            blockers.append("Another campaign active")
        if budget.get("remaining_before_reserve", 10800 - budget["global_spent"] - 2700) < 120:
            blockers.append("Daily budget cannot admit Q0")
    if CAMPAIGN.exists() and not (CAMPAIGN / "ledger.jsonl").is_file():
        blockers.append("Reserved root exists without a campaign ledger")
    if not MARKET_EXECUTION_ENABLED or REGISTRATION_SHA256 is None:
        blockers.append("Cost-study campaign has no active approval")
    else:
        try:
            require_campaign()
        except (OSError, KeyError, ValueError, PermissionError) as exc:
            blockers.append("Cost-study approval invalid: " + str(exc))
    return dict(status="blocked" if blockers else "ready", observed_utc=utc(time.time()),
                market_execution_enabled=MARKET_EXECUTION_ENABLED,
                blockers=blockers, host=host, inputs=inputs, budget=budget,
                root_exists=CAMPAIGN.exists())
