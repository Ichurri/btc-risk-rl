"""The later evaluation permit must bind executable bytes, not a caller string."""

from pathlib import Path

import pytest


def _fixture(tmp_path):
    paths = (
        "src/btc_risk_rl/evaluation/access.py",
        "src/btc_risk_rl/evaluation/historical_path.py",
        "src/btc_risk_rl/agents/models.py",
        "src/btc_risk_rl/env/accounting.py",
        "src/btc_risk_rl/features/market.py",
        "src/btc_risk_rl/config.py",
        "src/btc_risk_rl/reporting/oos_contrast.py",
        "pyproject.toml", "uv.lock", "configs/initial.toml",
    )
    for name in paths:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n")
    access = tmp_path / paths[0]
    access.write_text("ENABLED = {'technical_2023': False}\n"
                      "REGISTRATION_SHA256 = {'technical_2023': None}\n")
    return access


def test_execution_identity_changes_for_algorithm_but_not_gate_declarations(tmp_path):
    from btc_risk_rl.evaluation.code_identity import execution_code_sha256

    access = _fixture(tmp_path)
    first = execution_code_sha256(tmp_path)
    assert len(first) == 64
    access.write_text("ENABLED = {'technical_2023': True}\n"
                      "REGISTRATION_SHA256 = {'technical_2023': 'a' * 64}\n")
    assert execution_code_sha256(tmp_path) == first
    algorithm = tmp_path / "src/btc_risk_rl/evaluation/historical_path.py"
    algorithm.write_text("changed\n")
    assert execution_code_sha256(tmp_path) != first
    algorithm.unlink()
    with pytest.raises(ValueError, match="missing"):
        execution_code_sha256(tmp_path)


def test_evaluation_command_is_included_if_present(tmp_path):
    from btc_risk_rl.evaluation.code_identity import execution_code_sha256

    _fixture(tmp_path)
    original = execution_code_sha256(tmp_path)
    command = Path(tmp_path) / "scripts/run_oos_v12_evaluation.py"
    command.parent.mkdir(parents=True)
    command.write_text("print('fixture')\n")
    assert execution_code_sha256(tmp_path) != original
