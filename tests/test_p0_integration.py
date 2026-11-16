"""Authorized profile guard and complete unit/checkpoint orchestration, synthetic only."""

from dataclasses import replace

import pytest
import torch
from test_simulator import accepted_synthetic as accepted_fixture

accepted_synthetic = accepted_fixture


def test_approved_profile_fixed_and_bound_before_results():
    from btc_risk_rl.pilots.protocol import P0Settings, approved

    p = approved()
    assert p["authorized"] and p["risk"]["bound_selected"] == -__import__("math").log(0.9)
    s = P0Settings(seed=410047)
    assert s.n_q == s.n_b == 400 and s.iterations == 2 and s.n_a == 64
    with pytest.raises(ValueError):
        replace(s, actor_lr=0.003)
    with pytest.raises(ValueError):
        replace(s, seed=20260922)


@pytest.mark.parametrize("condition", ["C0", "C5"])
def test_unit_execution_resume_matches_continuous_and_checkpoints(tmp_path, config, condition):
    from btc_risk_rl.agents.models import fingerprint
    from btc_risk_rl.agents.synthetic import SyntheticMarket, SyntheticSettings
    from btc_risk_rl.agents.trainer import SyntheticExperiment
    from btc_risk_rl.pilots.worker import complete_unit

    settings = replace(SyntheticSettings(), n_a=1, n_q=2, n_b=2, actor_epochs=1, critic_epochs=1)
    source = SyntheticMarket(config)
    continuous = SyntheticExperiment(source, settings, condition=condition, run_id="synthetic-unit")
    continuous.run()
    checkpoint = None
    results = []
    for unit in range(3):
        result = complete_unit(
            source,
            settings,
            condition=condition,
            run_id="synthetic-unit",
            root=tmp_path,
            unit=unit,
            previous=checkpoint,
        )
        checkpoint = result["checkpoint"]
        results.append(result)
    final = results[-1]
    assert final["report"]["actor_sha256"] == fingerprint(continuous.actor)
    assert final["report"]["critic_sha256"] == fingerprint(continuous.critic)
    assert sum(r["resources"]["trajectories"] for r in results) == 12
    assert sum(r["resources"]["transitions"] for r in results) == 2160
    state = torch.load(tmp_path / "checkpoint-2/state.pt", weights_only=True)
    for name in ("actor_optimizer", "critic_optimizer"):
        expected = getattr(continuous, name).state_dict()
        for key, values in expected["state"].items():
            for field, value in values.items():
                assert torch.equal(value, state[name]["state"][key][field])


def test_proposal_json_cannot_authorize_worker(tmp_path):
    from btc_risk_rl.pilots.protocol import approved

    p = tmp_path / "false.json"
    p.write_text('{"authorized": true}')
    with pytest.raises(ValueError):
        approved(p)


def test_warning_thresholds_are_diagnostics_not_integrity_failures():
    from btc_risk_rl.pilots.diagnostics import warnings

    report = {
        "stability": [
            {
                "phase": "actor",
                "iteration": 0,
                "ratio_min": 0.2,
                "ratio_max": 3.0,
                "surrogate_clip_fraction": 0.6,
                "gradient_norm": 101.0,
            }
        ],
        "audits": [
            {
                "iteration": 1,
                "rho_q": 0.3,
                "rho_b": 0.1,
                "lambda_after": 1.1,
                "q_tail": {"mass": 10},
                "b_tail": {"mass": 20},
            }
        ],
        "collection_diagnostics": [{"role": "A", "iteration": 0, "near_endpoint_fraction": 0.02}],
    }
    result = warnings(report)
    assert len(result) == 3
    assert "active_clip" in result[0]["reasons"] and "tail_mass" in result[1]["reasons"]
    assert report["audits"][0]["lambda_after"] == 1.1


def test_p0_permit_required_for_training_source(accepted_synthetic):
    from btc_risk_rl.agents.checkpoint import digest
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.agents.trainer import SyntheticExperiment
    from btc_risk_rl.pilots.protocol import P0Settings

    config, _, out, _ = accepted_synthetic
    source = TrainingMarket(config, out, expected_manifest=digest(out / "manifest.json"))
    with pytest.raises(PermissionError, match="lease"):
        SyntheticExperiment(source, P0Settings(), condition="C0", run_id="unauthorized")


