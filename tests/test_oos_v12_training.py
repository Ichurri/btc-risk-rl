"""Synthetic and static gates for the new OOS training campaign."""

import hashlib
import json
import multiprocessing
import os
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest


def test_campaign_roots_match_frozen_paths_exactly():
    from btc_risk_rl.pilots import oos_v12_training as campaign

    expected = campaign.frozen_protocol()["campaign_roots"]
    assert {name: str(path.relative_to(campaign.ROOT))
            for name, path in campaign.CAMPAIGNS.items()} == expected
    assert {path.parent for path in campaign.CAMPAIGNS.values()} == {
        campaign.ROOT / "artifacts"
    }


def _hold_precheck_lock(artifacts, ready, release):
    from btc_risk_rl.pilots.oos_v12_launch import OOSPrecheckAttempt

    with OOSPrecheckAttempt(artifacts, gate=lambda: None):
        ready.set()
        if not release.wait(20):
            raise TimeoutError("Lock test did not release the holder")


def test_precheck_and_all_profile_supervisors_compete_for_one_lock(tmp_path):
    from btc_risk_rl.pilots import oos_v12_training as campaign
    from btc_risk_rl.pilots.p2r import P2RSharedBudget

    artifacts = tmp_path / "artifacts"
    context = multiprocessing.get_context("spawn")
    ready, release = context.Event(), context.Event()
    holder = context.Process(target=_hold_precheck_lock,
                             args=(artifacts, ready, release))
    holder.start()
    try:
        assert ready.wait(10)
        assert holder.is_alive() and holder.pid != os.getpid()
        for profile in campaign.PROFILES:
            root = tmp_path / campaign.CAMPAIGNS[profile].relative_to(campaign.ROOT)
            with pytest.raises(ValueError, match="global daily budget"):
                P2RSharedBudget(root.parent, root.name, now=time.time())
    finally:
        release.set()
        holder.join(10)
        if holder.is_alive():
            holder.terminate()
            holder.join(5)
    assert holder.exitcode == 0


def test_rosters_are_complete_rotated_and_disjoint():
    from btc_risk_rl.pilots.oos_v12_training import roster

    aux_21, aux_22, main = (roster(name) for name in ("wf-2021", "wf-2022", "main-2018-2022"))
    assert [len(aux_21), len(aux_22), len(main)] == [9, 9, 108]
    assert {row[0] for row in aux_21} == {row[0] for row in aux_22}
    assert {row[0] for row in aux_21}.isdisjoint({row[0] for row in main})
    assert [row[1] for row in main[:9]] == [
        "C0", "C5", "C10", "C5", "C10", "C0", "C10", "C0", "C5"
    ]
    assert all(row[2] == 0 for row in aux_21 + aux_22 + main)


