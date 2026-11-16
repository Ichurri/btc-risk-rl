"""P2 infrastructure only: fabricated paths, small learning batches, no market."""

from dataclasses import replace

import numpy as np
import pytest
import torch
from test_h5_resume import equal_tree


def make(config, tmp_path, *, enabled=True, iterations=2, name="run"):
    from btc_risk_rl.agents.synthetic import SyntheticMarket
    from btc_risk_rl.agents.trainer import SyntheticExperiment
    from btc_risk_rl.pilots.p2 import Diagnostic, P2SyntheticSettings

    s = P2SyntheticSettings(
        iterations=iterations, n_a=1, n_q=2, n_b=2, actor_epochs=1, critic_epochs=4, hidden=4
    )
    return SyntheticExperiment(
        SyntheticMarket(config),
        s,
        condition="C5",
        run_id="same",
        journal=tmp_path / name / "journal",
        diagnostic=Diagnostic(tmp_path / name / "D", n=2) if enabled else None,
    )


def test_p2_has_separate_diagnostic_infrastructure():
    import importlib.util

    assert importlib.util.find_spec("btc_risk_rl.pilots.p2") is not None


def test_d_does_not_change_learning(config, tmp_path):
    off = make(config, tmp_path, enabled=False, name="off")
    on = make(config, tmp_path, name="on")
    off.run()
    state = torch.random.get_rng_state().clone()
    on.run()
    assert torch.equal(state, torch.random.get_rng_state())
    for name in ("actor", "critic", "actor_optimizer", "critic_optimizer"):
        equal_tree(getattr(off, name).state_dict(), getattr(on, name).state_dict())
        if name in ("actor", "critic"):
            for a, b in zip(getattr(off, name).parameters(), getattr(on, name).parameters()):
                assert torch.equal(a.grad, b.grad)
    assert (off.eta, off.multiplier) == (on.eta, on.multiplier)
    assert off.events == on.events and off.audits == on.audits
    assert off.collector.used == on.collector.used
    for x, y in zip(off.batches, on.batches):
        for a, b in zip(x, y):
            for field in ("actions", "rewards", "observations", "log_probs"):
                np.testing.assert_array_equal(getattr(a, field), getattr(b, field))
    assert on.diagnostic.collector.trajectories == 4
    assert on.boundary == "after_dual_and_D"
    for k, record in enumerate(on.diagnostic.records):
        actor = [e for e in on.events if e["event"] == "actor"][k]
        assert record["policy_version"] == f"policy-{k}:{actor['actor_before']}"
        assert record["critic_pre"] == actor["critic_before"]
        assert record["A"]["pre"]["count"] == 180
        assert record["D"]["post"]["count"] == 360
        assert record["D"]["pre"]["target_stats"] == record["D"]["post"]["target_stats"]


@pytest.mark.parametrize("pause", [0, 1])
def test_p2_resume_no_regeneration(config, tmp_path, pause):
    from btc_risk_rl.agents.checkpoint import load_checkpoint, save_checkpoint
    from btc_risk_rl.pilots.p2 import file_hash

    full = make(config, tmp_path, name="full")
    full.run()
    part = make(config, tmp_path, name="part")
    part.run(pause_after=pause)
    existing = {str(p): file_hash(p) for p in (tmp_path / "part" / "D").glob("*.npz")}
    save_checkpoint(part, tmp_path / "cp")
    resumed = load_checkpoint(
        tmp_path / "cp", part.collector.source, journal=tmp_path / "part" / "journal"
    )
    resumed.run()
    assert all(file_hash(__import__("pathlib").Path(p)) == h for p, h in existing.items())
    for name in ("actor", "critic", "actor_optimizer", "critic_optimizer"):
        equal_tree(getattr(full, name).state_dict(), getattr(resumed, name).state_dict())
    assert full.events == resumed.events
    for a, b in zip(full.diagnostic.records, resumed.diagnostic.records):
        for key in ("A", "D", "overlap", "policy_version", "critic_pre", "critic_post"):
            assert a[key] == b[key]
    assert resumed.diagnostic.collector.trajectories == 4
    assert resumed.diagnostic.collector.used == {(0, "D"), (1, "D")}


