"""Checkpoint, failure and budget invariants on tiny synthetic learning only."""

from dataclasses import replace

import numpy as np
import pytest
import torch


def make(config, journal=None):
    from btc_risk_rl.agents.synthetic import SyntheticMarket, SyntheticSettings
    from btc_risk_rl.agents.trainer import SyntheticExperiment

    settings = replace(SyntheticSettings(), n_a=1, n_q=2, n_b=2, actor_epochs=1, critic_epochs=1)
    return SyntheticExperiment(
        SyntheticMarket(config), settings, condition="C5", run_id="resume-test", journal=journal
    )


def equal_tree(a, b):
    if isinstance(a, torch.Tensor):
        assert torch.equal(a, b)
    elif isinstance(a, dict):
        assert a.keys() == b.keys()
        for key in a:
            equal_tree(a[key], b[key])
    elif isinstance(a, (list, tuple)):
        assert len(a) == len(b)
        for x, y in zip(a, b):
            equal_tree(x, y)
    else:
        assert a == b


@pytest.mark.parametrize("pause_after", [0, 1])
def test_resume_exact_including_optimizers_samples_and_resources(config, tmp_path, pause_after):
    from btc_risk_rl.agents.checkpoint import load_checkpoint, save_checkpoint

    continuous = make(config)
    continuous.run()
    partial = make(config, tmp_path / "journal")
    paused = partial.run(pause_after=pause_after)
    assert paused["status"] == "paused"
    point = tmp_path / "checkpoint"
    save_checkpoint(partial, point)
    restored = load_checkpoint(point, partial.collector.source, journal=tmp_path / "journal")
    result = restored.run()
    for name in ("actor", "critic", "actor_optimizer", "critic_optimizer"):
        equal_tree(getattr(continuous, name).state_dict(), getattr(restored, name).state_dict())
    assert restored.multiplier == continuous.multiplier and restored.eta == continuous.eta
    assert result["transitions"] == continuous.collector.transitions
    assert result["trajectories"] == continuous.collector.trajectories
    assert restored.actor_updates == continuous.actor_updates
    assert restored.critic_updates == continuous.critic_updates
    equal_tree(restored.events, continuous.events)
    for a, b in zip(continuous.batches[-len(restored.batches) :], restored.batches):
        for x, y in zip(a, b):
            assert x.realization == y.realization and x.policy_version == y.policy_version
            np.testing.assert_array_equal(x.actions, y.actions)
            np.testing.assert_array_equal(x.observations, y.observations)
    with pytest.raises(FileExistsError):
        save_checkpoint(restored, point)


def test_corrupt_incompatible_and_mid_phase_checkpoint_rejected(config, tmp_path):
    from btc_risk_rl.agents.checkpoint import load_checkpoint, save_checkpoint

    run = make(config, tmp_path / "journal")
    with pytest.raises(ValueError, match="boundary"):
        save_checkpoint(run, tmp_path / "early")
    run.run(pause_after=1)
    point = tmp_path / "checkpoint"
    save_checkpoint(run, point)
    with (point / "state.pt").open("ab") as f:
        f.write(b"corrupt")
    with pytest.raises(ValueError, match="hash"):
        load_checkpoint(point, run.collector.source, journal=tmp_path / "journal")


def test_failed_continuation_cannot_roll_back_to_prior_checkpoint(config, tmp_path, monkeypatch):
    from btc_risk_rl.agents.checkpoint import load_checkpoint, save_checkpoint
    from btc_risk_rl.agents.trainer import RunAbort

    run = make(config, tmp_path / "journal")
    run.run(pause_after=1)
    point = tmp_path / "checkpoint"
    save_checkpoint(run, point)
    loaded = load_checkpoint(point, run.collector.source, journal=tmp_path / "journal")

    def fail(*args, **kwargs):
        raise ValueError("intentional unit failure")

    monkeypatch.setattr(loaded.collector, "collect", fail)
    with pytest.raises(RunAbort):
        loaded.run()
    with pytest.raises(ValueError, match="journal"):
        load_checkpoint(point, run.collector.source, journal=tmp_path / "journal")
    with pytest.raises(ValueError):
        save_checkpoint(loaded, tmp_path / "failed")


def test_budget_refuses_unit_and_preserves_save_margin():
    from btc_risk_rl.agents.telemetry import TimeBudget

    clock = [0.0]
    budget = TimeBudget(
        total=30,
        reserve=5,
        estimates={"q0": 4, "iteration": 12},
        profile="synthetic",
        clock=lambda: clock[0],
    )
    assert budget.can_start("iteration", "synthetic")
    clock[0] = 14
    assert not budget.can_start("iteration", "synthetic")
    with pytest.raises(ValueError, match="profile"):
        budget.can_start("q0", "accepted_train_collection_only")
    clock[0] = 26
    with pytest.raises(TimeoutError):
        budget.check_reserve()


