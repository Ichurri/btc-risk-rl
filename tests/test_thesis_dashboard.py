"""Evidence integrity and comparability tests; no models or market loaders."""

import copy
import json
from pathlib import Path

import pytest

from btc_risk_rl.reporting.dashboard import CROSS, ROOT, build, load_data, validate_pair


def test_crossed_comparison_matches_audited_values_and_accepted_coverage():
    data = load_data()
    original = json.loads((ROOT / CROSS).read_text())
    assert len(data["cross"]) == 9
    assert data["campaigns"]["P2"]["status"] == "failed"
    assert data["campaigns"]["P3"]["accepted"] == 198
    assert data["campaigns"]["WF05"]["accepted"] == 11
    for exported, source in zip(data["cross"], original["pairs"], strict=True):
        assert (exported["seed"], exported["condition"]) == (source["seed"], source["condition"])
        assert exported["cells"] == source["cells"]
        assert exported["coverage"] == source["coverage"]
    assert all(not path.startswith("data/") for path in data["sources"])
    assert all(not path.endswith((".pt", ".npz", ".csv")) for path in data["sources"])


def test_rejects_incomplete_or_incompatible_comparison():
    original = json.loads((ROOT / CROSS).read_text())["pairs"][0]
    bad = copy.deepcopy(original)
    bad["coverage"]["D_b0"]["observations_evaluated"] -= 1
    with pytest.raises(ValueError, match="incompleto"):
        validate_pair(bad)
    bad = copy.deepcopy(original)
    bad["cells"]["critic_b1_on_D_b0"]["target_sq"] += 1
    with pytest.raises(ValueError, match="cero incompatible"):
        validate_pair(bad)
    bad = copy.deepcopy(original)
    bad["cells"]["critic_b0_on_D_b0"]["mse"] = 0
    with pytest.raises(ValueError, match="MSE incompatible"):
        validate_pair(bad)


def test_output_guard_preserves_original_artifacts():
    with pytest.raises(ValueError, match="reports/"):
        build(ROOT / "artifacts/dashboard.html")


def test_dashboard_has_no_remote_runtime_assets():
    html = Path(__file__).parents[1] / "src/btc_risk_rl/reporting/dashboard.html"
    text = html.read_text()
    assert "fetch(" not in text
    assert "<script src=" not in text
    assert "@import" not in text
    assert "Sin evidencia disponible" in text
    assert "review" in text and "incomplete" in text


def test_generation_is_repeatable_and_does_not_change_sources():
    import hashlib
    import shutil

    data = load_data()
    output = ROOT / "reports/dashboard-test/index.html"
    try:
        build(output)
        first = output.read_bytes()
        build(output)
        assert output.read_bytes() == first
        for relative, source in data["sources"].items():
            assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == source["sha256"]
    finally:
        shutil.rmtree(output.parent, ignore_errors=True)
