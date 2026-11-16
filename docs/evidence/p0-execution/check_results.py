"""Read-only closure audit: frozen settings, resources, timing and artifact hashes."""

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent
results = json.loads((EVIDENCE / "campaign-results/results.json").read_text())
approved = json.loads((ROOT / "docs/protocols/P0-approved-v1.json").read_text())
assert results["status"] == "completed" and results["failure"] is None
assert len(results["runs"]) == 9
assert results["resources"] == dict(
    trajectories=19152, transitions=3447360, actor_updates=144, critic_updates=144
)
roster = [(b["seed"], c) for b in approved["blocks"] for c in b["order"]]
assert [(r["seed"], r["condition"]) for r in results["runs"]] == roster
assert len(results["days"]) == 1
for day in results["days"].values():
    assert day["active_seconds"] < 10800 and day["charged_wall_seconds"] < 10800
for r in results["runs"]:
    assert r["status"] == "completed" and r["complete_iterations"] == 2
    assert r["resources"] == dict(
        trajectories=2128, transitions=383040, actor_updates=16, critic_updates=16
    )
    assert r["settings"]["bound"] == -math.log(0.9)
    assert r["settings"]["n_a"] == 64 and r["settings"]["n_q"] == r["settings"]["n_b"] == 400
    assert len(r["days"]) == 1
    assert [u["unit"] for u in r["measured_units"]] == [0, 1, 2]
    for u in r["measured_units"]:
        assert u["supervisor"]["status"] == "passed"
        assert u["supervisor"]["work_seconds"] < (1800 if u["unit"] == 0 else 2700)
        assert u["supervisor"]["rss_peak_bytes"] < 10 * 1024**3
    if r["condition"] == "C0":
        assert all(a["lambda_after"] == 0 for a in r["audits"])
    else:
        for a in r["audits"]:
            expected = max(0, a["lambda_before"] + 0.1 * (a["f_b"] - r["settings"]["bound"]))
            assert a["lambda_after"] == expected
for filename, sha in results["identity"]["code"].items():
    assert hashlib.sha256((ROOT / filename).read_bytes()).hexdigest() == sha
for a in results["artifacts"]:
    assert (
        hashlib.sha256((ROOT / "artifacts/p0-approved-v1" / a["path"]).read_bytes()).hexdigest()
        == a["sha256"]
    )
    if "state_sha256" in a:
        path = ROOT / "artifacts/p0-approved-v1" / Path(a["path"]).parent / "state.pt"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == a["state_sha256"]
assert not results["validation_accessed"] and not results["final_accessed"]
output = dict(
    status="passed",
    source_results_sha256=hashlib.sha256(
        (EVIDENCE / "campaign-results/results.json").read_bytes()
    ).hexdigest(),
    verified_runs=9,
    complete_iterations=18,
    artifact_hashes=len(results["artifacts"]),
    checks=[
        "order",
        "frozen_settings",
        "resources",
        "daily_limits",
        "unit_limits",
        "memory",
        "dual_sign_and_C0",
        "code_and_checkpoints",
    ],
    scope="logs_and_binary_hashes_only_no_market_evaluation",
)
with (EVIDENCE / "closure-checks.json").open("x") as f:
    json.dump(output, f, indent=2)
    f.write("\n")
print(json.dumps(output))