def test_metrics_and_pooling_are_sums_not_mean_ratios():
    from btc_risk_rl.pilots.p2_metrics import metric, overlap, pool

    a = metric(np.array([[2.0, 0.0]]), np.array([[1.0, 1.0]]))
    assert a["mse"] == 1 and a["z"] == 1 and a["bias"] == 0
    b = metric(np.array([[0.0, 0.0]]), np.array([[2.0, 2.0]]))
    pooled = pool([a, b])
    assert pooled["mse"] == 2.5 and pooled["z"] == 2.5 and pooled["bias"] == -1
    assert pooled["relative_mse"] != (a["relative_mse"] + b["relative_mse"]) / 2
    d = [{"start": "s:2", "times": ["s:2", "s:3"]}] * 2
    learn = [{"start": "s:1", "times": ["s:1", "s:2"]}]
    o = overlap(d, learn, learn)
    assert o["duplicates"] == {"numerator": 1, "denominator": 2}
    assert o["exact_A"]["numerator"] == 0
    assert o["transition_occurrences"] == {"numerator": 2, "denominator": 4}
    assert o["unique_transitions"] == {"numerator": 1, "denominator": 2}
    assert not metric(np.zeros((1, 2)), np.zeros((1, 2)))["informative"]


def test_market_block_precedes_paths_or_loaders(tmp_path):
    from btc_risk_rl.pilots.p2 import entrypoint

    for profile in ("market", "validation", "final", "accepted_train_collection_only"):
        with pytest.raises((PermissionError, ValueError, OSError)):
            entrypoint(profile=profile, output=tmp_path / profile,
                       config="does-not-exist", protocol=tmp_path / "unregistered.json")
        assert not (tmp_path / profile).exists()


def test_partial_and_corrupt_d_cannot_checkpoint(config, tmp_path):
    from btc_risk_rl.agents.checkpoint import load_checkpoint, save_checkpoint

    run = make(config, tmp_path)
    run.run(pause_after=1)
    run.boundary = "after_dual"
    with pytest.raises(ValueError):
        save_checkpoint(run, tmp_path / "bad")
    run.boundary = "after_dual_and_D"
    save_checkpoint(run, tmp_path / "cp")
    path = next((tmp_path / "run" / "D").glob("*.npz"))
    path.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="diagnostic|Diagnostic"):
        load_checkpoint(tmp_path / "cp", run.collector.source, journal=tmp_path / "run" / "journal")


def test_d_failure_invalidates_whole_unit(config, tmp_path, monkeypatch):
    from btc_risk_rl.agents.checkpoint import save_checkpoint
    from btc_risk_rl.agents.trainer import RunAbort

    run = make(config, tmp_path)

    def fail(*args, **kwargs):
        raise ValueError("synthetic incomplete D")

    monkeypatch.setattr(run.diagnostic, "finish", fail)
    with pytest.raises(RunAbort):
        run.run()
    assert run.failed and run.journal.last()["status"] == "failed"
    with pytest.raises(ValueError):
        save_checkpoint(run, tmp_path / "bad")


def test_ten_iterations_supported_only_explicit_synthetic(config, tmp_path):
    from btc_risk_rl.agents.synthetic import SyntheticSettings
    from btc_risk_rl.pilots.p2 import P2SyntheticSettings

    assert P2SyntheticSettings(iterations=10).iterations == 10
    with pytest.raises(ValueError):
        replace(SyntheticSettings(), iterations=10)
    with pytest.raises(ValueError):
        P2SyntheticSettings(iterations=11)


def test_joint_gates_require_same_two_seeds_and_every_condition():
    from copy import deepcopy

    from btc_risk_rl.pilots.p2_metrics import campaign_gate, summarize, warning_rates

    def records():
        rows = []
        for k in range(10):
            d = summarize(2.0 if k < 3 else 0.5, 1.0, 0.0, 1)
            a = summarize(0.4, 1.0, 0.0, 1)
            rows.append(
                dict(
                    iteration=k,
                    D=dict(pre=d, post=d),
                    A=dict(pre=a, post=a),
                    gap=d["relative_mse"] - a["relative_mse"],
                )
            )
        return rows

    runs = [
        dict(seed=s, condition=c, status="passed", records=records())
        for s in (610031, 610047, 610081)
        for c in ("C0", "C5", "C10")
    ]
    assert campaign_gate(runs)["decision"] == "advance_to_discussion"
    assert warning_rates(runs[0]["records"])["D/post/relative_mse"]["numerator"] == 3
    broken = deepcopy(runs)
    # Two different bad seeds in C5; cannot combine improvements and low biases across seeds.
    for k in (7, 8, 9):
        broken[1]["records"][k]["D"]["post"] = summarize(0.5, 1, 0.4, 1)
        broken[4]["records"][k]["D"]["post"] = summarize(3, 1, 0, 1)
    assert campaign_gate(broken)["decision"] == "review"
    assert campaign_gate(runs[:-1])["decision"] == "review"


