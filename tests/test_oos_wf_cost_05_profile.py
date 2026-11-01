"""Synthetic-only checks for the prospectively closed fifth WF profile."""

import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

import pytest
import torch

from btc_risk_rl.pilots.p2r import P2RJournal


def _hashes(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*")) if path.is_file()}


def test_fifth_profile_preserves_science_and_historical_roots():
    from btc_risk_rl.pilots import wf_cost_replacement_05_exec as profile
    from btc_risk_rl.pilots.wf_cost_replacement_05 import inspect_candidate
    from btc_risk_rl.pilots.wf_permits import authorized_wf_permits

    assert profile.CAMPAIGN.name == "oos-v12-wf-cost-only-05"
    assert profile.REGISTRATION.name == "OOS-v1-2-wf-cost-05-approval.json"
    assert not profile.CAMPAIGN.exists() and not profile.REGISTRATION.exists()
    assert profile.MARKET_EXECUTION_ENABLED is False
    assert profile.REGISTRATION_SHA256 is None
    assert authorized_wf_permits()[profile.WFCostPermit] == profile.CAMPAIGN
    assert profile.roster() == (("2021", 276696733, "C10"),
                                ("2022", 498614892, "C10"))
    assert len(profile.units()) == 22
    assert sum(profile.unit_cap(unit) for _, unit in profile.units()) == 3840
    result = inspect_candidate()
    assert result["historical_artifacts_verified"]
    assert result["root_absent"] and result["approval_absent"]
    assert result["historical_roots"]["04"]["files"] == 1860


def test_fifth_public_and_worker_gates_reject_before_root():
    from btc_risk_rl.pilots import wf_cost_replacement_05_exec as profile

    roots_before = [_hashes(Path("artifacts") / f"oos-v12-wf-cost-only-{n:02d}")
                    for n in range(1, 5)]
    for command in (
        [sys.executable, "scripts/run_oos_wf_cost_05.py", "--run"],
        [sys.executable, "-m", "btc_risk_rl.pilots.wf_cost_replacement_05_worker",
         "/tmp/nonexistent-wf05-request.json"],
    ):
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        assert result.returncode != 0
        assert "NOT AUTHORIZED" in result.stderr
    assert not profile.CAMPAIGN.exists()
    assert roots_before == [_hashes(Path("artifacts") / f"oos-v12-wf-cost-only-{n:02d}")
                            for n in range(1, 5)]


def test_fifth_first_start_and_orphan_rejection_with_real_supervisor(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import wf_cost_replacement_05_units as units
    from btc_risk_rl.pilots.wf_cost import WFCostLedger

    root = tmp_path / "oos-v12-wf-cost-only-05"
    monkeypatch.setattr(units, "CAMPAIGN", root)
    monkeypatch.setattr(units, "require_campaign", lambda: {"synthetic_only": True})
    monkeypatch.setattr(units, "_launch_readiness", lambda: ({"ok": True}, {"ok": True}))

    class Shared:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    monkeypatch.setattr(units, "P2RSharedBudget", Shared)

    def synthetic_q0(_inputs, _budget, _shared, sessions, token):
        with WFCostLedger(root, now=time.time(),
                          identity={"profile": "wf05_fixture", "roster": units.roster()},
                          session_journal=sessions, session_token=token) as ledger:
            ledger.preflight_done(time.time())
            assert ledger.admit_unit("2021", 0, time.time()) == "start"
            ledger.begin_unit("2021", 0, time.time())
            checkpoint = root / "wf-2021/checkpoint-0"
            checkpoint.mkdir(parents=True)
            (checkpoint / "state.pt").write_bytes(b"synthetic-checkpoint")
            (checkpoint / "manifest.json").write_text(json.dumps({
                "schema_version": "p2_complete_boundary_v1", "boundary": "after_q0",
                "profile": "wf_cost_only", "run_id": "wf-2021", "condition": "C10",
                "state_sha256": hashlib.sha256(b"synthetic-checkpoint").hexdigest(),
            }))
            ledger.accept_unit("2021", 0, time.time(), checkpoint,
                               report={"boundary": "after_q0", "actor_updates": 0,
                                       "critic_updates": 0, "market_training_executed": False},
                               resources={"actor_updates": 0, "critic_updates": 0})
            return ledger.state

    monkeypatch.setattr(units, "_run_locked_session", synthetic_q0)
    assert units.run_units()["status"] == "ready"
    assert (root / "sessions.jsonl").is_file()
    assert (root / "ledger.jsonl").is_file()
    assert (root / "wf-2021/checkpoint-0/state.pt").read_bytes() == b"synthetic-checkpoint"
    with WFCostLedger(root, now=time.time(),
                      identity={"profile": "wf05_fixture", "roster": units.roster()}) as ledger:
        ledger.preflight_done(time.time())
        assert ledger.state["pending"] is None
        assert ledger.admit_unit("2021", 1, time.time()) == "start"
    orphan = tmp_path / "orphan"
    orphan.mkdir()
    monkeypatch.setattr(units, "CAMPAIGN", orphan)
    with pytest.raises(ValueError, match="root exists without a valid ledger"):
        units.run_units()
    assert not (orphan / "sessions.jsonl").exists()


def test_fifth_watched_preflight_opens_no_protected_rows():
    result = subprocess.run(
        [sys.executable, "-m", "scripts.audit_oos_wf_cost_05_preflight"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["preflight"]["status"] == "blocked"
    assert payload["preflight"]["market_execution_enabled"] is False
    assert payload["protected_or_shared_csv_opened"] is False
    assert payload["market_trajectories_generated"] == 0
    assert payload["optimizer_steps"] == 0


@pytest.mark.parametrize(("change", "failed"), [
    ({"power": {"ac": False, "battery_percent": 50}}, "ac"),
    ({"power": {"ac": True, "battery_percent": 49}}, "battery"),
    ({"memory_available_bytes": 4 * 1024**3 - 1}, "memory"),
    ({"disk_free_bytes": 20 * 1024**3 - 1}, "disk"),
])
def test_fifth_supervisor_records_failed_resource_snapshot(tmp_path, change, failed):
    from btc_risk_rl.pilots.wf_cost_replacement_05_units import observe_resource_guard

    observed = {"power": {"ac": True, "battery_percent": 50},
                "memory_available_bytes": 4 * 1024**3,
                "disk_free_bytes": 20 * 1024**3} | change
    journal_path = tmp_path / "supervisor.jsonl"
    journal = P2RJournal(journal_path, campaign="wf05-synthetic")
    assert not observe_resource_guard(journal, observed, run_id="synthetic", unit=1,
                                      phase="Q", disposition="fail")
    record = json.loads(journal_path.read_text().splitlines()[-1])
    assert record["resource_snapshot"] == observed
    assert record["failed_checks"] == [failed]


def test_05_q0_and_unit_one_in_distinct_workers_with_ledger_reentry(tmp_path):
    from wf05_process_fixture import controlled_source, small_settings

    from btc_risk_rl.agents.checkpoint import provenance
    from btc_risk_rl.pilots.p2_budget import state_hash
    from btc_risk_rl.pilots.p2r_units import _verify_completion
    from btc_risk_rl.pilots.wf_cost import WFCostLedger, digest, roster

    root = tmp_path / "oos-v12-wf-cost-only-05"
    work = root / "wf-2021"
    source = controlled_source()
    settings = small_settings()
    manifest = root / "folds/wf-2021/manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"source_identity": source.identity()}))
    identity = {"profile": "wf_cost_05_synthetic_test_only", "roster": roster(),
                "source": {"2021": source.identity()}}

    def worker(unit, prior, ledger):
        token = f"synthetic-token-{unit}"
        request = dict(root=str(work), fold="2021", settings=asdict(settings),
                       config=str(Path("configs/initial.toml").resolve()),
                       run_id="wf-2021", condition="C10", unit=unit,
                       previous=prior, token=token, atomic_checkpoint=True)
        work.mkdir(exist_ok=True)
        request_path = work / f"request-{unit}.json"
        request_path.write_text(json.dumps(request))
        started = time.time()
        ledger.begin_unit("2021", unit, started)
        ledger.state["pending"].update(token=token, supervisor_pid=os.getpid(),
                                       request_sha256=digest(request_path))
        ledger.persist(time.time())
        child = subprocess.run(
            [sys.executable, "tests/wf05_process_fixture.py", str(root),
             str(request_path)], capture_output=True, text=True, check=False,
        )
        assert child.returncode == 0, child.stderr
        worker_pid = int(child.stdout.strip())
        point = work / f"checkpoint-{unit}"
        payload = json.loads((work / f"unit-{unit}.json").read_text())
        assert payload["checkpoint_sha256"] == digest(point / "state.pt")
        assert _verify_completion(work, unit, settings, "C10", "wf-2021",
                                  {"status": "passed"}, provenance(source),
                                  diagnostic_n=64)[1] == (
                                      "after_q0" if unit == 0 else "after_dual_and_D")
        ledger.accept_unit("2021", unit, time.time(), point,
                           report=payload["report"], resources=payload["resources"])
        return worker_pid, point, payload

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    now = time.time()
    with WFCostLedger(root, identity=identity, now=now) as first:
        first.preflight_done(time.time())
        assert first.admit_unit("2021", 0, time.time()) == "start"
        pid_q0, q0, q0_payload = worker(0, None, first)
        assert first.state["status"] == "ready"
        assert first.state["pending"] is None and len(first.state["units"]) == 1
        assert q0_payload["resources"]["actor_updates"] == 0
    q0_sha = digest(q0 / "state.pt")

    with WFCostLedger(root, identity=identity, now=time.time()) as second:
        second.preflight_done(time.time())
        assert second.state["runs"]["wf-2021"]["checkpoint"] == str(q0)
        assert second.admit_unit("2021", 1, time.time()) == "start"
        pid_one, one, payload = worker(1, str(q0), second)
        assert second.state["status"] == "ready"
        assert second.state["pending"] is None and len(second.state["units"]) == 2
        assert second.state["runs"]["wf-2021"]["checkpoint"] == str(one)
    assert pid_q0 != pid_one
    assert digest(q0 / "state.pt") == q0_sha
    assert payload["resources"]["actor_updates"] == 8
    assert payload["resources"]["critic_updates"] == 16
    rows = [json.loads(line) for line in (root / "ledger.jsonl").read_text().splitlines()]
    assert all(row["state_hash"] == state_hash(row) for row in rows)
    assert all(row["previous_hash"] == rows[i - 1]["state_hash"]
               for i, row in enumerate(rows) if i)
    assert rows[-1]["status"] == "ready" and rows[-1]["pending"] is None
    assert [entry["unit"] for entry in rows[-1]["units"]] == [0, 1]
    assert hashlib.sha256((one / "state.pt").read_bytes()).hexdigest() == payload["checkpoint_sha256"]
