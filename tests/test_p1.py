"""P1 approved profile, shared budget and paired metrics; synthetic data only."""

import json
from dataclasses import replace
from datetime import datetime, timezone

import numpy as np
import pytest


def test_p1_frozen_roster():
    from btc_risk_rl.pilots.p1_protocol import P1Settings, entries

    rows = entries()
    assert len(rows) == 18
    assert [(r["seed"], r["condition"], r["epochs"]) for r in rows[:2]] == [
        (510031, "C0", 2),
        (510031, "C0", 4),
    ]
    assert [r["epochs"] for r in rows[6:8]] == [4, 2]
    assert {r["seed"] for r in rows} == {510031, 510047, 510081}
    with pytest.raises(ValueError):
        replace(P1Settings(), critic_epochs=3)
    with pytest.raises(ValueError):
        replace(P1Settings(), seed=410031)
    with pytest.raises(ValueError):
        replace(P1Settings(), actor_lr=0.002)


def test_daily_other_campaign_debit_and_lock(tmp_path):
    from btc_risk_rl.pilots.budget import CampaignLedger
    from btc_risk_rl.pilots.shared_budget import SharedBudget

    now = datetime(2026, 9, 24, 12, tzinfo=timezone.utc).timestamp()
    p0 = tmp_path / "p0-approved-v1"
    p0.mkdir()
    state = dict(status="completed", days={"2026-09-24": dict(charged_wall_seconds=1400)})
    (p0 / "ledger.jsonl").write_text(json.dumps(state) + "\n")
    with SharedBudget(tmp_path, "p1-approved-v1", now=now) as bank:
        assert bank.external_seconds == 1400
        with pytest.raises(ValueError):
            SharedBudget(tmp_path, "p1-approved-v1", now=now)
        with CampaignLedger(
            tmp_path / "p1-approved-v1",
            now=now,
            identity={},
            external_seconds=bank.external_seconds,
        ) as ledger:
            assert ledger.day["hard_deadline"] == now + 9400
    with SharedBudget(tmp_path, "p1-approved-v1", now=now + 10) as bank:
        with CampaignLedger(
            tmp_path / "p1-approved-v1",
            now=now + 10,
            identity={},
            external_seconds=bank.external_seconds,
        ) as ledger:
            assert ledger.day["hard_deadline"] == now + 9400


def test_paired_critic_diagnostics_do_not_change_actor(config):
    from btc_risk_rl.agents.synthetic import SyntheticMarket, SyntheticSettings
    from btc_risk_rl.agents.trainer import SyntheticExperiment

    runs = []
    for epochs in (2, 4):
        settings = replace(SyntheticSettings(), iterations=1, critic_epochs=epochs)
        run = SyntheticExperiment(
            SyntheticMarket(config), settings, condition="C5", run_id="paired"
        )
        report = run.run()
        runs.append((run, report))
    a, b = (r[1] for r in runs)
    assert a["actor_sha256"] == b["actor_sha256"]
    assert a["critic_updates"] * 2 == b["critic_updates"]
    for run, report in runs:
        records = [x for x in report["stability"] if x["phase"] == "fixed_A"]
        assert [x["measurement"] for x in records] == [
            "before_actor",
            "after_actor_before_critic",
            "after_critic",
        ]
        assert len({x["batch_sha256"] for x in records}) == 1
        assert records[0]["mse"] == records[1]["mse"]
        assert records[0]["risk_penalty_nonzero"] == 0
        g = run.fixed[0]["returns"]
        v = run.fixed[0]["old_values"]
        assert records[0]["mse"] == float(np.mean((g - v) ** 2))
        assert records[0]["denominator"] == float(np.mean(g**2) + 1e-12)
    assert a["stability"][1]["batch_sha256"] == b["stability"][1]["batch_sha256"]


