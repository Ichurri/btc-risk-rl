"""P2R Q0/Q-A-B-D integration uses fabricated SyntheticMarket routes only."""

import hashlib
import importlib.util
import json
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

import pytest
import torch

from btc_risk_rl.agents.synthetic import SyntheticMarket
from btc_risk_rl.pilots.p2 import P2SyntheticSettings, tree_hash
from btc_risk_rl.pilots.p2_runner import complete_unit
from btc_risk_rl.pilots.p2r import read_worker_progress
from btc_risk_rl.pilots.p2r_units import run_synthetic_units


def fixture_power(tmp_path):
    root = tmp_path / "power"
    for name, kind, field, value in (
        ("ADP1", "Mains", "online", "1"),
        ("BAT1", "Battery", "capacity", "80"),
    ):
        item = root / name
        item.mkdir(parents=True)
        (item / "type").write_text(kind)
        (item / field).write_text(value)
        if kind == "Battery":
            (item / "scope").write_text("System")
    return root


def settings():
    return P2SyntheticSettings(iterations=2, hidden=4, n_a=1, n_q=2, n_b=2,
                               actor_epochs=1, critic_epochs=4, seed=610031)


def run(root, power, *, max_units=None, condition="C5"):
    return run_synthetic_units(
        root, Path("configs/initial.toml"), settings(), condition,
        max_units=max_units, power_root=power, memory_available=4 * 1024**3,
        disk_free=10 * 1024**3, fixture_window=True, heartbeat_seconds=.05,
    )


def checkpoint_state(root, condition, unit):
    return torch.load(root / f"run-00-{condition}" / f"checkpoint-{unit}" / "state.pt",
                      map_location="cpu", weights_only=True)


def assert_learning_equal(left, right):
    for key in ("actor", "critic", "actor_optimizer", "critic_optimizer"):
        assert tree_hash(left[key]) == tree_hash(right[key])
    for key in ("eta", "multiplier", "generation", "next_iteration", "boundary",
                "actor_updates", "critic_updates", "events", "audits"):
        assert tree_hash(left["attrs"][key]) == tree_hash(right["attrs"][key])
    for key in ("used", "transitions", "trajectories"):
        assert left["collector"][key] == right["collector"][key]


def test_q0_and_iteration_match_existing_algorithm(config, tmp_path):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    power = fixture_power(tmp_path)
    integrated = tmp_path / "artifacts" / "p2r-synthetic-integrated"
    state = run(integrated, power, max_units=2)
    assert state["status"] == "ready"
    assert [(u["unit"], u["resources"]) for u in state["units"]] == [
        (0, dict(trajectories=2, transitions=360, diagnostic_trajectories=0,
                 diagnostic_transitions=0, actor_updates=0, critic_updates=0)),
        (1, dict(trajectories=5, transitions=900, diagnostic_trajectories=2,
                 diagnostic_transitions=360, actor_updates=1, critic_updates=4)),
    ]
    work = integrated / "run-00-C5"
    assert [json.loads((work / f"checkpoint-{i}" / "manifest.json").read_text())["boundary"]
            for i in (0, 1)] == ["after_q0", "after_dual_and_D"]

    reference = tmp_path / "reference"
    source = SyntheticMarket(config)
    first = complete_unit(source, settings(), root=reference, condition="C5",
                          run_id="run-00-C5", unit=0)
    second = complete_unit(source, settings(), root=reference, condition="C5",
                           run_id="run-00-C5", unit=1, previous=first["checkpoint"])
    assert [first["resources"], second["resources"]] == [u["resources"] for u in state["units"]]
    for unit in (0, 1):
        assert_learning_equal(checkpoint_state(integrated, "C5", unit),
                              torch.load(reference / f"checkpoint-{unit}" / "state.pt",
                                         map_location="cpu", weights_only=True))


@pytest.mark.parametrize("cut", [1, 2])
def test_resume_from_complete_boundary_matches_continuous(tmp_path, cut):
    power = fixture_power(tmp_path)
    continuous = tmp_path / "artifacts" / "p2r-synthetic-continuous"
    resumed = tmp_path / "artifacts" / "p2r-synthetic-resumed"
    full = run(continuous, power)
    assert full["status"] == "completed" and len(full["units"]) == 3
    partial = run(resumed, power, max_units=cut)
    assert partial["status"] == "ready" and len(partial["units"]) == cut
    before = {str(p.relative_to(resumed)): p.read_bytes()
              for p in (resumed / "run-00-C5" / "D").glob("*.npz")}
    done = run(resumed, power)
    assert done["status"] == "completed" and len(done["units"]) == 3
    assert all((resumed / name).read_bytes() == data for name, data in before.items())
    assert done["resources"] == full["resources"]
    assert_learning_equal(checkpoint_state(continuous, "C5", 2),
                          checkpoint_state(resumed, "C5", 2))


