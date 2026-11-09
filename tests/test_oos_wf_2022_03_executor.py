"""Controlled-source checks for the independent 2022 cost executor."""

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch


def test_2022_profile_has_independent_pinned_approval(monkeypatch):
    from btc_risk_rl.pilots import wf_cost_2022_03_exec as profile
    from btc_risk_rl.pilots import wf_cost_2022_03_orchestrator as budget
    from btc_risk_rl.pilots.wf_permits import authorized_wf_permits

    assert profile.CAMPAIGN.name == "oos-v12-wf-cost-only-2022-03"
    assert profile.ROSTER == (("2022", 498614892, "C10"),)
    assert profile.UNITS == tuple(range(11))
    assert authorized_wf_permits()[profile.WF2022Permit] == profile.CAMPAIGN
    assert budget.APPROVAL.name == "OOS-v1-2-wf-cost-2022-only-03-approval.json"
    assert budget.JOURNAL_NAME == "wf-2022-only-03-attempts.jsonl"
    if profile.MARKET_EXECUTION_ENABLED:
        assert profile.REGISTRATION_SHA256 == budget.REGISTRATION_SHA256
        assert budget.APPROVAL.is_file()
        from datetime import datetime
        from zoneinfo import ZoneInfo

        admitted = datetime(2026, 11, 10, 1, tzinfo=ZoneInfo("America/La_Paz"))
        monkeypatch.setattr(profile.time, "time", lambda: admitted.timestamp())
        assert profile.require_campaign()["campaign"] == profile.CAMPAIGN.name
    else:
        assert profile.REGISTRATION_SHA256 is None
        assert not budget.MARKET_EXECUTION_ENABLED
        assert budget.REGISTRATION_SHA256 is None
        # A superseded approval file may remain for audit; the code gate still closes.
        with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
            profile.require_campaign()


def test_2022_ledger_rejects_other_run_and_incomplete_checkpoint(tmp_path):
    from btc_risk_rl.pilots.wf_cost_2022_03_exec import WF2022Ledger

    with WF2022Ledger(tmp_path, now=1000.0, identity={"fixture": True}) as ledger:
        ledger.preflight_done(1000.0)
        with pytest.raises(ValueError, match="order"):
            ledger.begin_unit("wf-2021", 0, 1001.0)
        ledger.begin_unit("wf-2022", 0, 1001.0)
        with pytest.raises(ValueError, match="checkpoint"):
            ledger.accept_unit(0, 1002.0, tmp_path / "missing", report={})
        assert ledger.state["status"] == "failed"


