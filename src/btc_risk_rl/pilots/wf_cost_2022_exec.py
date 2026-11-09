"""Independent 2022-only cost profile with a pinned approval gate."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from btc_risk_rl.pilots.budget import LA_PAZ, CampaignLedger
from btc_risk_rl.pilots.p2_budget import P2Ledger, state_hash
from btc_risk_rl.pilots.protocol import ROOT
from btc_risk_rl.pilots.wf_cost import (
    CONFIG,
    SHARD_MANIFEST_SHA256,
    TRAIN_SHARD,
    WFCostPermit,
    WFCostSettings,
    digest,
)
from btc_risk_rl.pilots.wf_cost_2022_orchestrator import CAMPAIGN, PROPOSAL
from btc_risk_rl.pilots.wf_cost_2022_orchestrator import (
    require_campaign as require_registered_campaign,
)

ROSTER = (("2022", 498614892, "C10"),)
UNITS = tuple(range(11))
EXPECTED_ROUTES = 4678
EXPECTED_FIT_ROWS = 7703
AUTHORIZATION = ROOT / "docs/protocols/OOS-2022-02-autorizacion-20261109.md"
# Kept separate from prior WF gates. The hash is pinned only after final tests.
MARKET_EXECUTION_ENABLED = False
REGISTRATION_SHA256 = None


def _expected_settings() -> dict:
    return asdict(WFCostSettings(seed=498614892))


def require_recent_prepare(path: Path, *, now: float) -> None:
    """Demand four successful metered checks on this La Paz date before service launch."""
    path = Path(path)
    if not path.is_file():
        raise ValueError("WF 2022 prepare checks absent")
    try:
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        completed = [row for row in rows if row.get("event") == "check_end"][-4:]
        day = datetime.fromtimestamp(now, LA_PAZ).date()
        if (len(completed) != 4
                or [row["name"] for row in completed] !=
                ["suite", "ruff", "preflight", "fold"]
                or len({row["token"] for row in completed}) != 1
                or now - completed[-1]["epoch"] > 900
                or any(row["status"] != "ready" or row["epoch"] > now
                       or datetime.fromtimestamp(row["epoch"], LA_PAZ).date() != day
                       for row in completed)):
            raise ValueError("WF 2022 prepare checks invalid or stale")
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("WF 2022 prepare checks invalid") from exc


def code_sha256() -> str:
    """Hash executable source and lock; normalize only the approval digest line."""
    files = sorted((ROOT / "src/btc_risk_rl").rglob("*.py")) + [
        ROOT / "scripts/run_oos_wf_cost_2022.py",
        ROOT / "scripts/audit_oos_wf_cost_2022_preflight.py",
        ROOT / "pyproject.toml", ROOT / "uv.lock",
    ]
    mapping = {}
    for path in files:
        raw = path.read_bytes()
        if path.name in {"wf_cost_2022_exec.py", "wf_cost_2022_orchestrator.py"}:
            lines = raw.splitlines(keepends=True)
            matched = [i for i, line in enumerate(lines) if line.startswith(
                (b"REGISTRATION_SHA256 = ", b"MARKET_EXECUTION_ENABLED = "))]
            if len(matched) != 2:
                raise ValueError("WF 2022 approval declaration changed")
            for index in matched:
                name = lines[index].split(b" = ", 1)[0]
                lines[index] = name + b" = <pinned approval>\n"
            raw = b"".join(lines)
        mapping[str(path.relative_to(ROOT))] = hashlib.sha256(raw).hexdigest()
    return hashlib.sha256(json.dumps(mapping, sort_keys=True).encode()).hexdigest()


def require_campaign() -> dict:
    """Reject forged or stale permits before any request, source or root access."""
    if not MARKET_EXECUTION_ENABLED or REGISTRATION_SHA256 is None:
        raise PermissionError("WF 2022 market cost study NOT AUTHORIZED")
    # The orchestrator has its own independent code gate and approval digest.
    from btc_risk_rl.pilots import wf_cost_2022_orchestrator as budget

    registration = require_registered_campaign()
    if (registration.get("code_sha256") != code_sha256()
            or registration.get("config_sha256") != digest(CONFIG)
            or registration.get("training_shard_manifest_sha256") != SHARD_MANIFEST_SHA256
            or registration.get("authorization_sha256") != digest(AUTHORIZATION)
            or registration.get("root") != str(CAMPAIGN)
            or registration.get("roster") != [list(row) for row in ROSTER]
            or budget.REGISTRATION_SHA256 != REGISTRATION_SHA256
            or not budget.MARKET_EXECUTION_ENABLED):
        raise PermissionError("WF 2022 approval inputs changed")
    return registration


class WF2022Ledger(P2Ledger):
    """Eleven complete frontiers for one independent C10 training-cost run."""

    preserve_completed = True
    iterations = 10

    def __init__(self, root, *, now, identity, external_seconds=0):
        super().__init__(root, now=now, identity=identity,
                         external_seconds=external_seconds)
        if len(self.state["days"]) > 2:
            self.state["status"] = "incomplete"
            self.persist(now)
            self.lock.close()
            raise ValueError("WF 2022 active-day limit exceeded")

    def begin_unit(self, run_id: str, unit: int, now: float):
        if (run_id != "wf-2022" or type(unit) is not int or unit not in UNITS
                or len(self.state["units"]) != unit):
            raise ValueError("WF 2022 run or unit order changed")
        run = self.state["runs"].setdefault(run_id, {"days": [], "resources": {}})
        sessions = run.setdefault("sessions", [])
        if self.session_id not in sessions:
            sessions.append(self.session_id)
        CampaignLedger.begin(self, run_id, "q0" if unit == 0 else "iteration", now)
        self.state["pending"]["unit"] = unit
        self.persist(now)

    def accept_unit(self, unit: int, now: float, checkpoint: Path, *,
                    report: dict, resources: dict | None = None,
                    evidence: dict | None = None):
        from btc_risk_rl.pilots.wf_cost_2022_orchestrator import UNIT_CAPS

        try:
            point = Path(checkpoint)
            canonical = self.root / "wf-2022" / f"checkpoint-{unit}"
            if (self.state["status"] != "running"
                    or self.state["pending"].get("unit") != unit
                    or len(self.state["units"]) != unit):
                raise ValueError("WF 2022 pending unit mismatch")
            if (point.resolve() != canonical.resolve() or point.is_symlink()
                    or not (point / "state.pt").is_file()
                    or not (point / "manifest.json").is_file()):
                raise ValueError("WF 2022 complete checkpoint missing")
            manifest = json.loads((point / "manifest.json").read_text())
            boundary = "after_q0" if unit == 0 else "after_dual_and_D"
            if (manifest.get("schema_version") != "p2_complete_boundary_v1"
                    or manifest.get("boundary") != boundary
                    or manifest.get("profile") != "wf_cost_only"
                    or manifest.get("run_id") != "wf-2022"
                    or manifest.get("condition") != "C10"
                    or manifest.get("state_sha256") != digest(point / "state.pt")):
                raise ValueError("WF 2022 checkpoint identity/hash mismatch")
            if (report.get("boundary") != boundary
                    or report.get("actor_updates") != 8 * unit
                    or report.get("critic_updates") != 16 * unit
                    or report.get("market_training_executed") is not (unit > 0)):
                raise ValueError("WF 2022 report marker/counters mismatch")
            if now - self.state["pending"]["start"] > UNIT_CAPS[unit]:
                raise ValueError("WF 2022 unit cap exceeded")
            expected = {"actor_updates": 0 if unit == 0 else 8,
                        "critic_updates": 0 if unit == 0 else 16}
            if resources is not None and any(resources.get(k) != v for k, v in expected.items()):
                raise ValueError("WF 2022 optimizer delta mismatch")
            self.finish(now, resources=resources or expected, condition="C10",
                        checkpoint=str(point), checkpoint_sha256=digest(point / "state.pt"),
                        work_seconds=now - self.state["pending"]["start"],
                        work_ended=now, **(evidence or {}))
            if len(self.state["units"]) == 11:
                self.state["status"] = "completed"
                self.persist(now)
        except (OSError, TypeError, ValueError) as exc:
            if self.state["status"] == "running":
                self.fail(now, str(exc))
            raise


class WF2022Permit(WFCostPermit):
    """Exact worker lease for the approved 2022-only root and single roster row."""

    def _pending(self):
        require_campaign()
        state = json.loads((CAMPAIGN / "ledger.jsonl").read_text().splitlines()[-1])
        pending = state.get("pending") or {}
        if (state.get("state_hash") != state_hash(state)
                or state.get("status") != "running"
                or pending.get("token") != self.token
                or pending.get("supervisor_pid") != os.getppid()):
            raise PermissionError("No active WF 2022 supervisor lease")
        return state, pending

    def validate(self, settings, condition, run_id):
        state, pending = self._pending()
        if (type(settings) is not WFCostSettings
                or (run_id, condition, settings.seed) !=
                ("wf-2022", "C10", 498614892)
                or state.get("cursor") != 0
                or pending.get("run_id") != "wf-2022"):
            raise PermissionError("WF 2022 run identity mismatch")

    def validate_d(self, source, seed, run_id):
        from btc_risk_rl.agents.market_source import TrainingMarket

        state, _ = self._pending()
        identity = source.identity()
        recorded = json.loads((CAMPAIGN / "folds/wf-2022/manifest.json").read_text())
        if (type(source) is not TrainingMarket or seed != 498614892
                or run_id != "wf-2022" or identity.get("fold") != "2022"
                or identity.get("training_shard_manifest_sha256") != SHARD_MANIFEST_SHA256
                or len(source.route_ids) != EXPECTED_ROUTES
                or source.audit.get("fit_count") != EXPECTED_FIT_ROWS
                or recorded.get("source_identity") != identity
                or state["identity"]["source"] != identity
                or source.audit.get("normalizer_refitted")
                or source.audit.get("validation_observations_loaded")):
            raise PermissionError("WF 2022 source escaped accepted training fold")

    def validate_request(self, path, request):
        state, pending = self._pending()
        unit = pending.get("unit")
        work = CAMPAIGN / "wf-2022"
        previous = state["runs"].get("wf-2022", {}).get("checkpoint")
        if (type(unit) is not int or unit not in UNITS
                or Path(path).resolve() != (work / f"request-{unit}.json").resolve()
                or pending.get("request_sha256") != digest(path)
                or request.get("root") != str(work)
                or request.get("run_id") != "wf-2022"
                or request.get("fold") != "2022"
                or request.get("condition") != "C10"
                or request.get("unit") != unit
                or request.get("previous") != previous
                or request.get("token") != self.token
                or request.get("settings") != _expected_settings()
                or request.get("config") != str(CONFIG)
                or request.get("atomic_checkpoint") is not True):
            raise PermissionError("WF 2022 request does not match pending unit")


def inspect_inputs() -> dict:
    """Hash only the isolated H1 training shard and pinned control files."""
    opened = []
    hashes = {}
    for path in (PROPOSAL, AUTHORIZATION, CONFIG, TRAIN_SHARD / "manifest.json"):
        hashes[str(path)] = digest(path)
        opened.append(str(path))
    if hashes[str(TRAIN_SHARD / "manifest.json")] != SHARD_MANIFEST_SHA256:
        raise ValueError("WF 2022 training shard manifest changed")
    parent = json.loads((TRAIN_SHARD / "manifest.json").read_text())
    if (parent.get("status") != "accepted_for_p2r_training_only"
            or parent.get("train_end_exclusive_ms") != 1672531200000):
        raise ValueError("WF 2022 shard scope changed")
    for name, expected in parent["files"].items():
        path = TRAIN_SHARD / name
        if path.is_symlink() or digest(path) != expected:
            raise ValueError(f"WF 2022 shard product changed: {name}")
        opened.append(str(path))
        hashes[str(path)] = expected
    return dict(ok=True, opened=opened, sha256=hashes,
                accepted_training_end_exclusive_ms=1672531200000)


def inspect_preflight() -> dict:
    """Read-only host and budget snapshot, with no campaign creation."""
    import time

    from btc_risk_rl.pilots.budget import utc
    from btc_risk_rl.pilots.wf_cost import inspect_budget, inspect_host
    from btc_risk_rl.pilots.wf_cost_replacement_05_units import resource_ready

    host = inspect_host()
    blockers = []
    if not resource_ready(host):
        blockers.append("Power, battery, memory or disk guard failed")
    if host["linger"] != "yes" or host["user_manager"] != "running":
        blockers.append("systemd --user or Linger guard failed")
    try:
        inputs = inspect_inputs()
    except (OSError, KeyError, ValueError) as exc:
        inputs = dict(ok=False, error=str(exc), opened=[])
        blockers.append("Training input integrity: " + str(exc))
    try:
        budget = inspect_budget(campaign=CAMPAIGN)
    except (OSError, KeyError, ValueError) as exc:
        budget = dict(ok=False, error=str(exc))
        blockers.append("Shared budget: " + str(exc))
    else:
        if not budget["ok"] or budget["remaining_before_reserve"] < 120:
            blockers.append("Shared budget cannot admit Q0")
    if CAMPAIGN.is_symlink():
        blockers.append("WF 2022 campaign root is a symlink")
    elif CAMPAIGN.exists() and not (CAMPAIGN / "ledger.jsonl").is_file():
        blockers.append("WF 2022 root exists without ledger")
    try:
        require_campaign()
    except (OSError, KeyError, ValueError, PermissionError) as exc:
        blockers.append("WF 2022 approval: " + str(exc))
    return dict(status="blocked" if blockers else "ready", observed_utc=utc(time.time()),
                market_execution_enabled=MARKET_EXECUTION_ENABLED,
                blockers=blockers, host=host, inputs=inputs, budget=budget,
                code_sha256=code_sha256(), root_exists=CAMPAIGN.exists())
