"""P3 training-only entry/lease guards; no historical optimization here."""

import json
import os
import subprocess
import sys

import pytest

from btc_risk_rl.pilots import p3_market
from btc_risk_rl.pilots.p2_budget import state_hash


def test_public_and_worker_commands_fail_before_loading_or_creating_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(p3_market, "CAMPAIGN", tmp_path / "p3-approved-v1")
    monkeypatch.setattr(p3_market, "TrainingMarket", lambda *_a, **_k: pytest.fail("market loaded"), raising=False)
    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        p3_market.run_market_units()
    assert not p3_market.CAMPAIGN.exists()
    for command in ([sys.executable, "scripts/run_p3_market.py"],
                    [sys.executable, "-m", "btc_risk_rl.pilots.p3_worker", str(tmp_path / "forged.json")]):
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        assert result.returncode != 0 and "NOT AUTHORIZED" in result.stderr
    assert not p3_market.CAMPAIGN.exists()


def test_editing_approval_json_cannot_activate_p3(tmp_path, monkeypatch):
    forged = tmp_path / "P3-market-approval.json"
    forged.write_text(json.dumps(dict(active=True, scope="accepted_training_2018_2022_only")))
    monkeypatch.setattr(p3_market, "REGISTRATION", forged)
    with pytest.raises(PermissionError, match="NOT AUTHORIZED"):
        p3_market.P3MarketPermit.require_campaign()


def test_market_lease_binds_seed_condition_beta_pending_hash_and_parent(tmp_path, monkeypatch):
    campaign = tmp_path / "p3-approved-v1"
    run_root = campaign / "run-00-C0-b0"
    run_root.mkdir(parents=True)
    monkeypatch.setattr(p3_market, "CAMPAIGN", campaign)
    monkeypatch.setattr(p3_market.P3MarketPermit, "require_campaign", lambda *_: {})
    settings = p3_market.P3MarketSettings(seed=710031, critic_beta=0)
    request = dict(root=str(run_root), run_id="run-00-C0-b0", condition="C0",
                   beta=0, unit=0, previous=None, atomic_checkpoint=True,
                   config=str(p3_market.CONFIG), settings=__import__("dataclasses").asdict(settings),
                   token="token")
    path = run_root / "request-0.json"
    path.write_text(json.dumps(request))
    state = dict(status="running", cursor=0, pending=dict(
        unit=0, run_id=request["run_id"], token="token", supervisor_pid=os.getppid(),
        request_sha256=p3_market.digest(path)), runs={})
    state["state_hash"] = state_hash(state)
    (campaign / "ledger.jsonl").write_text(json.dumps(state) + "\n")
    permit = p3_market.P3MarketPermit("token")
    permit.validate(settings, "C0", request["run_id"])
    permit.validate_request(path, request)
    wrong = request | {"beta": 1}
    with pytest.raises(PermissionError, match="request"):
        permit.validate_request(path, wrong)
    with pytest.raises(PermissionError, match="lease"):
        permit.validate(p3_market.P3MarketSettings(seed=710031, critic_beta=1),
                        "C0", request["run_id"])


def test_preflight_rejects_protocol_tamper_before_source_load(monkeypatch):
    monkeypatch.setitem(p3_market.ANCHORS, p3_market.PROTOCOL, "0" * 64)
    monkeypatch.setattr(p3_market, "TrainingMarket", lambda *_a, **_k: pytest.fail("market loaded"), raising=False)
    with pytest.raises(ValueError, match="frozen input changed"):
        p3_market.inspect_preflight()


def test_p3_market_unit_requires_lease_before_any_output(tmp_path):
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.pilots.p2_runner import complete_unit

    # This object has no data and cannot generate a route; type gate runs first.
    source = object.__new__(TrainingMarket)
    output = tmp_path / "blocked"
    with pytest.raises(PermissionError, match="registered lease"):
        complete_unit(source, p3_market.P3MarketSettings(seed=710031, critic_beta=0),
                      root=output, condition="C0", run_id="run-00-C0-b0", unit=0,
                      atomic_checkpoint=True)
    assert not output.exists()
