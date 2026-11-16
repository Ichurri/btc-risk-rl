"""Replacement WF executor: isolated gate and synthetic lifecycle."""

import hashlib
import json
import runpy
import subprocess
import sys
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from btc_risk_rl.pilots import wf_cost_replacement_exec as replacement


def test_failed_replacement_permission_is_closed_but_record_pinned(tmp_path, monkeypatch):
    root = tmp_path / "oos-v12-wf-cost-only-02"
    monkeypatch.setattr(replacement, "CAMPAIGN", root)
    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        replacement.run_historical_units()
    assert not root.exists()
    assert replacement.CAMPAIGN.name == "oos-v12-wf-cost-only-02"
    assert replacement.MARKET_EXECUTION_ENABLED is False
    assert replacement.digest(replacement.REGISTRATION) == replacement.REGISTRATION_SHA256


def test_code_hash_masks_only_registration_digest_literal(tmp_path):
    source = tmp_path / "wf_cost_replacement_exec.py"
    source.write_text("MARKET_EXECUTION_ENABLED = True\nREGISTRATION_SHA256 = None\n")
    before = replacement._code_file_sha256(source)
    source.write_text("MARKET_EXECUTION_ENABLED = True\nREGISTRATION_SHA256 = 'a' * 64\n")
    assert replacement._code_file_sha256(source) == before
    source.write_text("MARKET_EXECUTION_ENABLED = False\nREGISTRATION_SHA256 = 'a' * 64\n")
    assert replacement._code_file_sha256(source) != before


def test_forged_approval_cannot_enable_replacement(tmp_path, monkeypatch):
    approval = tmp_path / "approval.json"
    approval.write_text(json.dumps({"active": True, "campaign": "oos-v12-wf-cost-only-02"}))
    monkeypatch.setattr(replacement, "REGISTRATION", approval)
    monkeypatch.setattr(replacement, "REGISTRATION_SHA256", None)
    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        replacement.require_campaign()
    monkeypatch.setattr(replacement, "REGISTRATION_SHA256", replacement.digest(approval))
    monkeypatch.setattr(replacement, "MARKET_EXECUTION_ENABLED", True)
    with pytest.raises(PermissionError, match="inconsistent"):
        replacement.require_campaign()


