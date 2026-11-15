"""Synthetic evaluation records cannot admit partial or altered policies."""

import json
import subprocess
import sys

import pytest


def _identity():
    return {
        "partition": "technical_2023", "approval_sha256": "a" * 64,
        "training_ledger_sha256": "b" * 64,
        "export_manifest_sha256": "c" * 64,
        "roster": [
            {"run_id": "run-00-C0-b0", "seed": 101, "condition": "C0",
             "checkpoint_sha256": "d" * 64},
            {"run_id": "run-01-C5-b0", "seed": 101, "condition": "C5",
             "checkpoint_sha256": "e" * 64},
        ],
    }


def test_complete_boundary_survives_new_process_and_preserves_plan(tmp_path):
    from btc_risk_rl.evaluation.ledger import EvaluationLedger

    root = tmp_path / "invented-evaluation"
    ledger = EvaluationLedger.create(root, _identity())
    first = _identity()["roster"][0]
    ledger.begin(first, token="token-0")
    ledger.accept(first, token="token-0", report_sha256="f" * 64,
                  trace_sha256="1" * 64, seconds=2.5)
    assert ledger.state["status"] == "ready"
    assert ledger.state["cursor"] == 1
    script = """
import json, sys
from pathlib import Path
from btc_risk_rl.evaluation.ledger import EvaluationLedger
root, identity = Path(sys.argv[1]), json.loads(sys.argv[2])
reopened = EvaluationLedger.open(root, identity)
second = identity['roster'][1]
reopened.begin(second, token='token-1')
reopened.accept(second, token='token-1', report_sha256='2' * 64,
                trace_sha256='3' * 64, seconds=3.5)
"""
    subprocess.run([sys.executable, "-c", script, str(root), json.dumps(_identity())],
                   check=True, capture_output=True, text=True)
    reopened = EvaluationLedger.open(root, _identity())
    assert reopened.state["status"] == "completed"
    assert reopened.state["cursor"] == 2
    assert len(reopened.state["accepted"]) == 2
    assert len((root / "ledger.jsonl").read_text().splitlines()) == 5
    with pytest.raises(FileExistsError):
        EvaluationLedger.create(root, _identity())


def test_orphaned_partial_unit_is_failed_and_cannot_resume(tmp_path):
    from btc_risk_rl.evaluation.ledger import EvaluationLedger

    root = tmp_path / "invented-evaluation"
    ledger = EvaluationLedger.create(root, _identity())
    first = _identity()["roster"][0]
    ledger.begin(first, token="token-0")
    reopened = EvaluationLedger.open(root, _identity())
    assert reopened.state["status"] == "running"
    reopened.mark_interrupted("process_lost")
    assert reopened.state["status"] == "failed"
    assert reopened.state["accepted"] == []
    with pytest.raises(ValueError, match="failed"):
        reopened.begin(first, token="retry")
    assert EvaluationLedger.open(root, _identity()).state["status"] == "failed"


def test_altered_identity_token_or_ledger_is_rejected(tmp_path):
    from btc_risk_rl.evaluation.ledger import EvaluationLedger

    root = tmp_path / "invented-evaluation"
    ledger = EvaluationLedger.create(root, _identity())
    first = _identity()["roster"][0]
    with pytest.raises(ValueError, match="pending"):
        ledger.accept(first, token="not-started", report_sha256="f" * 64,
                      trace_sha256="1" * 64, seconds=1.0)
    with pytest.raises(ValueError, match="roster"):
        ledger.begin(_identity()["roster"][1], token="wrong")
    ledger.begin(first, token="token-0")
    with pytest.raises(ValueError, match="token"):
        ledger.accept(first, token="wrong", report_sha256="f" * 64,
                      trace_sha256="1" * 64, seconds=1.0)
    changed = _identity()
    changed["roster"][0]["seed"] = 102
    with pytest.raises(ValueError, match="identity"):
        EvaluationLedger.open(root, changed)
    path = root / "ledger.jsonl"
    lines = path.read_text().splitlines()
    forged = json.loads(lines[-1])
    forged["cursor"] = 1
    lines[-1] = json.dumps(forged)
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="chain"):
        EvaluationLedger.open(root, _identity())