def test_closed_gate_rejects_before_root_or_request(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import oos_v12_training as campaign

    monkeypatch.setattr(campaign, "MARKET_EXECUTION_ENABLED", False)
    monkeypatch.setattr(campaign, "REGISTRATION_SHA256", None)
    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        campaign.require_campaign()
    assert list(tmp_path.iterdir()) == []


def test_nightly_selector_skips_complete_and_rejects_partial(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import oos_v12_launch as launch
    from btc_risk_rl.pilots import oos_v12_training as campaign
    from btc_risk_rl.pilots.p2_budget import state_hash

    roots = {name: tmp_path / value for name, value in zip(
        campaign.PROFILES,
        ("oos-v12-training-wf-2021-01", "oos-v12-training-wf-2022-01",
         "oos-v12-training-main-01"), strict=True)}
    monkeypatch.setattr(campaign, "CAMPAIGNS", roots)
    monkeypatch.setattr(launch, "CAMPAIGNS", roots)

    def ledger(profile, status, cursor, units, pending=None):
        root = roots[profile]
        root.mkdir(exist_ok=True)
        row = dict(status=status, cursor=cursor, units=[{}] * units,
                   pending=pending, days={}, previous_hash=None)
        row["state_hash"] = state_hash(row)
        (root / "ledger.jsonl").write_text(json.dumps(row) + "\n")

    ledger("wf-2021", "completed", 9, 99)
    assert launch.select_next_profile(roots, now=1794391200) == "wf-2022"
    ledger("wf-2022", "ready", 0, 0)
    assert launch.select_next_profile(roots, now=1794391200) == "wf-2022"
    ledger("wf-2022", "running", 0, 0, {"unit": 0})
    with pytest.raises(ValueError, match="not resumable"):
        launch.select_next_profile(roots, now=1794391200)


def test_nightly_selector_recognizes_pinned_legacy_completion_without_replay(tmp_path):
    from btc_risk_rl.pilots import oos_v12_launch as launch
    from btc_risk_rl.pilots import oos_v12_training as campaign
    from btc_risk_rl.pilots.p2_budget import state_hash

    roots = {profile: tmp_path / "artifacts" / campaign.CAMPAIGNS[profile].name
             for profile in campaign.PROFILES}
    legacy = tmp_path / "artifacts/artifacts/oos-v12-training-wf-2021-01"
    legacy.mkdir(parents=True)
    checkpoint = legacy / "run-08-C5-b0/checkpoint-10/state.pt"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"complete synthetic checkpoint")
    units = [{} for _ in range(98)] + [{
        "checkpoint": str(checkpoint.parent),
        "checkpoint_sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
    }]
    state = dict(status="completed", cursor=9, units=units, pending=None,
                 days={}, previous_hash=None)
    state["state_hash"] = state_hash(state)
    ledger = legacy / "ledger.jsonl"
    ledger.write_text(json.dumps(state) + "\n")
    entry = {"wf-2021": {
        "root": legacy,
        "ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
        "last_checkpoint_sha256": units[-1]["checkpoint_sha256"],
    }}

    assert not roots["wf-2021"].exists()
    assert launch.select_next_profile(roots, legacy_completed=entry,
                                      now=1794391200) == "wf-2022"
    assert not roots["wf-2021"].exists()
    ledger.write_text(ledger.read_text() + " ")
    with pytest.raises(ValueError, match="legacy.*hash"):
        launch.select_next_profile(roots, legacy_completed=entry,
                                   now=1794391200)


def test_nightly_selector_rejects_false_completed_ledger(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import oos_v12_launch as launch
    from btc_risk_rl.pilots import oos_v12_training as campaign
    from btc_risk_rl.pilots.p2_budget import state_hash

    roots = {name: tmp_path / value for name, value in zip(
        campaign.PROFILES,
        ("oos-v12-training-wf-2021-01", "oos-v12-training-wf-2022-01",
         "oos-v12-training-main-01"), strict=True)}
    monkeypatch.setattr(launch, "CAMPAIGNS", roots)
    root = roots["wf-2021"]
    root.mkdir()
    row = dict(status="completed", cursor=9, units=[{}] * 98, pending=None,
               days={}, previous_hash=None)
    row["state_hash"] = state_hash(row)
    (root / "ledger.jsonl").write_text(json.dumps(row) + "\n")
    with pytest.raises(ValueError, match="completed count"):
        launch.select_next_profile(roots, now=1794391200)


def test_nightly_selector_rejects_orphan_root(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import oos_v12_launch as launch
    from btc_risk_rl.pilots import oos_v12_training as campaign

    roots = {name: tmp_path / value for name, value in zip(
        campaign.PROFILES,
        ("oos-v12-training-wf-2021-01", "oos-v12-training-wf-2022-01",
         "oos-v12-training-main-01"), strict=True)}
    monkeypatch.setattr(launch, "CAMPAIGNS", roots)
    roots["wf-2021"].mkdir()
    with pytest.raises(ValueError, match="root exists without"):
        launch.select_next_profile(roots, now=1794391200)


def test_nightly_runner_advances_only_after_complete_profile(monkeypatch):
    from btc_risk_rl.pilots import oos_v12_launch as launch

    chosen = iter(("wf-2021", "wf-2022"))
    calls = []
    monkeypatch.setattr(launch, "require_campaign", lambda: None)
    monkeypatch.setattr(launch, "window_admissible", lambda _epoch: True)
    monkeypatch.setattr(launch, "select_next_profile", lambda: next(chosen))

    def run(profile):
        calls.append(profile)
        return {"status": "completed" if profile == "wf-2021" else "ready",
                "pending": None}

    monkeypatch.setattr(launch, "prepare_and_run", run)
    assert launch.run_nightly() == "paused_at_complete_boundary"
    assert calls == ["wf-2021", "wf-2022"]


def test_oos_service_context_is_exactly_allowlisted():
    from btc_risk_rl.pilots.p2r import check_service_context

    prefix = "/user.slice/user-1000.slice/user@1000.service/app.slice/"
    assert check_service_context(invocation_id="synthetic-id",
                                 cgroup=prefix + "oos-v12-training.service",
                                 linger="yes") == "ready"
    with pytest.raises(ValueError, match="requires a systemd user service"):
        check_service_context(invocation_id="synthetic-id",
                              cgroup=prefix + "oos-v12-training-other.service",
                              linger="yes")


def test_forged_approval_cannot_open_training_gate(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import oos_v12_training as campaign

    fake = tmp_path / "approval.json"
    fake.write_text(json.dumps({"active": True, "scope": "accepted_training_only",
                                "campaign_roots": campaign.frozen_protocol()["campaign_roots"],
                                "freeze_sha256": campaign.FREEZE_SHA256}))
    monkeypatch.setattr(campaign, "APPROVAL", fake)
    monkeypatch.setattr(campaign, "MARKET_EXECUTION_ENABLED", True)
    monkeypatch.setattr(campaign, "REGISTRATION_SHA256", "0" * 64)
    with pytest.raises(PermissionError, match="hash mismatch"):
        campaign.require_campaign()
    monkeypatch.setattr(campaign, "REGISTRATION_SHA256", campaign.digest(fake))
    with pytest.raises(PermissionError, match="identity mismatch"):
        campaign.require_campaign()


def test_new_ledger_reserves_2700_and_rejects_failed(tmp_path):
    from btc_risk_rl.pilots.oos_v12_training import OOSLedger

    identity = {"fixture": True}
    start = datetime(2026, 11, 11, 1, tzinfo=ZoneInfo("America/La_Paz")).timestamp()
    with OOSLedger(tmp_path / "campaign", now=start, identity=identity) as ledger:
        assert ledger.day["hard_deadline"] - ledger.day["work_deadline"] >= 2700
        ledger.fail(start + 1, "synthetic_failure")
    with pytest.raises(ValueError, match="failed/incomplete"):
        OOSLedger(tmp_path / "campaign", now=start + 2, identity=identity)


def test_expanded_window_stops_at_midnight_with_reserve(tmp_path):
    from btc_risk_rl.pilots.oos_v12_training import OOSLedger, window_admissible

    zone = ZoneInfo("America/La_Paz")
    def at(hour, minute):
        return datetime(2026, 11, 11, hour, minute, tzinfo=zone).timestamp()
    assert window_admissible(at(0, 59))
    assert window_admissible(at(1, 0))
    assert window_admissible(at(8, 59))
    assert window_admissible(at(9, 0))
    with OOSLedger(tmp_path / "night", now=at(8, 50), identity={"fixture": True}) as ledger:
        assert ledger.day["hard_deadline"] > at(9, 0)
        assert ledger.day["hard_deadline"] <= at(23, 59) + 60
        assert ledger.day["hard_deadline"] - ledger.day["work_deadline"] >= 2700
        ledger.preflight_done(at(8, 50))
        assert ledger.admit("C0", "q0", at(8, 50)) == "start"


def test_expanded_ledger_charges_external_time_and_pauses_before_midnight(tmp_path):
    from btc_risk_rl.pilots.oos_v12_training import OOSLedger

    zone = ZoneInfo("America/La_Paz")
    morning = datetime(2026, 11, 12, 9, tzinfo=zone).timestamp()
    with OOSLedger(tmp_path / "morning", now=morning, identity={"fixture": True},
                   external_seconds=10800) as ledger:
        assert ledger.day["hard_deadline"] == pytest.approx(morning + 39600)
        ledger.preflight_done(morning)
        assert ledger.day["work_deadline"] <= ledger.day["hard_deadline"] - 2700
    late = datetime(2026, 11, 12, 23, 30, tzinfo=zone).timestamp()
    with OOSLedger(tmp_path / "late", now=late, identity={"fixture": True}) as ledger:
        ledger.preflight_done(late)
        assert ledger.admit("C0", "q0", late) == "pause"


def test_expanded_budget_counts_old_day_conservatively_and_new_work(tmp_path):
    from btc_risk_rl.pilots.oos_v12_budget import inspect_oos_debit
    from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal

    artifacts = tmp_path / "artifacts"
    day = datetime(2026, 11, 11, 1, tzinfo=ZoneInfo("America/La_Paz")).timestamp()
    path = artifacts / "shared-pilot-budget/oos-v12-training-preflight.jsonl"
    with WFCostSessionJournal(path, campaign="oos-v12-training-v1") as journal:
        token = journal.start(now=day, monotonic=0, invocation_id="old")
        journal.end(token, now=day + 6942.163, monotonic=6942.163, status="ready")
        token = journal.start(now=day + 10000, monotonic=10000, invocation_id="new")
        journal.end(token, now=day + 10100, monotonic=10100, status="ready")
    debit = inspect_oos_debit(artifacts, now=day + 10100,
                              prior_day_adjustment_seconds=10800 - 6942.163)
    assert debit["by_day"]["2026-11-11"] == pytest.approx(10900)


def test_twenty_active_days_count_precheck_days_across_campaigns(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import oos_v12_training as training
    from btc_risk_rl.pilots.oos_v12_training import OOSLedger
    from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal

    artifacts = tmp_path / "artifacts"
    path = artifacts / "shared-pilot-budget/oos-v12-training-preflight.jsonl"
    zone = ZoneInfo("America/La_Paz")
    with WFCostSessionJournal(path, campaign="oos-v12-training-v1") as journal:
        for day in range(1, 21):
            epoch = datetime(2026, 11, day, 1, tzinfo=zone).timestamp()
            token = journal.start(now=epoch, monotonic=epoch,
                                  invocation_id=f"fixture-{day}")
            journal.end(token, now=epoch + 10, monotonic=epoch + 10,
                        status="ready")
    now = datetime(2026, 11, 21, 1, tzinfo=zone).timestamp()
    root = artifacts / "oos-v12-training-main-01"
    monkeypatch.setattr(training, "window_admissible", lambda _now: True)
    with pytest.raises(ValueError, match="twenty active days exhausted"):
        OOSLedger(root, now=now, identity={"fixture": True})
    assert json.loads((root / "ledger.jsonl").read_text().splitlines()[-1])[
        "status"] == "incomplete"


def test_frozen_protocol_has_no_evaluation_permission():
    payload = json.loads(Path("docs/protocols/OOS-v1-2-training-freeze-20261110.json").read_text())
    assert payload["status"] == "training_authorized_evaluation_closed"
    assert len(payload["roster"]) == 126
    assert payload["budget"]["daily_closure_reserve_seconds"] == 2700
    assert payload["analysis"]["final_2024_2025"].endswith("currently closed")


def test_settings_and_run_id_are_frozen():
    from btc_risk_rl.pilots.oos_v12_training import OOSSettings, roster, run_id_for

    first = roster("main-2018-2022")[0]
    settings = OOSSettings(seed=first[0])
    assert settings.iterations == 10
    assert settings.critic_epochs == 4
    assert settings.critic_beta == 0
    assert run_id_for("main-2018-2022", 0, first) == "run-00-C0-b0"
    with pytest.raises(ValueError):
        OOSSettings(seed=first[0], critic_epochs=2)
    with pytest.raises(ValueError):
        run_id_for("main-2018-2022", 0, roster("main-2018-2022")[1])


def test_market_permit_rejects_wrong_profile_and_ledger(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import oos_v12_training as campaign

    monkeypatch.setattr(campaign, "require_campaign", lambda: {"fixture": True})
    monkeypatch.setattr(campaign, "CAMPAIGNS", {"main-2018-2022": tmp_path / "main"})
    permit = campaign.OOSPermit("fixture", "main-2018-2022")
    settings = campaign.OOSSettings(seed=campaign.roster("main-2018-2022")[0][0])
    with pytest.raises((PermissionError, OSError)):
        permit.validate(settings, "C0", "run-00-C0-b0")
    with pytest.raises(ValueError):
        campaign.OOSPermit("fixture", "wrong-profile")


def test_public_and_worker_entries_fail_before_market_access(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import oos_v12_training as campaign

    monkeypatch.setattr(campaign, "MARKET_EXECUTION_ENABLED", False)
    monkeypatch.setattr(campaign, "REGISTRATION_SHA256", None)
    monkeypatch.setattr(campaign, "CAMPAIGNS", {"wf-2021": tmp_path / "campaign"})
    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        campaign.run_historical_units("wf-2021")
    from btc_risk_rl.pilots.oos_v12_worker import run_request

    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        run_request("wf-2021", tmp_path / "nonexistent-request.json")
    assert not (tmp_path / "campaign").exists()


def test_direct_worker_entry_cannot_replay_legacy_completed_profile(monkeypatch):
    from btc_risk_rl.pilots import oos_v12_training as campaign

    monkeypatch.setattr(campaign, "require_campaign", lambda: {"fixture": True})
    monkeypatch.setattr(campaign, "source_for",
                        lambda _profile: pytest.fail("historical source was loaded"))
    with pytest.raises(PermissionError, match="legacy completed profile"):
        campaign.run_historical_units("wf-2021")


def _controlled_worker(tmp_path, monkeypatch):
    import torch

    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.agents.synthetic import SyntheticMarket
    from btc_risk_rl.config import load_config
    from btc_risk_rl.pilots import oos_v12_training as campaign
    from btc_risk_rl.pilots.p2_budget import state_hash

    root = tmp_path / "main"
    work = root / "run-00-C0-b0"
    work.mkdir(parents=True)
    monkeypatch.setattr(campaign, "CAMPAIGNS", {"main-2018-2022": root})
    monkeypatch.setattr(campaign, "require_campaign", lambda: {"fixture": True})
    monkeypatch.setattr(campaign.OOSSettings, "__post_init__", lambda self: None)
    original_init = campaign.OOSSettings.__init__
    small = dict(hidden=4, iterations=1, n_a=2, n_q=2, n_b=2,
                 actor_epochs=1, critic_epochs=1, minibatch=1, fragment_steps=180)
    monkeypatch.setattr(campaign.OOSSettings, "__init__",
                        lambda self, **values: original_init(self, **{**small, **values}))
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda _n: None)
    config = load_config(Path("configs/initial.toml"))
    fabricated = SyntheticMarket(config, routes=1)
    source = TrainingMarket.__new__(TrainingMarket)
    source.config = config
    source._view = SimpleNamespace(training_path=fabricated.path)
    source.route_ids = (0,)
    source.audit = {"normalizer_refitted": False,
                    "validation_observations_loaded": False}
    source._identity = {"profile": source.profile, "manifest_sha256": "controlled",
                        "training_shard_manifest_sha256": "controlled", "files": {}}
    monkeypatch.setattr(campaign, "source_for", lambda _profile: source)
    monkeypatch.setattr(campaign.OOSPermit, "validate_d",
                        lambda self, _source, _seed, run_id: self.validate(
                            self.settings, self.condition, run_id))
    seed = campaign.roster("main-2018-2022")[0][0]
    settings = campaign.OOSSettings(seed=seed)
    token = "controlled-lease"
    request = dict(root=str(work), run_id="run-00-C0-b0", condition="C0", unit=0,
                   previous=None, token=token, beta=0,
                   config=str(campaign.ROOT / "configs/initial.toml"),
                   atomic_checkpoint=True, settings=asdict(settings))
    request_path = work / "request-0.json"
    request_path.write_text(json.dumps(request))
    state = dict(status="running", cursor=0,
                 pending=dict(unit=0, run_id="run-00-C0-b0", token=token,
                              request_sha256=hashlib.sha256(request_path.read_bytes()).hexdigest(),
                              supervisor_pid=os.getppid()), runs={})

    def persist():
        state["state_hash"] = state_hash(state)
        (root / "ledger.jsonl").write_text(json.dumps(state) + "\n")

    persist()
    return SimpleNamespace(root=root, work=work, source=source, settings=settings,
                           request=request, request_path=request_path, state=state,
                           persist=persist)


def test_worker_q0_and_iteration_complete_with_controlled_source(tmp_path, monkeypatch):
    from btc_risk_rl.agents.checkpoint import provenance
    from btc_risk_rl.pilots.oos_v12_worker import run_request
    from btc_risk_rl.pilots.p2r_units import _verify_completion

    case = _controlled_worker(tmp_path, monkeypatch)
    run_request("main-2018-2022", case.request_path)
    point = case.work / "checkpoint-0"
    assert json.loads((point / "manifest.json").read_text())["boundary"] == "after_q0"
    assert _verify_completion(case.work, 0, case.settings, "C0", "run-00-C0-b0",
                              {"status": "passed"}, provenance(case.source),
                              diagnostic_n=64)[1] == "after_q0"
    previous_hash = hashlib.sha256((point / "state.pt").read_bytes()).hexdigest()
    case.request.update(unit=1, previous=str(point))
    case.request_path = case.work / "request-1.json"
    case.request_path.write_text(json.dumps(case.request))
    case.state["runs"] = {"run-00-C0-b0": {"checkpoint": str(point)}}
    case.state["pending"].update(unit=1,
                                 request_sha256=hashlib.sha256(case.request_path.read_bytes()).hexdigest())
    case.persist()
    run_request("main-2018-2022", case.request_path)
    final = case.work / "checkpoint-1"
    assert json.loads((final / "manifest.json").read_text())["boundary"] == "after_dual_and_D"
    assert hashlib.sha256((point / "state.pt").read_bytes()).hexdigest() == previous_hash
    report = json.loads((case.work / "unit-1.json").read_text())
    assert report["resources"]["actor_updates"] == 2
    assert report["resources"]["critic_updates"] == 2
    assert _verify_completion(case.work, 1, case.settings, "C0", "run-00-C0-b0",
                              {"status": "passed"}, provenance(case.source),
                              diagnostic_n=64)[1] == "after_dual_and_D"


def test_worker_rejects_forged_request_before_source(tmp_path, monkeypatch):
    from btc_risk_rl.pilots.oos_v12_worker import run_request

    case = _controlled_worker(tmp_path, monkeypatch)
    case.request["condition"] = "C5"
    case.request_path.write_text(json.dumps(case.request))
    with pytest.raises(PermissionError, match="pending unit"):
        run_request("main-2018-2022", case.request_path)
    assert not (case.work / "checkpoint-0").exists()


def _run_controlled_child(profile, request, pid_path):
    from btc_risk_rl.pilots.oos_v12_worker import run_request

    pid_path.write_text(str(os.getpid()))
    run_request(profile, request)


def test_q0_and_iteration_resume_in_distinct_processes(tmp_path, monkeypatch):
    case = _controlled_worker(tmp_path, monkeypatch)
    case.state["pending"]["supervisor_pid"] = os.getpid()
    case.persist()
    context = multiprocessing.get_context("fork")
    for unit in (0, 1):
        if unit:
            first = case.work / "checkpoint-0"
            case.request.update(unit=1, previous=str(first))
            case.request_path = case.work / "request-1.json"
            case.request_path.write_text(json.dumps(case.request))
            case.state["runs"] = {"run-00-C0-b0": {"checkpoint": str(first)}}
            case.state["pending"].update(
                unit=1, request_sha256=hashlib.sha256(case.request_path.read_bytes()).hexdigest())
            case.persist()
        child = context.Process(target=_run_controlled_child,
                                args=("main-2018-2022", case.request_path,
                                      case.work / f"pid-{unit}.txt"))
        child.start()
        child.join(30)
        assert child.exitcode == 0
    assert (case.work / "pid-0.txt").read_text() != (case.work / "pid-1.txt").read_text()
    assert json.loads((case.work / "checkpoint-1/manifest.json").read_text())[
        "boundary"] == "after_dual_and_D"


def test_precheck_and_ledger_intervals_merge_without_duplicate(tmp_path):
    from btc_risk_rl.pilots.oos_v12_budget import inspect_oos_debit
    from btc_risk_rl.pilots.p2_budget import state_hash
    from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal

    artifacts = tmp_path / "artifacts"
    root = artifacts / "oos-v12-training-wf-2021-01"
    root.mkdir(parents=True)
    day = datetime(2026, 11, 11, 1, 0, tzinfo=ZoneInfo("America/La_Paz")).timestamp()
    ledger = {"status": "ready", "days": {"2026-11-11": {
        "started_utc_epoch": day + 50, "charged_wall_seconds": 100}},
        "previous_hash": None}
    ledger["state_hash"] = state_hash(ledger)
    (root / "ledger.jsonl").write_text(json.dumps(ledger) + "\n")
    journal_path = artifacts / "shared-pilot-budget/oos-v12-training-preflight.jsonl"
    with WFCostSessionJournal(journal_path, campaign="oos-v12-training-v1") as journal:
        token = journal.start(now=day, monotonic=0, invocation_id="fixture")
        journal.end(token, now=day + 70, monotonic=70, status="ready")
    debit = inspect_oos_debit(artifacts, now=day + 150)
    assert debit["by_day"]["2026-11-11"] == 150
    assert not debit["blocked"]


def test_open_precheck_blocks_reentry_and_charges_conservatively(tmp_path):
    from btc_risk_rl.pilots.oos_v12_budget import inspect_oos_debit
    from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal

    artifacts = tmp_path / "artifacts"
    day = datetime(2026, 11, 11, 1, 0, tzinfo=ZoneInfo("America/La_Paz")).timestamp()
    journal_path = artifacts / "shared-pilot-budget/oos-v12-training-preflight.jsonl"
    with WFCostSessionJournal(journal_path, campaign="oos-v12-training-v1") as journal:
        journal.start(now=day, monotonic=0, invocation_id="fixture")
    debit = inspect_oos_debit(artifacts, now=day + 60)
    assert debit["blocked"]
    assert debit["by_day"]["2026-11-11"] == 50400


@pytest.mark.parametrize("campaign_name", (
    "oos-v12-training-wf-2021-01",
    "oos-v12-training-wf-2022-01",
    "oos-v12-training-main-01",
))
def test_shared_budget_debits_oos_precheck_and_ledger_once(tmp_path, campaign_name):
    from btc_risk_rl.pilots.p2_budget import state_hash
    from btc_risk_rl.pilots.p2r import P2RSharedBudget
    from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal

    artifacts = tmp_path / "artifacts"
    root = artifacts / campaign_name
    root.mkdir(parents=True)
    day = datetime(2026, 11, 11, 1, 0, tzinfo=ZoneInfo("America/La_Paz")).timestamp()
    ledger = {"status": "ready", "days": {"2026-11-11": {
        "started_utc_epoch": day + 50, "charged_wall_seconds": 100}}, "previous_hash": None}
    ledger["state_hash"] = state_hash(ledger)
    (root / "ledger.jsonl").write_text(json.dumps(ledger) + "\n")
    path = artifacts / "shared-pilot-budget/oos-v12-training-preflight.jsonl"
    with WFCostSessionJournal(path, campaign="oos-v12-training-v1") as journal:
        token = journal.start(now=day, monotonic=0, invocation_id="fixture")
        journal.end(token, now=day + 70, monotonic=70, status="ready")
    with P2RSharedBudget(artifacts, "another-campaign", now=day + 150) as shared:
        assert shared.external_seconds == 150
    with P2RSharedBudget(artifacts, root.name, now=day + 150) as shared:
        assert shared.external_seconds == 50


def test_precheck_budget_counts_own_existing_ledger(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import oos_v12_training as campaign
    from btc_risk_rl.pilots import wf_cost
    from btc_risk_rl.pilots.p2_budget import state_hash

    artifacts = tmp_path / "artifacts"
    root = artifacts / "oos-v12-training-wf-2021-01"
    root.mkdir(parents=True)
    day = datetime(2026, 11, 11, 1, 0, tzinfo=ZoneInfo("America/La_Paz")).timestamp()
    ledger = {"status": "ready", "days": {"2026-11-11": {
        "started_utc_epoch": day, "charged_wall_seconds": 600}},
        "previous_hash": None}
    ledger["state_hash"] = state_hash(ledger)
    (root / "ledger.jsonl").write_text(json.dumps(ledger) + "\n")
    monkeypatch.setattr(wf_cost, "ROOT", tmp_path)
    budget = campaign.read_budget("wf-2021", now=day + 600)
    assert budget["global_spent"] == 600
    assert budget["remaining_before_reserve"] == 50400 - 600 - 2700


def test_preflight_rejects_low_memory_without_trajectories(monkeypatch):
    from btc_risk_rl.pilots import oos_v12_training as campaign

    monkeypatch.setattr(campaign, "require_campaign", lambda: {"fixture": True})
    monkeypatch.setattr(campaign, "source_for", lambda _profile: SimpleNamespace(
        route_ids=tuple(range(3639)),
        audit={"validation_observations_loaded": False, "normalizer_refitted": False},
        identity=lambda: {"profile": "accepted_train_collection_only", "fold": "2021"},
    ))
    monkeypatch.setattr(campaign, "read_host", lambda: {
        "power": {"ac": True, "battery_percent": 100},
        "memory_available_bytes": 4 * 1024**3,
        "disk_free_bytes": 100 * 1024**3,
        "user_manager": "running", "linger": "yes",
    })
    monkeypatch.setattr(campaign, "read_budget", lambda *_args, **_kwargs: {
        "ok": True, "remaining_before_reserve": 8100,
    })
    result = campaign.inspect_preflight("wf-2021")
    assert result["status"] == "blocked"
    assert "memory" in " ".join(result["blockers"]).lower()
    assert result["trajectories_generated"] == 0


def test_watched_preflight_refuses_protected_files(tmp_path):
    from btc_risk_rl.pilots.oos_v12_training import watch_open

    root = tmp_path / "repo"
    train = root / "data/processed/p2r-training-h1"
    opened = []
    watch_open("open", (str(train / "bars.csv"),), opened, root=root, training_shard=train)
    assert opened == ["data/processed/p2r-training-h1/bars.csv"]
    with pytest.raises(PermissionError):
        watch_open("open", (str(root / "data/processed/segmented-B-h1/features.csv"),),
                   opened, root=root, training_shard=train)
    with pytest.raises(PermissionError):
        watch_open("open", (str(root / "data/validation-2023.csv"),),
                   opened, root=root, training_shard=train)


def test_precheck_journal_starts_before_a_check_and_closes(tmp_path):
    from btc_risk_rl.pilots.oos_v12_launch import OOSPrecheckAttempt

    artifacts = tmp_path / "artifacts"
    seen = []
    with OOSPrecheckAttempt(artifacts, gate=lambda: None) as attempt:
        def check():
            assert attempt.journal_path.exists()
            seen.append("inside")
            return "ready"

        assert attempt.run_check("fixture", check) == "ready"
    assert seen == ["inside"]
    rows = [json.loads(x) for x in attempt.journal_path.read_text().splitlines()]
    assert [row["event"] for row in rows] == ["start", "end"]
    assert rows[-1]["status"] == "ready"


def test_precheck_session_covers_source_loading_and_supervision(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import oos_v12_launch as launch
    from btc_risk_rl.pilots.oos_v12_budget import inspect_oos_debit
    from btc_risk_rl.pilots.p2r import P2RSharedBudget

    start = datetime(2026, 11, 11, 1, tzinfo=ZoneInfo("America/La_Paz")).timestamp()
    clock = [start]
    monkeypatch.setattr(launch, "ROOT", tmp_path)
    monkeypatch.setattr(launch, "select_next_profile", lambda: "wf-2021")
    monkeypatch.setattr(launch.time, "time", lambda: clock[0])
    monkeypatch.setattr(launch, "require_campaign", lambda: {})
    monkeypatch.setattr(launch, "window_admissible", lambda _epoch: True)
    monkeypatch.setattr(launch, "read_budget", lambda *_args, **_kwargs: {
        "ok": True, "remaining_before_reserve": 8100})
    monkeypatch.setenv("INVOCATION_ID", "fixture-invocation")

    def command(args, **_kwargs):
        if args[1].endswith("audit_oos_v12_training_preflight.py"):
            return {"stdout": json.dumps({"status": "ready",
                                          "protected_or_shared_csv_opened": False}),
                    "stderr": ""}
        return {"stdout": "ready", "stderr": ""}

    monkeypatch.setattr(launch, "_checked_command", command)

    def supervised(_profile):
        assert os.environ["OOS_PREP_TOKEN"]
        clock[0] += 120  # synthetic source loading before the unit ledger exists
        artifacts = tmp_path / "artifacts"
        debit = inspect_oos_debit(artifacts, now=clock[0],
                                  active_prep_token=os.environ["OOS_PREP_TOKEN"])
        assert debit["by_day"]["2026-11-11"] == 120
        assert not debit["blocked"]
        with P2RSharedBudget(artifacts, "oos-v12-training-wf-2021-01",
                             now=clock[0]) as shared:
            assert shared.external_seconds == 120
        return {"status": "ready"}

    monkeypatch.setattr(launch, "run_historical_units", supervised)
    assert launch.prepare_and_run("wf-2021")["status"] == "ready"
    journal = tmp_path / "artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl"
    rows = [json.loads(line) for line in journal.read_text().splitlines()]
    assert rows[-1]["status"] == "ready"
    assert rows[-1]["wall_seconds"] == 120


def test_precheck_reentry_requires_same_invocation_and_chain(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import oos_v12_launch as launch

    monkeypatch.setattr(launch, "ROOT", tmp_path)
    monkeypatch.setenv("INVOCATION_ID", "fixture-invocation")
    with launch.OOSPrecheckAttempt(tmp_path / "artifacts", gate=lambda: None) as attempt:
        for name in ("suite", "ruff", "wf-2021"):
            attempt.run_check(name, lambda: "ready")
    launch.require_recent_prepare("wf-2021")
    monkeypatch.setenv("INVOCATION_ID", "forged-invocation")
    with pytest.raises(PermissionError, match="invalid or stale"):
        launch.require_recent_prepare("wf-2021")
    monkeypatch.setenv("INVOCATION_ID", "fixture-invocation")
    path = tmp_path / "artifacts/shared-pilot-budget/oos-v12-training-checks.jsonl"
    rows = path.read_text().splitlines()
    rows[-1] = rows[-1].replace('"ready"', '"failed"')
    path.write_text("\n".join(rows) + "\n")
    with pytest.raises(PermissionError, match="chain invalid"):
        launch.require_recent_prepare("wf-2021")
