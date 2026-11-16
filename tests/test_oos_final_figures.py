"""Synthetic checks for presentation figures; no historical source reads."""

import pytest


def _render_module():
    import importlib.util
    from pathlib import Path

    script = Path(__file__).resolve().parents[1] / "scripts/render_oos_final.py"
    spec = importlib.util.spec_from_file_location("render_oos_final", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_render_rejects_cross_campaign_audit_and_writes_only_complete_pairs(tmp_path):
    import hashlib
    import json

    from btc_risk_rl.evaluation.inference import compare_blocks

    module = _render_module()
    records = []
    rows = []
    for seed in range(36):
        values = (1.0 + seed / 100, 1.01 + seed / 100, 1.005 + seed / 100)
        rows.append(values)
        for condition, value in zip(("C0", "C5", "C10"), values, strict=True):
            records.append({"seed": seed, "condition": condition,
                            "sortino_annualized": value,
                            "run_id": f"run-{seed:02d}-{condition}-b0",
                            "report_sha256": "a" * 64})
    contrast = {"status": "passed", "complete_policies": 108, "blocks": 36,
                "run_records": records, "final_ledger_sha256": "b" * 64,
                "comparisons": compare_blocks(rows)}
    contrast_path = tmp_path / "contrast.json"
    contrast_path.write_text(json.dumps(contrast))
    audit = {"status": "verified", "comparison_recomputed_exactly": True,
             "report_trace_reaudits": 108, "accepted_policies": 108,
             "steps_per_policy": 4386, "all_sortino_defined": True,
             "complete_blocks": 36, "final_ledger_sha256": "b" * 64,
             "final_contrast_sha256": hashlib.sha256(contrast_path.read_bytes()).hexdigest()}
    audit_path = tmp_path / "audit.json"
    audit_path.write_text(json.dumps(audit))
    output = tmp_path / "exhibits"
    module.render(contrast_path, audit_path, output)
    assert len((output / "paired-blocks.csv").read_text().splitlines()) == 37
    assert "36 bloques" in (output / "paired-blocks.svg").read_text()
    assert "C5 − C0" in (output / "paired-inference.svg").read_text()
    audit["final_ledger_sha256"] = "c" * 64
    audit_path.write_text(json.dumps(audit))
    with pytest.raises(ValueError, match="do not match"):
        module.render(contrast_path, audit_path, tmp_path / "other")
    assert not (tmp_path / "other").exists()


def test_paired_svg_labels_population_source_and_zero_reference():
    paired_differences_svg = _render_module().paired_differences_svg

    rows = [(101, 0.1, 0.2, 0.05), (102, -0.2, -0.1, -0.3)]
    svg = paired_differences_svg(
        rows, source="artifacts/example/final-contrast.json", period="2024–2025",
    )
    assert "<svg" in svg
    assert "C5 − C0" in svg and "C10 − C0" in svg
    assert "36 bloques" not in svg
    assert "2 bloques" in svg
    assert "artifacts/example/final-contrast.json" in svg
    assert "2024–2025" in svg
    assert "Referencia: 0" in svg


def test_paired_svg_rejects_missing_or_nonfinite_primary_metrics():
    paired_differences_svg = _render_module().paired_differences_svg

    for rows in ([], [(101, 0.1, None, 0.3)], [(101, 0.1, float("nan"), 0.3)]):
        with pytest.raises(ValueError):
            paired_differences_svg(rows, source="x", period="2024–2025")
