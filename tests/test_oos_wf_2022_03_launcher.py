"""Initial WF 2022-03 admission is read-only until every gate passes."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest


def _epoch(hour, minute=0):
    return datetime(2026, 11, 10, hour, minute,
                    tzinfo=ZoneInfo("America/La_Paz")).timestamp()


def test_launcher_rejects_closed_gate_before_preflight(monkeypatch, tmp_path):
    from btc_risk_rl.pilots import wf_cost_2022_03_launch as launch

    monkeypatch.setattr(launch, "CAMPAIGN", tmp_path / "absent")
    monkeypatch.setattr(launch, "require_campaign", lambda: (_ for _ in ()).throw(
        PermissionError("closed")))
    with pytest.raises(PermissionError, match="closed"):
        launch.launch_once(now=_epoch(1), preflight=lambda: (_ for _ in ()).throw(
            AssertionError("preflight accessed")), invoke=lambda _action: (_ for _ in ()).throw(
                AssertionError("training invoked")))
    assert not launch.CAMPAIGN.exists()


def test_launcher_skips_outside_window_and_blocked_preflight(monkeypatch, tmp_path):
    from btc_risk_rl.pilots import wf_cost_2022_03_launch as launch

    monkeypatch.setattr(launch, "CAMPAIGN", tmp_path / "absent")
    monkeypatch.setattr(launch, "require_campaign", lambda: {"authorized": True})
    invoked = []
    assert launch.launch_once(now=_epoch(0, 59), preflight=lambda: {"status": "ready"},
                              invoke=invoked.append)["status"] == "outside_window"
    assert launch.launch_once(now=_epoch(9), preflight=lambda: {"status": "ready"},
                              invoke=invoked.append)["status"] == "outside_window"
    assert launch.launch_once(now=_epoch(8, 40), preflight=lambda: {"status": "ready"},
                              invoke=invoked.append)["status"] == "insufficient_window"
    assert launch.launch_once(now=_epoch(1), preflight=lambda: {"status": "blocked"},
                              invoke=invoked.append)["status"] == "blocked"
    assert not invoked
    assert not launch.CAMPAIGN.exists()


def test_launcher_runs_prepare_then_run_only_from_absent_root(monkeypatch, tmp_path):
    from btc_risk_rl.pilots import wf_cost_2022_03_launch as launch

    root = tmp_path / "campaign"
    monkeypatch.setattr(launch, "CAMPAIGN", root)
    monkeypatch.setattr(launch, "require_campaign", lambda: {"authorized": True})
    invoked = []
    result = launch.launch_once(now=_epoch(1), preflight=lambda: {"status": "ready"},
                                invoke=invoked.append)
    assert result["status"] == "launched"
    assert invoked == ["prepare", "run"]
    root.mkdir()
    assert launch.launch_once(now=_epoch(1), preflight=lambda: {"status": "ready"},
                              invoke=invoked.append)["status"] == "root_exists"
    assert invoked == ["prepare", "run"]