def test_p2_budget_ten_units_shared_midnight_days_and_corruption(tmp_path):
    import json
    from datetime import datetime, timezone

    from btc_risk_rl.pilots.p2_budget import P2Ledger

    now = datetime(2026, 9, 25, 12, tzinfo=timezone.utc).timestamp()
    root = tmp_path / "ledger"
    with P2Ledger(root, now=now, identity={"test": True}, external_seconds=6000) as ledger:
        ledger.preflight_done(now + 1)
        assert ledger.admit("C0", "iteration", now + 2) == "start"
        assert ledger.admit("C0", "iteration", now + 301) == "pause"
        ledger.begin("r", "q0", now + 2)
        ledger.state["pending"].update(unit=0)
        ledger.finish(
            now + 3, resources={"diagnostic_trajectories": 0}, condition="C0", checkpoint="test"
        )
        assert ledger.state["cursor"] == 0
        for k in range(1, 11):
            ledger.begin("r", "iteration", now + 3 * k + 1)
            ledger.state["pending"].update(unit=k)
            ledger.finish(
                now + 3 * k + 2,
                resources={"diagnostic_trajectories": 64},
                condition="C0",
                checkpoint="test",
            )
        assert ledger.state["cursor"] == 1
        assert ledger.state["resources"]["diagnostic_trajectories"] == 640
    # Two more active days; fourth rejected. Separate from per-run session count.
    for day in (1, 2):
        with P2Ledger(root, now=now + 86400 * day, identity={"test": True}) as ledger:
            ledger.preflight_done(now + 86400 * day + 1)
            ledger.begin(f"r{day}", "q0", now + 86400 * day + 2)
            ledger.finish(now + 86400 * day + 3, resources={}, condition="C0")
    with pytest.raises(ValueError, match="days"):
        P2Ledger(root, now=now + 86400 * 3, identity={"test": True})
    # A well-formed JSON mutation is corruption, not a new budget.
    path = root / "ledger.jsonl"
    lines = path.read_text().splitlines()
    state = json.loads(lines[-1])
    state["cursor"] = 0
    lines[-1] = json.dumps(state)
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="hash"):
        P2Ledger(root, now=now + 86400 * 3, identity={"test": True})
    midnight = datetime(2026, 9, 26, 3, 50, tzinfo=timezone.utc).timestamp()
    with P2Ledger(tmp_path / "midnight", now=midnight, identity={}) as ledger:
        ledger.preflight_done(midnight + 1)
        assert ledger.admit("C0", "q0", midnight + 2) == "pause"


def test_supervised_synthetic_unit_persists_counts_and_phase(config, tmp_path):
    from btc_risk_rl.agents.synthetic import SyntheticMarket
    from btc_risk_rl.pilots.p2 import P2SyntheticSettings
    from btc_risk_rl.pilots.p2_runner import complete_unit

    s = P2SyntheticSettings(iterations=2, n_a=1, n_q=2, n_b=2, hidden=4, actor_epochs=1)
    root = tmp_path / "unit"
    first = complete_unit(SyntheticMarket(config), s, root=root, condition="C0", run_id="x", unit=0)
    second = complete_unit(
        SyntheticMarket(config),
        s,
        root=root,
        condition="C0",
        run_id="x",
        unit=1,
        previous=first["checkpoint"],
    )
    assert second["resources"]["diagnostic_trajectories"] == 2
    assert second["resources"]["diagnostic_transitions"] == 360
    assert second["resources"]["trajectories"] == 5
    assert second["report"]["boundary"] == "after_dual_and_D"
    assert (root / "closing-1.json").exists()
    with pytest.raises(Exception):
        complete_unit(
            SyntheticMarket(config),
            s,
            root=root,
            condition="C0",
            run_id="x",
            unit=1,
            previous=first["checkpoint"],
        )


def test_d_900_second_watchdog(tmp_path):
    import json
    import sys
    import time

    from btc_risk_rl.pilots.supervisor import supervise

    marker = tmp_path / "phase.json"
    marker.write_text(json.dumps({"phase": "D", "started_monotonic": time.monotonic() - 901}))
    result = supervise(
        [sys.executable, "-c", "import time; time.sleep(2)"],
        output=tmp_path / "worker.log",
        seconds=10,
        rss_limit=10 * 1024**3,
        phase_marker=marker,
        poll=0.01,
        grace=0.01,
    )
    assert result["reason"] == "diagnostic_time"


