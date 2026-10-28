"""Synthetic proof of a fresh WF cost root and unapproved replacement design."""

import hashlib
import json
import subprocess
import sys

import pytest

from btc_risk_rl.pilots.wf_cost_replacement import (
    BASE_DESIGN_SHA256,
    BASE_PROTOCOL_SHA256,
    TRAIN_MANIFEST_SHA256,
    inspect_candidate,
    validate_replacement_spec,
)

_PROCESS = """
import json
import sys
from pathlib import Path
from btc_risk_rl.pilots.wf_cost import WFCostLedger, digest, roster
from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal
from btc_risk_rl.pilots.wf_cost_units import first_q0_audit_pause

root = Path(sys.argv[1])
mode = sys.argv[2]
now = {"q0": 1000, "reenter": 1100, "altered": 1200, "preledger_fail": 1300}[mode]
with WFCostSessionJournal(root / "sessions.jsonl", campaign=root.name) as journal:
    token = journal.start(now=now, monotonic=now, invocation_id="synthetic-" + mode)
    try:
        if mode == "preledger_fail":
            raise ValueError("synthetic preledger identity failure")
        identity = {"fixture": "new-root", "roster": roster()}
        if mode == "altered":
            identity["roster"] = (("2021", 276696734, "C10"), roster()[1])
        with WFCostLedger(root, identity=identity, now=now + 1,
                          session_journal=journal, session_token=token) as ledger:
            ledger.preflight_done(now + 2)
            if mode == "q0":
                ledger.begin_unit("2021", 0, now + 3)
                point = root / "wf-2021/checkpoint-0"
                point.mkdir(parents=True)
                (point / "state.pt").write_bytes(b"synthetic-new-root-q0")
                (point / "manifest.json").write_text(json.dumps({
                    "schema_version": "p2_complete_boundary_v1", "boundary": "after_q0",
                    "state_sha256": digest(point / "state.pt"),
                    "profile": "wf_cost_only", "run_id": "wf-2021", "condition": "C10",
                }))
                ledger.accept_unit("2021", 0, now + 10, point, report={
                    "market_training_executed": False, "actor_updates": 0,
                    "critic_updates": 0, "boundary": "after_q0",
                })
                assert first_q0_audit_pause(ledger.state)
                print("q0_paused")
            else:
                assert ledger.admit_unit("2021", 1, now + 3) == "start"
                assert len(ledger.state["units"]) == 1
                print("unit_1_admitted")
    except ValueError as exc:
        journal.end(token, now=now + 4, monotonic=now + 4,
                    status="failed", reason=str(exc))
        print("preledger_failed:" + str(exc))
    else:
        journal.end(token, now=now + 11, monotonic=now + 11, status="ready")
"""


def _run(root, mode):
    return subprocess.run([sys.executable, "-c", _PROCESS, str(root), mode],
                          capture_output=True, text=True, check=False)


def test_fresh_root_q0_pause_then_new_process_admits_unit_one(tmp_path):
    root = tmp_path / "oos-v12-wf-cost-only-02"
    assert not root.exists()
    first = _run(root, "q0")
    assert first.returncode == 0, first.stderr
    assert first.stdout.strip() == "q0_paused"
    state = json.loads((root / "ledger.jsonl").read_text().splitlines()[-1])
    assert state["status"] == "ready"
    assert len(state["units"]) == 1 and state["pending"] is None
    second = _run(root, "reenter")
    assert second.returncode == 0, second.stderr
    assert second.stdout.strip() == "unit_1_admitted"
    state = json.loads((root / "ledger.jsonl").read_text().splitlines()[-1])
    assert len(state["units"]) == 1 and state["pending"] is None
    sessions = [json.loads(line) for line in (root / "sessions.jsonl").read_text().splitlines()]
    assert [row["event"] for row in sessions] == ["start", "end", "start", "end"]
    assert [row.get("status") for row in sessions if row["event"] == "end"] == ["ready"] * 2


