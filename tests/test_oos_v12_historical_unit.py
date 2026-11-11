"""A historical evaluation unit is exercised with invented bars only."""

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


def _fixture(tmp_path, partition="technical_2023"):
    start, end, steps = PERIODS[partition]
    n = steps + 43
    times = start - 43 * STEP_MS + np.arange(n, dtype=np.int64) * STEP_MS
    price = 100.0 + 0.001 * np.arange(n)
    source = "a" * 64
    export = tmp_path / "invented-export"
    export.mkdir()
    pd.DataFrame({
        "open_time_ms": times, "close_time_ms": times + STEP_MS - 1,
        "open": price, "high": price + 0.3, "low": price - 0.3,
        "close": price + 0.1, "volume": np.full(n, 50.0),
    }).to_csv(export / "bars.csv", index=False, float_format="%.17g")
    (export / "manifest.json").write_text(json.dumps({
        "schema": "oos_v12_evaluation_export_v1", "status": "accepted",
        "partition": partition, "start_ms": start, "end_exclusive_ms": end,
        "warmup_bars": 42, "rows": n, "bars_sha256": _sha(export / "bars.csv"),
        "training_scaler_sha256": "b" * 64, "source_manifest_sha256": source,
    }, sort_keys=True))
    checkpoint = tmp_path / "run-00-C0-b0/checkpoint-10"
    checkpoint.mkdir(parents=True)
    actor = Actor(hidden=8, seed=31)
    torch.save({"actor": actor.state_dict(), "diagnostic": {"synthetic": True},
                "attrs": {"next_iteration": 10, "generation": 10,
                          "boundary": "after_dual_and_D", "actor_updates": 80,
                          "critic_updates": 160}}, checkpoint / "state.pt")
    settings = {"seed": 101, "critic_beta": 0, "iterations": 10, "hidden": 8}
    identity = {"source": "invented"}
    (checkpoint / "manifest.json").write_text(json.dumps({
        "schema_version": "p2_complete_boundary_v1", "profile": "oos_v12_train_only",
        "condition": "C0", "run_id": "run-00-C0-b0", "risk_enabled": False,
        "boundary": "after_dual_and_D", "state_sha256": _sha(checkpoint / "state.pt"),
        "settings": settings, "provenance": {"data": identity},
    }))
    scaler = TrainScaler(FEATURES, [0.0] * 10, [1.0] * 10,
                         "2018-01-01T00:00:00+00:00", "2023-01-01T00:00:00+00:00", 10073)
    kwargs = dict(
        partition=partition, export_manifest_sha256=_sha(export / "manifest.json"),
        source_manifest_sha256=source, scaler=scaler, scaler_sha256="b" * 64,
        run_id="run-00-C0-b0", seed=101, condition="C0",
        checkpoint_state_sha256=_sha(checkpoint / "state.pt"),
        settings=settings, source_identity=identity,
        actor_updates=80, critic_updates=160,
    )
    return export, checkpoint, kwargs


@pytest.mark.parametrize("partition", ["technical_2023", "final_2024_2025"])
def test_complete_synthetic_historical_unit_is_audited_and_reproducible(
    tmp_path, config, partition,
):
    from btc_risk_rl.evaluation.historical_unit import evaluate_verified_unit

    export, checkpoint, kwargs = _fixture(tmp_path, partition)
    first = evaluate_verified_unit(export, checkpoint, tmp_path / "first", config=config, **kwargs)
    second = evaluate_verified_unit(export, checkpoint, tmp_path / "second", config=config, **kwargs)
    assert first["status"] == second["status"] == "completed"
    assert first["partition"] == partition
    assert first["steps"] == PERIODS[partition][2]
    assert first["sortino_annualized"] == second["sortino_annualized"]
    assert first["trace_sha256"] == second["trace_sha256"]
    assert first["checkpoint_state_sha256"] == kwargs["checkpoint_state_sha256"]
    assert first["source_manifest_sha256"] == kwargs["source_manifest_sha256"]
    assert (tmp_path / "first" / "trace.jsonl").is_file()
    assert (tmp_path / "first" / "report.json").is_file()
    with pytest.raises(FileExistsError):
        evaluate_verified_unit(export, checkpoint, tmp_path / "first", config=config, **kwargs)


def test_source_identity_is_rejected_before_opening_bars(tmp_path, config, monkeypatch):
    from btc_risk_rl.evaluation.historical_unit import evaluate_verified_unit

    export, checkpoint, kwargs = _fixture(tmp_path)
    opened = []
    original = pd.read_csv

    def watched(path, *args, **settings):
        opened.append(str(path))
        return original(path, *args, **settings)

    monkeypatch.setattr(pd, "read_csv", watched)
    kwargs["source_manifest_sha256"] = "c" * 64
    with pytest.raises(ValueError, match="source manifest"):
        evaluate_verified_unit(export, checkpoint, tmp_path / "rejected",
                               config=config, **kwargs)
    assert opened == []
    assert not (tmp_path / "rejected" / "report.json").exists()


def test_persisted_report_recomputes_metrics_and_rejects_tampering(tmp_path, config):
    from btc_risk_rl.evaluation.historical_unit import (
        evaluate_verified_unit,
        read_verified_unit_report,
    )

    export, checkpoint, kwargs = _fixture(tmp_path)
    output = tmp_path / "accepted"
    report = evaluate_verified_unit(export, checkpoint, output, config=config, **kwargs)
    expected = dict(
        expected_run_id=kwargs["run_id"], expected_seed=kwargs["seed"],
        expected_condition=kwargs["condition"], expected_partition=kwargs["partition"],
        expected_checkpoint_sha256=kwargs["checkpoint_state_sha256"],
        expected_export_manifest_sha256=kwargs["export_manifest_sha256"],
    )
    assert read_verified_unit_report(output, config=config, **expected) == report
    changed = dict(report)
    changed["sortino_annualized"] += 1.0
    (output / "report.json").write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="metrics"):
        read_verified_unit_report(output, config=config, **expected)
    (output / "report.json").write_text(json.dumps(report))
    with (output / "trace.jsonl").open("a") as stream:
        stream.write("{}\n")
    with pytest.raises(ValueError, match="trace hash"):
        read_verified_unit_report(output, config=config, **expected)
