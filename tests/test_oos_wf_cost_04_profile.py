"""Synthetic-only checks for the closed fourth WF cost profile."""

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


def _root_hashes(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*")) if path.is_file()}


def test_04_identity_and_registered_gate():
    from btc_risk_rl.pilots import wf_cost_replacement_04_exec as profile
    from btc_risk_rl.pilots.wf_cost_replacement_04 import inspect_candidate
    from btc_risk_rl.pilots.wf_permits import authorized_wf_permits

    assert profile.CAMPAIGN.name == "oos-v12-wf-cost-only-04"
    assert profile.REGISTRATION.name == "OOS-v1-2-wf-cost-04-approval.json"
    assert profile.REGISTRATION.exists()
    assert profile.MARKET_EXECUTION_ENABLED is True
    assert profile.REGISTRATION_SHA256 == profile.digest(profile.REGISTRATION)
    approval = json.loads(profile.REGISTRATION.read_text())
    assert approval["approved_base_commit"] == "ce62fed"
    assert approval["campaign"] == profile.CAMPAIGN.name
    assert approval["code_sha256"] == profile.code_sha256()
    assert approval["not_before_day_la_paz"] == "2026-10-30"
    assert approval["stop_after_first_accepted_q0"] is True
    assert authorized_wf_permits()[profile.WFCostPermit] == profile.CAMPAIGN
    assert profile.roster() == (("2021", 276696733, "C10"),
                                ("2022", 498614892, "C10"))
    assert len(profile.units()) == 22
    assert sum(profile.unit_cap(unit) for _, unit in profile.units()) == 3840
    candidate = inspect_candidate()
    assert candidate["historical_artifacts_verified"]
    assert candidate["failed_03_pending"]
    assert candidate["root_absent"] is (not profile.CAMPAIGN.exists())
    assert not candidate["approval_absent"]


def test_04_public_and_worker_commands_reject_closed_gate_before_root():
    from btc_risk_rl.pilots import wf_cost_replacement_04_exec as profile

    before = _root_hashes(profile.CAMPAIGN)
    for command in (
        [sys.executable, "-c", "import sys; from btc_risk_rl.pilots import "
         "wf_cost_replacement_04_exec as p; p.MARKET_EXECUTION_ENABLED=False; "
         "from scripts.run_oos_wf_cost_04 import main; "
         "sys.argv=['run','--run']; main()"],
        [sys.executable, "-c", "import sys; from btc_risk_rl.pilots import "
         "wf_cost_replacement_04_exec as p; p.MARKET_EXECUTION_ENABLED=False; "
         "from btc_risk_rl.pilots.wf_cost_replacement_04_worker import main; "
         "sys.argv=['worker','/tmp/nonexistent-wf04-request.json']; main()"],
    ):
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        assert result.returncode != 0
        assert "NOT AUTHORIZED" in result.stderr
    assert _root_hashes(profile.CAMPAIGN) == before


def test_04_registration_and_day_guards_reject_forgery(monkeypatch):
    from btc_risk_rl.pilots import wf_cost_replacement_04_exec as profile

    before = _root_hashes(profile.CAMPAIGN)
    monkeypatch.setattr(profile, "_local_day", lambda: "2026-10-29")
    with pytest.raises(PermissionError, match="before authorized day"):
        profile.require_campaign()
    monkeypatch.setattr(profile, "_local_day", lambda: "2026-10-30")
    assert profile.require_campaign()["campaign"] == profile.CAMPAIGN.name
    monkeypatch.setattr(profile, "REGISTRATION_SHA256", "0" * 64)
    with pytest.raises(PermissionError, match="hash mismatch"):
        profile.require_campaign()
    assert _root_hashes(profile.CAMPAIGN) == before


def test_04_watched_preflight_never_opens_protected_rows():
    from btc_risk_rl.pilots import wf_cost_replacement_04_exec as profile

    result = subprocess.run(
        [sys.executable, "-m", "scripts.audit_oos_wf_cost_04_preflight"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["preflight"]["status"] == (
        "blocked" if payload["preflight"]["blockers"] else "ready")
    assert payload["preflight"]["market_execution_enabled"] is True
    assert payload["preflight"]["root_exists"] is profile.CAMPAIGN.exists()
    assert payload["protected_or_shared_csv_opened"] is False
    assert payload["market_trajectories_generated"] == 0
    assert payload["optimizer_steps"] == 0


def test_04_q0_and_unit_one_in_distinct_workers_with_ledger_reentry(tmp_path):
    from wf04_process_fixture import controlled_source, small_settings

    from btc_risk_rl.agents.checkpoint import provenance
    from btc_risk_rl.pilots.p2_budget import state_hash
    from btc_risk_rl.pilots.p2r_units import _verify_completion
    from btc_risk_rl.pilots.wf_cost import WFCostLedger, digest, roster

    root = tmp_path / "oos-v12-wf-cost-only-04"
    work = root / "wf-2021"
    source = controlled_source()
    settings = small_settings()
    manifest = root / "folds/wf-2021/manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"source_identity": source.identity()}))
    identity = {"profile": "wf_cost_04_synthetic_test_only", "roster": roster(),
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
            [sys.executable, "tests/wf04_process_fixture.py", str(root),
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
