"""The technical gate is an all-policy integrity decision, not selection."""

import hashlib
import json

import pytest


def _roster(blocks):
    return [
        {"run_id": f"run-{3 * block + offset:02d}-{condition}-b{block}",
         "seed": 100 + block, "condition": condition,
         "checkpoint_sha256": "a" * 64}
        for block in range(blocks)
        for offset, condition in enumerate(("C0", "C5", "C10"))
    ]


def test_technical_roster_requires_complete_paired_blocks_and_defined_sortino():
    from btc_risk_rl.evaluation.technical_closure import check_technical_decision

    roster = _roster(1)
    reports = [{"sortino_annualized": value} for value in (0.0, -3.0, 2.0)]
    assert check_technical_decision(roster, reports, expected_blocks=1) == 3
    with pytest.raises(ValueError, match="undefined"):
        check_technical_decision(roster, reports[:2] + [{"sortino_annualized": None}],
                                 expected_blocks=1)
    with pytest.raises(ValueError, match="paired"):
        altered = [dict(row) for row in roster]
        altered[2]["seed"] += 1
        check_technical_decision(altered, reports, expected_blocks=1)
    with pytest.raises(ValueError, match="complete"):
        check_technical_decision(roster, reports[:2], expected_blocks=1)


def test_technical_closure_rejects_incomplete_ledger_before_writing(tmp_path):
    from btc_risk_rl.evaluation.ledger import EvaluationLedger
    from btc_risk_rl.evaluation.technical_closure import write_technical_closure

    roster = _roster(36)
    ledger = EvaluationLedger.create(tmp_path / "invented-technical", {
        "partition": "technical_2023", "approval_sha256": "b" * 64,
        "training_ledger_sha256": "c" * 64,
        "export_manifest_sha256": "d" * 64, "roster": roster,
    })
    destination = tmp_path / "technical-closure.json"
    with pytest.raises(ValueError, match="complete"):
        write_technical_closure(ledger, destination, expected_roster=roster,
                                config=None, code_sha256="e" * 64)
    assert not destination.exists()


def test_technical_closure_records_only_integrity_after_108_complete_units(
        tmp_path, monkeypatch):
    from btc_risk_rl.evaluation import technical_closure
    from btc_risk_rl.evaluation.ledger import EvaluationLedger

    roster = _roster(36)
    ledger = EvaluationLedger.create(tmp_path / "invented-technical", {
        "partition": "technical_2023", "approval_sha256": "b" * 64,
        "training_ledger_sha256": "c" * 64,
        "export_manifest_sha256": "d" * 64, "roster": roster,
    })
    for index, run in enumerate(roster):
        output = ledger.root / run["run_id"]
        output.mkdir()
        (output / "report.json").write_text(json.dumps({
            "sortino_annualized": -2.0 if index % 2 else 3.0,
        }))
        ledger.begin(run, token=f"unit-{index}")
        ledger.accept(run, token=f"unit-{index}", report_sha256="e" * 64,
                      trace_sha256="f" * 64, seconds=1.0)
    checked = []
    def fake_trace_audit(actual, *, config):
        checked.append(actual.state["cursor"])
        return 108

    monkeypatch.setattr(technical_closure, "verify_accepted_outputs",
                        fake_trace_audit)
    destination = tmp_path / "technical-closure.json"
    closure = technical_closure.write_technical_closure(
        ledger, destination, expected_roster=roster,
        config=None, code_sha256="a" * 64,
    )
    assert checked == [108]
    assert closure["status"] == "passed"
    assert closure["complete_policies"] == 108
    assert closure["evaluation_ledger_sha256"] == hashlib.sha256(
        ledger.path.read_bytes()).hexdigest()
    assert "sortino" not in destination.read_text()
    with pytest.raises(FileExistsError):
        technical_closure.write_technical_closure(
            ledger, destination, expected_roster=roster,
            config=None, code_sha256="a" * 64,
        )
    with pytest.raises(ValueError, match="roster"):
        technical_closure.write_technical_closure(
            ledger, tmp_path / "different.json", expected_roster=roster[::-1],
            config=None, code_sha256="a" * 64,
        )