def test_2022_worker_rejects_closed_gate_before_request(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_2022_03_exec as profile
    from btc_risk_rl.pilots import wf_cost_2022_03_worker as worker

    monkeypatch.setattr(profile, "MARKET_EXECUTION_ENABLED", False)
    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        worker.run_request(tmp_path / "missing.json")
    assert not (tmp_path / "missing.json").exists()


def test_2022_forged_registration_rejected_before_worker_request(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_2022_03_exec as profile
    from btc_risk_rl.pilots import wf_cost_2022_03_orchestrator as budget
    from btc_risk_rl.pilots import wf_cost_2022_03_worker as worker

    monkeypatch.setattr(profile, "MARKET_EXECUTION_ENABLED", True)
    monkeypatch.setattr(budget, "MARKET_EXECUTION_ENABLED", True)
    monkeypatch.setattr(budget, "REGISTRATION_SHA256", "0" * 64)
    monkeypatch.setattr(profile, "REGISTRATION_SHA256", "0" * 64)
    with pytest.raises(PermissionError, match="approval hash mismatch"):
        worker.run_request(tmp_path / "missing.json")
    assert not (tmp_path / "missing.json").exists()


def test_2022_preflight_rejects_symlinked_campaign_root(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_2022_03_exec as profile

    target = tmp_path / "foreign"
    target.mkdir()
    (target / "ledger.jsonl").write_text("{}\n")
    link = tmp_path / profile.CAMPAIGN.name
    link.symlink_to(target, target_is_directory=True)
    monkeypatch.setattr(profile, "CAMPAIGN", link)
    monkeypatch.setattr(profile, "inspect_inputs", lambda: {"ok": True, "opened": []})
    monkeypatch.setattr(profile, "require_campaign", lambda: {"controlled": True})
    result = profile.inspect_preflight()
    assert result["status"] == "blocked"
    assert any("symlink" in blocker.lower() for blocker in result["blockers"])


def test_service_resource_drop_before_root_is_a_metered_block(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_2022_03_units as units
    from btc_risk_rl.pilots.wf_cost_2022_03_orchestrator import PreflightBlocked
    from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal

    campaign = tmp_path / units.CAMPAIGN.name
    monkeypatch.setattr(units, "CAMPAIGN", campaign)
    monkeypatch.setattr(units, "require_campaign", lambda: {"controlled": True})
    monkeypatch.setattr(units, "require_recent_prepare", lambda *_a, **_kw: None)
    monkeypatch.setattr(units, "check_service_context", lambda **_kw: None)
    monkeypatch.setattr(units, "inspect_host", lambda: {"memory_available_bytes": 0})
    monkeypatch.setattr(units, "resource_ready", lambda _host: False)
    with pytest.raises(PreflightBlocked, match="host preflight"):
        units.run_units()
    assert not campaign.exists()
    from btc_risk_rl.pilots.wf_cost_2022_03_orchestrator import JOURNAL_NAME

    journal = tmp_path / "shared-pilot-budget" / JOURNAL_NAME
    with WFCostSessionJournal(journal, campaign=campaign.name, read_only=True) as recorded:
        assert recorded.sessions[0]["end"]["status"] == "ready"


def test_stale_prepare_before_root_is_a_metered_block(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_2022_03_units as units
    from btc_risk_rl.pilots.wf_cost_2022_03_orchestrator import PreflightBlocked
    from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal

    campaign = tmp_path / units.CAMPAIGN.name
    monkeypatch.setattr(units, "CAMPAIGN", campaign)
    monkeypatch.setattr(units, "require_campaign", lambda: {"controlled": True})

    def stale(*_a, **_kw):
        raise ValueError("WF 2022 prepare checks invalid or stale")

    monkeypatch.setattr(units, "require_recent_prepare", stale)
    with pytest.raises(PreflightBlocked, match="prepare"):
        units.run_units()
    assert not campaign.exists()
    from btc_risk_rl.pilots.wf_cost_2022_03_orchestrator import JOURNAL_NAME

    journal = tmp_path / "shared-pilot-budget" / JOURNAL_NAME
    with WFCostSessionJournal(journal, campaign=campaign.name, read_only=True) as recorded:
        assert recorded.sessions[0]["end"]["status"] == "ready"


def test_2022_launch_requires_same_day_complete_prepare(tmp_path):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from btc_risk_rl.pilots import wf_cost_2022_03_exec as profile

    stamp = datetime(2026, 11, 6, 23, 5, tzinfo=ZoneInfo("America/La_Paz")).timestamp()
    journal = tmp_path / "checks.jsonl"
    with pytest.raises(ValueError, match="prepare"):
        profile.require_recent_prepare(journal, now=stamp)
    rows = [dict(event="check_end", name=name, status="ready", token="first",
                 epoch=stamp - 10 + index) for index, name in enumerate(
                     ("suite", "ruff", "preflight", "fold"))]
    journal.write_text("".join(json.dumps(row) + "\n" for row in rows))
    profile.require_recent_prepare(journal, now=stamp)
    with pytest.raises(ValueError, match="prepare"):
        profile.require_recent_prepare(journal, now=stamp + 901)
    with pytest.raises(ValueError, match="prepare"):
        profile.require_recent_prepare(journal, now=stamp + 86400)
    rows[-1]["status"] = "blocked"
    journal.write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(ValueError, match="prepare"):
        profile.require_recent_prepare(journal, now=stamp)


def test_watched_2022_preflight_refuses_shared_h1_csv_before_open():
    command = (
        "import runpy; "
        "runpy.run_path('scripts/audit_oos_wf_cost_2022_03_preflight.py', run_name='__main__'); "
        "open('data/processed/segmented-B-h1/bars.csv', 'rb')"
    )
    result = subprocess.run([sys.executable, "-c", command], capture_output=True,
                            text=True, check=False)
    assert result.returncode != 0
    assert "WF 2022 protected market file opened" in result.stderr


def _controlled_request(tmp_path, monkeypatch):
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.agents.synthetic import SyntheticMarket
    from btc_risk_rl.config import load_config
    from btc_risk_rl.pilots import wf_cost, wf_cost_source
    from btc_risk_rl.pilots import wf_cost_2022_03_exec as profile
    from btc_risk_rl.pilots.p2_budget import state_hash

    campaign = tmp_path / profile.CAMPAIGN.name
    work = campaign / "wf-2022"
    work.mkdir(parents=True)
    monkeypatch.setattr(profile, "CAMPAIGN", campaign)
    monkeypatch.setattr(profile, "require_campaign", lambda: {"controlled": True})
    monkeypatch.setattr(wf_cost.WFCostSettings, "__post_init__", lambda self: None)
    small = dict(hidden=4, iterations=1, n_a=2, n_q=2, n_b=2,
                 actor_epochs=1, critic_epochs=1, minibatch=1, fragment_steps=180)
    settings = wf_cost.WFCostSettings(seed=498614892, **small)
    monkeypatch.setattr(profile, "_expected_settings", lambda: asdict(settings))
    monkeypatch.setattr(profile, "EXPECTED_ROUTES", 1)
    monkeypatch.setattr(profile, "EXPECTED_FIT_ROWS", 2)
    config = load_config(Path("configs/initial.toml"))
    fabricated = SyntheticMarket(config, routes=1)
    source = TrainingMarket.__new__(TrainingMarket)
    source.config = config
    source._view = SimpleNamespace(training_path=fabricated.path)
    source.route_ids = (0,)
    source.audit = {"fit_count": 2, "normalizer_refitted": False,
                    "validation_observations_loaded": False}
    source._identity = {"profile": source.profile, "fold": "2022",
                        "manifest_sha256": "controlled-only",
                        "training_shard_manifest_sha256": profile.SHARD_MANIFEST_SHA256,
                        "scaler_sha256": "controlled-only", "files": {}}
    fold_manifest = campaign / "folds/wf-2022/manifest.json"
    fold_manifest.parent.mkdir(parents=True)
    fold_manifest.write_text(json.dumps({"source_identity": source.identity()}))
    monkeypatch.setattr(wf_cost_source, "build_fold_source", lambda _fold: source)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda _n: None)
    token = "controlled-lease"
    request = dict(root=str(work), run_id="wf-2022", fold="2022",
                   condition="C10", unit=0, previous=None, token=token,
                   config=str(profile.CONFIG), atomic_checkpoint=True,
                   settings=asdict(settings))
    path = work / "request-0.json"
    path.write_text(json.dumps(request))
    state = dict(status="running", cursor=0,
                 pending=dict(unit=0, run_id="wf-2022", token=token,
                              request_sha256=profile.digest(path),
                              supervisor_pid=os.getppid()),
                 runs={}, identity={"source": source.identity()})

    def persist():
        state["state_hash"] = state_hash(state)
        (campaign / "ledger.jsonl").write_text(json.dumps(state) + "\n")

    persist()
    return SimpleNamespace(campaign=campaign, work=work, source=source,
                           settings=settings, request=request, path=path,
                           state=state, persist=persist)


def test_2022_worker_completes_q0_and_resumes_into_qabd_with_controlled_source(
    tmp_path, monkeypatch,
):
    from btc_risk_rl.agents.checkpoint import provenance
    from btc_risk_rl.pilots.p2r_units import _verify_completion
    from btc_risk_rl.pilots.wf_cost_2022_03_worker import run_request

    case = _controlled_request(tmp_path, monkeypatch)
    run_request(case.path)
    first = case.work / "checkpoint-0"
    first_sha = hashlib.sha256((first / "state.pt").read_bytes()).hexdigest()
    payload0 = json.loads((case.work / "unit-0.json").read_text())
    assert payload0["report"]["market_training_executed"] is False
    assert _verify_completion(case.work, 0, case.settings, "C10", "wf-2022",
                              {"status": "passed"}, provenance(case.source),
                              diagnostic_n=64)[1] == "after_q0"
    case.request["unit"] = 1
    case.request["previous"] = str(first)
    case.path = case.work / "request-1.json"
    case.path.write_text(json.dumps(case.request))
    case.state["runs"] = {"wf-2022": {"checkpoint": str(first)}}
    case.state["pending"]["unit"] = 1
    case.state["pending"]["request_sha256"] = hashlib.sha256(case.path.read_bytes()).hexdigest()
    case.persist()
    run_request(case.path)
    second = case.work / "checkpoint-1"
    payload1 = json.loads((case.work / "unit-1.json").read_text())
    assert hashlib.sha256((first / "state.pt").read_bytes()).hexdigest() == first_sha
    assert payload1["report"]["market_training_executed"] is True
    assert payload1["resources"]["actor_updates"] == 2
    assert payload1["resources"]["critic_updates"] == 2
    assert _verify_completion(case.work, 1, case.settings, "C10", "wf-2022",
                              {"status": "passed"}, provenance(case.source),
                              diagnostic_n=64)[1] == "after_dual_and_D"
    assert (second / "state.pt").is_file()


def test_2022_supervisor_accepts_q0_then_unit_one_in_new_session(tmp_path, monkeypatch):
    """Exercise the real worker, verifier, ledger and attempt journal on a controlled path."""
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.agents.synthetic import SyntheticMarket
    from btc_risk_rl.config import load_config
    from btc_risk_rl.pilots import wf_cost_2022_03_exec as profile
    from btc_risk_rl.pilots import wf_cost_2022_03_units as units
    from btc_risk_rl.pilots import wf_cost_source
    from btc_risk_rl.pilots.wf_cost_2022_03_worker import run_request

    campaign = tmp_path / profile.CAMPAIGN.name
    monkeypatch.setattr(profile, "CAMPAIGN", campaign)
    monkeypatch.setattr(units, "CAMPAIGN", campaign)
    monkeypatch.setattr(profile, "require_campaign", lambda: {"controlled": True})
    monkeypatch.setattr(units, "require_campaign", lambda: {"controlled": True})
    monkeypatch.setattr(units, "require_recent_prepare", lambda *_a, **_kw: None)
    real_attempt = units.BudgetAttempt
    monkeypatch.setattr(units, "BudgetAttempt", lambda *a, **kw: real_attempt(
        *a, **{**kw, "night_window": False}))
    monkeypatch.setattr(profile.os, "getppid", os.getpid)
    monkeypatch.setattr(profile, "EXPECTED_ROUTES", 1)
    monkeypatch.setattr(profile, "EXPECTED_FIT_ROWS", 2)
    monkeypatch.setattr(units, "EXPECTED_ROUTES", 1)
    monkeypatch.setattr(units, "EXPECTED_FIT_ROWS", 2)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda _n: None)
    config = load_config(Path("configs/initial.toml"))
    fabricated = SyntheticMarket(config, routes=1)
    source = TrainingMarket.__new__(TrainingMarket)
    source.config = config
    source._view = SimpleNamespace(training_path=fabricated.path)
    source.route_ids = (0,)
    source.audit = {"fit_count": 2, "normalizer_refitted": False,
                    "validation_observations_loaded": False}
    source._identity = {"profile": source.profile, "fold": "2022",
                        "manifest_sha256": "controlled-only",
                        "training_shard_manifest_sha256": profile.SHARD_MANIFEST_SHA256,
                        "scaler_sha256": "controlled-only", "files": {}}
    monkeypatch.setattr(units, "build_fold_source", lambda _fold: source)
    monkeypatch.setattr(wf_cost_source, "build_fold_source", lambda _fold: source)
    monkeypatch.setattr(units, "_preflight", lambda: (
        {"power": {"ac": True, "battery_percent": 100},
         "memory_available_bytes": 8 * 1024**3, "disk_free_bytes": 100 * 1024**3},
        {"ok": True, "sha256": {"controlled": "fixture"}},
        {"ok": True, "global_spent": 0.0},
    ))
    monkeypatch.setattr(units, "inspect_budget", lambda **_kw: {
        "ok": True, "global_spent": 0.0,
    })
    monkeypatch.setattr(units, "_resources", lambda: {
        "power": {"ac": True, "battery_percent": 100},
        "memory_available_bytes": 8 * 1024**3, "disk_free_bytes": 100 * 1024**3,
    })

    def controlled_supervise(command, **_kw):
        run_request(command[-1])
        return {"status": "passed", "wall_seconds": 1.0, "rss_peak_bytes": 0}

    monkeypatch.setattr(units, "supervise", controlled_supervise)
    first_state = units.run_units(stop_after_q0=True)
    first_point = campaign / "wf-2022/checkpoint-0/state.pt"
    sha0 = hashlib.sha256(first_point.read_bytes()).hexdigest()
    assert first_state["status"] == "ready"
    assert len(first_state["units"]) == 1
    assert first_state["pending"] is None
    # A fresh interpreter can re-enter the accepted frontier without replaying Q0.
    inspect = subprocess.run(
        [sys.executable, "-c",
         "import json,sys,time; from pathlib import Path; "
         "from btc_risk_rl.pilots.wf_cost_2022_03_exec import WF2022Ledger; "
         "p=Path(sys.argv[1]); s=json.loads((p/'ledger.jsonl').read_text().splitlines()[-1]); "
         "l=WF2022Ledger(p,now=time.time(),identity=s['identity']); "
         "assert l.state['status']=='ready' and len(l.state['units'])==1; l.lock.close()",
         str(campaign)],
        capture_output=True, text=True, check=False,
    )
    assert inspect.returncode == 0, inspect.stderr
    from btc_risk_rl.pilots.wf_cost_2022_03_orchestrator import PreflightBlocked

    original_external = units._external

    def occupied(_now):
        raise PreflightBlocked("Another campaign is active")

    monkeypatch.setattr(units, "_external", occupied)
    paused = units.run_units()
    assert paused["status"] == "ready" and len(paused["units"]) == 1
    assert paused["pending"] is None
    assert hashlib.sha256(first_point.read_bytes()).hexdigest() == sha0
    monkeypatch.setattr(units, "_external", original_external)
    second_state = units.run_units(stop_after_unit=1)
    assert len(second_state["units"]) >= 2
    assert hashlib.sha256(first_point.read_bytes()).hexdigest() == sha0
    assert second_state["units"][1]["checkpoint"].endswith("checkpoint-1")
    assert (campaign / "wf-2022/checkpoint-1/state.pt").is_file()


@pytest.mark.parametrize("change", ["token", "root", "seed", "condition"])
def test_2022_worker_rejects_changed_lease_or_identity(tmp_path, monkeypatch, change):
    from btc_risk_rl.pilots.wf_cost_2022_03_worker import run_request

    case = _controlled_request(tmp_path, monkeypatch)
    if change == "token":
        case.request["token"] = "forged"
    elif change == "root":
        case.request["root"] = str(tmp_path / "foreign")
    elif change == "seed":
        case.request["settings"]["seed"] = 276696733
    else:
        case.request["condition"] = "C5"
    case.path.write_text(json.dumps(case.request))
    case.state["pending"]["request_sha256"] = hashlib.sha256(case.path.read_bytes()).hexdigest()
    case.persist()
    with pytest.raises(PermissionError):
        run_request(case.path)
    assert not (case.work / "checkpoint-0").exists()
