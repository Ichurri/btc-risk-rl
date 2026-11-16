"""Read-only P2R value-error audit on already accepted checkpoints/reports.

No market loader, trajectory collector, policy evaluation, or optimizer is used.
All moments are reconstructed from the frozen full-batch diagnostic sums.
"""

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[3]
CAMPAIGN = ROOT / "artifacts/p2r-approved-v2"
CLOSURE = ROOT / "docs/evidence/p2r-market-2026-10-07/results.json"
CLOSURE_SHA256 = "77e784caf50a0d0716ac9b0a7055f9f034b06b0ec4aaa0a43fb172ee2b90fbc6"
LEDGER_SHA256 = "fe443e5e32d26a7de075fa6e34771c8f20651bbe566f9097bfdb367d17d0b866"
ROSTER = (
    (610031, "C0"), (610031, "C5"), (610031, "C10"),
    (610047, "C5"), (610047, "C10"), (610047, "C0"),
    (610081, "C10"), (610081, "C0"), (610081, "C5"),
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pooled(metrics):
    n = sum(m["count"] for m in metrics)
    sse = sum(m["sse"] for m in metrics)
    target_sq = sum(m["target_sq"] for m in metrics)
    error_sum = sum(m["error_sum"] for m in metrics)
    mse, z = sse / n, target_sq / n
    pv = sum(
        m["count"] * (m["prediction_stats"]["std"] ** 2
                      + m["prediction_stats"]["mean"] ** 2)
        for m in metrics
    ) / n
    pm = sum(m["count"] * m["prediction_stats"]["mean"] for m in metrics) / n
    gm = sum(m["count"] * m["target_stats"]["mean"] for m in metrics) / n
    gv = sum(
        m["count"] * (m["target_stats"]["std"] ** 2
                      + m["target_stats"]["mean"] ** 2)
        for m in metrics
    ) / n - gm**2
    cross = (pv + z - mse) / 2
    covariance = cross - pm * gm
    centered = (pv - pm**2) - 2 * covariance
    mean_component = pm**2 - 2 * pm * gm
    assert math.isclose(z, gv + gm**2, rel_tol=1e-11, abs_tol=1e-12)
    assert math.isclose(mse - z, centered + mean_component, rel_tol=1e-10, abs_tol=1e-12)
    assert math.isclose(error_sum / n, pm - gm, rel_tol=1e-10, abs_tol=1e-12)
    return dict(
        n=n, mse=mse, z=z, relative_mse=mse / (z + 1e-12),
        bias=error_sum / n, normalized_bias=(error_sum / n) / math.sqrt(z + 1e-12),
        prediction_mean=pm, prediction_sd=math.sqrt(max(0, pv - pm**2)),
        target_mean=gm, target_sd=math.sqrt(max(0, gv)),
        prediction_target_covariance=covariance,
        prediction_second_moment=pv, prediction_target_cross_moment=cross,
        excess_mse_over_zero=mse - z,
        centered_excess_component=centered, mean_excess_component=mean_component,
        half_scale_algebraic_relative_mse=(0.25 * pv - cross + z) / (z + 1e-12),
    )


def main():
    assert sha256(CLOSURE) == CLOSURE_SHA256
    closure = json.loads(CLOSURE.read_text())
    assert closure["numerical_technical_decision"] == "review"
    assert sha256(CAMPAIGN / "ledger.jsonl") == LEDGER_SHA256
    ledger = json.loads((CAMPAIGN / "ledger.jsonl").read_text().splitlines()[-1])
    assert ledger["status"] == "completed" and len(ledger["units"]) == 99
    summaries = []
    records_by_seed = defaultdict(list)
    for i, (seed, condition) in enumerate(ROSTER):
        run_id = f"run-{i:02d}-{condition}"
        run_root = CAMPAIGN / run_id
        unit = json.loads((run_root / "unit-10.json").read_text())
        entry = ledger["units"][11 * i + 10]
        state_path = run_root / "checkpoint-10/state.pt"
        assert entry["run_id"] == run_id and entry["unit"] == 10
        assert unit["checkpoint_sha256"] == entry["checkpoint_sha256"] == sha256(state_path)
        saved = torch.load(state_path, map_location="cpu", weights_only=True)
        records = unit["report"]["diagnostic"]["records"]
        assert saved["diagnostic"]["records"] == records
        assert [row["iteration"] for row in records] == list(range(10))
        assert unit["report"]["settings"]["seed"] == seed
        assert unit["report"]["condition"] == condition
        windows = {}
        for label, indices in (("early", (0, 1, 2)), ("late", (7, 8, 9))):
            windows[label] = {
                batch: {
                    stage: pooled([records[k][batch][stage] for k in indices])
                    for stage in ("pre", "post")
                }
                for batch in ("A", "D")
            }
        thirds = {
            label: [
                pooled([records[k]["D"]["post"]["thirds"][j] for k in indices])
                for j in range(3)
            ]
            for label, indices in (("early", (0, 1, 2)), ("late", (7, 8, 9)))
        }
        late_risk = [records[k]["risk"] for k in (7, 8, 9)]
        summaries.append(dict(
            run_id=run_id, seed=seed, condition=condition, windows=windows,
            D_post_thirds=thirds,
            D_post_late_per_iteration=[records[k]["D"]["post"]["relative_mse"]
                                       for k in (7, 8, 9)],
            A_post_late_per_iteration=[records[k]["A"]["post"]["relative_mse"]
                                       for k in (7, 8, 9)],
            late_risk_gradient_active=sum(r["initial_risk_gradient_norm"] > 0
                                          for r in late_risk),
            late_shortfalls_A=sum(r["shortfalls"]["numerator"] for r in late_risk),
        ))
        records_by_seed[seed].append(records)
    seed_shared_routes = {}
    for seed, triplet in records_by_seed.items():
        same_routes = [len({tuple(a["route_id"] for a in records[k]["archives"])
                            for records in triplet}) == 1 for k in range(10)]
        same_policy = [len({records[k]["policy_version"] for records in triplet}) == 1
                       for k in range(10)]
        same_targets = [len({records[k]["targets_sha256"] for records in triplet}) == 1
                        for k in range(10)]
        assert all(same_routes)
        seed_shared_routes[str(seed)] = dict(
            D_route_ids_same_across_conditions_all_iterations=all(same_routes),
            same_policy_iterations=[k for k, equal in enumerate(same_policy) if equal],
            same_target_iterations=[k for k, equal in enumerate(same_targets) if equal],
        )
    print(json.dumps(dict(
        audit_kind="algebra_on_existing_full_batch_metrics_with_checkpoint_binding",
        ledger_sha256=LEDGER_SHA256,
        closure_results_sha256=CLOSURE_SHA256,
        numerical_result_unchanged=closure["numerical_technical_decision"],
        windows_definition=dict(early=[0, 1, 2], late=[7, 8, 9]),
        independent_seed_blocks=3, seed_shared_routes=seed_shared_routes,
        summaries=summaries,
    ), sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
