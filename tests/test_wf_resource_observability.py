"""Synthetic evidence for WF resource decisions and durable observations."""

import hashlib
import json

import pytest

from btc_risk_rl.pilots import wf_cost_replacement_04_units as units
from btc_risk_rl.pilots.p2r import P2RJournal

GIB = 1024**3


def snapshot(*, ac=True, battery=50, memory=4 * GIB, disk=20 * GIB):
    return {"power": {"ac": ac, "battery_percent": battery},
            "memory_available_bytes": memory, "disk_free_bytes": disk}


@pytest.mark.parametrize(
    ("observed", "failed"),
    [
        (snapshot(ac=False), "ac"),
        (snapshot(battery=49), "battery"),
        (snapshot(memory=4 * GIB - 1), "memory"),
        (snapshot(disk=20 * GIB - 1), "disk"),
    ],
)
def test_each_failed_resource_records_exact_decision_snapshot(tmp_path, observed, failed):
    assert callable(getattr(units, "observe_resource_guard", None)), "resource observation missing"
    path = tmp_path / "supervisor.jsonl"
    journal = P2RJournal(path, campaign="synthetic-only")
    accepted = units.observe_resource_guard(
        journal, observed, run_id="synthetic", unit=1,
        phase="Q", disposition="fail",
    )
    assert accepted is False
    assert units.resource_ready(observed) is False
    row = json.loads(path.read_text().splitlines()[-1])
    assert row["event"] == "resource_guard_failed"
    assert row["resource_snapshot"] == observed
    assert row["failed_checks"] == [failed]
    assert row["disposition"] == "fail"
    assert row["resource_limits"] == {
        "battery_min_percent": 50,
        "memory_min_bytes": 4 * GIB,
        "disk_min_bytes": 20 * GIB,
        "ac_required": True,
    }
    assert P2RJournal(path, campaign="synthetic-only").last["sha256"] == row["sha256"]


def test_boundary_values_pass_without_failure_record(tmp_path):
    assert callable(getattr(units, "observe_resource_guard", None)), "resource observation missing"
    path = tmp_path / "supervisor.jsonl"
    journal = P2RJournal(path, campaign="synthetic-only")
    observed = snapshot()
    assert units.observe_resource_guard(
        journal, observed, run_id="synthetic", unit=2,
        phase="between_units", disposition="pause",
    ) is True
    assert units.resource_ready(observed) is True
    assert not path.exists()


def test_pause_records_values_and_preserves_synthetic_artifacts(tmp_path):
    assert callable(getattr(units, "observe_resource_guard", None)), "resource observation missing"
    campaign = tmp_path / "synthetic-campaign"
    checkpoint = campaign / "checkpoint-0"
    checkpoint.mkdir(parents=True)
    (checkpoint / "state.pt").write_bytes(b"accepted synthetic checkpoint")
    (campaign / "ledger.jsonl").write_text('{"status":"ready","pending":null}\n')
    def hashes():
        return {str(path.relative_to(campaign)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in campaign.rglob("*") if path.is_file() and path.name != "supervisor.jsonl"}
    before = hashes()
    journal = P2RJournal(campaign / "supervisor.jsonl", campaign="synthetic-only")
    observed = snapshot(ac=False, battery=49, memory=4 * GIB - 1, disk=20 * GIB - 1)
    assert units.observe_resource_guard(
        journal, observed, run_id="synthetic", unit=1,
        phase="between_units", disposition="pause",
    ) is False
    assert hashes() == before
    row = json.loads((campaign / "supervisor.jsonl").read_text().splitlines()[-1])
    assert row["failed_checks"] == ["ac", "battery", "memory", "disk"]
    assert row["resource_snapshot"] == observed


def test_unreadable_power_is_labeled_as_missing_measurement(monkeypatch, tmp_path):
    def unreadable():
        raise ValueError("synthetic sensor unavailable")

    monkeypatch.setattr(units, "read_power", unreadable)
    monkeypatch.setattr(units, "CAMPAIGN", tmp_path / "synthetic-campaign")
    observed = units._unit_resources()
    assert observed["power"]["ac"] is False
    assert observed["power"]["battery_percent"] == -1
    assert observed["power"]["values_observed"] is False
    assert "synthetic sensor unavailable" in observed["power"]["sensor_error"]
