"""Independent, disabled execution profile for the fresh WF cost study."""

import hashlib
import json
import os
import time
from dataclasses import asdict
from pathlib import Path

from btc_risk_rl.pilots.protocol import ROOT
from btc_risk_rl.pilots.wf_cost import (
    CONFIG,
    DESIGN,
    EXPECTED,
    PROTOCOL,
    SHARD_MANIFEST_SHA256,
    TRAIN_SHARD,
    WFCostLedger,
    WFCostSessionJournal,
    WFCostSettings,
    admit,
    digest,
    guard_fold_path,
    inspect_host,
    roster,
    unit_cap,
    units,
)
from btc_risk_rl.pilots.wf_cost import (
    WFCostPermit as _OriginalPermit,
)
from btc_risk_rl.pilots.wf_cost import (
    inspect_budget as _inspect_budget,
)
from btc_risk_rl.pilots.wf_cost import (
    inspect_inputs as _inspect_inputs,
)
from btc_risk_rl.pilots.wf_cost_replacement import SPEC, inspect_candidate

CAMPAIGN = ROOT / "artifacts/oos-v12-wf-cost-only-02"
REGISTRATION = ROOT / "docs/protocols/OOS-v1-2-wf-cost-replacement-approval.json"
# A later campaign authorization must set both values in a separate reviewed commit.
MARKET_EXECUTION_ENABLED = False
REGISTRATION_SHA256 = None


def code_sha256():
    """Pin executable Python and dependency lock without opening market data."""
    files = sorted((ROOT / "src/btc_risk_rl").rglob("*.py")) + [
        ROOT / "scripts/run_oos_wf_cost_replacement.py",
        ROOT / "scripts/audit_oos_wf_cost_replacement_preflight.py",
        ROOT / "pyproject.toml", ROOT / "uv.lock",
    ]
    mapping = {str(path.relative_to(ROOT)): digest(path) for path in files}
    return hashlib.sha256(json.dumps(mapping, sort_keys=True).encode()).hexdigest()


def require_campaign():
    """Reject before requests, market input, root creation or session writes."""
    if not MARKET_EXECUTION_ENABLED or REGISTRATION_SHA256 is None:
        raise PermissionError("WF replacement market study NOT AUTHORIZED")
    if digest(REGISTRATION) != REGISTRATION_SHA256:
        raise PermissionError("WF replacement registration hash mismatch")
    entry = json.loads(REGISTRATION.read_text())
    if (entry.get("active") is not True
            or entry.get("scope") != "cost_measurement_training_folds_only"
            or entry.get("campaign") != CAMPAIGN.name
            or entry.get("protocol_sha256") != digest(PROTOCOL)
            or entry.get("design_sha256") != digest(DESIGN)
            or entry.get("replacement_spec_sha256") != digest(SPEC)
            or entry.get("code_sha256") != code_sha256()
            or entry.get("training_shard_manifest_sha256") != SHARD_MANIFEST_SHA256):
        raise PermissionError("WF replacement registration inconsistent")
    return entry


def inspect_inputs():
    """Open training-exclusive products and pinned metadata only."""
    result = _inspect_inputs(campaign=CAMPAIGN)
    spec = inspect_candidate()
    if not spec["historical_artifacts_verified"]:
        raise ValueError("Historical study evidence changed")
    result["opened"].extend(spec["opened"])
    result["sha256"].update(spec["sha256"])
    return result


def inspect_budget(*, now=None):
    return _inspect_budget(now=now, campaign=CAMPAIGN)


def inspect_preflight():
    """Read-only snapshot; the absent replacement permission is a blocker."""
    from btc_risk_rl.pilots.budget import utc
    from btc_risk_rl.pilots.wf_cost_units import resource_ready

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
        budget = inspect_budget()
    except (OSError, KeyError, ValueError) as exc:
        budget = dict(ok=False, error=str(exc))
        blockers.append("Shared budget: " + str(exc))
    else:
        if not budget["ok"] or budget["remaining_before_reserve"] < 120:
            blockers.append("Shared budget cannot admit Q0")
    if CAMPAIGN.exists() and not (CAMPAIGN / "ledger.jsonl").is_file():
        blockers.append("Replacement root exists without a campaign ledger")
    if not MARKET_EXECUTION_ENABLED or REGISTRATION_SHA256 is None:
        blockers.append("WF replacement campaign has no active approval")
    else:
        try:
            require_campaign()
        except (OSError, KeyError, ValueError, PermissionError) as exc:
            blockers.append("WF replacement approval invalid: " + str(exc))
    return dict(status="blocked" if blockers else "ready", observed_utc=utc(time.time()),
                market_execution_enabled=MARKET_EXECUTION_ENABLED,
                blockers=blockers, host=host, inputs=inputs, budget=budget,
                code_sha256=code_sha256(),
                root_exists=CAMPAIGN.exists())


class WFCostPermit(_OriginalPermit):
    """Replacement worker lease bound to the new root and its own approval."""

    def _pending(self):
        from btc_risk_rl.pilots.p2_budget import state_hash

        require_campaign()
        state = json.loads((CAMPAIGN / "ledger.jsonl").read_text().splitlines()[-1])
        pending = state.get("pending") or {}
        if (state.get("state_hash") != state_hash(state)
                or state.get("status") != "running"
                or pending.get("token") != self.token
                or pending.get("supervisor_pid") != os.getppid()):
            raise PermissionError("No active WF replacement supervisor lease")
        return state, pending

    def validate_d(self, source, seed, run_id):
        from btc_risk_rl.agents.market_source import TrainingMarket

        state, _ = self._pending()
        fold, expected_seed, _ = roster()[state["cursor"]]
        identity = source.identity()
        recorded = json.loads((CAMPAIGN / "folds" / f"wf-{fold}" / "manifest.json").read_text())
        if (type(source) is not TrainingMarket or seed != expected_seed
                or run_id != f"wf-{fold}" or identity.get("fold") != fold
                or identity.get("training_shard_manifest_sha256") != SHARD_MANIFEST_SHA256
                or len(source.route_ids) != EXPECTED[fold][0]
                or recorded.get("source_identity") != identity
                or state["identity"]["source"].get(fold) != identity
                or source.audit["normalizer_refitted"]
                or source.audit["validation_observations_loaded"]):
            raise PermissionError("WF replacement D escaped accepted fold")

    def validate_request(self, path, request):
        state, pending = self._pending()
        fold, seed, condition = roster()[state["cursor"]]
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
            raise PermissionError("WF replacement request does not match pending unit")


def run_historical_units():
    require_campaign()
    from btc_risk_rl.pilots.wf_cost_replacement_units import run_units

    return run_units()


__all__ = ["CAMPAIGN", "CONFIG", "DESIGN", "PROTOCOL", "REGISTRATION",
           "MARKET_EXECUTION_ENABLED", "REGISTRATION_SHA256", "WFCostLedger",
           "WFCostSessionJournal", "WFCostSettings", "WFCostPermit", "digest",
           "roster", "units", "unit_cap", "admit", "guard_fold_path", "inspect_budget",
           "inspect_host", "inspect_inputs", "inspect_preflight", "require_campaign",
           "run_historical_units", "TRAIN_SHARD", "code_sha256"]
