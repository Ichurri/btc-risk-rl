"""Synthetic checks for an isolated, disabled third WF cost profile."""

import hashlib
import json
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

_PROCESS = r'''
import hashlib
import itertools
import json
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from btc_risk_rl.pilots import wf_cost_replacement_03_units as units

root = Path(sys.argv[1])
mode = sys.argv[2]
epoch = datetime(2026, 10, 29, 12, tzinfo=ZoneInfo("America/La_Paz")).timestamp()
if mode != "q0":
    epoch += 100
units.CAMPAIGN = root
clock = itertools.count()
units.time.time = lambda: epoch + next(clock) * 0.01
units.require_campaign = lambda: None
units.check_service_context = lambda **_kw: "ready"
units.inspect_host = lambda: {
    "power": {"ac": True, "battery_percent": 100},
    "memory_available_bytes": 5 * 1024**3, "disk_free_bytes": 25 * 1024**3,
    "linger": "yes", "user_manager": "running",
}
units.inspect_inputs = lambda: {"ok": True, "sha256": {"synthetic": "fixture"}}
units.inspect_budget = lambda: {"ok": True, "global_spent": 0,
                               "remaining_before_reserve": 1000}
units.build_fold_source = lambda fold: SimpleNamespace(
    identity=lambda: {"fold": fold, "synthetic": True},
    route_ids=(0, 1), audit={"fit_count": 2},
)
units.provenance = lambda _source: {"synthetic": True}
units.code_sha256 = lambda: "synthetic-code"
units._unit_resources = lambda: {"unit": True}
units.resource_ready = lambda host: mode == "q0" or not host.get("unit", False)
units.supervise = lambda *_args, **_kw: {"status": "passed"}

def complete(work, unit, *_args, **_kw):
    assert unit == 0 and mode == "q0"
    point = work / "checkpoint-0"
    point.mkdir()
    state = point / "state.pt"
    state.write_bytes(b"03 synthetic Q0")
    sha = hashlib.sha256(state.read_bytes()).hexdigest()
    (point / "manifest.json").write_text(json.dumps({
        "schema_version": "p2_complete_boundary_v1", "boundary": "after_q0",
        "state_sha256": sha, "profile": "wf_cost_only",
        "run_id": "wf-2021", "condition": "C10",
    }))
    (work / "unit-0.json").write_text(json.dumps({"synthetic": True}))
    return ({"checkpoint": str(point), "checkpoint_sha256": sha,
             "report": {"boundary": "after_q0", "actor_updates": 0,
                        "critic_updates": 0, "market_training_executed": False},
             "resources": {"actor_updates": 0, "critic_updates": 0}}, "after_q0")

units._verify_completion = complete
if mode == "altered":
    old = units.roster
    units.roster = lambda: (("2021", 276696734, "C10"), old()[1])
if mode == "preledger":
    def fail():
        raise ValueError("synthetic failure before ledger")
    units.inspect_inputs = fail
try:
    state = units.run_units()
except (ValueError, PermissionError) as exc:
    print("rejected:" + str(exc))
    sys.exit(2)
print(json.dumps({"status": state["status"], "units": len(state["units"])}))
'''


def _run(root, mode):
    return subprocess.run([sys.executable, "-c", _PROCESS, str(root), mode],
                          capture_output=True, text=True, check=False)


def test_03_public_and_worker_closed_before_root_or_request(tmp_path):
    from btc_risk_rl.pilots import wf_cost_replacement_03_exec as profile

    root = tmp_path / "oos-v12-wf-cost-only-03"
    request = tmp_path / "missing-request.json"
    assert profile.CAMPAIGN.name == root.name
    assert profile.REGISTRATION.name == "OOS-v1-2-wf-cost-03-approval.json"
    assert profile.MARKET_EXECUTION_ENABLED is False
    assert profile.REGISTRATION_SHA256 is None
    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        profile.require_campaign()
    public = subprocess.run([sys.executable, "scripts/run_oos_wf_cost_03.py", "--run"],
                            capture_output=True, text=True, check=False)
    worker = subprocess.run([sys.executable, "-m",
                             "btc_risk_rl.pilots.wf_cost_replacement_03_worker",
                             str(request)], capture_output=True, text=True, check=False)
    assert public.returncode != 0 and "NOT AUTHORIZED" in public.stderr
    assert worker.returncode != 0 and "NOT AUTHORIZED" in worker.stderr
    assert not profile.CAMPAIGN.exists() and not profile.REGISTRATION.exists()
    assert not root.exists() and not request.exists()


