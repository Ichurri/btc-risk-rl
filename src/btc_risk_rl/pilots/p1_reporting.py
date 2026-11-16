"""Predefined paired P1 criterion, independent of runtime decisions."""

import math


def primary(rows):
    if len(rows) != 18 or any(r["status"] != "completed" for r in rows):
        return dict(status="not_evaluable_incomplete_campaign", criterion_met=False, seeds=[])
    seeds = []
    for seed in (510031, 510047, 510081):
        conditions = []
        for condition in ("C0", "C5", "C10"):
            pair = {
                r["critic_epochs"]: r
                for r in rows
                if r["seed"] == seed and r["condition"] == condition
            }

            def first(row, label):
                return next(
                    s
                    for s in row["stability"]
                    if s["phase"] == "fixed_A" and s["iteration"] == 0 and s["measurement"] == label
                )

            pre = [first(pair[e], "before_actor") for e in (2, 4)]
            post = [first(pair[e], "after_critic") for e in (2, 4)]
            if (
                pre[0]["batch_sha256"] != pre[1]["batch_sha256"]
                or post[0]["actor_sha256"] != post[1]["actor_sha256"]
            ):
                raise ValueError("P1 paired integrity failed")
            a, b = (s["mse"] for s in post)
            if not all(math.isfinite(x) and x >= 0 for x in (a, b)):
                raise ValueError("Nonfinite/negative primary MSE")
            conditions.append(
                dict(
                    condition=condition,
                    mse_e2=a,
                    mse_e4=b,
                    reduction=None if a == 0 else 1 - b / a,
                    meets=b <= 0.8 * a,
                    batch=pre[0]["batch_sha256"],
                    actor=post[0]["actor_sha256"],
                )
            )
        if any(
            {k: v for k, v in c.items() if k != "condition"}
            != {k: v for k, v in conditions[0].items() if k != "condition"}
            for c in conditions
        ):
            raise ValueError(
                "Conditions should repeat initial comparison, not independent replicas"
            )
        seeds.append(dict(seed=seed, **conditions[0], controls=conditions))
    return dict(
        status="evaluated",
        criterion_met=sum(s["meets"] for s in seeds) >= 2,
        successful_seeds=sum(s["meets"] for s in seeds),
        independent_seed_blocks=3,
        seeds=seeds,
        interpretation="in_sample_fit_only_not_generalization_profit_or_CVaR",
    )