def test_c0_checkpoint_risk_flag_allowed_but_c5_c10_cannot_disable(accepted_synthetic, monkeypatch):
    from btc_risk_rl.agents.checkpoint import digest
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.agents.trainer import SyntheticExperiment
    from btc_risk_rl.pilots.protocol import P0Settings, Permit

    config, _, out, _ = accepted_synthetic
    source = TrainingMarket(config, out, expected_manifest=digest(out / "manifest.json"))
    calls = []
    monkeypatch.setattr(Permit, "validate", lambda self, *args: calls.append(args))
    # False is exactly the flag serialized by a C0 checkpoint. No learning occurs.
    run = SyntheticExperiment(
        source,
        P0Settings(),
        condition="C0",
        risk_enabled=False,
        run_id="synthetic-authorized-guard",
        permit=Permit("test"),
    )
    assert run.enabled is False and len(calls) == 1
    for condition in ("C5", "C10"):
        with pytest.raises(PermissionError):
            SyntheticExperiment(
                source,
                P0Settings(),
                condition=condition,
                risk_enabled=False,
                run_id="blocked",
                permit=Permit("test"),
            )


def test_two_consecutive_synthetic_runs_use_one_global_day_and_exact_budget(
    tmp_path, config, monkeypatch
):
    import json

    from btc_risk_rl.agents.synthetic import SyntheticMarket, SyntheticSettings
    from btc_risk_rl.pilots import runner
    from btc_risk_rl.pilots.worker import complete_unit

    settings = replace(SyntheticSettings(), n_a=1, n_q=2, n_b=2, actor_epochs=1, critic_epochs=1)
    import time
    from types import SimpleNamespace

    started = time.monotonic()
    monkeypatch.setattr(
        runner,
        "time",
        SimpleNamespace(
            time=lambda: 1790222400.0 + time.monotonic() - started, monotonic=time.monotonic
        ),
    )
    source = SyntheticMarket(config)
    monkeypatch.setattr(runner, "CAMPAIGN", tmp_path)
    monkeypatch.setattr(runner, "fingerprint", lambda: "explicit_synthetic_campaign_test")
    monkeypatch.setattr(runner, "roster", lambda: [(settings.seed, "C0"), (settings.seed, "C5")])
    monkeypatch.setattr(runner, "preflight", lambda: {"profile": "synthetic"})
    monkeypatch.setattr(
        runner,
        "expected_resources",
        lambda unit: dict(
            trajectories=2 if unit == 0 else 5,
            transitions=360 if unit == 0 else 900,
            actor_updates=0 if unit == 0 else 1,
            critic_updates=0 if unit == 0 else 1,
        ),
    )

    def synthetic_worker(*args, **kwargs):
        state = json.loads((tmp_path / "ledger.jsonl").read_text().splitlines()[-1])
        pending = state["pending"]
        condition = runner.roster()[state["cursor"]][1]
        complete_unit(
            source,
            settings,
            condition=condition,
            run_id=pending["run_id"],
            root=tmp_path / pending["run_id"],
            unit=pending["unit"],
            previous=pending["previous"],
        )
        return dict(status="passed", wall_seconds=0.001)

    monkeypatch.setattr(runner, "supervise", synthetic_worker)
    state = runner.run_campaign()
    assert state["status"] == "completed" and state["cursor"] == 2
    assert len(state["days"]) == 1 and len(state["units"]) == 6
    assert state["resources"] == dict(
        trajectories=24, transitions=4320, actor_updates=4, critic_updates=4
    )
    assert sum(len(r["days"]) for r in state["runs"].values()) == 2


@pytest.mark.parametrize("status", ["ready", "completed"])
def test_late_invocation_preserves_paused_or_completed_campaign(tmp_path, monkeypatch, status):
    import time
    from types import SimpleNamespace

    from btc_risk_rl.pilots import runner
    from btc_risk_rl.pilots.budget import CampaignLedger

    t = 1790222400
    with CampaignLedger(tmp_path, now=t, identity="synthetic-late") as ledger:
        ledger.preflight_done(t + 10)
        ledger.state["status"] = status
        ledger.persist(t + 20)
    monkeypatch.setattr(runner, "CAMPAIGN", tmp_path)
    monkeypatch.setattr(runner, "fingerprint", lambda: "synthetic-late")
    monkeypatch.setattr(
        runner, "time", SimpleNamespace(time=lambda: t + 14400, monotonic=time.monotonic)
    )
    monkeypatch.setattr(runner, "preflight", lambda: pytest.fail("Late invocation must not load"))
    state = runner.run_campaign()
    assert state["status"] == status and not state.get("deadline_violation")
