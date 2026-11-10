"""Frozen training-only identities and closed gate for the OOS v1.2 campaign."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from btc_risk_rl.pilots.budget import CampaignLedger
from btc_risk_rl.pilots.p2_budget import P2Ledger, state_hash
from btc_risk_rl.pilots.protocol import ROOT, P0Settings

FREEZE = ROOT / "docs/protocols/OOS-v1-2-training-freeze-20261110.json"
FREEZE_SHA256 = "0651f396f3157eaa5abd6bb7faf7ec1c6463210d255fa2fbd8a932e2999870a0"
APPROVAL = ROOT / "docs/protocols/OOS-v1-2-training-approval-20261110.json"
MARKET_EXECUTION_ENABLED = False
REGISTRATION_SHA256 = None
PROFILES = ("wf-2021", "wf-2022", "main-2018-2022")
LA_PAZ = ZoneInfo("America/La_Paz")
LAUNCH_MEMORY_MIN_BYTES = 6_026_846_208
CAMPAIGNS = {
    profile: ROOT / "artifacts" / name
    for profile, name in json.loads(FREEZE.read_text())["campaign_roots"].items()
}


def digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def window_admissible(epoch: float) -> bool:
    local = datetime.fromtimestamp(epoch, LA_PAZ)
    return 1 <= local.hour < 9


def frozen_protocol() -> dict:
    """Reject edited protocol or inputs before a campaign can be authorized."""
    if digest(FREEZE) != FREEZE_SHA256:
        raise ValueError("OOS frozen protocol changed")
    data = json.loads(FREEZE.read_text())
    if (data.get("protocol_id") != "oos-v1.2-training-freeze-20261110"
            or data.get("status") != "training_authorized_evaluation_closed"):
        raise ValueError("OOS frozen training status changed")
    for name, expected in data["inputs_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"OOS frozen input changed: {name}")
    return data


def code_sha256() -> str:
    """Pin executable code while allowing only the two approval declarations to change."""
    files = sorted((ROOT / "src/btc_risk_rl").rglob("*.py")) + [
        ROOT / "scripts/run_oos_v12_training.py",
        ROOT / "scripts/launch_oos_v12_training_once.py",
        ROOT / "scripts/audit_oos_v12_training_preflight.py",
        ROOT / "scripts/launch_oos_v12_nightly.py",
        ROOT / "scripts/write_oos_v12_report.py",
        ROOT / "ops/systemd/oos-v12-training.service",
        ROOT / "ops/systemd/oos-v12-training.timer",
        ROOT / "pyproject.toml", ROOT / "uv.lock",
    ]
    mapping = {}
    for path in files:
        raw = path.read_bytes()
        if path.name == "oos_v12_training.py":
            lines = raw.splitlines(keepends=True)
            matched = [i for i, line in enumerate(lines) if line.startswith(
                (b"MARKET_EXECUTION_ENABLED = ", b"REGISTRATION_SHA256 = "))]
            if len(matched) != 2:
                raise ValueError("OOS approval declarations changed")
            for index in matched:
                name = lines[index].split(b" = ", 1)[0]
                lines[index] = name + b" = <pinned approval>\n"
            raw = b"".join(lines)
        mapping[str(path.relative_to(ROOT))] = hashlib.sha256(raw).hexdigest()
    return hashlib.sha256(json.dumps(mapping, sort_keys=True).encode()).hexdigest()


def roster(profile: str) -> tuple[tuple[int, str, int], ...]:
    if profile not in PROFILES:
        raise ValueError("Unknown OOS training profile")
    rows = tuple((r["seed"], r["condition"], r["beta"])
                 for r in frozen_protocol()["roster"] if r["source"] == profile)
    expected = 108 if profile == "main-2018-2022" else 9
    if (len(rows) != expected or len(set(rows)) != expected
            or any(condition not in {"C0", "C5", "C10"} or beta != 0
                   for _, condition, beta in rows)):
        raise ValueError("OOS roster invalid")
    return rows


def run_id_for(profile: str, index: int, row: tuple[int, str, int]) -> str:
    rows = roster(profile)
    if type(index) is not int or not 0 <= index < len(rows) or row != rows[index]:
        raise ValueError("OOS run identity disagrees with frozen order")
    return f"run-{index:02d}-{row[1]}-b0"


@dataclass(frozen=True)
class OOSSettings(P0Settings):
    purpose: str = "oos_v12_train_only"
    seed: int = 1869792951
    iterations: int = 10
    critic_epochs: int = 4
    critic_beta: int = 0

    def __post_init__(self):
        candidate = json.loads((ROOT / "docs/protocols/P2-infrastructure-v1.json").read_text())[
            "training_candidate"
        ]
        expected = dict(
            purpose="oos_v12_train_only", hidden=candidate["hidden"],
            iterations=10, n_a=candidate["n_a"], n_q=candidate["n_q"],
            n_b=candidate["n_b"], actor_epochs=candidate["actor_epochs"],
            critic_epochs=4, minibatch=candidate["minibatch_trajectories"],
            actor_lr=candidate["actor_lr"], critic_lr=candidate["critic_lr"],
            dual_lr=candidate["dual_lr"], clip=candidate["clip"],
            bound=frozen_protocol()["design"]["risk_bound"], seed=self.seed,
            fragment_steps=candidate["fragment_steps"], critic_beta=0,
        )
        allowed = {seed for profile in PROFILES for seed, _, _ in roster(profile)}
        if asdict(self) != expected or self.seed not in allowed:
            raise ValueError("OOS settings differ from frozen design")


def require_campaign() -> dict:
    """Reject any public/worker entry before reading a request or market source."""
    if not MARKET_EXECUTION_ENABLED or REGISTRATION_SHA256 is None:
        raise PermissionError("OOS market campaign NOT AUTHORIZED")
    if not APPROVAL.is_file() or digest(APPROVAL) != REGISTRATION_SHA256:
        raise PermissionError("OOS market approval hash mismatch")
    approval = json.loads(APPROVAL.read_text())
    if (approval.get("active") is not True
            or approval.get("scope") != "accepted_training_only"
            or approval.get("freeze_sha256") != FREEZE_SHA256
            or approval.get("campaign_roots") != frozen_protocol()["campaign_roots"]
            or approval.get("inputs_sha256") != frozen_protocol()["inputs_sha256"]
            or approval.get("code_sha256") != code_sha256()
            or approval.get("not_after_day_la_paz") != "2026-11-16"
            or datetime.now(LA_PAZ).date().isoformat() > "2026-11-16"):
        raise PermissionError("OOS market approval identity mismatch")
    return approval


def read_host() -> dict:
    from btc_risk_rl.pilots.wf_cost import inspect_host

    return inspect_host()


def read_budget(profile: str, *, now=None, active_prep_token=None) -> dict:
    from btc_risk_rl.pilots.wf_cost import inspect_budget

    if profile not in PROFILES:
        raise ValueError("Unknown OOS training profile")
    # Admission before the ledger opens must count the current campaign too.
    # The unit supervisor separately excludes it when computing external debit.
    return inspect_budget(now=now,
                          campaign=ROOT / "artifacts/__oos_v12_budget_probe__",
                          active_oos_prep_token=active_prep_token)


def inspect_preflight(profile: str, *, active_prep_token=None) -> dict:
    """Inspect one accepted training source and host without collecting a route."""
    require_campaign()
    frozen_protocol()
    source = source_for(profile)
    identity = source.identity()
    expected = 7048 if profile == "main-2018-2022" else (
        3639 if profile == "wf-2021" else 4678
    )
    host = read_host()
    budget = read_budget(profile, active_prep_token=active_prep_token)
    blockers = []
    if (len(source.route_ids) != expected
            or identity.get("profile") != "accepted_train_collection_only"
            or source.audit.get("validation_observations_loaded")
            or source.audit.get("normalizer_refitted")):
        blockers.append("accepted training identity or route count changed")
    if host["power"].get("ac") is not True or host["power"].get("battery_percent", -1) < 50:
        blockers.append("power or battery below requirement")
    if (host.get("memory_available_bytes") is None
            or host["memory_available_bytes"] < LAUNCH_MEMORY_MIN_BYTES):
        blockers.append("launch memory below 6,026,846,208 bytes")
    if host.get("disk_free_bytes", 0) < 20 * 1024**3:
        blockers.append("disk below 20 GiB")
    if host.get("user_manager") != "running" or host.get("linger") != "yes":
        blockers.append("systemd user manager or Linger unavailable")
    if not budget["ok"] or budget["remaining_before_reserve"] < 1800:
        blockers.append("shared budget insufficient for Q0 cap and closing reserve")
    if not window_admissible(__import__("time").time()):
        blockers.append("outside 01:00–09:00 La Paz window")
    return dict(status="blocked" if blockers else "ready", blockers=blockers,
                profile=profile, source_identity=identity, route_count=len(source.route_ids),
                host=host, budget=budget, trajectories_generated=0, optimizer_steps=0)


def watch_open(event, args, opened, *, root=ROOT, training_shard=None):
    """Audit Python file opens and fail closed on any non-shard market file."""
    if event != "open" or not args or not isinstance(args[0], (str, bytes)):
        return
    root = Path(root).resolve()
    training_shard = (Path(training_shard) if training_shard is not None else
                      root / "data/processed/p2r-training-h1").resolve()
    raw = args[0]
    path = Path(raw.decode() if isinstance(raw, bytes) else raw)
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    if path.is_relative_to(root):
        relative = path.relative_to(root)
        if relative.parts[0] not in {".venv", "src"}:
            opened.append(str(relative))
        shared_manifest = (root / "data/processed/segmented-B-h1/manifest.json").resolve()
        if (path.is_relative_to(root / "data") and not path.is_relative_to(training_shard)
                and path != shared_manifest):
            raise PermissionError(f"OOS protected or shared market file opened: {path}")


class OOSPermit:
    """Exact worker lease for one frozen source profile and pending unit."""

    def __init__(self, token: str, profile: str):
        if profile not in PROFILES:
            raise ValueError("Unknown OOS training profile")
        self.token, self.profile = token, profile
        self.settings = self.condition = self.run_id = None

    def _pending(self):
        require_campaign()
        path = CAMPAIGNS[self.profile] / "ledger.jsonl"
        state = json.loads(path.read_text().splitlines()[-1])
        index = state.get("cursor")
        if (state.get("state_hash") != state_hash(state)
                or state.get("status") != "running"
                or type(index) is not int or not 0 <= index < len(roster(self.profile))):
            raise PermissionError("No active OOS supervisor lease")
        return state, index, state.get("pending") or {}

    def validate(self, settings, condition, run_id):
        if type(settings) is not OOSSettings:
            raise PermissionError("OOS settings required")
        state, index, pending = self._pending()
        row = roster(self.profile)[index]
        if (pending.get("token") != self.token
                or pending.get("supervisor_pid") != os.getppid()
                or pending.get("run_id") != run_id
                or row != (settings.seed, condition, settings.critic_beta)
                or run_id != run_id_for(self.profile, index, row)):
            raise PermissionError("No active OOS supervisor lease")
        self.settings, self.condition, self.run_id = settings, condition, run_id
        return state

    def validate_request(self, request_path, request):
        state, index, pending = self._pending()
        row = roster(self.profile)[index]
        run_id = run_id_for(self.profile, index, row)
        root = CAMPAIGNS[self.profile] / run_id
        unit = pending.get("unit")
        previous = state["runs"].get(run_id, {}).get("checkpoint")
        if (pending.get("token") != self.token
                or pending.get("supervisor_pid") != os.getppid()
                or pending.get("run_id") != run_id
                or type(unit) is not int or not 0 <= unit <= 10
                or Path(request_path).resolve() != (root / f"request-{unit}.json").resolve()
                or pending.get("request_sha256") != digest(request_path)
                or request.get("root") != str(root)
                or request.get("run_id") != run_id
                or request.get("condition") != row[1]
                or type(request.get("beta")) is not int or request["beta"] != 0
                or request.get("settings") != asdict(OOSSettings(seed=row[0]))
                or request.get("unit") != unit
                or request.get("previous") != previous
                or request.get("token") != self.token
                or request.get("atomic_checkpoint") is not True
                or request.get("config") != str(ROOT / "configs/initial.toml")):
            raise PermissionError("OOS worker request differs from pending unit")

    def validate_d(self, source, seed, run_id):
        from btc_risk_rl.agents.market_source import TrainingMarket

        if type(source) is not TrainingMarket or seed != getattr(self.settings, "seed", None):
            raise PermissionError("OOS diagnostic source/seed mismatch")
        state = self.validate(self.settings, self.condition, run_id)
        identity = source.identity()
        expected_routes = 7048 if self.profile == "main-2018-2022" else (
            3639 if self.profile == "wf-2021" else 4678
        )
        expected_fold = self.profile.removeprefix("wf-") if self.profile.startswith("wf-") else None
        if (run_id != self.run_id or len(source.route_ids) != expected_routes
                or identity.get("profile") != "accepted_train_collection_only"
                or identity.get("manifest_sha256") !=
                frozen_protocol()["inputs_sha256"]["docs/evidence/segmented-h1/manifest.json"]
                or identity.get("training_shard_manifest_sha256") !=
                frozen_protocol()["inputs_sha256"]["data/processed/p2r-training-h1/manifest.json"]
                or identity.get("fold") != expected_fold
                or state["identity"]["code"]["data"] != identity):
            raise PermissionError("OOS diagnostic source identity mismatch")
        if source.audit.get("validation_observations_loaded") or source.audit.get(
                "normalizer_refitted"):
            raise PermissionError("OOS diagnostic source escaped accepted training")


class OOSLedger(P2Ledger):
    """Chained 20-day ledger with the 2,700 s daily closing reservation."""

    iterations = 10
    preserve_completed = True

    def __init__(self, root, *, now, identity, external_seconds=0):
        if not window_admissible(now):
            raise ValueError("OOS outside 01:00-09:00 La Paz window")
        self.previous_hash = None
        path = Path(root) / "ledger.jsonl"
        if path.exists():
            for line in path.read_text().splitlines():
                state = json.loads(line)
                if (state.get("previous_hash") != self.previous_hash
                        or state.get("state_hash") != state_hash(state)):
                    raise ValueError("OOS ledger hash chain corrupt")
                self.previous_hash = state["state_hash"]
        self.session_id = __import__("uuid").uuid4().hex
        CampaignLedger.__init__(self, root, now=now,
                                identity={"profile": "oos_v12_train_only", **identity},
                                external_seconds=external_seconds)
        if self.state["status"] == "completed":
            return
        if len(self.state["days"]) > 20:
            self.state["status"] = "incomplete"
            self.persist(now)
            self.lock.close()
            raise ValueError("OOS twenty active days exhausted")
        from btc_risk_rl.pilots.oos_v12_budget import inspect_oos_debit

        if len(inspect_oos_debit(Path(root).parent, now=now)["active_days"]) > 20:
            self.state["status"] = "incomplete"
            self.persist(now)
            self.lock.close()
            raise ValueError("OOS shared twenty active days exhausted")
        day = datetime.fromtimestamp(now, LA_PAZ).date()
        nine = datetime.combine(day, time(9), LA_PAZ).timestamp()
        self.day["hard_deadline"] = min(self.day["hard_deadline"], nine)
        self.day["work_deadline"] = min(self.day["work_deadline"],
                                        self.day["hard_deadline"] - 2700)
        self.persist(now)

    def begin(self, run_id, kind, now):
        if self.state["status"] != "ready":
            raise ValueError("Campaign not ready")
        run = self.state["runs"].setdefault(run_id, {"days": [], "resources": {}})
        sessions = run.setdefault("sessions", [])
        if self.day_key not in run["days"]:
            if len(run["days"]) >= 3:
                self.state["status"] = "incomplete"
                self.persist(now)
                raise ValueError("OOS per-run active-day limit exhausted")
            run["days"].append(self.day_key)
        if self.session_id not in sessions:
            if len(sessions) >= 3:
                self.state["status"] = "incomplete"
                self.persist(now)
                raise ValueError("OOS per-run session limit exhausted")
            sessions.append(self.session_id)
        self.state.update(status="running", pending=dict(run_id=run_id, kind=kind, start=now))
        self.persist(now)


def source_for(profile: str):
    """Load only an H1 training prefix, with a separate scaler for each fold."""
    if profile not in PROFILES:
        raise ValueError("Unknown OOS training profile")
    if profile.startswith("wf-"):
        from btc_risk_rl.pilots.wf_cost_source import build_fold_source

        return build_fold_source(profile.removeprefix("wf-"))
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.config import load_config

    frozen = frozen_protocol()
    return TrainingMarket(
        load_config(ROOT / "configs/initial.toml"),
        ROOT / "data/processed/segmented-B-h1",
        expected_manifest=frozen["inputs_sha256"]["docs/evidence/segmented-h1/manifest.json"],
        training_shard=ROOT / "data/processed/p2r-training-h1",
        expected_shard_manifest=frozen["inputs_sha256"][
            "data/processed/p2r-training-h1/manifest.json"
        ],
    )


def run_historical_units(profile: str):
    """Execute only a registered training campaign under systemd supervision."""
    require_campaign()  # Before a source read, request read, or artifact root creation.
    if profile not in PROFILES:
        raise ValueError("Unknown OOS training profile")
    from btc_risk_rl.agents.checkpoint import provenance
    from btc_risk_rl.pilots.oos_v12_launch import require_recent_prepare
    from btc_risk_rl.pilots.p2r import check_service_context
    from btc_risk_rl.pilots.p2r_units import _run_units

    require_recent_prepare(profile)
    check_service_context(require_linger=True)
    source = source_for(profile)
    rows = roster(profile)
    first = OOSSettings(seed=rows[0][0])
    preflight_identity = provenance(source)
    if (preflight_identity["data"]["profile"] != "accepted_train_collection_only"
            or source.audit.get("validation_observations_loaded")
            or source.audit.get("normalizer_refitted")):
        raise PermissionError("OOS source escaped accepted training")
    return _run_units(
        CAMPAIGNS[profile], ROOT / "configs/initial.toml", first,
        roster=rows, source=source,
        settings_for=lambda seed, _condition, _beta: OOSSettings(seed=seed),
        command_for=lambda request: [sys.executable, "-m",
                                     "btc_risk_rl.pilots.oos_v12_worker", profile,
                                     str(request)],
        profile="oos_v12_market_units", diagnostic_n=64,
        require_service=True, require_linger=True, ledger_type=OOSLedger,
        protocol_identity={"freeze_sha256": FREEZE_SHA256,
                           "source_identity": source.identity()},
    )
