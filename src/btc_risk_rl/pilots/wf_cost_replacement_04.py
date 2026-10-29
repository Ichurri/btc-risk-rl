"""Read-only identity and immutable-prior audit for the fourth WF cost profile."""

import hashlib
import json
from pathlib import Path

from btc_risk_rl.pilots.protocol import ROOT
from btc_risk_rl.pilots.wf_cost_replacement import (
    BASE_DESIGN_SHA256,
    BASE_PROTOCOL,
    BASE_PROTOCOL_SHA256,
    TRAIN_MANIFEST,
    TRAIN_MANIFEST_SHA256,
)
from btc_risk_rl.pilots.wf_cost_replacement_03 import inspect_candidate as inspect_03

SPEC = ROOT / "docs/protocols/OOS-v1-2-wf-cost-04-profile-v1.json"
PRIOR_MANIFEST_SHA256 = "4c722aa3308cef493132d7d157cbc38d8f52f8f270ae07b84a3cfa1f1e313830"
PRIOR_03_AUDIT_SHA256 = "811241db23de6ade4d7bd8d012279e23de71bca5f8782e61e67a5150a6a455c2"
APPROVAL_02_SHA256 = "c0d6973d98951dabe1cbc0cfef2f79304c2662cba01e09ff58276547c453f242"
APPROVAL_03_SHA256 = "6f877eaf18663f0427ef9f5ad9e412eeec6da761d7355bbc110563e784c6c4b4"


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_spec(spec, original, *, original_sha256):
    """Require the prior science and a fresh, disabled root/approval pair."""
    expected = {
        "schema_version", "status", "base_design", "base_design_sha256",
        "base_protocol_sha256", "training_shard_manifest_sha256",
        "prior_roots_manifest", "prior_roots_manifest_sha256",
        "prior_03_audit", "prior_03_audit_sha256",
        "failed_02_approval_sha256", "failed_03_approval_sha256",
        "campaign_root", "approval_record", "market_execution_authorized",
        "reuse_prior_artifacts", "require_new_session_journal", "require_q0_pause",
        "require_roster_canonicalization",
    }
    if (set(spec) != expected or spec["schema_version"] != 1
            or spec["status"] != "infrastructure_only_not_authorized"
            or spec["base_design"] != "docs/protocols/OOS-v1-2-wf-cost-executor-v1.json"
            or spec["base_design_sha256"] != original_sha256
            or original_sha256 != BASE_DESIGN_SHA256
            or spec["base_protocol_sha256"] != BASE_PROTOCOL_SHA256
            or spec["training_shard_manifest_sha256"] != TRAIN_MANIFEST_SHA256
            or spec["prior_roots_manifest"] !=
            "docs/evidence/oos-v1-2-wf-first-start-fix/hashes-before.json"
            or spec["prior_roots_manifest_sha256"] != PRIOR_MANIFEST_SHA256
            or spec["prior_03_audit"] !=
            "docs/evidence/oos-v1-2-wf-cost-03-campaign/audit-failure.json"
            or spec["prior_03_audit_sha256"] != PRIOR_03_AUDIT_SHA256
            or spec["failed_02_approval_sha256"] != APPROVAL_02_SHA256
            or spec["failed_03_approval_sha256"] != APPROVAL_03_SHA256
            or spec["campaign_root"] != "artifacts/oos-v12-wf-cost-only-04"
            or spec["campaign_root"] == original["campaign_root_reserved_not_created"]
            or spec["approval_record"] !=
            "docs/protocols/OOS-v1-2-wf-cost-04-approval.json"
            or spec["market_execution_authorized"] is not False
            or spec["reuse_prior_artifacts"] is not False
            or spec["require_new_session_journal"] is not True
            or spec["require_q0_pause"] is not True
            or spec["require_roster_canonicalization"] is not True):
        raise ValueError("WF cost 04 profile changed its frozen scope")


def inspect_candidate(root=ROOT):
    """Audit all three prior roots without opening market rows or writing."""
    root = Path(root)
    prior_03 = inspect_03(root)
    if not prior_03["historical_artifacts_verified"]:
        raise ValueError("WF cost prior roots changed")
    spec_path = root / SPEC.relative_to(ROOT)
    spec = json.loads(spec_path.read_text())
    base = root / spec["base_design"]
    original = json.loads(base.read_text())
    validate_spec(spec, original, original_sha256=_sha(base))
    opened = [root / path for path in prior_03["opened"]]
    opened.extend([spec_path, base])
    for path, expected in ((root / BASE_PROTOCOL.relative_to(ROOT), BASE_PROTOCOL_SHA256),
                           (root / TRAIN_MANIFEST.relative_to(ROOT), TRAIN_MANIFEST_SHA256),
                           (root / spec["prior_roots_manifest"], PRIOR_MANIFEST_SHA256)):
        if _sha(path) != expected:
            raise ValueError(f"WF cost 04 pinned input changed: {path.name}")
        opened.append(path)
    audit_path = root / spec["prior_03_audit"]
    if _sha(audit_path) != PRIOR_03_AUDIT_SHA256:
        raise ValueError("WF cost 03 audit changed")
    opened.append(audit_path)
    audit = json.loads(audit_path.read_text())
    third = root / "artifacts/oos-v12-wf-cost-only-03"
    current = {str(path.relative_to(third)): _sha(path)
               for path in sorted(third.rglob("*")) if path.is_file()}
    if current != audit["root_files_sha256"]:
        raise ValueError("WF cost historical root changed: 03")
    opened.extend(third / relative for relative in current)
    approval_03 = root / "docs/protocols/OOS-v1-2-wf-cost-03-approval.json"
    if _sha(approval_03) != APPROVAL_03_SHA256:
        raise ValueError("WF cost 03 historical approval changed")
    opened.append(approval_03)
    ledger = json.loads((third / "ledger.jsonl").read_text().splitlines()[-1])
    if (ledger.get("status") != "failed" or ledger.get("units") != []
            or ledger.get("pending", {}).get("unit") != 0):
        raise ValueError("WF cost 03 failed ledger changed")
    from btc_risk_rl.pilots import wf_cost_replacement_03_exec

    if wf_cost_replacement_03_exec.MARKET_EXECUTION_ENABLED:
        raise ValueError("WF cost 03 gate unexpectedly enabled")
    campaign = root / spec["campaign_root"]
    approval = root / spec["approval_record"]
    blockers = ["no active approval"]
    if campaign.exists():
        blockers.append("new campaign root already exists")
    if approval.exists():
        blockers.append("new approval record already exists")
    opened = sorted(set(opened))
    return dict(status="blocked", blockers=blockers,
                replacement_root=str(campaign), approval_record=str(approval),
                root_absent=not campaign.exists(), approval_absent=not approval.exists(),
                historical_artifacts_verified=True,
                failed_02_session_accounted=prior_03["failed_02_session_accounted"],
                failed_03_pending=True,
                opened=[str(path) for path in opened],
                sha256={str(path): _sha(path) for path in opened})
