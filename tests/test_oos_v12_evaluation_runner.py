"""Real synthetic evaluation units pass through the durable batch boundary."""

import hashlib
import json

import numpy as np
import pandas as pd
import pytest
import torch

from btc_risk_rl.agents.models import Actor
from btc_risk_rl.config import STEP_MS
from btc_risk_rl.evaluation.historical_path import PERIODS
from btc_risk_rl.features.market import FEATURES, TrainScaler


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path):
    start, end, steps = PERIODS["technical_2023"]
    n = steps + 43
    times = start - 43 * STEP_MS + np.arange(n, dtype=np.int64) * STEP_MS
    prices = 100 + np.arange(n) * 0.001
    export = tmp_path / "invented-export"
    export.mkdir()
    pd.DataFrame({
        "open_time_ms": times, "close_time_ms": times + STEP_MS - 1,
        "open": prices, "high": prices + 0.3,
        "low": prices - 0.3, "close": prices + 0.1,
        "volume": np.full(n, 50.0),
    }).to_csv(export / "bars.csv", index=False, float_format="%.17g")
    (export / "manifest.json").write_text(json.dumps({
        "schema": "oos_v12_evaluation_export_v1", "status": "accepted",
        "partition": "technical_2023", "start_ms": start,
        "end_exclusive_ms": end, "warmup_bars": 42, "rows": n,
        "bars_sha256": _sha(export / "bars.csv"),
        "training_scaler_sha256": "b" * 64,
        "source_manifest_sha256": "a" * 64,
    }, sort_keys=True))
    checkpoint = tmp_path / "checkpoint-10"
    checkpoint.mkdir()
    actor = Actor(hidden=8, seed=31)
    torch.save({"actor": actor.state_dict(), "diagnostic": {"synthetic": True},
                "attrs": {"next_iteration": 10, "generation": 10,
                          "boundary": "after_dual_and_D", "actor_updates": 80,
                          "critic_updates": 160}}, checkpoint / "state.pt")
    settings = {"seed": 101, "critic_beta": 0, "iterations": 10, "hidden": 8}
    (checkpoint / "manifest.json").write_text(json.dumps({
        "schema_version": "p2_complete_boundary_v1", "profile": "oos_v12_train_only",
        "condition": "C0", "run_id": "run-00-C0-b0", "risk_enabled": False,
        "boundary": "after_dual_and_D", "state_sha256": _sha(checkpoint / "state.pt"),
        "settings": settings, "provenance": {"data": {"source": "invented"}},
    }))
    scaler = TrainScaler(FEATURES, [0.0] * 10, [1.0] * 10,
                         "2018-01-01T00:00:00+00:00", "2023-01-01T00:00:00+00:00", 10073)
    identity = {
        "partition": "technical_2023", "approval_sha256": "c" * 64,
        "training_ledger_sha256": "d" * 64,
        "export_manifest_sha256": _sha(export / "manifest.json"),
        "roster": [{"run_id": "run-00-C0-b0", "seed": 101, "condition": "C0",
                    "checkpoint_sha256": _sha(checkpoint / "state.pt")}],
    }
    kwargs = dict(
        partition="technical_2023", export_manifest_sha256=identity["export_manifest_sha256"],
        source_manifest_sha256="a" * 64, scaler=scaler, scaler_sha256="b" * 64,
        run_id="run-00-C0-b0", seed=101, condition="C0",
        checkpoint_state_sha256=identity["roster"][0]["checkpoint_sha256"],
        settings=settings, source_identity={"source": "invented"},
        actor_updates=80, critic_updates=160,
    )
    return export, checkpoint, identity, kwargs


def test_synthetic_policy_is_audited_before_durable_acceptance(tmp_path, config):
    from btc_risk_rl.evaluation.ledger import EvaluationLedger
    from btc_risk_rl.evaluation.runner import run_one_verified_unit

    export, checkpoint, identity, kwargs = _fixture(tmp_path)
    ledger = EvaluationLedger.create(tmp_path / "invented-batch", identity)
    report = run_one_verified_unit(ledger, export, checkpoint,
                                   config=config, evaluation_kwargs=kwargs)
    assert report["status"] == "completed"
    assert ledger.state["status"] == "completed"
    accepted = ledger.state["accepted"][0]
    output = ledger.root / kwargs["run_id"]
    assert accepted["report_sha256"] == _sha(output / "report.json")
    assert accepted["trace_sha256"] == _sha(output / "trace.jsonl")
    with pytest.raises(ValueError, match="complete"):
        run_one_verified_unit(ledger, export, checkpoint,
                              config=config, evaluation_kwargs=kwargs)


def test_synthetic_bad_checkpoint_fails_permanently_without_acceptance(tmp_path, config):
    from btc_risk_rl.evaluation.ledger import EvaluationLedger
    from btc_risk_rl.evaluation.runner import run_one_verified_unit

    export, checkpoint, identity, kwargs = _fixture(tmp_path)
    ledger = EvaluationLedger.create(tmp_path / "invented-batch", identity)
    (checkpoint / "state.pt").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="hash"):
        run_one_verified_unit(ledger, export, checkpoint,
                              config=config, evaluation_kwargs=kwargs)
    assert ledger.state["status"] == "failed"
    assert ledger.state["accepted"] == []
    with pytest.raises(ValueError, match="failed"):
        run_one_verified_unit(ledger, export, checkpoint,
                              config=config, evaluation_kwargs=kwargs)


def test_orphaned_unit_is_failed_before_any_reentry(tmp_path, config):
    from btc_risk_rl.evaluation.ledger import EvaluationLedger
    from btc_risk_rl.evaluation.runner import run_one_verified_unit

    export, checkpoint, identity, kwargs = _fixture(tmp_path)
    ledger = EvaluationLedger.create(tmp_path / "invented-batch", identity)
    ledger.begin(identity["roster"][0], token="dead-process")
    with pytest.raises(ValueError, match="interrupted"):
        run_one_verified_unit(EvaluationLedger.open(ledger.root, identity),
                              export, checkpoint, config=config,
                              evaluation_kwargs=kwargs)
    assert ledger.state["status"] == "failed"
    assert not (ledger.root / kwargs["run_id"]).exists()


def test_accepted_output_is_rechecked_and_tampering_rejected(tmp_path, config):
    from btc_risk_rl.evaluation.ledger import EvaluationLedger
    from btc_risk_rl.evaluation.runner import (
        run_one_verified_unit,
        verify_accepted_outputs,
    )

    export, checkpoint, identity, kwargs = _fixture(tmp_path)
    ledger = EvaluationLedger.create(tmp_path / "invented-batch", identity)
    run_one_verified_unit(ledger, export, checkpoint,
                          config=config, evaluation_kwargs=kwargs)
    assert verify_accepted_outputs(EvaluationLedger.open(ledger.root, identity),
                                   config=config) == 1
    report_path = ledger.root / kwargs["run_id"] / "report.json"
    with report_path.open("a") as stream:
        stream.write(" ")
    with pytest.raises(ValueError, match="accepted report hash"):
        verify_accepted_outputs(EvaluationLedger.open(ledger.root, identity),
                                config=config)
