"""Static/algebraic proposal checks only: no market/model/runner imports or samples."""

import hashlib
import json
import math
import platform
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
candidate_path = ROOT / "docs/proposals/P2-candidate-v1.json"
p = json.loads(candidate_path.read_text())
p1 = json.loads((ROOT / "docs/protocols/P1-approved-v1.json").read_text())
checks = []
assert not p["authorized"] and not p["executable"]
assert p["status"] == "PROPUESTA PARA REVISIÓN, NO AUTORIZADA PARA EJECUCIÓN"
assert p["risk"]["bound_selected"] == -math.log(0.9)
assert (
    p["data"] == p1["data"] and not p["data"]["validation_access"] and not p["data"]["final_access"]
)
a, b = dict(p["training_candidate"]), dict(p1["training_candidate"])
assert a.pop("iterations") == 10 and a.pop("critic_epochs") == 4
assert a.pop("critic_epochs_status") == "provisional_candidate_not_confirmatory"
b.pop("iterations")
b.pop("critic_epochs_arms")
assert a == b
checks.append(
    "non_authorization_fixed_d_and_unchanged_learning_parameters_except_K_and_provisional_epochs"
)
seeds = [b["seed"] for b in p["blocks"]]
assert seeds == [610031, 610047, 610081]
assert not set(seeds) & {410031, 410047, 410081, 510031, 510047, 510081}
roster = [(b["seed"], c) for b in p["blocks"] for c in b["order"]]
assert len(roster) == len(set(roster)) == 9
assert [b["order"] for b in p["blocks"]] == [b["order"] for b in p1["blocks"]]
checks.append("nine_runs_three_new_seed_blocks_rotated_order")
k, n_a, n_q, n_b, n_d, h = 10, 64, 400, 400, 64, 180
learning = n_q + k * (n_a + n_q + n_b)
diagnostic = k * n_d
resources = dict(
    learning_trajectories=9 * learning,
    diagnostic_trajectories=9 * diagnostic,
    total_trajectories=9 * (learning + diagnostic),
    learning_transitions=9 * learning * h,
    diagnostic_transitions=9 * diagnostic * h,
    total_transitions=9 * (learning + diagnostic) * h,
    actor_steps=9 * k * 2 * 4,
    critic_steps=9 * k * 4 * 4,
)
assert resources == dict(
    learning_trajectories=81360,
    diagnostic_trajectories=5760,
    total_trajectories=87120,
    learning_transitions=14644800,
    diagnostic_transitions=1036800,
    total_transitions=15681600,
    actor_steps=720,
    critic_steps=1440,
)
assert p["diagnostic_candidate"]["n"] == 64 and p["diagnostic_candidate"]["iterations"] == list(
    range(10)
)
assert p["diagnostic_candidate"]["policy"] == "frozen_pi_k_that_generated_A_k"
# Coordinate disjointness is algebraic, not an empirical RNG-independence test.
coords_d = {(seed, 7002, i, s) for seed in seeds for i in range(k) for s in (0, 1)}
coords_learning = {
    (seed, role, i, s) for seed in seeds for role in (1, 2, 3) for i in range(k + 1) for s in (0, 1)
}
assert not coords_d & coords_learning
checks.append("resource_arithmetic_and_disjoint_D_coordinates_no_rng_draws")
# MC sums and a policy-correspondence counterexample on hand-defined numbers.
r = [1.0, -2.0, 3.0] + [0.0] * 177
g = [sum(r[j:]) for j in range(180)]
assert g[:4] == [2.0, 1.0, 3.0, 0.0] and len(g) == 180
old_policy_target = 1.0
new_policy_target = 4.0
perfect_old_critic = 1.0
assert (perfect_old_critic - old_policy_target) ** 2 == 0
assert (perfect_old_critic - new_policy_target) ** 2 == 9
checks.append("full_MC_H180_and_policy_shift_counterexample_not_agent_validation")
# Pooled ratios differ from mean-of-ratios with different target scale.
assert (1 + 4) / (1 + 16) == 5 / 17 and (1 / 1 + 4 / 16) / 2 == 0.625
# A diagnostic improvement can coexist with R>1; bias is signed.
target = [0.1, -0.1]
before = [0.4, 0.4]
after = [0.2, 0.2]


