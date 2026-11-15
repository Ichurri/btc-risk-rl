"""Evaluation partition gates remain closed until independent approvals."""

import hashlib
import json

import pytest


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _synthetic_freezes(tmp_path, monkeypatch, access):
    for path_name, constant in (("METHOD_PATH", "METHOD_SHA256"),
                                ("TRAINING_PATH", "TRAINING_SHA256")):
        path = tmp_path / getattr(access, path_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"synthetic {path_name}")
        monkeypatch.setattr(access, constant, _sha(path))


def test_post_closure_all_historical_evaluation_gates_are_closed(tmp_path):
    from btc_risk_rl.evaluation import access

    assert set(access.ENABLED) == {
        "technical_2023_source", "technical_2023",
        "final_2024_2025_source", "final_2024_2025",
    }
    assert all(enabled is False for enabled in access.ENABLED.values())
    for partition in access.ENABLED:
        with pytest.raises(PermissionError, match="disabled"):
            access.read_pinned_approval(partition, tmp_path)
    assert not list(tmp_path.iterdir())


def test_disabled_partition_gates_reject_without_opening_files(tmp_path, monkeypatch):
    from btc_risk_rl.evaluation import access
    from btc_risk_rl.evaluation.access import (
        read_pinned_approval,
        require_evaluation_access,
    )

    for partition in ("technical_2023", "final_2024_2025"):
        monkeypatch.setitem(access.ENABLED, partition, False)
        with pytest.raises(PermissionError, match="disabled"):
            read_pinned_approval(partition, tmp_path)
        with pytest.raises(PermissionError, match="disabled"):
            require_evaluation_access(partition, tmp_path,
                                      training_ledger_sha256="a" * 64,
                                      export_manifest_sha256="b" * 64,
                                      source_manifest_sha256="c" * 64,
                                      scaler_sha256="d" * 64)
    assert list(tmp_path.iterdir()) == []


def test_source_export_requires_separate_pinned_permit(tmp_path, monkeypatch):
    from btc_risk_rl.evaluation import access

    monkeypatch.setitem(access.ENABLED, "technical_2023_source", False)
    with pytest.raises(PermissionError, match="disabled"):
        access.require_source_export_access(
            tmp_path, training_ledger_sha256="a" * 64,
            h1_manifest_sha256="b" * 64,
            raw_manifest_sha256="c" * 64, scaler_sha256="d" * 64,
        )
    _synthetic_freezes(tmp_path, monkeypatch, access)
    monkeypatch.setattr(access, "execution_code_sha256", lambda _root: "e" * 64)
    approval = {
        "status": "approved", "partition": "technical_2023_source",
        "method_freeze_sha256": access.METHOD_SHA256,
        "training_freeze_sha256": access.TRAINING_SHA256,
        "training_ledger_sha256": "a" * 64,
        "h1_manifest_sha256": "b" * 64,
        "raw_manifest_sha256": "c" * 64,
        "scaler_sha256": "d" * 64,
        "code_sha256": "e" * 64,
    }
    path = tmp_path / "source-approval.json"
    path.write_text(json.dumps(approval, sort_keys=True))
    monkeypatch.setitem(access.ENABLED, "technical_2023_source", True)
    monkeypatch.setitem(access.APPROVAL_PATHS, "technical_2023_source", path)
    monkeypatch.setitem(access.REGISTRATION_SHA256, "technical_2023_source", _sha(path))
    assert access.require_source_export_access(
        tmp_path, training_ledger_sha256="a" * 64,
        h1_manifest_sha256="b" * 64,
        raw_manifest_sha256="c" * 64, scaler_sha256="d" * 64,
    ) == approval
    with pytest.raises(PermissionError, match="identity"):
        access.require_source_export_access(
            tmp_path, training_ledger_sha256="a" * 64,
            h1_manifest_sha256="b" * 64,
            raw_manifest_sha256="c" * 64, scaler_sha256="f" * 64,
        )


