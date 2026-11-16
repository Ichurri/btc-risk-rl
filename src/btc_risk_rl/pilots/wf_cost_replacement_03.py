"""Read-only identity and immutable-prior audit for a third WF cost profile."""

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
from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal

SPEC = ROOT / "docs/protocols/OOS-v1-2-wf-cost-03-profile-v1.json"
APPROVAL_02 = ROOT / "docs/protocols/OOS-v1-2-wf-cost-replacement-approval.json"
PRIOR_MANIFEST_SHA256 = "4c722aa3308cef493132d7d157cbc38d8f52f8f270ae07b84a3cfa1f1e313830"
APPROVAL_02_SHA256 = "c0d6973d98951dabe1cbc0cfef2f79304c2662cba01e09ff58276547c453f242"


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_spec(spec, original, *, original_sha256):
    """Only the new root and approval differ from the pinned scientific design."""
    expected = {
        "schema_version", "status", "base_design", "base_design_sha256",
        "base_protocol_sha256", "training_shard_manifest_sha256",
        "prior_roots_manifest", "prior_roots_manifest_sha256",
        "failed_02_approval_sha256", "campaign_root", "approval_record",
        "market_execution_authorized", "reuse_prior_artifacts",
        "require_new_session_journal", "require_q0_pause",
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
            or spec["failed_02_approval_sha256"] != APPROVAL_02_SHA256
            or spec["campaign_root"] != "artifacts/oos-v12-wf-cost-only-03"
            or spec["campaign_root"] == original["campaign_root_reserved_not_created"]
            or spec["approval_record"] !=
            "docs/protocols/OOS-v1-2-wf-cost-03-approval.json"
            or spec["market_execution_authorized"] is not False
            or spec["reuse_prior_artifacts"] is not False
            or spec["require_new_session_journal"] is not True
            or spec["require_q0_pause"] is not True
            or spec["require_roster_canonicalization"] is not True):
        raise ValueError("WF cost 03 profile changed its frozen scope")


def inspect_candidate(root=ROOT):
    """Verify prior roots and pinned metadata without writing or opening market rows."""
    root = Path(root)
    spec_path = root / SPEC.relative_to(ROOT)
    spec = json.loads(spec_path.read_text())
    base = root / spec["base_design"]
    original = json.loads(base.read_text())
    validate_spec(spec, original, original_sha256=_sha(base))
    opened = [spec_path, base]
    for path, expected in ((root / BASE_PROTOCOL.relative_to(ROOT), BASE_PROTOCOL_SHA256),
                           (root / TRAIN_MANIFEST.relative_to(ROOT), TRAIN_MANIFEST_SHA256)):
        if _sha(path) != expected:
            raise ValueError(f"WF cost 03 pinned input changed: {path.name}")
        opened.append(path)
    prior_path = root / spec["prior_roots_manifest"]
    if _sha(prior_path) != PRIOR_MANIFEST_SHA256:
        raise ValueError("WF cost prior roots manifest changed")
    opened.append(prior_path)
    prior = json.loads(prior_path.read_text())
    if set(prior) != {"oos-v12-wf-cost-only-01", "oos-v12-wf-cost-only-02"}:
        raise ValueError("WF cost prior roots roster changed")
    for name, record in prior.items():
        directory = root / "artifacts" / name
        current = {str(path.relative_to(directory)): _sha(path)
                   for path in sorted(directory.rglob("*")) if path.is_file()}
        if current != record["files"]:
            raise ValueError(f"WF cost historical root changed: {name}")
        opened.extend(directory / relative for relative in current)
    if _sha(root / APPROVAL_02.relative_to(ROOT)) != APPROVAL_02_SHA256:
        raise ValueError("WF cost 02 historical approval changed")
    opened.append(root / APPROVAL_02.relative_to(ROOT))
    second = root / "artifacts/oos-v12-wf-cost-only-02"
    if (second / "ledger.jsonl").exists():
        raise ValueError("Failed WF cost 02 unexpectedly has a ledger")
    with WFCostSessionJournal(second / "sessions.jsonl", campaign=second.name,
                              read_only=True) as sessions:
        if len(sessions.sessions) != 1 or sessions.sessions[0]["end"]["status"] != "failed":
            raise ValueError("Failed WF cost 02 session changed")
        stamp = sessions.sessions[0]["start"]["epoch"]
        failed_session_accounted = sessions.charges({}, now=stamp + 1).blocked
    from btc_risk_rl.pilots import wf_cost, wf_cost_replacement_exec

    if (wf_cost.MARKET_EXECUTION_ENABLED
            or wf_cost_replacement_exec.MARKET_EXECUTION_ENABLED):
        raise ValueError("Prior WF cost market gate unexpectedly enabled")
    campaign = root / spec["campaign_root"]
    approval = root / spec["approval_record"]
    blockers = ["no active approval"]
    if campaign.exists():
        blockers.append("new campaign root already exists")
    if approval.exists():
        blockers.append("new approval record already exists")
    return dict(status="blocked", blockers=blockers,
                replacement_root=str(campaign), approval_record=str(approval),
                root_absent=not campaign.exists(), approval_absent=not approval.exists(),
                historical_artifacts_verified=True,
                failed_02_session_accounted=failed_session_accounted,
                opened=[str(path) for path in opened],
                sha256={str(path): _sha(path) for path in opened})
