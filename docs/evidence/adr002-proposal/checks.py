"""Independent synthetic arithmetic for a proposal; no environment or agent imports."""

import hashlib
import json
import math
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def tail_mean(losses, alpha):
    remaining = alpha * len(losses)
    total = 0.0
    for loss in sorted(losses, reverse=True):
        weight = min(1.0, remaining)
        total += weight * loss
        remaining -= weight
        if remaining <= 0:
            break
    return total / (alpha * len(losses))


def variational(losses, alpha):
    return min(
        eta + sum(max(loss - eta, 0.0) for loss in losses) / (alpha * len(losses))
        for eta in losses
    )


def close(actual, expected, tol=1e-12):
    assert math.isclose(actual, expected, rel_tol=0, abs_tol=tol), (actual, expected)


def cut_rule(length, reason):
    assert 0 < length <= 180
    assert reason in {"collection_window", "segment_boundary", "partition_boundary"}
    if length == 180:
        return {"status": "complete", "bootstrap": 0, "trace": 0, "cvar": True}
    if reason == "collection_window":
        return {"status": "await_complete", "bootstrap": 1, "trace": 0, "cvar": False}
    return {"status": "reject_episode", "bootstrap": None, "trace": None, "cvar": False}


def main():
    results = {}
    close(sum((0.1, -0.1)), 0)
    close(0.1 - 0.99 * 0.1, 0.001)
    results["discount"] = {"undiscounted": 0, "discounted": 0.001,
                           "last_weight_gamma_099_h180": 0.99**179}

    rewards, values = [0.02, -0.01, 0.03], [0.04, 0.025, 0.01, 0.0]
    direct = [sum(rewards[j:]) - values[j] for j in range(3)]
    delta = [rewards[j] + values[j + 1] - values[j] for j in range(3)]
    gae = [sum(delta[j:]) for j in range(3)]
    for actual, expected in zip(gae, [0, -0.005, 0.02], strict=True):
        close(actual, expected)
    for actual, expected in zip(gae, direct, strict=True):
        close(actual, expected)
    leaked_delta = delta[:-1] + [delta[-1] + 0.7]
    for j in range(3):
        close(sum(leaked_delta[j:]) - direct[j], 0.7)
    partial_target = sum(rewards[:2]) + values[2]
    close(partial_target, 0.02)
    close(sum(rewards), 0.04)
    results["advantages"] = {"direct": direct, "gae": gae,
                             "partial_bootstrap_target": partial_target,
                             "observed_complete_return": sum(rewards), "terminal_leak": 0.7}

    losses = [0.2, 0.1, -0.02, -0.1]
    close(tail_mean(losses, 0.375), 1 / 6)
    cases = []
    for sample in (losses, [0.2, 0.2, -0.1, -0.1], [-0.1] * 4):
        for alpha in (0.05, 0.1, 0.375, 0.5, 1.0):
            observed = tail_mean(sample, alpha)
            close(observed, variational(sample, alpha))
            cases.append({"losses": sample, "alpha": alpha, "cvar": observed})
    results["cvar_empirical"] = cases

    p, alpha, multiplier = 0.25, 0.5, 0.4
    theta = math.log(p / (1 - p))
    eta = -0.1
    outcomes = [(p, -0.2, 1 - p), (1 - p, 0.1, -p)]
    mean_score = sum(prob * reward * score for prob, reward, score in outcomes)
    risk_score = sum(
        prob * max(-reward - eta, 0) * score / alpha for prob, reward, score in outcomes
    )
    close(mean_score, -0.05625)
    close(risk_score, 0.1125)
    combined = mean_score - multiplier * risk_score
    close(combined, -0.10125)

    def objective(angle, penalty):
        probability = 1 / (1 + math.exp(-angle))
        return 0.1 - 0.3 * probability - penalty * (0.6 * probability - 0.1)

    derivatives = []
    for penalty in (0.0, multiplier):
        eps = 1e-6
        numerical = (objective(theta + eps, penalty) - objective(theta - eps, penalty)) / (2 * eps)
        analytical = (-0.3 - penalty * 0.6) * p * (1 - p)
        close(numerical, analytical, tol=1e-10)
        close(mean_score - penalty * risk_score, analytical)
        derivatives.append({"lambda_risk": penalty, "finite_difference": numerical,
                            "closed_form": analytical})
    results["gradient_enumeration_no_optimization"] = derivatives

    cuts = []
    for length in (60, 179, 180):
        for reason in ("collection_window", "segment_boundary", "partition_boundary"):
            rule = cut_rule(length, reason)
            assert rule["cvar"] == (length == 180)
            if length == 180:
                assert rule["bootstrap"] == rule["trace"] == 0
            elif reason != "collection_window":
                assert rule["status"] == "reject_episode" and rule["bootstrap"] is None
            else:
                assert rule["status"] == "await_complete" and rule["bootstrap"] == 1
            cuts.append({"length": length, "reason": reason, **rule})
    results["cut_examples_specification_only"] = cuts
    # Deployment clock never implies a portfolio reset. This checks its schedule only.
    training_clock = [(180 - j) / 180 for j in range(181)]
    deployment_clock = [1.0] * 2190
    assert training_clock[0] == 1 and training_clock[-1] == 0
    assert all(h == 1 for h in deployment_clock)
    results["clock_schedule_only"] = {"training_states": len(training_clock),
                                     "validation_actions": len(deployment_clock)}

    protected = subprocess.check_output(
        ["git", "ls-files", "src", "configs", "tests", "scripts", "uv.lock", "pyproject.toml"],
        text=True,
    ).splitlines()
    fingerprints = {}
    for name in protected:
        current = Path(name).read_bytes()
        committed = subprocess.check_output(["git", "show", f"cc913b6:{name}"])
        assert current == committed, f"H2 changed: {name}"
        fingerprints[name] = hashlib.sha256(current).hexdigest()
    print(json.dumps({
        "status": "passed", "scope": "synthetic proposal calculations, no agent or market data",
        "utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "platform": platform.platform(),
        "base_commit": subprocess.check_output(["git", "rev-parse", "cc913b6"], text=True).strip(),
        "head_at_run": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "groups": len(results), "results": results, "unchanged_h2_files_sha256": fingerprints,
    }, indent=2))


if __name__ == "__main__":
    main()