@pytest.fixture(autouse=True)
def single_cpu_thread():
    before = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(before)


def test_full_ten_iteration_state_and_d64_targets_independently(config, tmp_path):
    from btc_risk_rl.agents.checkpoint import validate_state
    from btc_risk_rl.agents.collector import load_trajectory

    run = make(config, tmp_path, iterations=10)
    report = run.run()
    validate_state(run)
    assert report["next_iteration"] == 10 and report["diagnostic"]["trajectories"] == 20
    assert report["trajectories"] == 52
    for record in run.diagnostic.records:
        batch = [load_trajectory(__import__("pathlib").Path(a["path"])) for a in record["archives"]]
        targets = np.array([[sum(t.rewards[j:]) for j in range(180)] for t in batch])
        assert record["D"]["post"]["z"] == pytest.approx(float(np.mean(targets**2)))
    other = make(config, tmp_path, iterations=1, name="d64")
    other.diagnostic.n = 64
    other.run()
    validate_state(other)
    assert other.diagnostic.records[0]["D"]["post"]["count"] == 64 * 180
    assert other.diagnostic.records[0]["overlap"]["exact_A"]["denominator"] == 64


def test_rejects_censored_d_returned_by_faulty_collector(config, tmp_path, monkeypatch):
    from btc_risk_rl.agents.trainer import RunAbort

    run = make(config, tmp_path)
    collect = run.diagnostic.collector.collect

    def partial(*args, **kwargs):
        batch = collect(*args, **kwargs)
        return (batch[0].fragment(0, 60), batch[1])

    monkeypatch.setattr(run.diagnostic.collector, "collect", partial)
    with pytest.raises(RunAbort, match="Incomplete"):
        run.run()
    assert run.failed


def test_cli_rejects_without_importing_config_or_source(tmp_path):
    import subprocess
    import sys

    output = tmp_path / "not-created"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_p2.py",
            "--profile",
            "market",
            "--protocol",
            "/missing/protocol",
            "--config",
            "/missing/config",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2 and "NOT AUTHORIZED" in result.stderr
    assert not output.exists()


def test_output_cannot_reset_global_campaign_budget(tmp_path):
    from btc_risk_rl.pilots.p2_runner import run_synthetic

    output = tmp_path / "p2-approved-v1-synthetic"
    with pytest.raises(ValueError, match="canonical"):
        run_synthetic(output, "/nonexistent/config")
    assert not output.exists()


def test_failed_d_preserves_completed_and_partial_fragments(config, tmp_path, monkeypatch):
    from btc_risk_rl.agents.models import FrozenPolicy
    from btc_risk_rl.agents.trainer import RunAbort

    run = make(config, tmp_path)
    original = FrozenPolicy.sample
    calls = [0]

    def failing(policy, *args, **kwargs):
        if run.phase == "D":
            calls[0] += 1
            if calls[0] == 201:
                raise ValueError("deliberate second D realization failure")
        return original(policy, *args, **kwargs)

    monkeypatch.setattr(FrozenPolicy, "sample", failing)
    with pytest.raises(RunAbort):
        run.run()
    assert len(list((tmp_path / "run" / "D" / "fragments").glob("*.npz"))) == 3
    with np.load(tmp_path / "run" / "D" / "failed-0.npz", allow_pickle=False) as data:
        assert len(data["rewards"]) == 20
    assert run.next_iteration == 0 and run.journal.last()["status"] == "failed"


def test_synthetic_worker_cli_reads_config_and_checkpoints(tmp_path):
    import json
    import subprocess
    import sys
    from dataclasses import asdict
    from pathlib import Path

    from btc_risk_rl.pilots.p2 import P2SyntheticSettings

    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            dict(
                settings=asdict(P2SyntheticSettings(n_q=1)),
                config=str(Path("configs/initial.toml").resolve()),
                root=str(tmp_path / "worker"),
                condition="C0",
                run_id="synthetic-child",
                unit=0,
            )
        )
    )
    child = subprocess.run(
        [sys.executable, "-m", "btc_risk_rl.pilots.p2_runner", "--synthetic-request", str(request)],
        capture_output=True,
        text=True,
    )
    assert child.returncode == 0, child.stderr
    assert (tmp_path / "worker" / "checkpoint-0" / "manifest.json").exists()