def test_p1_lease_binds_arm_and_parent(tmp_path, monkeypatch):
    import os

    from btc_risk_rl.pilots import p1_protocol as p

    monkeypatch.setattr(p, "CAMPAIGN", tmp_path)
    row = p.entries()[0]
    state = dict(
        status="running",
        cursor=0,
        pending=dict(token="lease", supervisor_pid=os.getppid(), run_id=row["run_id"]),
    )
    (tmp_path / "ledger.jsonl").write_text(json.dumps(state) + "\n")
    p.P1Permit("lease").validate(p.P1Settings(), row["condition"], row["run_id"])
    with pytest.raises(PermissionError):
        p.P1Permit("lease").validate(p.P1Settings(critic_epochs=4), row["condition"], row["run_id"])
    with pytest.raises(PermissionError):
        p.P1Permit("wrong").validate(p.P1Settings(), row["condition"], row["run_id"])


def test_four_epoch_checkpoint_diagnostics_and_adam_resume(tmp_path, config):
    import torch

    from btc_risk_rl.agents.models import fingerprint
    from btc_risk_rl.agents.synthetic import SyntheticMarket, SyntheticSettings
    from btc_risk_rl.agents.trainer import SyntheticExperiment
    from btc_risk_rl.pilots.worker import complete_unit

    s = replace(SyntheticSettings(), critic_epochs=4, n_a=1, n_q=2, n_b=2)
    source = SyntheticMarket(config)
    continuous = SyntheticExperiment(source, s, condition="C5", run_id="four-epochs")
    report = continuous.run()
    previous = None
    for unit in range(3):
        out = complete_unit(
            source,
            s,
            condition="C5",
            run_id="four-epochs",
            root=tmp_path,
            unit=unit,
            previous=previous,
        )
        previous = out["checkpoint"]
    assert out["report"]["stability"] == report["stability"]
    assert out["report"]["critic_sha256"] == fingerprint(continuous.critic)
    state = torch.load(tmp_path / "checkpoint-2/state.pt", weights_only=True)
    for name in ("actor_optimizer", "critic_optimizer"):
        for key, v in getattr(continuous, name).state_dict()["state"].items():
            for field, t in v.items():
                assert torch.equal(t, state[name]["state"][key][field])
    assert out["report"]["trajectories"] == report["trajectories"]


def test_external_budget_exhausted_and_other_day(tmp_path):
    from btc_risk_rl.pilots.budget import CampaignLedger

    now = datetime(2026, 9, 24, 12, tzinfo=timezone.utc).timestamp()
    with CampaignLedger(tmp_path, now=now, identity={}, external_seconds=10800) as ledger:
        assert ledger.day["hard_deadline"] == now
    with CampaignLedger(tmp_path, now=now + 86400, identity={}, external_seconds=0) as ledger:
        assert ledger.day["hard_deadline"] == now + 86400 + 10800


def test_p1_pair_integrity_rejects_different_initial_A(tmp_path):
    from btc_risk_rl.pilots.p1_protocol import check_first_pair

    records = [
        dict(phase="fixed_A", iteration=0, measurement="before_actor", batch_sha256="same"),
        dict(
            phase="fixed_A",
            iteration=0,
            measurement="after_actor_before_critic",
            actor_sha256="same-actor",
        ),
    ]
    result = dict(report=dict(settings=dict(seed=510031), stability=records))
    old = tmp_path / "run-00-C0-e2"
    old.mkdir()
    (old / "unit-1.json").write_text(json.dumps(result))
    check_first_pair(tmp_path, result)
    changed = json.loads(json.dumps(result))
    changed["report"]["stability"][0]["batch_sha256"] = "different"
    with pytest.raises(ValueError):
        check_first_pair(tmp_path, changed)


def test_fixed_diagnostics_leave_learning_and_rng_unchanged(config, monkeypatch):
    import torch

    from btc_risk_rl.agents import fixed_diagnostics as diagnostic
    from btc_risk_rl.agents.synthetic import SyntheticMarket, SyntheticSettings
    from btc_risk_rl.agents.trainer import SyntheticExperiment

    s = replace(SyntheticSettings(), n_a=1, n_q=2, n_b=2)
    first = SyntheticExperiment(SyntheticMarket(config), s, condition="C5", run_id="no-effect")
    a = first.run()
    monkeypatch.setattr(
        diagnostic, "fixed_diagnostic", lambda *args: dict(phase="disabled_for_test")
    )
    second = SyntheticExperiment(SyntheticMarket(config), s, condition="C5", run_id="no-effect")
    b = second.run()
    assert a["actor_sha256"] == b["actor_sha256"] and a["critic_sha256"] == b["critic_sha256"]
    assert a["events"] == b["events"] and a["audits"] == b["audits"]
    for name in ("actor_optimizer", "critic_optimizer"):
        x, y = getattr(first, name).state_dict(), getattr(second, name).state_dict()
        for key in x["state"]:
            for field in x["state"][key]:
                assert torch.equal(x["state"][key][field], y["state"][key][field])


