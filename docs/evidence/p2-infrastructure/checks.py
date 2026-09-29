"""Static/algebraic evidence only. Never loads market data or runs a learner."""

import argparse
import importlib.metadata
import json
import platform
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import numpy as np

from btc_risk_rl.pilots.p2_metrics import metric, overlap, pool


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    original = json.loads((root / "docs/proposals/P2-candidate-v1.json").read_text())
    approved = json.loads((root / "docs/protocols/P2-infrastructure-v1.json").read_text())
    for key in (
        "data",
        "conditions",
        "risk",
        "training_candidate",
        "runtime",
        "blocks",
        "budget_proposal",
        "diagnostics",
        "calendar",
        "diagnostic_candidate",
    ):
        assert approved[key] == original[key], key
    assert approved["infrastructure_authorized"] and not approved["market_execution_authorized"]
    expected = dict(
        original["assessment_candidate"], threshold_status="accepted_for_P2_not_confirmatory"
    )
    assert approved["assessment_candidate"] == expected
    a = metric(np.array([[2.0, 0.0]]), np.ones((1, 2)))
    b = metric(np.zeros((1, 2)), np.full((1, 2), 2.0))
    pooled = pool([a, b])
    assert pooled["mse"] == pooled["z"] == 2.5 and pooled["bias"] == -1
    n_q, k, n_a, n_b, d = 400, 10, 64, 400, 64
    budget = dict(
        learning_trajectories=9 * (n_q + k * (n_a + n_q + n_b)),
        diagnostic_trajectories=9 * k * d,
        actor_updates=9 * k * 2 * 4,
        critic_updates=9 * k * 4 * 4,
    )
    assert budget == dict(
        learning_trajectories=81360,
        diagnostic_trajectories=5760,
        actor_updates=720,
        critic_updates=1440,
    )
    # Hash existing P0/P1 evidence only, no loading tensors/data/trajectories.
    p0 = json.loads((root / "docs/evidence/p0-diagnosis/results.json").read_text())
    historical = dict(p0["original_files_sha256"])
    p1 = json.loads((root / "docs/evidence/p1-execution/campaign-results/results.json").read_text())
    historical["artifacts/p1-approved-v1/ledger.jsonl"] = p1["ledger_sha256"]
    for item in p1["artifacts"]:
        path = Path("artifacts/p1-approved-v1") / item["path"]
        historical[str(path)] = item["sha256"]
        if "state_sha256" in item:
            historical[str(path.parent / "state.pt")] = item["state_sha256"]
    for name, expected_hash in historical.items():
        assert digest(root / name) == expected_hash, name
    tests = (
        ET.parse(root / "docs/evidence/p2-infrastructure/pytest.xml").getroot().find("testsuite")
    )
    assert tests is not None and tests.attrib["failures"] == tests.attrib["errors"] == "0"
    result = dict(
        scope="synthetic_tests_plus_static_and_algebraic_only",
        utc=datetime.now(timezone.utc).isoformat(),
        head_before_delivery=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        python=platform.python_version(),
        versions={p: importlib.metadata.version(p) for p in ("torch", "numpy", "pytest", "ruff")},
        configuration_unchanged_except_authorization_metadata=True,
        historical_files_verified=len(historical),
        historical_evidence_intact=True,
        planned_market_budget_not_executed=budget,
        pooled_algebraic=pooled,
        partial_overlap=overlap(
            [dict(start="s:2", times=["s:2", "s:3"])] * 2,
            [dict(start="s:1", times=["s:1", "s:2"])],
            [dict(start="s:1", times=["s:1", "s:2"])],
        ),
        pytest={k: tests.attrib[k] for k in ("tests", "failures", "errors", "skipped", "time")},
        code_sha256={
            str(p.relative_to(root)): digest(p) for p in sorted((root / "src").rglob("*.py"))
        },
        market_execution=False,
        validation_access=False,
        final_access=False,
    )
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            dict(status="passed", historical_files=len(historical), tests=tests.attrib["tests"])
        )
    )


if __name__ == "__main__":
    main()