def test_p2_budget_rejects_backwards_runtime_clock(tmp_path):
    from btc_risk_rl.pilots.p2_budget import P2Ledger

    with P2Ledger(tmp_path, now=1790222400, identity={}) as ledger:
        with pytest.raises(ValueError, match="backwards"):
            ledger.persist(1790222399)


def test_public_synthetic_supervisor_pauses_resumes_shared_budget(tmp_path, monkeypatch):
    import json
    import time
    from datetime import datetime, timedelta
    from pathlib import Path

    from btc_risk_rl.pilots import p2_runner
    from btc_risk_rl.pilots.budget import LA_PAZ
    from btc_risk_rl.pilots.p2_budget import P2Ledger

    root = tmp_path / "p2-approved-v1-synthetic"
    monkeypatch.setattr(p2_runner, "SYNTHETIC_ROOT", root)
    other = tmp_path / "p0-approved-v1"
    other.mkdir()
    local_now = datetime.fromtimestamp(time.time(), LA_PAZ)
    midnight = datetime.combine(local_now.date() + timedelta(days=1),
                                datetime.min.time(), LA_PAZ).timestamp()
    if midnight - time.time() < 3700:
        pytest.skip("real La Paz midnight leaves no approved Q0 admission window")
    day = local_now.date().isoformat()
    (other / "ledger.jsonl").write_text(
        json.dumps(dict(status="completed", days={day: {"charged_wall_seconds": 1000}})) + "\n"
    )
    admit = P2Ledger.admit
    for unit in range(3):
        calls = [0]

        def once(self, *args):
            calls[0] += 1
            return admit(self, *args) if calls[0] == 1 else "pause"

        monkeypatch.setattr(P2Ledger, "admit", once)
        state = p2_runner.run_synthetic(root, Path("configs/initial.toml"))
        assert state["status"] == "ready"
        assert state["runs"]["run-00-C0"]["next_unit"] == unit + 1
        assert state["days"][day]["external_seconds"] == 1000
    assert state["resources"]["diagnostic_trajectories"] == 4
    assert state["resources"]["trajectories"] == 12
    assert len(state["runs"]["run-00-C0"]["days"]) == 1


def test_p2_initial_full_A_risk_gradient_and_denominators(config, tmp_path):
    from btc_risk_rl.pilots.p2_metrics import learning_rates

    run = make(config, tmp_path)
    report = run.run()
    rates = learning_rates(report)
    assert rates["critic"]["completed"] == rates["critic"]["expected"] == 8
    assert rates["risk_active_iterations"]["denominator"] == 2
    assert rates["risk_active_after_initial"]["denominator"] == 1
    before = [
        r
        for r in run.telemetry.stability
        if r["phase"] == "fixed_A" and r["measurement"] == "before_actor"
    ]
    for record, prior in zip(run.diagnostic.records, before):
        assert record["risk"]["initial_total_gradient_norm"] >= 0
        assert record["risk"]["initial_risk_gradient_norm"] == pytest.approx(
            prior["initial_risk_gradient_norm"], abs=1e-12
        )
        assert record["risk"]["shortfalls"]["denominator"] == 1


def test_p2_counts_sessions_separately_from_days_and_completion_is_readonly(tmp_path):
    from btc_risk_rl.pilots.p2_budget import P2Ledger

    t = 1790222400
    root = tmp_path / "sessions"
    for j in range(3):
        now = t + j * 100
        with P2Ledger(root, now=now, identity={}) as ledger:
            ledger.preflight_done(now + 1)
            ledger.begin("r", "q0", now + 2)
            ledger.finish(now + 3, resources={}, condition="C0")
    with P2Ledger(root, now=t + 301, identity={}) as ledger:
        with pytest.raises(ValueError, match="sessions"):
            ledger.begin("r", "q0", t + 302)
        assert ledger.state["status"] == "incomplete"
    complete = tmp_path / "complete"
    with P2Ledger(complete, now=t, identity={}) as ledger:
        ledger.state["status"] = "completed"
        ledger.persist(t + 1)
    original = (complete / "ledger.jsonl").read_bytes()
    for offset in (12000, 4 * 86400):
        with P2Ledger(complete, now=t + offset, identity={}) as ledger:
            assert ledger.state["status"] == "completed"
    assert (complete / "ledger.jsonl").read_bytes() == original