def test_synthetic_technical_permission_binds_all_inputs(tmp_path, monkeypatch):
    from btc_risk_rl.evaluation import access

    _synthetic_freezes(tmp_path, monkeypatch, access)
    monkeypatch.setattr(access, "execution_code_sha256", lambda _root: "e" * 64)
    approval = {
        "status": "approved", "partition": "technical_2023",
        "method_freeze_sha256": access.METHOD_SHA256,
        "training_freeze_sha256": access.TRAINING_SHA256,
        "training_ledger_sha256": "a" * 64,
        "export_manifest_sha256": "b" * 64,
        "source_manifest_sha256": "c" * 64,
        "scaler_sha256": "d" * 64,
        "code_sha256": "e" * 64,
    }
    path = tmp_path / "technical-approval.json"
    path.write_text(json.dumps(approval, sort_keys=True))
    monkeypatch.setitem(access.ENABLED, "technical_2023", True)
    monkeypatch.setitem(access.APPROVAL_PATHS, "technical_2023", path)
    monkeypatch.setitem(access.REGISTRATION_SHA256, "technical_2023", _sha(path))
    assert access.read_pinned_approval("technical_2023", tmp_path) == approval
    result = access.require_evaluation_access(
        "technical_2023", tmp_path, training_ledger_sha256="a" * 64,
        export_manifest_sha256="b" * 64, source_manifest_sha256="c" * 64,
        scaler_sha256="d" * 64,
    )
    assert result == approval
    method = tmp_path / access.METHOD_PATH
    method.write_text("tampered")
    with pytest.raises(PermissionError, match="frozen protocol"):
        access.require_evaluation_access(
            "technical_2023", tmp_path, training_ledger_sha256="a" * 64,
            export_manifest_sha256="b" * 64, source_manifest_sha256="c" * 64,
            scaler_sha256="d" * 64,
        )
    method.write_text("synthetic METHOD_PATH")
    with pytest.raises(PermissionError, match="identity"):
        access.require_evaluation_access(
            "technical_2023", tmp_path, training_ledger_sha256="a" * 64,
            export_manifest_sha256="b" * 64, source_manifest_sha256="c" * 64,
            scaler_sha256="f" * 64,
        )
    path.write_text(json.dumps({**approval, "code_sha256": "f" * 64}))
    with pytest.raises(PermissionError, match="approval hash"):
        access.require_evaluation_access(
            "technical_2023", tmp_path, training_ledger_sha256="a" * 64,
            export_manifest_sha256="b" * 64, source_manifest_sha256="c" * 64,
            scaler_sha256="d" * 64,
        )


def test_synthetic_final_requires_pinned_passed_technical_closure(tmp_path, monkeypatch):
    from btc_risk_rl.evaluation import access

    _synthetic_freezes(tmp_path, monkeypatch, access)
    monkeypatch.setattr(access, "execution_code_sha256", lambda _root: "e" * 64)
    closure_path = tmp_path / "technical-closure.json"
    closure_path.write_text(json.dumps({"status": "passed", "complete_policies": 108,
                                        "partition": "technical_2023"}))
    approval = {
        "status": "approved", "partition": "final_2024_2025",
        "method_freeze_sha256": access.METHOD_SHA256,
        "training_freeze_sha256": access.TRAINING_SHA256,
        "training_ledger_sha256": "a" * 64,
        "export_manifest_sha256": "b" * 64,
        "source_manifest_sha256": "c" * 64,
        "scaler_sha256": "d" * 64,
        "code_sha256": "e" * 64,
        "technical_closure_sha256": _sha(closure_path),
    }
    approval_path = tmp_path / "final-approval.json"
    approval_path.write_text(json.dumps(approval, sort_keys=True))
    monkeypatch.setitem(access.ENABLED, "final_2024_2025", True)
    monkeypatch.setitem(access.APPROVAL_PATHS, "final_2024_2025", approval_path)
    monkeypatch.setitem(access.REGISTRATION_SHA256, "final_2024_2025", _sha(approval_path))
    assert access.require_evaluation_access(
        "final_2024_2025", tmp_path, training_ledger_sha256="a" * 64,
        export_manifest_sha256="b" * 64, source_manifest_sha256="c" * 64,
        scaler_sha256="d" * 64,
        technical_closure_path=closure_path,
    ) == approval
    closure_path.write_text(json.dumps({"status": "failed", "complete_policies": 108,
                                        "partition": "technical_2023"}))
    with pytest.raises(PermissionError, match="technical closure"):
        access.require_evaluation_access(
            "final_2024_2025", tmp_path, training_ledger_sha256="a" * 64,
            export_manifest_sha256="b" * 64, source_manifest_sha256="c" * 64,
            scaler_sha256="d" * 64,
            technical_closure_path=closure_path,
        )


