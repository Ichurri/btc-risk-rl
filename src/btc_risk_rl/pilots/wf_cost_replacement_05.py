"""Read-only provenance audit for a fifth, unapproved WF cost profile."""

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
from btc_risk_rl.pilots.wf_cost_replacement_04 import inspect_candidate as inspect_04

SPEC = ROOT / "docs/protocols/OOS-v1-2-wf-cost-05-profile-v1.json"
PRIOR_04_PROFILE_SHA256 = "b188f93b0248d230dc4b122ed0e650be1c545dd7464184b744c69ef231772fbb"
PRIOR_04_AUDIT_SHA256 = "866987791f96d9f8ce1ccfd2c82e22adda320962d0ee029307062cdca46db95c"
APPROVAL_04_SHA256 = "f9230d841757a3cf99ce79c81e50ad2c9794bf4615781fae3e0a4f2c1c74275d"
EXPECTED_04_MAP_SHA256 = "3c22543a9238b07f84ae790e92fcd8b627d53483898e15204d9a8a5fb6a859da"


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_spec(spec, original, *, original_sha256):
    """Only replace the root and registration; require all pinned invariants."""
    expected = {
        "schema_version": 1,
        "status": "infrastructure_only_not_authorized",
        "base_design": "docs/protocols/OOS-v1-2-wf-cost-executor-v1.json",
        "base_design_sha256": BASE_DESIGN_SHA256,
        "base_protocol_sha256": BASE_PROTOCOL_SHA256,
        "training_shard_manifest_sha256": TRAIN_MANIFEST_SHA256,
        "prior_04_profile": "docs/protocols/OOS-v1-2-wf-cost-04-profile-v1.json",
        "prior_04_profile_sha256": PRIOR_04_PROFILE_SHA256,
        "prior_04_resource_audit": "docs/evidence/wf04-resource-diagnostic-20261030/results.json",
        "prior_04_resource_audit_sha256": PRIOR_04_AUDIT_SHA256,
        "prior_04_approval_sha256": APPROVAL_04_SHA256,
        "campaign_root": "artifacts/oos-v12-wf-cost-only-05",
        "approval_record": "docs/protocols/OOS-v1-2-wf-cost-05-approval.json",
        "market_execution_authorized": False,
        "reuse_prior_artifacts": False,
        "require_new_session_journal": True,
        "require_q0_pause": True,
        "require_roster_canonicalization": True,
        "require_resource_guard_snapshot": True,
    }
    if (spec != expected or original_sha256 != BASE_DESIGN_SHA256
            or spec["campaign_root"] == original["campaign_root_reserved_not_created"]):
        raise ValueError("WF cost 05 profile changed its frozen scope")


def inspect_candidate(root=ROOT):
    """Audit 01–04 and pinned metadata without writing or opening market rows."""
    root = Path(root)
    prior = inspect_04(root)
    if not prior["historical_artifacts_verified"]:
        raise ValueError("WF cost prior roots changed")
    spec_path = root / SPEC.relative_to(ROOT)
    spec = json.loads(spec_path.read_text())
    base = root / spec["base_design"]
    original = json.loads(base.read_text())
    validate_spec(spec, original, original_sha256=_sha(base))
    opened = [root / path for path in prior["opened"]]
    opened.extend((spec_path, base))
    pinned = (
        (root / BASE_PROTOCOL.relative_to(ROOT), BASE_PROTOCOL_SHA256),
        (root / TRAIN_MANIFEST.relative_to(ROOT), TRAIN_MANIFEST_SHA256),
        (root / spec["prior_04_profile"], PRIOR_04_PROFILE_SHA256),
        (root / spec["prior_04_resource_audit"], PRIOR_04_AUDIT_SHA256),
        (root / "docs/protocols/OOS-v1-2-wf-cost-04-approval.json", APPROVAL_04_SHA256),
    )
    for path, expected in pinned:
        if _sha(path) != expected:
            raise ValueError(f"WF cost 05 pinned input changed: {path.name}")
        opened.append(path)
    audit = json.loads((root / spec["prior_04_resource_audit"]).read_text())
    historical_roots = audit["historical_roots"]
    if set(historical_roots) != {"01", "02", "03", "04"}:
        raise ValueError("WF historical roots audit roster changed")
    for number, record in historical_roots.items():
        directory = root / "artifacts" / f"oos-v12-wf-cost-only-{number}"
        current = {str(path.relative_to(directory)): _sha(path)
                   for path in sorted(directory.rglob("*")) if path.is_file()}
        current_hash = hashlib.sha256(json.dumps(current, sort_keys=True).encode()).hexdigest()
        if current_hash != record["mapping_sha256"] or len(current) != record["files"]:
            raise ValueError(f"WF cost historical root changed: {number}")
        opened.extend(directory / relative for relative in current)
    if historical_roots["04"]["mapping_sha256"] != EXPECTED_04_MAP_SHA256:
        raise ValueError("WF cost 04 audit changed")
    fourth = root / "artifacts/oos-v12-wf-cost-only-04"
    ledger = json.loads((fourth / "ledger.jsonl").read_text().splitlines()[-1])
    if (ledger["status"] != "failed" or len(ledger["units"]) != 8
            or ledger["pending"]["unit"] != 8):
        raise ValueError("WF cost 04 failed ledger changed")
    from btc_risk_rl.pilots import wf_cost_replacement_04_exec

    if wf_cost_replacement_04_exec.MARKET_EXECUTION_ENABLED:
        raise ValueError("WF cost 04 gate unexpectedly enabled")
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
                historical_artifacts_verified=True, historical_roots=historical_roots,
                failed_02_session_accounted=prior["failed_02_session_accounted"],
                failed_04_pending=True,
                opened=[str(path) for path in opened],
                sha256={str(path): _sha(path) for path in opened})