def test_fresh_root_rejects_changed_identity_and_preserves_q0(tmp_path):
    root = tmp_path / "oos-v12-wf-cost-only-02"
    assert _run(root, "q0").returncode == 0
    ledger = root / "ledger.jsonl"
    point = root / "wf-2021/checkpoint-0/state.pt"
    before = (hashlib.sha256(ledger.read_bytes()).hexdigest(),
              hashlib.sha256(point.read_bytes()).hexdigest())
    altered = _run(root, "altered")
    assert altered.returncode == 0, altered.stderr
    assert "Campaign identity mismatch" in altered.stdout
    assert (hashlib.sha256(ledger.read_bytes()).hexdigest(),
            hashlib.sha256(point.read_bytes()).hexdigest()) == before
    assert not (root / "wf-2021/checkpoint-1").exists()
    sessions = [json.loads(line) for line in (root / "sessions.jsonl").read_text().splitlines()]
    assert sessions[-1]["status"] == "failed"


def test_fresh_root_preledger_failure_is_durable_without_unit(tmp_path):
    root = tmp_path / "oos-v12-wf-cost-only-02"
    failed = _run(root, "preledger_fail")
    assert failed.returncode == 0, failed.stderr
    assert "synthetic preledger identity failure" in failed.stdout
    assert not (root / "ledger.jsonl").exists()
    sessions = [json.loads(line) for line in (root / "sessions.jsonl").read_text().splitlines()]
    assert [row["event"] for row in sessions] == ["start", "end"]
    assert sessions[-1]["status"] == "failed"


def test_replacement_spec_keeps_design_and_requires_distinct_paths():
    original = {
        "roster": [["2021", 276696733, "C10"], ["2022", 498614892, "C10"]],
        "total_units": 22,
        "campaign_root_reserved_not_created": "artifacts/oos-v12-wf-cost-only-01",
    }
    candidate = {
        "schema_version": 1,
        "status": "proposal_not_authorized",
        "base_design": "docs/protocols/OOS-v1-2-wf-cost-executor-v1.json",
        "base_design_sha256": BASE_DESIGN_SHA256,
        "base_protocol_sha256": BASE_PROTOCOL_SHA256,
        "training_shard_manifest_sha256": TRAIN_MANIFEST_SHA256,
        "replacement_root": "artifacts/oos-v12-wf-cost-only-02",
        "approval_record": "docs/protocols/OOS-v1-2-wf-cost-replacement-approval.json",
        "market_execution_authorized": False,
        "reuse_partial_artifacts": False,
        "require_new_session_journal": True,
        "require_q0_pause": True,
        "require_roster_canonicalization": True,
    }
    validate_replacement_spec(candidate, original, original_sha256=BASE_DESIGN_SHA256)
    for field, bad in (("replacement_root", original["campaign_root_reserved_not_created"]),
                       ("approval_record", "docs/protocols/OOS-v1-2-wf-cost-approval.json"),
                       ("market_execution_authorized", True),
                       ("reuse_partial_artifacts", True),
                       ("base_design_sha256", "2" * 64)):
        changed = {**candidate, field: bad}
        with pytest.raises(ValueError):
            validate_replacement_spec(changed, original,
                                      original_sha256=BASE_DESIGN_SHA256)


def test_candidate_preflight_is_read_only_and_blocked():
    from btc_risk_rl.pilots.protocol import ROOT

    root = ROOT / "artifacts/oos-v12-wf-cost-only-02"
    approval = ROOT / "docs/protocols/OOS-v1-2-wf-cost-replacement-approval.json"
    assert not root.exists() and approval.is_file()
    result = inspect_candidate()
    assert result["status"] == "blocked"
    assert "proposal_not_authorized" in result["blockers"]
    assert "replacement_approval_path_already_exists" in result["blockers"]
    assert result["root_absent"] and not result["approval_absent"]
    assert result["historical_artifacts_verified"] is True
    assert str(ROOT / "artifacts/oos-v12-wf-cost-only-01/ledger.jsonl") in result["opened"]
    assert not root.exists() and approval.is_file()
    assert all("validation" not in path and "final" not in path
               for path in result["opened"])
