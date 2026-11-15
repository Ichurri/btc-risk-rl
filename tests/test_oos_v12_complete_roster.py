"""A complete invented training ledger is required before evaluation."""

import hashlib
import json

import pytest

from btc_risk_rl.pilots.p2_budget import state_hash


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path):
    roster = [(1000 + block, condition, 0)
              for block in range(36) for condition in ("C0", "C5", "C10")]
    freeze = tmp_path / "freeze.json"
    freeze.write_text(json.dumps({
        "status": "training_authorized_evaluation_closed",
        "campaign_roots": {"main-2018-2022": "artifacts/invented-main"},
        "roster": [dict(source="main-2018-2022", block=i // 3,
                        seed=seed, condition=condition, beta=beta)
                   for i, (seed, condition, beta) in enumerate(roster)],
    }))
    root = tmp_path / "artifacts/invented-main"
    root.mkdir(parents=True)
    units, runs = [], {}
    for i, (_, condition, _) in enumerate(roster):
        run = f"run-{i:02d}-{condition}-b0"
        totals = {"trajectories": 0, "actor_updates": 0,
                  "critic_updates": 0, "diagnostic_trajectories": 0}
        for unit in range(11):
            run_root = root / run
            checkpoint = run_root / f"checkpoint-{unit}"
            checkpoint.mkdir(parents=True)
            (checkpoint / "state.pt").write_bytes(f"invented-{i}-{unit}".encode())
            report = run_root / f"unit-{unit}.json"
            request = run_root / f"request-{unit}.json"
            report.write_text(json.dumps({"unit": unit}))
            request.write_text(json.dumps({"unit": unit}))
            resources = {
                "trajectories": 400 if unit == 0 else 864,
                "actor_updates": 0 if unit == 0 else 8,
                "critic_updates": 0 if unit == 0 else 16,
                "diagnostic_trajectories": 0 if unit == 0 else 64,
            }
            for key, value in resources.items():
                totals[key] += value
            units.append({
                "run_id": run, "unit": unit, "seconds": 1.0,
                "checkpoint": str(checkpoint),
                "checkpoint_sha256": _sha(checkpoint / "state.pt"),
                "report_sha256": _sha(report), "request_sha256": _sha(request),
                "resources": resources,
                "supervisor": {"rss_peak_bytes": 1024**2},
            })
        runs[run] = {"resources": totals}
    state = {"previous_hash": None, "status": "completed", "cursor": 108,
             "pending": None, "units": units, "runs": runs,
             "identity": {"profile": "oos_v12_market_units",
                          "roster": [list(row) for row in roster]}}
    state["state_hash"] = state_hash(state)
    (root / "ledger.jsonl").write_text(json.dumps(state, sort_keys=True) + "\n")
    return freeze, root


def test_full_invented_roster_and_all_file_hashes_required(tmp_path):
    from btc_risk_rl.evaluation.complete_roster import verify_complete_main_roster

    freeze, root = _fixture(tmp_path)
    result = verify_complete_main_roster(
        tmp_path, freeze_path=freeze, freeze_sha256=_sha(freeze),
    )
    assert result["complete_runs"] == 108
    assert result["accepted_units"] == 1188
    assert len(result["runs"]) == 108
    assert result["runs"][0]["seed"] == 1000
    (root / "run-00-C0-b0/unit-5.json").write_text("tampered")
    with pytest.raises(ValueError, match="report hash"):
        verify_complete_main_roster(tmp_path, freeze_path=freeze,
                                    freeze_sha256=_sha(freeze))


def test_incomplete_main_ledger_and_changed_freeze_rejected(tmp_path):
    from btc_risk_rl.evaluation.complete_roster import verify_complete_main_roster

    freeze, root = _fixture(tmp_path)
    with pytest.raises(ValueError, match="freeze hash"):
        verify_complete_main_roster(tmp_path, freeze_path=freeze,
                                    freeze_sha256="a" * 64)
    path = root / "ledger.jsonl"
    state = json.loads(path.read_text())
    state["status"] = "ready"
    state["state_hash"] = state_hash(state)
    path.write_text(json.dumps(state) + "\n")
    with pytest.raises(ValueError, match="completed"):
        verify_complete_main_roster(tmp_path, freeze_path=freeze,
                                    freeze_sha256=_sha(freeze))
