"""Rebuild only the cost-study identity; collect no trajectories."""

import hashlib
import json
import subprocess

from btc_risk_rl.agents.checkpoint import provenance
from btc_risk_rl.pilots.wf_cost import CAMPAIGN, CONFIG, ROOT, digest, inspect_inputs, roster
from btc_risk_rl.pilots.wf_cost_source import build_fold_source


def check() -> dict:
    state = json.loads((CAMPAIGN / "ledger.jsonl").read_text().splitlines()[-1])
    inputs = inspect_inputs()
    sources = {fold: build_fold_source(fold) for fold, _, _ in roster()}
    current = {
        "profile": "wf_cost_training_folds_only",
        "roster": roster(),
        "source": {fold: source.identity() for fold, source in sources.items()},
        "input_sha256": inputs["sha256"],
        "config_sha256": digest(CONFIG),
        "code": {
            fold: {key: value for key, value in provenance(source).items()
                   if key not in {"threads", "deterministic"}}
            for fold, source in sources.items()
        },
        "diagnostic_n": 64,
    }
    old = state["identity"]
    # The operational flag was closed after the failure. Compare the identity
    # with the exact approved source bytes that ran in both historical services.
    frozen = subprocess.check_output(
        ["git", "show", "86e83ed:src/btc_risk_rl/pilots/wf_cost.py"], cwd=ROOT
    )
    frozen_hash = hashlib.sha256(frozen).hexdigest()
    for fold in current["code"]:
        key = "src/btc_risk_rl/pilots/wf_cost.py"
        assert old["code"][fold]["code"][key] == frozen_hash
        current["code"][fold]["code"][key] = frozen_hash
    assert set(old) == set(current)
    assert all(old[key] == current[key] for key in old if key != "roster")
    assert old["roster"] == [list(item) for item in current["roster"]]
    assert old == json.loads(json.dumps(current))
    assert state["status"] == "ready" and len(state["units"]) == 1
    assert state["pending"] is None
    work = CAMPAIGN / "wf-2021"
    assert not (work / "checkpoint-1").exists()
    assert not (work / "unit-1.json").exists()
    return {
        "status": "reproduced_identity_type_mismatch_only",
        "field": "identity.roster",
        "stored_type": type(old["roster"]).__name__,
        "reconstructed_type": type(current["roster"]).__name__,
        "other_fields_equal": True,
        "json_normalized_identity_equal": True,
        "accepted_units": 1,
        "unit_1_checkpoint_exists": False,
        "unit_1_report_exists": False,
    }


if __name__ == "__main__":
    print(json.dumps(check(), indent=2, sort_keys=True))