def test_03_forged_registration_still_rejected(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_replacement_03_exec as profile

    approval = tmp_path / "approval.json"
    approval.write_text(json.dumps({"active": True, "campaign": profile.CAMPAIGN.name}))
    monkeypatch.setattr(profile, "REGISTRATION", approval)
    monkeypatch.setattr(profile, "REGISTRATION_SHA256", profile.digest(approval))
    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        profile.require_campaign()
    monkeypatch.setattr(profile, "MARKET_EXECUTION_ENABLED", True)
    with pytest.raises(PermissionError, match="inconsistent"):
        profile.require_campaign()
    assert not profile.CAMPAIGN.exists()


def test_03_fold_paths_cannot_fall_back_to_01(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_replacement_03_exec as profile

    root = tmp_path / "artifacts/oos-v12-wf-cost-only-03"
    monkeypatch.setattr(profile, "CAMPAIGN", root)
    assert profile.guard_fold_path(root / "folds/wf-2021") == root / "folds/wf-2021"
    with pytest.raises(ValueError, match="escapes"):
        profile.guard_fold_path(tmp_path / "artifacts/oos-v12-wf-cost-only-01/folds/wf-2021")


def test_03_first_q0_pause_then_new_process_reentry(tmp_path):
    root = tmp_path / "oos-v12-wf-cost-only-03"
    assert not root.exists()
    first = _run(root, "q0")
    assert first.returncode == 0, first.stderr
    assert json.loads(first.stdout) == {"status": "ready", "units": 1}
    ledger = root / "ledger.jsonl"
    point = root / "wf-2021/checkpoint-0/state.pt"
    before = hashlib.sha256(point.read_bytes()).hexdigest()
    state = json.loads(ledger.read_text().splitlines()[-1])
    assert state["status"] == "ready" and state["pending"] is None
    assert len(state["units"]) == 1
    second = _run(root, "reentry")
    assert second.returncode == 0, second.stderr
    assert json.loads(second.stdout) == {"status": "ready", "units": 1}
    assert hashlib.sha256(point.read_bytes()).hexdigest() == before
    events = [json.loads(row) for row in (root / "sessions.jsonl").read_text().splitlines()]
    assert [row["event"] for row in events] == ["start", "end", "start", "end"]
    assert all(row["status"] == "ready" for row in events if row["event"] == "end")


def test_03_orphan_and_altered_identity_rejected_without_new_unit(tmp_path):
    orphan = tmp_path / "oos-v12-wf-cost-only-03-orphan"
    orphan.mkdir()
    marker = orphan / "preserve.txt"
    marker.write_text("untouched")
    result = _run(orphan, "q0")
    assert result.returncode == 2 and "root exists without a valid ledger" in result.stdout
    assert list(orphan.iterdir()) == [marker]

    root = tmp_path / "oos-v12-wf-cost-only-03"
    assert _run(root, "q0").returncode == 0
    ledger = root / "ledger.jsonl"
    checkpoint = root / "wf-2021/checkpoint-0/state.pt"
    before = (hashlib.sha256(ledger.read_bytes()).hexdigest(),
              hashlib.sha256(checkpoint.read_bytes()).hexdigest())
    altered = _run(root, "altered")
    assert altered.returncode == 2 and "Campaign identity mismatch" in altered.stdout
    assert (hashlib.sha256(ledger.read_bytes()).hexdigest(),
            hashlib.sha256(checkpoint.read_bytes()).hexdigest()) == before
    assert not (root / "wf-2021/checkpoint-1").exists()


def test_03_preledger_failure_is_durable(tmp_path):
    root = tmp_path / "oos-v12-wf-cost-only-03"
    failed = _run(root, "preledger")
    assert failed.returncode == 2 and "synthetic failure before ledger" in failed.stdout
    assert not (root / "ledger.jsonl").exists()
    rows = [json.loads(row) for row in (root / "sessions.jsonl").read_text().splitlines()]
    assert [row["event"] for row in rows] == ["start", "end"]
    assert rows[-1]["status"] == "failed"
    assert _run(root, "q0").returncode == 2


def test_03_budget_charges_failed_02_session_on_its_local_day(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost
    from btc_risk_rl.pilots import wf_cost_replacement_03_exec as profile
    from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal

    monkeypatch.setattr(wf_cost, "ROOT", tmp_path)
    old = tmp_path / "artifacts/oos-v12-wf-cost-only-02/sessions.jsonl"
    now = datetime(2026, 10, 27, 12, tzinfo=ZoneInfo("America/La_Paz")).timestamp()
    with WFCostSessionJournal(old, campaign=old.parent.name) as sessions:
        token = sessions.start(now=now, monotonic=100, invocation_id="synthetic-failure")
        sessions.end(token, now=now + 1, monotonic=101,
                     status="failed", reason="synthetic first-start fault")
    monkeypatch.setattr(profile, "CAMPAIGN",
                        tmp_path / "artifacts/oos-v12-wf-cost-only-03")
    budget = profile.inspect_budget(now=now + 2)
    assert budget["global_spent"] == 10800
    assert budget["remaining_before_reserve"] == 0
    assert any(row["reason"] == "failed_or_unclosed_session"
               and "only-02/sessions.jsonl" in row["path"] for row in budget["sources"])


def test_03_spec_keeps_frozen_science_and_new_identity():
    from btc_risk_rl.pilots import wf_cost_replacement_03 as proposal
    from btc_risk_rl.pilots import wf_cost_replacement_03_exec as profile

    result = proposal.inspect_candidate()
    assert result["status"] == "blocked"
    assert result["replacement_root"].endswith("oos-v12-wf-cost-only-03")
    assert result["root_absent"] and result["approval_absent"]
    assert result["historical_artifacts_verified"]
    assert result["failed_02_session_accounted"]
    assert not any("validation" in p or "final" in p for p in result["opened"])
    assert profile.roster() == (("2021", 276696733, "C10"),
                                ("2022", 498614892, "C10"))
    assert sum(profile.unit_cap(unit) for unit in range(11)) == 1920
    assert profile.WFCostSettings(seed=276696733).critic_epochs == 4
    assert profile.WFCostSettings(seed=498614892).critic_beta == 0


def test_03_watched_preflight_no_protected_data(tmp_path):
    output = tmp_path / "preflight.json"
    result = subprocess.run([sys.executable, "-m",
                             "scripts.audit_oos_wf_cost_03_preflight"],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    output.write_text(result.stdout)
    payload = json.loads(output.read_text())
    assert payload["preflight"]["status"] == "blocked"
    assert "no active approval" in " ".join(payload["preflight"]["blockers"])
    assert payload["protected_or_shared_csv_opened"] is False
    assert payload["market_trajectories_generated"] == 0
    assert payload["optimizer_steps"] == 0
    assert payload["fold_metadata"]["2021"]["episodes"] == 3639
    assert payload["fold_metadata"]["2022"]["episodes"] == 4678