def test_access_gate_computes_code_identity_instead_of_trusting_caller(tmp_path, monkeypatch):
    from btc_risk_rl.evaluation import access

    _synthetic_freezes(tmp_path, monkeypatch, access)
    approval = {
        "status": "approved", "partition": "technical_2023",
        "method_freeze_sha256": access.METHOD_SHA256,
        "training_freeze_sha256": access.TRAINING_SHA256,
        "training_ledger_sha256": "a" * 64,
        "export_manifest_sha256": "b" * 64,
        "source_manifest_sha256": "c" * 64,
        "scaler_sha256": "d" * 64,
        "code_sha256": "e" * 64,
    }
    path = tmp_path / "approval.json"
    path.write_text(json.dumps(approval, sort_keys=True))
    monkeypatch.setitem(access.ENABLED, "technical_2023", True)
    monkeypatch.setitem(access.APPROVAL_PATHS, "technical_2023", path)
    monkeypatch.setitem(access.REGISTRATION_SHA256, "technical_2023", _sha(path))
    monkeypatch.setattr(access, "execution_code_sha256", lambda _root: "e" * 64,
                        raising=False)
    assert access.require_evaluation_access(
        "technical_2023", tmp_path, training_ledger_sha256="a" * 64,
        export_manifest_sha256="b" * 64, source_manifest_sha256="c" * 64,
        scaler_sha256="d" * 64,
    ) == approval
    monkeypatch.setattr(access, "execution_code_sha256", lambda _root: "f" * 64)
    with pytest.raises(PermissionError, match="identity"):
        access.require_evaluation_access(
            "technical_2023", tmp_path, training_ledger_sha256="a" * 64,
            export_manifest_sha256="b" * 64, source_manifest_sha256="c" * 64,
            scaler_sha256="d" * 64,
        )


def test_final_source_requires_independent_pin_and_passed_technical_closure(
    tmp_path, monkeypatch,
):
    from btc_risk_rl.evaluation import access

    monkeypatch.setitem(access.ENABLED, "final_2024_2025_source", False)
    _synthetic_freezes(tmp_path, monkeypatch, access)
    closure = tmp_path / "closure.json"
    closure.write_text(json.dumps({"status": "passed", "partition": "technical_2023",
                                   "complete_policies": 108}))
    with pytest.raises(PermissionError, match="disabled"):
        access.require_final_source_access(
            tmp_path, training_ledger_sha256="a" * 64,
            technical_closure_path=closure, technical_export_sha256="b" * 64,
            h1_manifest_sha256="c" * 64, scaler_sha256="d" * 64,
        )
    approval = {
        "status": "approved", "partition": "final_2024_2025_source",
        "method_freeze_sha256": access.METHOD_SHA256,
        "training_freeze_sha256": access.TRAINING_SHA256,
        "training_ledger_sha256": "a" * 64,
        "technical_closure_sha256": _sha(closure),
        "technical_export_sha256": "b" * 64,
        "h1_manifest_sha256": "c" * 64,
        "scaler_sha256": "d" * 64,
        "code_sha256": "e" * 64,
    }
    permit = tmp_path / "source-final.json"
    permit.write_text(json.dumps(approval))
    monkeypatch.setitem(access.ENABLED, "final_2024_2025_source", True)
    monkeypatch.setitem(access.APPROVAL_PATHS, "final_2024_2025_source", permit)
    monkeypatch.setitem(access.REGISTRATION_SHA256, "final_2024_2025_source", _sha(permit))
    monkeypatch.setattr(access, "execution_code_sha256", lambda _root: "e" * 64)
    assert access.require_final_source_access(
        tmp_path, training_ledger_sha256="a" * 64,
        technical_closure_path=closure, technical_export_sha256="b" * 64,
        h1_manifest_sha256="c" * 64, scaler_sha256="d" * 64,
    ) == approval
    closure.write_text(json.dumps({"status": "failed", "partition": "technical_2023",
                                   "complete_policies": 108}))
    with pytest.raises(PermissionError, match="technical closure"):
        access.require_final_source_access(
            tmp_path, training_ledger_sha256="a" * 64,
            technical_closure_path=closure, technical_export_sha256="b" * 64,
            h1_manifest_sha256="c" * 64, scaler_sha256="d" * 64,
        )