def mse(v):
    return sum((x - y) ** 2 for x, y in zip(v, target, strict=True)) / 2


assert mse(after) < mse(before) and mse(after) / (sum(x * x for x in target) / 2 + 1e-12) > 1
assert sum(x - y for x, y in zip(after, target, strict=True)) / 2 == 0.2
checks.append("MSE_bias_denominator_and_pooled_ratio_algebra")


# Gates exercised on fabricated summaries, no pilot trajectory generation.
def gate(early, late, bias, gap, z):
    return z > 1e-12 and late <= 1 and late <= 0.8 * early and abs(bias) <= 0.25 and gap <= 0.5


assert gate(1.25, 1.0, 0.25, 0.5, 0.01)
assert not gate(1.0, 1.0, 0, 0, 0.01)
assert not gate(2.0, 1.1, 0, 0, 0.01)
assert not gate(2.0, 0.8, 0.251, 0, 0.01)
assert not gate(2.0, 0.8, 0, 0.501, 0.01)
assert not gate(2.0, 0.8, 0, 0, 0)
assert p["assessment_candidate"]["early_iterations"] == [0, 1, 2]
assert p["assessment_candidate"]["late_iterations"] == [7, 8, 9]
checks.append("predefined_gates_boundary_cases_and_undefined_scale")
# Overlapping synthetic integer intervals: distinct starts can share transitions.
a_times = set(range(180))
d_times = set(range(1, 181))
assert len(a_times & d_times) == 179 and 0 != 1
assert 10800 - 5424.038072 - 1800 < 2700 + 1800  # cannot assume room for arbitrary next units
assert p["budget_proposal"]["unknown_combined_iteration_D_cap_seconds"] == 2700
assert p["budget_proposal"]["diagnostic_phase_cap_seconds"] == 900
checks.append("overlap_not_identical_start_and_shared_budget_arithmetic")
timing = {}
for name, path, arm in [
    ("P0", "docs/evidence/p0-execution/campaign-results/results.json", None),
    ("P1_e4", "docs/evidence/p1-execution/campaign-results/results.json", 4),
]:
    data = json.loads((ROOT / path).read_text())
    timing[name] = {}
    for kind in ("q0", "iteration"):
        values = [
            u["supervisor"]["work_seconds"]
            for row in data["runs"]
            if arm is None or row["critic_epochs"] == arm
            for u in row["measured_units"]
            if u["kind"] == kind
        ]
        timing[name][kind] = dict(
            n=len(values), min=min(values), median=statistics.median(values), max=max(values)
        )
proxy = 9 * (timing["P1_e4"]["q0"]["median"] + 10 * timing["P1_e4"]["iteration"]["median"])
max_proxy = 9 * (timing["P1_e4"]["q0"]["max"] + 10 * timing["P1_e4"]["iteration"]["max"])
checks.append("timing_read_from_prior_small_JSON_only_D_cost_unknown")
operational = subprocess.check_output(
    [
        "git",
        "diff",
        "811d882",
        "--name-only",
        "--",
        "src",
        "scripts",
        "configs",
        "pyproject.toml",
        "uv.lock",
    ],
    cwd=ROOT,
    text=True,
)
assert operational == ""
checks.append("no_operational_changes_no_new_permission_registry")
result = dict(
    status="passed",
    groups=len(checks),
    checks=checks,
    resources=resources,
    measured_antecedents=timing,
    planning_proxy_learning_only_seconds=proxy,
    max_observed_proxy_learning_only_seconds=max_proxy,
    margin_1_5_proxy_seconds=1.5 * max_proxy,
    diagnostic_cost_measured=False,
    python=platform.python_version(),
    proposal_sha256=hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
    scope="static_and_algebraic_no_market_no_training_no_executor_validation",
)
with (OUT / "results-verified.json").open("x") as f:
    json.dump(result, f, indent=2)
print(json.dumps(result))
