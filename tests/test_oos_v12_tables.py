"""Tables use only complete, identity-matched OOS runs."""

import hashlib

import pytest

ROSTER = [(seed, condition, 0) for seed in (101, 102, 103)
          for condition in ("C0", "C5", "C10")]


def _state(tmp_path, *, units=11):
    run = "run-00-C0-b0"
    accepted = []
    for unit in range(units):
        root = tmp_path / run / f"checkpoint-{unit}"
        root.mkdir(parents=True)
        payload = f"synthetic-{unit}".encode()
        (root / "state.pt").write_bytes(payload)
        accepted.append({"run_id": run, "unit": unit, "seconds": 5.0,
                         "checkpoint": str(root),
                         "checkpoint_sha256": hashlib.sha256(payload).hexdigest(),
                         "resources": {"trajectories": 1, "actor_updates": int(unit > 0),
                                       "critic_updates": 2 * int(unit > 0),
                                       "diagnostic_trajectories": int(unit > 0)},
                         "supervisor": {"rss_peak_bytes": (unit + 1) * 1024**2}})
    resources = {key: sum(row["resources"][key] for row in accepted)
                 for key in accepted[0]["resources"]}
    return {"status": "ready", "cursor": int(units == 11), "pending": None,
            "identity": {"profile": "oos_v12_market_units",
                         "roster": [list(x) for x in ROSTER]},
            "runs": {run: {"resources": resources}}, "units": accepted}


def test_table_lists_only_complete_run_and_verified_checkpoint(tmp_path):
    from btc_risk_rl.reporting.oos_tables import completed_run_rows, render_markdown_table

    state = _state(tmp_path)
    rows = completed_run_rows("wf-2022", state, ROSTER, root=tmp_path)
    assert len(rows) == 1
    assert rows[0]["seed"] == 101
    assert rows[0]["condition"] == "C0"
    assert rows[0]["unit_seconds"] == 55.0
    assert rows[0]["actor_updates"] == 10
    assert rows[0]["critic_updates"] == 20
    assert rows[0]["peak_rss_mib"] == 11.0
    markdown = render_markdown_table(rows, profile="wf-2022", ledger_sha256="a" * 64)
    assert "55,000" in markdown
    assert "Trayectorias" in markdown
    assert "C0" in markdown
    assert "C5" not in markdown


def test_partial_run_is_not_a_comparable_table_row(tmp_path):
    from btc_risk_rl.reporting.oos_tables import completed_run_rows

    state = _state(tmp_path, units=3)
    assert completed_run_rows("wf-2022", state, ROSTER, root=tmp_path) == []


def test_table_rejects_altered_roster_and_checkpoint(tmp_path):
    from btc_risk_rl.reporting.oos_tables import completed_run_rows

    state = _state(tmp_path)
    altered = ROSTER.copy()
    altered[0] = (999, "C0", 0)
    with pytest.raises(ValueError, match="roster"):
        completed_run_rows("wf-2022", state, altered, root=tmp_path)
    (tmp_path / "run-00-C0-b0/checkpoint-5/state.pt").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checkpoint"):
        completed_run_rows("wf-2022", state, ROSTER, root=tmp_path)
