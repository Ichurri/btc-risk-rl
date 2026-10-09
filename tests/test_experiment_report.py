"""Synthetic, isolated checks for the offline experiment report."""

import hashlib
import json
from pathlib import Path

import pytest

from btc_risk_rl.reporting.experiments import load_campaign, p3_pairs, render_report


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _fixture(root: Path, campaign: str, units: list[tuple[str, int, float]], *, pending=None):
    base = root / "artifacts" / campaign
    accepted = []
    runs = {}
    for run, iteration, mse in units:
        unit = iteration + 1
        for index in range(unit):
            _write(base / run / f"unit-{index}.json", {
                "report": {"diagnostic": {"records": []}},
                "checkpoint_sha256": "a" * 64,
            })
            accepted.append({"run_id": run, "unit": index,
                             "kind": "q0" if index == 0 else "iteration",
                             "seconds": 10.0, "resources": {"trajectories": 64},
                             "checkpoint_sha256": "a" * 64})
        report = {
            "report": {
                "diagnostic": {"records": [
                    {"iteration": iteration, "A": {"post": {"mse": mse, "z": 1.0}},
                     "D": {"post": {"mse": mse, "z": 1.0}}}
                ]},
                "audits": [{"iteration": iteration + 1, "f_b": 0.12,
                            "lambda_after": 0.1}],
            },
            "checkpoint_sha256": "a" * 64,
        }
        path = base / run / f"unit-{unit}.json"
        _write(path, report)
        accepted.append({"run_id": run, "unit": unit, "kind": "iteration",
                         "seconds": 10.0, "resources": {"trajectories": 64},
                         "checkpoint_sha256": "a" * 64})
        runs[run] = {"next_unit": unit + 1}
    state = {"status": "ready", "cursor": 0, "pending": pending, "runs": runs,
             "units": accepted, "resources": {"trajectories": 64 * len(accepted)},
             "updated_utc": "2026-10-09T00:00:00Z"}
    if campaign == "p3-approved-v1":
        state["identity"] = {"roster": [
            [710031, run.split("-")[2], int(run[-1])] for run in sorted(runs)
        ]}
    base.mkdir(parents=True, exist_ok=True)
    (base / "ledger.jsonl").write_text(json.dumps(state) + "\n", encoding="utf-8")
    return base


def test_only_accepted_units_and_no_campaign_mix(tmp_path):
    base = _fixture(tmp_path, "p3-approved-v1", [("run-00-C0-b0", 0, 0.8)])
    _write(base / "run-00-C0-b0" / "unit-2.json", {"report": {"diagnostic": {
        "records": [{"iteration": 9, "D": {"post": {"mse": 999}}}]}}})
    _fixture(tmp_path, "p2r-approved-v2", [("run-00-C0", 0, 99)])
    campaign = load_campaign(tmp_path, "P3")
    assert campaign.records[0]["D"]["post"]["mse"] == 0.8
    assert len(campaign.records) == 1
    assert p3_pairs(campaign) == []
    assert "999" not in render_report([campaign])


def test_p3_pair_requires_same_seed_condition_and_completed_iteration(tmp_path):
    _fixture(tmp_path, "p3-approved-v1", [
        ("run-00-C0-b0", 0, 0.8), ("run-01-C0-b1", 0, 0.7),
        ("run-02-C5-b0", 1, 0.6), ("run-03-C5-b1", 0, 0.5),
    ])
    pairs = p3_pairs(load_campaign(tmp_path, "P3"))
    assert [(p["condition"], p["iteration"]) for p in pairs] == [("C0", 0)]
    assert pairs[0]["delta_mse"] == pytest.approx(-0.1)


def test_report_hash_check_and_missing_comparison(tmp_path):
    base = _fixture(tmp_path, "p3-approved-v1", [("run-00-C0-b0", 0, 0.8)])
    campaign = load_campaign(tmp_path, "P3")
    html = render_report([campaign])
    assert "Comparación pareada no disponible" in html
    assert "P3" in html and "origen" in html
    assert hashlib.sha256((base / "ledger.jsonl").read_bytes()).hexdigest() in html
    path = base / "run-00-C0-b0" / "unit-1.json"
    _write(path, {"checkpoint_sha256": "b" * 64, "report": {}})
    with pytest.raises(ValueError, match="huella"):
        load_campaign(tmp_path, "P3")


def test_only_ledger_and_accepted_report_are_opened(tmp_path, monkeypatch):
    base = _fixture(tmp_path, "p3-approved-v1", [("run-00-C0-b0", 0, 0.8)])
    _write(base / "run-00-C0-b0" / "unit-2.json", {"report": {"forbidden": True}})
    (tmp_path / "shared-validation-2023.csv").write_text("forbidden", encoding="utf-8")
    opened = []
    original = Path.read_bytes

    def tracked(path):
        opened.append(path.relative_to(tmp_path).as_posix())
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", tracked)
    load_campaign(tmp_path, "P3")
    assert opened == ["artifacts/p3-approved-v1/ledger.jsonl",
                      "artifacts/p3-approved-v1/run-00-C0-b0/unit-1.json"]


def test_incompatible_metrics_are_kept_separate(tmp_path):
    _fixture(tmp_path, "p3-approved-v1", [("run-00-C0-b0", 0, 0.8)])
    html = render_report([load_campaign(tmp_path, "P3")])
    assert "Crítico A β=0: MSE post actualización" in html
    assert "Crítico D β=0: MSE post actualización" in html
    assert "Crítico D β=1: MSE post actualización" in html
    assert "λ posterior a B" in html
    assert "unidad:</b> pérdida logarítmica" in html
    assert "unidad:</b> multiplicador sin dimensión" in html
    assert "src=\"http" not in html and "<script" not in html
    assert "<h1>Resultados experimentales</h1>" in html
    assert "Guía para el tutor" not in html
    assert "INGENIERÍA DEL PROYECTO" not in html