def test_public_and_worker_reject_forged_digest_before_request_or_root_access(
        tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_replacement_worker as worker
    from btc_risk_rl.pilots.protocol import ROOT

    public = runpy.run_path(str(ROOT / "scripts/run_oos_wf_cost_replacement.py"))["main"]

    request = tmp_path / "absent-request.json"
    monkeypatch.setattr(replacement, "REGISTRATION_SHA256", "0" * 64)
    monkeypatch.setattr(replacement, "MARKET_EXECUTION_ENABLED", True)
    monkeypatch.setattr(sys, "argv", ["run_oos_wf_cost_replacement", "--run"])
    with pytest.raises(SystemExit, match="hash mismatch"):
        public()
    monkeypatch.setattr(sys, "argv", ["wf_cost_replacement_worker", str(request)])
    with pytest.raises(PermissionError, match="hash mismatch"):
        worker.main()
    assert not request.exists()
    assert not (replacement.CAMPAIGN / "ledger.jsonl").exists()


def test_new_profile_reuses_exact_roster_caps_and_budget():
    from btc_risk_rl.pilots.wf_cost import BudgetState

    assert replacement.roster() == (("2021", 276696733, "C10"),
                                    ("2022", 498614892, "C10"))
    assert replacement.units() == tuple((fold, unit) for fold in ("2021", "2022")
                                        for unit in range(11))
    assert sum(replacement.unit_cap(unit) for _, unit in replacement.units()) == 3840
    assert replacement.admit(BudgetState(("2026-10-27",), 3500, 3500, 6000),
                             "2026-10-27", 1) == "pause"


def test_replacement_budget_debits_original_ledger_not_its_own(tmp_path, monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from btc_risk_rl.pilots import wf_cost

    monkeypatch.setattr(wf_cost, "ROOT", tmp_path)
    monkeypatch.setattr(replacement, "CAMPAIGN",
                        tmp_path / "artifacts/oos-v12-wf-cost-only-02")
    old = tmp_path / "artifacts/oos-v12-wf-cost-only-01/ledger.jsonl"
    old.parent.mkdir(parents=True)
    old.write_text(json.dumps({"status": "ready", "days": {
        "2026-10-27": {"charged_wall_seconds": 600.0}
    }}) + "\n")
    own = replacement.CAMPAIGN / "ledger.jsonl"
    own.parent.mkdir(parents=True)
    own.write_text(json.dumps({"status": "ready", "days": {
        "2026-10-27": {"charged_wall_seconds": 90.0}
    }}) + "\n")
    now = datetime(2026, 10, 27, 12, tzinfo=ZoneInfo("America/La_Paz")).timestamp()
    budget = replacement.inspect_budget(now=now)
    assert budget["global_spent"] == 600.0
    assert [row["path"] for row in budget["sources"]] == [str(old)]


_PROCESS = r'''
import json
import sys
from pathlib import Path
from btc_risk_rl.pilots.wf_cost_replacement_exec import WFCostLedger, WFCostSessionJournal, digest, roster
from btc_risk_rl.pilots.wf_cost_replacement_units import first_q0_audit_pause
root = Path(sys.argv[1])
mode = sys.argv[2]
now = 1000 if mode == "q0" else 1011
with WFCostSessionJournal(root / "sessions.jsonl", campaign=root.name) as journal:
    token = journal.start(now=now, monotonic=now, invocation_id="synthetic-" + mode)
    try:
        if mode == "before_ledger":
            raise ValueError("synthetic identity reconstruction failure")
        identity = {"fixture": "replacement-profile", "roster": roster()}
        if mode == "altered":
            identity["roster"] = (("2021", 1, "C10"), roster()[1])
        with WFCostLedger(root, identity=identity, now=now + 1,
                          session_journal=journal, session_token=token) as ledger:
            ledger.preflight_done(now + 2)
            if mode == "q0":
                ledger.begin_unit("2021", 0, now + 3)
                point = root / "wf-2021/checkpoint-0"
                point.mkdir(parents=True)
                (point / "state.pt").write_bytes(b"replacement synthetic Q0")
                (point / "manifest.json").write_text(json.dumps({
                    "schema_version": "p2_complete_boundary_v1", "boundary": "after_q0",
                    "state_sha256": digest(point / "state.pt"),
                    "profile": "wf_cost_only", "run_id": "wf-2021", "condition": "C10",
                }))
                ledger.accept_unit("2021", 0, now + 10, point, report={
                    "market_training_executed": False, "actor_updates": 0,
                    "critic_updates": 0, "boundary": "after_q0",
                })
                assert ledger.state["status"] == "ready"
                assert len(ledger.state["units"]) == 1
                assert first_q0_audit_pause(ledger.state)
                print("q0_paused")
            else:
                assert ledger.admit_unit("2021", 1, now + 3) == "start"
                assert len(ledger.state["units"]) == 1
                print("unit_1_admitted")
    except ValueError as exc:
        journal.end(token, now=now + 4, monotonic=now + 4,
                    status="failed", reason=str(exc))
        print("failed:" + str(exc))
    else:
        journal.end(token, now=now + 11, monotonic=now + 11, status="ready")
'''


def _synthetic(root, mode):
    return subprocess.run([sys.executable, "-c", _PROCESS, str(root), mode],
                          capture_output=True, text=True, check=False)


def test_replacement_q0_pause_new_process_and_shared_session_budget(tmp_path):
    root = tmp_path / "oos-v12-wf-cost-only-02"
    first = _synthetic(root, "q0")
    assert first.returncode == 0, first.stderr
    assert first.stdout.strip() == "q0_paused"
    ledger = root / "ledger.jsonl"
    checkpoint = root / "wf-2021/checkpoint-0/state.pt"
    before = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    second = _synthetic(root, "reentry")
    assert second.returncode == 0, second.stderr
    assert second.stdout.strip() == "unit_1_admitted"
    state = json.loads(ledger.read_text().splitlines()[-1])
    assert state["pending"] is None and len(state["units"]) == 1
    assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == before
    with replacement.WFCostSessionJournal(root / "sessions.jsonl", campaign=root.name,
                                          read_only=True) as sessions:
        charge = sessions.charges(state, now=1022)
    assert not charge.blocked
    assert charge.extra_by_day
    assert len(sessions.sessions) == 2


def test_replacement_preledger_failure_durable_and_roster_alteration_rejected(tmp_path):
    failed_root = tmp_path / "preledger"
    failed = _synthetic(failed_root, "before_ledger")
    assert failed.returncode == 0, failed.stderr
    assert not (failed_root / "ledger.jsonl").exists()
    sessions = [json.loads(x) for x in (failed_root / "sessions.jsonl").read_text().splitlines()]
    assert sessions[-1]["status"] == "failed"
    root = tmp_path / "oos-v12-wf-cost-only-02"
    assert _synthetic(root, "q0").returncode == 0
    ledger = root / "ledger.jsonl"
    before = hashlib.sha256(ledger.read_bytes()).hexdigest()
    altered = _synthetic(root, "altered")
    assert altered.returncode == 0, altered.stderr
    assert "Campaign identity mismatch" in altered.stdout
    assert hashlib.sha256(ledger.read_bytes()).hexdigest() == before


def test_replacement_supervisor_records_failure_before_ledger(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_replacement_units as units

    root = tmp_path / "oos-v12-wf-cost-only-02"
    monkeypatch.setattr(units, "CAMPAIGN", root)
    monkeypatch.setattr(units, "require_campaign", lambda: None)
    monkeypatch.setattr(units, "P2RSharedBudget",
                        lambda *_args, **_kwargs: nullcontext(SimpleNamespace(external_seconds=0)))
    monkeypatch.setattr(units, "_launch_readiness",
                        lambda: (_ for _ in ()).throw(ValueError("synthetic preledger failure")))
    with pytest.raises(ValueError, match="synthetic preledger failure"):
        units.run_units()
    assert not (root / "ledger.jsonl").exists()
    rows = [json.loads(x) for x in (root / "sessions.jsonl").read_text().splitlines()]
    assert [row["event"] for row in rows] == ["start", "end"]
    assert rows[-1]["status"] == "failed"


def _synthetic_supervisor_guards(monkeypatch, units, root):
    """Exercise the real supervisor entry and readiness without market I/O."""
    monkeypatch.setattr(units, "CAMPAIGN", root)
    monkeypatch.setattr(units, "require_campaign", lambda: None)
    monkeypatch.setattr(units, "check_service_context", lambda **_kwargs: "ready")
    monkeypatch.setattr(units, "inspect_host", lambda: {
        "power": {"ac": True, "battery_percent": 100},
        "memory_available_bytes": 5 * 1024**3,
        "disk_free_bytes": 25 * 1024**3,
        "linger": "yes", "user_manager": "running",
    })
    monkeypatch.setattr(units, "inspect_inputs", lambda: {
        "ok": True, "sha256": {"synthetic": "fixture"},
    })
    monkeypatch.setattr(units, "inspect_budget", lambda: {
        "ok": True, "remaining_before_reserve": 1000, "global_spent": 0,
    })
    monkeypatch.setattr(units, "build_fold_source", lambda fold: SimpleNamespace(
        identity=lambda: {"fold": fold, "fixture": True},
        route_ids=(0, 1), audit={"fit_count": 2},
    ))
    monkeypatch.setattr(units, "provenance", lambda _source: {"synthetic": True})
    monkeypatch.setattr(units, "_unit_resources", lambda: {"phase": "unit"})
    monkeypatch.setattr(units, "resource_ready",
                        lambda host: host.get("phase") != "unit")


def test_supervisor_first_start_accepts_absent_synthetic_root(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_replacement_units as units

    root = tmp_path / "oos-v12-wf-cost-only-synthetic"
    _synthetic_supervisor_guards(monkeypatch, units, root)
    assert not root.exists()
    assert units.run_units()["status"] == "ready"
    state = json.loads((root / "ledger.jsonl").read_text().splitlines()[-1])
    assert state["status"] == "ready" and state["units"] == []
    assert state.get("pending") is None
    rows = [json.loads(x) for x in (root / "sessions.jsonl").read_text().splitlines()]
    assert [row["event"] for row in rows] == ["start", "end"]
    assert rows[-1]["status"] == "ready"


def test_supervisor_rejects_existing_root_without_ledger_unchanged(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_replacement_units as units

    root = tmp_path / "oos-v12-wf-cost-only-synthetic"
    root.mkdir()
    marker = root / "historical-evidence.txt"
    marker.write_text("preserve")
    _synthetic_supervisor_guards(monkeypatch, units, root)
    with pytest.raises(ValueError, match="root exists without a valid ledger"):
        units.run_units()
    assert list(root.iterdir()) == [marker]
    assert marker.read_text() == "preserve"


def test_supervisor_reentry_accepts_existing_root_with_ledger(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_replacement_units as units

    root = tmp_path / "oos-v12-wf-cost-only-synthetic"
    _synthetic_supervisor_guards(monkeypatch, units, root)
    assert units.run_units()["status"] == "ready"
    ledger = root / "ledger.jsonl"
    first_state = json.loads(ledger.read_text().splitlines()[-1])
    assert units.run_units()["status"] == "ready"
    latest_state = json.loads(ledger.read_text().splitlines()[-1])
    assert latest_state["identity"] == first_state["identity"]
    assert latest_state["units"] == [] and latest_state.get("pending") is None
    rows = [json.loads(x) for x in (root / "sessions.jsonl").read_text().splitlines()]
    assert [row["event"] for row in rows] == ["start", "end", "start", "end"]
    assert all(row["status"] == "ready" for row in rows if row["event"] == "end")


def test_preflight_open_audit_excludes_protected_and_shared_csv():
    result = subprocess.run([sys.executable, "-m",
                             "scripts.audit_oos_wf_cost_replacement_preflight"],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "no active approval" in " ".join(payload["preflight"]["blockers"])
    assert (payload["fold_metadata"]["2021"]["episodes"],
            payload["fold_metadata"]["2021"]["fit_rows"]) == (3639, 5764)
    assert (payload["fold_metadata"]["2022"]["episodes"],
            payload["fold_metadata"]["2022"]["fit_rows"]) == (4678, 7703)
    assert payload["protected_or_shared_csv_opened"] is False
    assert payload["market_trajectories_generated"] == 0
    assert not any("segmented-B-h1/" in path and path.endswith(".csv")
                   for path in payload["files_opened"])
    assert payload["preflight"]["root_exists"] is True
    assert not (replacement.CAMPAIGN / "ledger.jsonl").exists()