def test_diagnostic_preserves_existing_grad_rng_and_parameters(config):
    import torch

    from btc_risk_rl.agents.fixed_diagnostics import fixed_diagnostic
    from btc_risk_rl.agents.synthetic import SyntheticMarket, SyntheticSettings
    from btc_risk_rl.agents.trainer import SyntheticExperiment

    run = SyntheticExperiment(
        SyntheticMarket(config),
        replace(SyntheticSettings(), n_a=1, n_q=2, n_b=2),
        condition="C5",
        run_id="snapshot",
    )
    run.run()
    state = torch.random.get_rng_state().clone()
    parameters = [
        (p, p.detach().clone(), None if p.grad is None else p.grad.clone())
        for m in (run.actor, run.critic)
        for p in m.parameters()
    ]
    fixed_diagnostic(run, run.fixed[1], 1, "before_actor")
    assert torch.equal(state, torch.random.get_rng_state())
    for p, value, grad in parameters:
        assert torch.equal(p, value)
        assert (p.grad is None) if grad is None else torch.equal(p.grad, grad)


def test_public_runner_cannot_bypass_global_budget(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import p1_protocol, runner
    from btc_risk_rl.pilots.shared_budget import SharedBudget

    monkeypatch.setattr(p1_protocol, "CAMPAIGN", tmp_path / "p1-approved-v1")
    with SharedBudget(tmp_path, "p0-approved-v1", now=1790240000):
        with pytest.raises(ValueError, match="global daily budget"):
            runner.run_campaign(1790240000, p1=True)


def test_primary_counts_three_seeds_not_nine_conditions():
    from btc_risk_rl.pilots.p1_reporting import primary

    rows = []
    for seed, reduction in zip((510031, 510047, 510081), (0.20, 0.30, 0.10)):
        for condition in ("C0", "C5", "C10"):
            for epochs in (2, 4):
                rows.append(
                    dict(
                        status="completed",
                        seed=seed,
                        condition=condition,
                        critic_epochs=epochs,
                        stability=[
                            dict(
                                phase="fixed_A",
                                iteration=0,
                                measurement="before_actor",
                                batch_sha256=str(seed),
                            ),
                            dict(
                                phase="fixed_A",
                                iteration=0,
                                measurement="after_critic",
                                actor_sha256=str(seed),
                                mse=1 if epochs == 2 else 1 - reduction,
                            ),
                        ],
                    )
                )
    result = primary(rows)
    assert result["criterion_met"] and result["successful_seeds"] == 2
    assert result["independent_seed_blocks"] == 3
    rows[-1]["stability"][-1]["actor_sha256"] = "bad"
    with pytest.raises(ValueError):
        primary(rows)


def test_primary_literal_zero_pair_keeps_reduction_undefined():
    from btc_risk_rl.pilots.p1_reporting import primary

    rows = []
    for seed in (510031, 510047, 510081):
        for condition in ("C0", "C5", "C10"):
            for epochs in (2, 4):
                rows.append(
                    dict(
                        status="completed",
                        seed=seed,
                        condition=condition,
                        critic_epochs=epochs,
                        stability=[
                            dict(
                                phase="fixed_A",
                                iteration=0,
                                measurement="before_actor",
                                batch_sha256=str(seed),
                            ),
                            dict(
                                phase="fixed_A",
                                iteration=0,
                                measurement="after_critic",
                                actor_sha256=str(seed),
                                mse=0.0,
                            ),
                        ],
                    )
                )
    result = primary(rows)
    assert result["criterion_met"] and all(r["reduction"] is None for r in result["seeds"])
