"""Read-only validation of a proposed fresh WF cost study; no execution path."""

import hashlib
import json
from pathlib import Path

from btc_risk_rl.pilots.protocol import ROOT

BASE_DESIGN_SHA256 = "66109d4400e04440c9450d1f1c0c7cc4332b66b9079703e3a1e62596032b5ad0"
BASE_PROTOCOL_SHA256 = "f6d81fd9f10938aee29480c701a1a52c0b84eba1db0ea42a21d2d84c3004cbe4"
TRAIN_MANIFEST_SHA256 = "62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9"
SPEC = ROOT / "docs/protocols/OOS-v1-2-wf-cost-replacement-proposal-v1.json"
BASE_PROTOCOL = ROOT / "docs/proposals/OOS-v1-2-costo-entrenamiento-cortes-v1.md"
TRAIN_MANIFEST = ROOT / "data/processed/p2r-training-h1/manifest.json"
FROZEN_EVIDENCE = ROOT / "docs/evidence/oos-v1-2-wf-cost-reentry/frozen-artifacts.json"


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_replacement_spec(spec, original, *, original_sha256):
    """Only root and approval change; every algorithm/budget field inherits v1."""
    expected_keys = {
        "schema_version", "status", "base_design", "base_design_sha256",
        "base_protocol_sha256", "training_shard_manifest_sha256",
        "replacement_root", "approval_record", "market_execution_authorized",
        "reuse_partial_artifacts", "require_new_session_journal",
        "require_q0_pause", "require_roster_canonicalization",
    }
    if set(spec) != expected_keys:
        raise ValueError("WF replacement spec has changed fields")
    if (spec["schema_version"] != 1
            or spec["status"] != "proposal_not_authorized"
            or spec["base_design"] != "docs/protocols/OOS-v1-2-wf-cost-executor-v1.json"
            or spec["base_design_sha256"] != original_sha256
            or spec["base_design_sha256"] != BASE_DESIGN_SHA256
            or spec["base_protocol_sha256"] != BASE_PROTOCOL_SHA256
            or spec["training_shard_manifest_sha256"] != TRAIN_MANIFEST_SHA256
            or spec["replacement_root"] != "artifacts/oos-v12-wf-cost-only-02"
            or spec["replacement_root"] == original["campaign_root_reserved_not_created"]
            or spec["approval_record"] !=
            "docs/protocols/OOS-v1-2-wf-cost-replacement-approval.json"
            or spec["market_execution_authorized"] is not False
            or spec["reuse_partial_artifacts"] is not False
            or spec["require_new_session_journal"] is not True
            or spec["require_q0_pause"] is not True
            or spec["require_roster_canonicalization"] is not True):
        raise ValueError("WF replacement spec is not an isolated proposal")


def inspect_candidate(root=ROOT):
    """Check proposal and pinned inputs without opening market rows or writing."""
    root = Path(root)
    spec_path = root / SPEC.relative_to(ROOT)
    spec = json.loads(spec_path.read_text())
    base_path = root / spec["base_design"]
    original = json.loads(base_path.read_text())
    design_sha = _sha(base_path)
    validate_replacement_spec(spec, original, original_sha256=design_sha)
    opened = [spec_path, base_path]
    for path, expected in ((root / BASE_PROTOCOL.relative_to(ROOT), BASE_PROTOCOL_SHA256),
                           (root / TRAIN_MANIFEST.relative_to(ROOT), TRAIN_MANIFEST_SHA256)):
        if _sha(path) != expected:
            raise ValueError(f"WF replacement pinned input changed: {path.name}")
        opened.append(path)
    frozen_path = root / FROZEN_EVIDENCE.relative_to(ROOT)
    frozen = json.loads(frozen_path.read_text())
    opened.append(frozen_path)
    if (frozen.get("status") != "frozen_historical_study_verified"
            or frozen.get("market_execution_enabled") is not False
            or frozen.get("ledger_status") != "ready"
            or frozen.get("units") != 1):
        raise ValueError("Historical WF evidence status changed")
    for relative, expected in frozen["sha256"].items():
        path = root / relative
        if _sha(path) != expected:
            raise ValueError(f"Historical WF artifact changed: {relative}")
        opened.append(path)
    proposed_root = root / spec["replacement_root"]
    approval = root / spec["approval_record"]
    from btc_risk_rl.pilots.wf_cost import MARKET_EXECUTION_ENABLED

    if MARKET_EXECUTION_ENABLED:
        raise ValueError("Historical WF execution gate unexpectedly enabled")
    blockers = ["proposal_not_authorized"]
    if proposed_root.exists():
        blockers.append("replacement_root_already_exists")
    if approval.exists():
        blockers.append("replacement_approval_path_already_exists")
    return dict(status="blocked", blockers=blockers,
                replacement_root=str(proposed_root), approval_record=str(approval),
                root_absent=not proposed_root.exists(), approval_absent=not approval.exists(),
                market_execution_enabled=False,
                historical_artifacts_verified=True,
                opened=[str(path) for path in opened],
                sha256={str(path): _sha(path) for path in opened})
