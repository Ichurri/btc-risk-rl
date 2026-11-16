"""Static/algebraic checks of the PROPOSED protocol, not tests of a market executor."""

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "docs/proposals/P0-candidate.json"
DOC = ROOT / "docs/proposals/P0-protocolo-v1.md"


def admission(remaining_work, observations, cap, margin):
    """Proposed gate only; fictional seconds. Never imports H5 or opens data."""
    if observations:
        assert all(math.isfinite(t) and t > 0 for t in observations)
        estimate = margin * max(observations)
        if estimate > cap:
            return "design_infeasible"
        required = estimate
    else:
        required = cap  # explicit bounded first-measurement exception, not an estimate
    return "start" if remaining_work >= required else "planned_pause"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    c = json.loads(CONFIG.read_text())
    t, b, d = c["training_candidate"], c["budget_proposal"], c["diagnostics"]
    groups = []
    assert c["status"] == "PROPOSED_NOT_AUTHORIZED"
    assert c["authorized"] is c["executable"] is False
    assert c["risk"]["bound_selected"] is None
    assert c["data"]["partition"] == "train" and c["data"]["accepted_starts"] == 7048
    assert c["data"]["end_exclusive"] == "2023-01-01T00:00:00Z"
    assert not any(c["data"][k] for k in ("normalizer_refit", "validation_access", "final_access"))
    groups.append("proposal_closed_train_only")

    assert t["horizon"] == 180 and t["gamma"] == t["gae_lambda"] == 1
    assert t["iterations"] == 2 and not t["bootstrap_after_horizon"]
    assert t["horizon"] % t["fragment_steps"] == 0
    assert t["separate_actor_critic"] and not t["advantage_normalization"]
    assert not t["gradient_clipping"] and t["entropy_coefficient"] == 0
    assert c["conditions"] == {"C0": 0, "C5": 0.05, "C10": 0.1}
    groups.append("adopted_contract_not_modified")

    assert [x["seed"] for x in c["blocks"]] == [410031, 410047, 410081]
    for position in range(3):
        assert {x["order"][position] for x in c["blocks"]} == set(c["conditions"])
    for x in c["blocks"]:
        assert len(x["order"]) == 3 and set(x["order"]) == set(c["conditions"])
    groups.append("three_paired_blocks_rotated_order")

    n = t["n_q"] + t["iterations"] * (t["n_a"] + t["n_q"] + t["n_b"])
    assert n == 2128 and n * t["horizon"] == 383040
    assert n * 9 == 19152 and n * 9 * t["horizon"] == 3447360
    steps = t["iterations"] * t["actor_epochs"] * math.ceil(t["n_a"] / t["minibatch_trajectories"])
    assert steps == 16 and steps * 9 == 144
    assert t["actor_epochs"] == t["critic_epochs"]
    assert t["n_q"] == t["n_b"] == 400
    assert [c["conditions"][k] * t["n_b"] for k in ("C5", "C10")] == [20, 40]
    groups.append("complete_calendar_resource_arithmetic")

    bounds = []
    for loss in c["risk"]["bound_candidates_simple_reference"]:
        bound = -math.log1p(-loss)
        assert math.isclose(math.exp(-bound), 1 - loss, abs_tol=1e-15)
        bounds.append({"reference_simple_loss": loss, "d": bound})
    assert bounds[0]["d"] < bounds[1]["d"] < bounds[2]["d"]
    assert c["risk"]["discussion_recommendation_simple_reference"] == 0.1
    groups.append("bound_conversion_only_not_cvar_certificate")

    assert (
        b["preflight_limit_seconds"] + b["work_limit_seconds"] + b["closing_reserve_seconds"]
        == 10800
    )
    assert b["daily_seconds"] == 10800
    assert b["max_sessions_per_run"] * 9 == b["max_campaign_sessions"] == 27
    assert b["unknown_q0_cap_seconds"] == 1800
    cap, margin = b["unknown_iteration_cap_seconds"], b["empirical_margin_multiplier"]
    assert cap == 2700 and margin == 1.5
    # Artificial durations illustrate the PROPOSAL; they are not measured or validated estimates.
    scenarios = [
        (8100, [], "start"),
        (2699, [], "planned_pause"),
        (2700, [], "start"),
        (2100, [1000, 1400], "start"),
        (2099, [1000, 1400], "planned_pause"),
        (8100, [1900], "design_infeasible"),
    ]
    for remaining, durations, expected in scenarios:
        assert admission(remaining, durations, cap, margin) == expected
    assert margin * max([1000, 1400, 900]) == margin * max([1000, 1400])
    groups.append("fictional_clock_admission_and_daily_reserve")

    # Algebraic two-session ledger, not a check of implemented H5 resume behavior.
    ledger = []
    for day, phases, seconds in [(1, ["Q0", "iteration0"], 1300), (2, ["iteration1"], 1200)]:
        count = sum(t["n_q"] if p == "Q0" else t["n_a"] + t["n_q"] + t["n_b"] for p in phases)
        prior = ledger[-1] if ledger else {"trajectories": 0, "seconds": 0}
        ledger.append(
            {
                "day": day,
                "trajectories": prior["trajectories"] + count,
                "seconds": prior["seconds"] + seconds + 60,
            }
        )
    assert ledger[-1]["trajectories"] == 2128 and ledger[-1]["seconds"] == 2620
    assert d["warnings_stop_run"] is d["favorable_risk_stop"] is False
    groups.append("fictional_cumulative_ledger_no_performance_stop")

    changed = subprocess.check_output(
        [
            "git",
            "diff",
            "--name-only",
            c["base_commit"],
            "--",
            "src",
            "scripts",
            "configs",
            "uv.lock",
            "AGENTS.md",
        ],
        cwd=ROOT,
        text=True,
    )
    assert changed.strip() == "", "This proposal must not change operational code/config/guards"
    document = DOC.read_text()
    for token in ["410031", "410047", "410081", "2128", "383040", "19152", "3447360"]:
        assert token in document
    groups.append("operational_files_unchanged_and_document_totals_match")
    result = {
        "status": "passed",
        "kind": "static_and_algebraic_proposal_only",
        "groups": groups,
        "bounds": bounds,
        "per_run": {"trajectories": n, "transitions": n * 180, "adam_steps_per_network": steps},
        "fictional_clock_scenarios": scenarios,
        "fictional_ledger": ledger,
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (CONFIG, DOC, Path(__file__).resolve())
        },
        "market_accessed": False,
        "learning_executed": False,
        "h5_verification_repeated": False,
    }
    with args.output.open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print(f"{len(groups)} groups passed; static/algebraic only; no H5 tests or market execution")


if __name__ == "__main__":
    main()
