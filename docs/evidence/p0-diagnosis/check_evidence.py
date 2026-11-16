"""Independent closure assertions over diagnostic JSON/CSV and original logs."""

import csv
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
evidence = Path(__file__).resolve().parent
result = json.loads((evidence / "results.json").read_text())
original = json.loads(
    (root / "docs/evidence/p0-execution/campaign-results/results.json").read_text()
)
rows = list(csv.DictReader((evidence / "metrics.csv").open()))
assert len(rows) == 162 and sum(x["phase"] == "targets" for x in rows) == 18
assert all(float(x["relative"]) > 1 for x in rows)
assert sum(len(r["warnings"]) for r in original["runs"]) == 162
for r in result["records"]:
    assert r["critic"]["mse_after"] < r["critic"]["mse_before"]
    assert r["critic"]["relative_after"] > 1
    assert r["correspondence"]["collection_diagnostics_exact"]
    assert (
        len([x for x in rows if x["run"] == r["run_id"] and int(x["iteration"]) == r["iteration"]])
        == 9
    )
    if r["iteration"] == 0 or r["condition"] == "C0":
        assert r["risk"]["penalty_max"] == r["risk"]["initial_risk_gradient_delta_norm"] == 0
risk_second = [r for r in result["records"] if r["condition"] != "C0" and r["iteration"] == 1]
assert sum(r["risk"]["penalty_max"] > 0 for r in risk_second) == 5
for r in risk_second:
    assert (r["risk"]["initial_risk_gradient_delta_norm"] > 0) == (r["risk"]["penalty_max"] > 0)
for k in (0, 1):
    pair = [
        r
        for r in result["records"]
        if r["seed"] == 410031 and r["condition"] in ("C0", "C5") and r["iteration"] == k
    ]
    assert pair[0]["risk"]["first_gradient_sha256"] == pair[1]["risk"]["first_gradient_sha256"]
    assert pair[0]["parameters"] == pair[1]["parameters"]
assert result["pairs"][0]["checkpoint_actor_adam_equal"] == [True] * 3
for file, sha in result["original_files_sha256"].items():
    assert hashlib.sha256((root / file).read_bytes()).hexdigest() == sha
for file, sha in original["identity"]["code"].items():
    assert hashlib.sha256((root / file).read_bytes()).hexdigest() == sha
print(
    "PASS: 162 metrics, 18 matched batches, 18 MSE reductions, five active risk batches, exact seed410031 paired gradients/parameters, unchanged originals/source"
)