@pytest.mark.parametrize("interrupt_unit", [0, 1])
def test_signal_inside_unit_fails_permanently(tmp_path, monkeypatch, interrupt_unit):
    import btc_risk_rl.pilots.p2r_units as units

    power = fixture_power(tmp_path)
    root = tmp_path / "artifacts" / f"p2r-synthetic-signal-{interrupt_unit}"
    if interrupt_unit:
        state = run(root, power, max_units=1)
        assert len(state["units"]) == 1
        checkpoint = root / "run-00-C5" / "checkpoint-0" / "state.pt"
        prior_sha = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    actual_supervise = units.supervise

    def signal_on_first_poll(*args, **kwargs):
        original = kwargs["on_poll"]
        sent = False

        def send(pid, elapsed, peak):
            nonlocal sent
            original(pid, elapsed, peak)
            if not sent:
                sent = True
                os.kill(os.getpid(), signal.SIGTERM)

        kwargs["on_poll"] = send
        return actual_supervise(*args, **kwargs)

    monkeypatch.setattr(units, "supervise", signal_on_first_poll)
    failed = run(root, power)
    assert failed["status"] == "failed"
    assert failed["failure"]["reason"] == "interrupted_supervisor_or_unit"
    assert len(failed["units"]) == interrupt_unit
    assert not (root / "run-00-C5" / f"checkpoint-{interrupt_unit}").exists()
    if interrupt_unit:
        assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == prior_sha
        assert failed["units"][0]["checkpoint_sha256"] == prior_sha
    with pytest.raises(ValueError, match="failed/incomplete"):
        run(root, power)


def test_market_profile_still_rejected_before_output(tmp_path):
    out = tmp_path / "artifacts" / "p2r-market-forbidden"
    command = [sys.executable, "scripts/run_p2r.py", "--profile", "market",
               "--mode", "algorithm", "--hold-seconds", "900", "--output", str(out)]
    result = __import__("subprocess").run(command, text=True, capture_output=True)
    assert result.returncode != 0 and "NOT AUTHORIZED" in result.stderr
    assert not out.exists()


def test_cli_exits_nonzero_when_synthetic_unit_failed(tmp_path, monkeypatch, capsys):
    import btc_risk_rl.pilots.p2r_units as units

    spec = importlib.util.spec_from_file_location("run_p2r", Path("scripts/run_p2r.py"))
    run_p2r = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run_p2r)
    monkeypatch.setattr(units, "run_synthetic_units",
                        lambda *args, **kwargs: {"status": "failed", "units": []})
    monkeypatch.setattr(sys, "argv", ["run_p2r.py", "--profile", "synthetic",
                                     "--mode", "algorithm", "--output",
                                     str(tmp_path / "p2r-synthetic-cli-failed")])
    with pytest.raises(SystemExit) as exit_info:
        run_p2r.main()
    assert exit_info.value.code == 1
    assert json.loads(capsys.readouterr().out) == {"status": "failed", "units": 0}


def test_previous_progress_is_not_misreported_as_new_unit(tmp_path):
    (tmp_path / "progress.json").write_text(json.dumps(
        {"unit": 0, "phase": "Q0", "counters": {"trajectories": 2}}))
    assert read_worker_progress(tmp_path, 1, allow_previous=True) == ("unknown", {})
    with pytest.raises(ValueError, match="Invalid worker progress"):
        read_worker_progress(tmp_path, 1)


def test_corrupt_preceding_checkpoint_fails_without_selective_replay(tmp_path):
    power = fixture_power(tmp_path)
    root = tmp_path / "artifacts" / "p2r-synthetic-corrupt"
    first = run(root, power, max_units=1)
    assert first["status"] == "ready" and len(first["units"]) == 1
    state_path = root / "run-00-C5" / "checkpoint-0" / "state.pt"
    state_path.write_bytes(b"corrupt synthetic checkpoint")
    failed = run(root, power)
    assert failed["status"] == "failed" and len(failed["units"]) == 1
    assert not (root / "run-00-C5" / "checkpoint-1").exists()
    with pytest.raises(ValueError, match="failed/incomplete"):
        run(root, power)


def test_default_heartbeat_is_recorded_within_five_seconds(tmp_path):
    power = fixture_power(tmp_path)
    root = tmp_path / "artifacts" / "p2r-synthetic-heartbeat-clock"
    result = run_synthetic_units(
        root, Path("configs/initial.toml"), settings(), "C5", max_units=1,
        power_root=power, memory_available=4 * 1024**3,
        disk_free=10 * 1024**3, fixture_window=True,
        synthetic_hold_seconds=12,
    )
    assert result["status"] == "ready" and len(result["units"]) == 1
    rows = [json.loads(line) for line in (root / "supervisor.jsonl").read_text().splitlines()]
    heartbeats = [datetime.fromisoformat(row["utc"]) for row in rows
                  if row["event"] == "heartbeat"]
    gaps = [(later - earlier).total_seconds()
            for earlier, later in zip(heartbeats, heartbeats[1:])]
    assert len(gaps) >= 2
    assert max(gaps) <= 5.0, gaps


def test_late_recorded_heartbeat_invalidates_synthetic_unit(tmp_path, monkeypatch):
    import btc_risk_rl.pilots.supervisor as supervision

    power = fixture_power(tmp_path)
    root = tmp_path / "artifacts" / "p2r-synthetic-heartbeat-late"
    actual_sleep = supervision.time.sleep
    delayed = False

    def delayed_first_poll(seconds):
        nonlocal delayed
        if not delayed:
            delayed = True
            return actual_sleep(5.2)
        return actual_sleep(seconds)

    monkeypatch.setattr(supervision.time, "sleep", delayed_first_poll)
    with pytest.raises(ValueError, match="heartbeat interval"):
        run_synthetic_units(
            root, Path("configs/initial.toml"), settings(), "C5", max_units=1,
            power_root=power, memory_available=4 * 1024**3,
            disk_free=10 * 1024**3, fixture_window=True,
            synthetic_hold_seconds=12,
        )
    ledger = json.loads((root / "ledger.jsonl").read_text().splitlines()[-1])
    assert ledger["status"] == "failed" and not ledger["units"]
    assert "heartbeat interval" in ledger["failure"]["error"]
    assert not (root / "run-00-C5" / "checkpoint-0").exists()
