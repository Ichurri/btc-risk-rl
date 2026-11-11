"""Independent synthetic arithmetic for the OOS legacy budget reconstruction."""

import pytest


def _unit(run_id, kind, unit, start, work_ended, end, work_seconds):
    return dict(run_id=run_id, kind=kind, unit=unit, start=start,
                work_ended=work_ended, end=end, work_seconds=work_seconds)


def test_reconstruction_uses_later_begin_and_condition_specific_history():
    from btc_risk_rl.pilots.oos_v12_audit import reconstruct_admissions

    units = [
        _unit("run-00-C0-b0", "q0", 0, 100, 110, 111, 10),
        _unit("run-00-C0-b0", "iteration", 1, 200, 220, 221, 20),
        _unit("run-01-C0-b0", "q0", 0, 300, 310, 311, 10),
        _unit("run-01-C0-b0", "iteration", 1, 400, 430, 431, 30),
        _unit("run-02-C5-b0", "iteration", 1, 500, 530, 531, 30),
    ]
    result = reconstruct_admissions(units, preparation_start=0, nine_epoch=20000)
    rows = result["units"]
    assert [r["required_seconds"] for r in rows] == [1800, 2700, 15, 30, 2700]
    assert result["counterfactual_hard_deadline"] == 10800
    assert result["counterfactual_work_deadline"] == 8100
    assert rows[-1]["admission_margin_seconds"] == pytest.approx(4900)
    assert result["all_fit_at_recorded_begin"] is True


def test_reconstruction_rejects_a_unit_that_cannot_fit_with_reserve():
    from btc_risk_rl.pilots.oos_v12_audit import reconstruct_admissions

    units = [_unit("run-00-C10-b0", "iteration", 1, 8000, 8050, 8051, 50)]
    result = reconstruct_admissions(units, preparation_start=0, nine_epoch=20000)
    assert result["units"][0]["admission_margin_seconds"] == pytest.approx(-2600)
    assert result["all_fit_at_recorded_begin"] is False


def test_reconstruction_includes_other_registered_debit_and_window():
    from btc_risk_rl.pilots.oos_v12_audit import reconstruct_admissions

    units = [_unit("run-00-C0-b0", "q0", 0, 6100, 6200, 6201, 100)]
    result = reconstruct_admissions(units, preparation_start=0, nine_epoch=9000,
                                    other_registered_seconds=1000)
    assert result["counterfactual_hard_deadline"] == 9000
    assert result["counterfactual_work_deadline"] == 6300
    assert result["units"][0]["admission_margin_seconds"] == pytest.approx(-1600)
