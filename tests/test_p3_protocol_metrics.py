"""P3 v1.1 decisions on fabricated H180 observations; no market trajectories."""

import hashlib
import json

import numpy as np
import pytest

from btc_risk_rl.pilots.p2_metrics import full_metric
from btc_risk_rl.pilots.p3_market import P3MarketSettings, roster
from btc_risk_rl.pilots.p3_metrics import assess_campaign, assess_pair, pool_exact
from btc_risk_rl.pilots.p3_units import assess_completed_campaign


def test_protocol_roster_and_settings_are_exactly_eighteen_new_runs():
    rows = roster()
    assert len(rows) == len(set(rows)) == 18
    assert rows[:6] == [
        (710031, "C0", 0), (710031, "C0", 1),
        (710031, "C5", 1), (710031, "C5", 0),
        (710031, "C10", 0), (710031, "C10", 1),
    ]
    assert rows[-2:] == [(710081, "C5", 0), (710081, "C5", 1)]
    settings = P3MarketSettings(seed=710031, critic_beta=1)
    assert (settings.iterations, settings.n_a, settings.n_q, settings.n_b) == (
        10, 64, 400, 400
    )
    assert (settings.critic_epochs, settings.actor_epochs, settings.bound) == (
        4, 2, 0.10536051565782628
    )
    with pytest.raises(ValueError):
        P3MarketSettings(seed=610031, critic_beta=1)
    with pytest.raises(ValueError):
        P3MarketSettings(seed=710031, critic_beta=2)
    with pytest.raises(ValueError):
        P3MarketSettings(seed=710031, critic_beta=1, critic_epochs=2)


def record(prediction, target):
    p = np.full((1, 180), prediction, dtype=np.float64)
    g = np.full((1, 180), target, dtype=np.float64)
    m = full_metric(p, g)
    return {"A": {"pre": m, "post": m}, "D": {"pre": m, "post": m}}


def records(prediction, target):
    return [dict(iteration=k, **record(prediction, target)) for k in range(10)]


def test_exact_zero_predictor_and_undefined_denominator():
    small = pool_exact([record(0.0, 1e-7)["D"]["post"]])
    assert small["z"] == pytest.approx(1e-14)
    assert small["r0"] == pytest.approx(1.0)
    assert small["r_epsilon"] < 0.95  # Old rule would pass the zero predictor.
    assert small["informative"] is False
    zero = pool_exact([record(0.0, 0.0)["D"]["post"]])
    assert zero["z"] == 0 and zero["r0"] is None and zero["b0"] is None


def test_paired_arms_use_their_own_targets_and_all_four_z_gates():
    pair = assess_pair(records(0.0, 1.0), records(0.8, 1.0))
    assert pair["informative"] is True
    assert pair["advance"] is True
    assert pair["delta_d"] == pytest.approx(-0.96)
    assert pair["delta_d3"] == pytest.approx(-0.96)
    assert pair["delta_a"] == pytest.approx(-0.96)
    assert pair["h1"] == pytest.approx(0.0)
    assert pair["checks"]["zero_exact"] is True
    assert pair["treatment"]["A_pre_early_third1"]["n"] == 3 * 60
    assert pair["treatment"]["D_post_late_third3"]["n"] == 3 * 60
    late = pair["treatment"]["D_post_late"]
    assert late["excess_mse"] == pytest.approx(late["e_v2"] - 2 * late["e_vg"])

    different_targets = assess_pair(records(0.0, 1.0), records(1.6, 2.0))
    assert different_targets["treatment"]["D_post_late"]["z"] == 4.0
    assert different_targets["delta_d"] == pytest.approx(-0.96)

    weak_last_third = records(0.8, 1.0)
    weak = full_metric(
        np.concatenate((np.full((1, 120), 0.8), np.zeros((1, 60))), axis=1),
        np.concatenate((np.ones((1, 120)), np.zeros((1, 60))), axis=1),
    )
    for k in (7, 8, 9):
        weak_last_third[k]["D"]["post"] = weak
    gate = assess_pair(records(0.0, 1.0), weak_last_third)
    assert gate["informative"] is False
    assert "treatment/D_late_third3" in gate["missing_z_gates"]
    assert gate["delta_d3"] is None


def test_campaign_counts_seed_blocks_not_nine_conditions():
    successful = []
    for seed, condition, beta in roster():
        successful.append(dict(seed=seed, condition=condition, beta=beta,
                               status="passed", records=records(0.0 if beta == 0 else 0.8, 1.0)))
    result = assess_campaign(successful)
    assert result["decision"] == "advance_to_discussion"
    assert result["independent_seed_blocks"] == 3
    assert result["seed_blocks_passing"] == 3
    successful[0]["status"] = "failed"
    assert assess_campaign(successful)["decision"] == "not_evaluable"


def test_completed_campaign_adjudicates_only_hash_pinned_reports(tmp_path):
    from btc_risk_rl.pilots.p3_market import run_id_for

    units = []
    for index, row in enumerate(roster()):
        seed, condition, beta = row
        run_id = run_id_for(index, row)
        work = tmp_path / run_id
        work.mkdir()
        for unit in range(11):
            point = work / f"checkpoint-{unit}"
            point.mkdir()
            state = point / "state.pt"
            state.write_bytes(f"synthetic-{index}-{unit}".encode())
            sha = hashlib.sha256(state.read_bytes()).hexdigest()
            payload = dict(beta=beta, checkpoint_sha256=sha,
                           report=dict(settings=dict(critic_beta=beta)))
            if unit == 10:
                payload["report"]["diagnostic"] = dict(
                    records=records(0.0 if beta == 0 else 0.8, 1.0),
                    trajectories=640, transitions=640 * 180,
                )
            path = work / f"unit-{unit}.json"
            path.write_text(json.dumps(payload))
            units.append(dict(run_id=run_id, unit=unit, checkpoint_sha256=sha,
                              report_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    state = dict(cursor=18, units=units)
    assert assess_completed_campaign(tmp_path, state)["decision"] == "advance_to_discussion"
    (tmp_path / "run-00-C0-b0/unit-0.json").write_text("{}")
    assert assess_completed_campaign(tmp_path, state)["decision"] == "not_evaluable"