def test_no_budget_for_next_iteration_pauses_without_collecting(config, tmp_path):
    from btc_risk_rl.agents.telemetry import TimeBudget

    run = make(config, tmp_path / "journal")
    budget = TimeBudget(
        total=20, reserve=5, estimates={"q0": 1, "iteration": 100}, profile="synthetic"
    )
    result = run.run(budget=budget)
    assert result["status"] == "paused" and run.next_iteration == 0
    assert run.collector.trajectories == 2
    assert run.actor_updates == run.critic_updates == 0
    assert run.telemetry.records[0]["phase"] == "Q"
    assert run.telemetry.records[0]["rss_peak_bytes"] > 0


def test_resume_budget_cannot_be_reset_and_interrupted_token_cannot_reload(config, tmp_path):
    from btc_risk_rl.agents.checkpoint import load_checkpoint, save_checkpoint
    from btc_risk_rl.agents.telemetry import TimeBudget

    run = make(config, tmp_path / "journal")
    budget = TimeBudget(
        total=100, reserve=5, estimates={"q0": 1, "iteration": 2}, profile="synthetic"
    )
    run.run(pause_after=0, budget=budget)
    save_checkpoint(run, tmp_path / "checkpoint")
    restored = load_checkpoint(
        tmp_path / "checkpoint", run.collector.source, journal=tmp_path / "journal"
    )
    assert restored.budget.consumed >= budget.consumed
    replacement = TimeBudget(
        total=100, reserve=5, estimates={"q0": 1, "iteration": 2}, profile="synthetic"
    )
    with pytest.raises(ValueError, match="budget"):
        restored.run(budget=replacement)
    # A consumed token after a process interruption is never a planned pause.
    with pytest.raises(ValueError, match="journal"):
        load_checkpoint(tmp_path / "checkpoint", run.collector.source, journal=tmp_path / "journal")


def test_incompatible_provenance_rejected_without_consuming_token(config, tmp_path, monkeypatch):
    import btc_risk_rl.agents.checkpoint as cp

    run = make(config, tmp_path / "journal")
    run.run(pause_after=0)
    cp.save_checkpoint(run, tmp_path / "checkpoint")
    actual = cp.provenance
    monkeypatch.setattr(
        cp, "provenance", lambda source: {**actual(source), "python": "incompatible"}
    )
    with pytest.raises(ValueError, match="Incompatible"):
        cp.load_checkpoint(
            tmp_path / "checkpoint", run.collector.source, journal=tmp_path / "journal"
        )
    assert run.journal.last()["status"] == "paused"


def test_stale_checkpoint_writer_cannot_roll_back_completed_continuation(config, tmp_path):
    from btc_risk_rl.agents.checkpoint import load_checkpoint, save_checkpoint

    old = make(config, tmp_path / "journal")
    old.run(pause_after=0)
    save_checkpoint(old, tmp_path / "initial")
    new = load_checkpoint(tmp_path / "initial", old.collector.source, journal=tmp_path / "journal")
    new.run()
    with pytest.raises(ValueError, match="journal"):
        save_checkpoint(old, tmp_path / "rollback")
    assert not (tmp_path / "rollback").exists()


def test_incomplete_payload_rejected_even_with_intact_transport_hash(config, tmp_path, monkeypatch):
    import btc_risk_rl.agents.checkpoint as cp

    run = make(config, tmp_path / "journal")
    run.run(pause_after=0)
    cp.save_checkpoint(run, tmp_path / "checkpoint")
    original_load = torch.load

    def malformed(*args, **kwargs):
        state = original_load(*args, **kwargs)
        del state["attrs"]["actor_updates"]
        return state

    monkeypatch.setattr(torch, "load", malformed)
    with pytest.raises(ValueError, match="attributes"):
        cp.load_checkpoint(
            tmp_path / "checkpoint", run.collector.source, journal=tmp_path / "journal"
        )
    assert run.journal.last()["status"] == "paused"


def test_journal_rejects_competing_writer(tmp_path):
    from btc_risk_rl.agents.journal import RunJournal

    first = RunJournal(tmp_path / "journal", create=True)
    second = RunJournal(tmp_path / "journal", create=False)
    first.append(status="running")
    with pytest.raises(ValueError, match="Stale"):
        second.append(status="paused")
    assert first.last()["status"] == "running"
