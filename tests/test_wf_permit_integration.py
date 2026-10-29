"""Controlled-source WF worker integration; never reads historical market data."""

import hashlib
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch


def _worker_case(tmp_path, monkeypatch):
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.agents.synthetic import SyntheticMarket
    from btc_risk_rl.config import load_config
    from btc_risk_rl.pilots import wf_cost, wf_cost_source
    from btc_risk_rl.pilots import wf_cost_replacement_03_exec as profile
    from btc_risk_rl.pilots import wf_cost_replacement_03_worker as worker
    from btc_risk_rl.pilots.p2_budget import state_hash

    campaign = tmp_path / "oos-v12-wf-cost-only-03"
    work = campaign / "wf-2021"
    work.mkdir(parents=True)
    monkeypatch.setattr(profile, "CAMPAIGN", campaign)
    monkeypatch.setattr(profile, "require_campaign", lambda: {"synthetic_fixture": True})
    monkeypatch.setattr(wf_cost.WFCostSettings, "__post_init__", lambda self: None)
    settings_type = wf_cost.WFCostSettings
    small = dict(hidden=4, iterations=1, n_a=2, n_q=2, n_b=2,
                 actor_epochs=1, critic_epochs=1, minibatch=1, fragment_steps=180)
    monkeypatch.setattr(profile, "WFCostSettings",
                        lambda **values: settings_type(**{**small, **values}))
    monkeypatch.setattr(profile, "EXPECTED", {"2021": (1, 2), "2022": (1, 2)})

    config = load_config(Path("configs/initial.toml"))
    fabricated = SyntheticMarket(config, routes=1)
    source = TrainingMarket.__new__(TrainingMarket)
    source.config = config
    source._view = SimpleNamespace(training_path=fabricated.path)
    source.route_ids = (0,)
    source.audit = {"normalizer_refitted": False,
                    "validation_observations_loaded": False}
    source._identity = {"profile": source.profile, "fold": "2021",
                        "manifest_sha256": "synthetic-only",
                        "training_shard_manifest_sha256": profile.SHARD_MANIFEST_SHA256,
                        "scaler_sha256": "synthetic-only", "files": {}}
    manifest = campaign / "folds/wf-2021/manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"source_identity": source.identity()}))
    monkeypatch.setattr(wf_cost_source, "build_fold_source", lambda fold: source)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda _n: None)

    token = "fixture-lease"
    request = dict(root=str(work), run_id="wf-2021", fold="2021",
                   condition="C10", unit=0, previous=None, token=token,
                   config=str(profile.CONFIG), atomic_checkpoint=True,
                   settings=asdict(profile.WFCostSettings(seed=276696733)))
    path = work / "request-0.json"
    path.write_text(json.dumps(request))
    state = dict(status="running", cursor=0,
                 pending=dict(unit=0, run_id="wf-2021", token=token,
                              request_sha256=profile.digest(path),
                              supervisor_pid=os.getppid()),
                 runs={}, identity={"source": {"2021": source.identity()}})

    def persist():
        state["state_hash"] = state_hash(state)
        (campaign / "ledger.jsonl").write_text(json.dumps(state) + "\n")

    persist()
    monkeypatch.setattr(sys, "argv", ["wf_cost_replacement_03_worker", str(path)])
    return SimpleNamespace(worker=worker, source=source, settings=settings_type(
        **request["settings"]), request=request, path=path, state=state,
        persist=persist, campaign=campaign, work=work)


def test_worker_q0_reaches_real_checkpoint_with_controlled_source(tmp_path, monkeypatch):
    from btc_risk_rl.agents.checkpoint import provenance
    from btc_risk_rl.pilots.p2r_units import _verify_completion

    case = _worker_case(tmp_path, monkeypatch)
    case.worker.main()
    point = case.work / "checkpoint-0"
    payload = json.loads((case.work / "unit-0.json").read_text())
    manifest = json.loads((point / "manifest.json").read_text())
    assert manifest["boundary"] == "after_q0"
    assert manifest["state_sha256"] == hashlib.sha256((point / "state.pt").read_bytes()).hexdigest()
    assert payload["resources"]["trajectories"] == case.settings.n_q
    assert payload["resources"]["actor_updates"] == 0
    assert payload["resources"]["critic_updates"] == 0
    assert _verify_completion(case.work, 0, case.settings, "C10", "wf-2021",
                              {"status": "passed"}, provenance(case.source),
                              diagnostic_n=64)[1] == "after_q0"


@pytest.mark.parametrize("change", ["token", "root", "seed", "condition"])
def test_worker_rejects_forged_lease_or_identity(tmp_path, monkeypatch, change):
    case = _worker_case(tmp_path, monkeypatch)
    if change == "token":
        case.request["token"] = "forged"
    elif change == "root":
        case.request["root"] = str(tmp_path / "foreign-root")
    elif change == "seed":
        case.request["settings"]["seed"] = 498614892
    else:
        case.request["condition"] = "C5"
    case.path.write_text(json.dumps(case.request))
    case.state["pending"]["request_sha256"] = hashlib.sha256(case.path.read_bytes()).hexdigest()
    case.persist()
    with pytest.raises(PermissionError):
        case.worker.main()
    assert not (case.work / "checkpoint-0").exists()
    assert not (tmp_path / "foreign-root").exists()


def test_complete_unit_rejects_foreign_root_before_writing(tmp_path, monkeypatch):
    from btc_risk_rl.pilots.p2_runner import complete_unit
    from btc_risk_rl.pilots.wf_cost_replacement_03_exec import WFCostPermit

    case = _worker_case(tmp_path, monkeypatch)
    foreign = tmp_path / "foreign-root"
    with pytest.raises(PermissionError):
        complete_unit(case.source, case.settings, root=foreign, condition="C10",
                      run_id="wf-2021", unit=0, permit=WFCostPermit("fixture-lease"),
                      n_d=64, atomic_checkpoint=True)
    assert not foreign.exists()


def test_only_named_wf_permit_types_are_listed(tmp_path, monkeypatch):
    from btc_risk_rl.agents.trainer import SyntheticExperiment
    from btc_risk_rl.pilots import wf_cost
    from btc_risk_rl.pilots import wf_cost_replacement_03_exec as third
    from btc_risk_rl.pilots import wf_cost_replacement_exec as replacement
    from btc_risk_rl.pilots.p2 import Diagnostic
    from btc_risk_rl.pilots.p2_runner import complete_unit
    from btc_risk_rl.pilots.wf_permits import authorized_wf_permits

    case = _worker_case(tmp_path, monkeypatch)
    assert set(authorized_wf_permits()) == {
        wf_cost.WFCostPermit, replacement.WFCostPermit, third.WFCostPermit,
    }

    class Forged(third.WFCostPermit):
        def validate(self, *_args):
            raise AssertionError("Forged lease must not be called")

    with pytest.raises(PermissionError, match="registered lease"):
        complete_unit(case.source, case.settings, root=case.work, condition="C10",
                      run_id="wf-2021", unit=0, permit=Forged("fixture-lease"),
                      n_d=64, atomic_checkpoint=True)
    with pytest.raises(PermissionError, match="explicit authorized profile"):
        SyntheticExperiment(case.source, case.settings, condition="C10", run_id="wf-2021",
                            permit=Forged("fixture-lease"),
                            diagnostic=Diagnostic(tmp_path / "forged-D", n=64))
    with pytest.raises(PermissionError, match="registered permit"):
        Diagnostic(tmp_path / "forged-D", n=64).bind(
            case.source, case.settings.seed, "wf-2021", permit=Forged("fixture-lease")
        )
    assert not (case.work / "checkpoint-0").exists()
