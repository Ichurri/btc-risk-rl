"""Verify the frozen evaluation and derive secondary evidence from saved traces."""

import argparse
import csv
import json
import tomllib
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from secondary_metrics import (
    BOOTSTRAP_SAMPLES,
    BOOTSTRAP_SEED,
    CONDITIONS,
    EVIDENCE,
    METRICS,
    REFERENCE,
    ROOT,
    SCOPE,
    drawdown,
    output_path,
    paired_summary,
    read_verified,
    summarize,
)

FINAL = ROOT / "artifacts/oos-v12-final-2024-2025-01"
AUDIT = ROOT / "docs/evidence/oos-v12-evaluation-20261115"
LEDGER_SHA = "b035e1fef6d5e95b2b75df660cc178382081552207be30358f632f49a7e513ad"
PAIRED_SHA = "31b95677b68b0ccdef3584f78b2c7755c12d3c91c804fce90e111cd6cafec44e"
REFERENCE_SHA = "177745bf76a575ba8c9bbd8c1e24f4386dbd8cb3686c7ac78977cc7ce9b905a7"
CONFIG_SHA = "1a6b5b401f20c9e4a11835cf4575b70c73d72bb4e844aca7552e3f934d911269"
STEPS, BLOCKS = 4386, 36
FIRST_MS, FOUR_HOURS_MS = 1704067200000, 14400000
TIMELINE = FIRST_MS + FOUR_HOURS_MS * np.arange(STEPS)


def verified_inputs():
    raw = read_verified(FINAL / "ledger.jsonl", LEDGER_SHA)
    state = json.loads(raw.splitlines()[-1])
    accepted = state["accepted"]
    roster = state["identity"]["roster"]
    if (state["status"] != "completed" or state["cursor"] != BLOCKS * 3
            or state["pending"] is not None or state["identity"]["partition"] != "final_2024_2025"
            or len(accepted) != BLOCKS * 3 or [entry["run"] for entry in accepted] != roster):
        raise ValueError("Ledger final incompleto o de procedencia incorrecta")
    primary = list(csv.DictReader(read_verified(
        AUDIT / "chapter-4/paired-blocks.csv", PAIRED_SHA
    ).decode().splitlines()))
    paired = {int(row["seed"]): row for row in primary}
    expected_pairs = {(seed, c) for seed in paired for c in CONDITIONS}
    actual_pairs = {(run["seed"], run["condition"]) for run in roster}
    run_ids = {run["run_id"] for run in roster}
    if (len(primary) != BLOCKS or len(paired) != BLOCKS
            or {int(row["block"]) for row in primary} != set(range(1, BLOCKS + 1))
            or actual_pairs != expected_pairs or len(run_ids) != BLOCKS * 3):
        raise ValueError("Bloques o identidades de la evaluación incompatibles")
    reference = json.loads(read_verified(
        ROOT / "docs/evidence/oos-v12-buy-hold-20261115/result.json", REFERENCE_SHA
    ))
    config = tomllib.loads(read_verified(ROOT / "configs/initial.toml", CONFIG_SHA).decode())

    for index, item in enumerate(accepted):
        run = item["run"]
        run_id = run["run_id"]
        if run_id != f"run-{index:02d}-{run['condition']}-b0":
            raise ValueError(f"Identificador de corrida incorrecto: {run_id}")
        trace_path = FINAL / run_id / "trace.jsonl"
        read_verified(trace_path, item["trace_sha256"])
        report = json.loads(read_verified(FINAL / run_id / "report.json", item["report_sha256"]))
        expected = {
            "status": "completed", "audit_accepted": True, "steps": STEPS,
            "partition": "final_2024_2025", "run_id": run_id, "seed": run["seed"],
            "condition": run["condition"], "trace_sha256": item["trace_sha256"],
            "checkpoint_state_sha256": run["checkpoint_sha256"],
            "export_manifest_sha256": reference["export_manifest_sha256"],
        }
        if any(report.get(key) != value for key, value in expected.items()):
            raise ValueError(f"Reporte incompatible con el ledger: {run_id}")
    return accepted, paired, reference, config


def load_series(item, initial):
    raw = read_verified(FINAL / item["run"]["run_id"] / "trace.jsonl", item["trace_sha256"])
    rows = [json.loads(line) for line in raw.splitlines()]
    times, steps, opens, closes, equity, btc, cash, returns = np.array([
        [row[key] for key in ("execution_ms", "step", "open_price", "close_price",
                              "equity", "btc_after", "cash_after", "simple_return")]
        for row in rows
    ], dtype=float).T
    if (not np.array_equal(times, TIMELINE)
            or not np.array_equal(steps, np.arange(1, STEPS + 1))
            or not np.isfinite(opens).all() or not np.isfinite(closes).all()
            or np.any(opens <= 0) or np.any(closes <= 0)
            or rows[0]["btc_before"] != 0 or rows[0]["cash_before"] != initial
            or not np.allclose(equity, btc * closes + cash, rtol=1e-12, atol=1e-12)):
        raise ValueError(f"Ruta de valoración inválida: {item['run']['run_id']}")
    equity = np.r_[initial, equity]
    if not np.allclose(equity[1:] / equity[:-1] - 1, returns, rtol=0, atol=2e-15):
        raise ValueError(f"Retornos incoherentes: {item['run']['run_id']}")
    return opens, closes, equity, np.r_[0, btc * closes / equity[1:]]


def check_match(actual, expected, name, *, tolerance=1e-12):
    if actual is None or not np.isclose(actual, expected, rtol=0, atol=tolerance):
        raise ValueError(f"No coincide con el resultado auditado: {name}")
    return abs(actual - expected)


def reference_series(opens, closes, config, reference):
    capital, fee, slip = (config["environment"][key] for key in
                          ("initial_cash", "commission", "slippage"))
    quantity = capital / (opens[0] * (1 + slip) * (1 + fee))
    check_match(quantity, reference["btc_purchased"], "cantidad BTC de la referencia")
    equity = np.r_[capital, quantity * closes]
    check_match(equity[-1], reference["final_equity"], "patrimonio de la referencia", tolerance=1e-9)
    return equity, np.r_[0, np.ones(STEPS)]


def write_csv(dest, file, fields, rows):
    with (dest / file).open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def condition_summary(policies, reference_metrics):
    rows = []
    for condition in (*CONDITIONS, REFERENCE):
        group = ([reference_metrics] if condition == REFERENCE else
                 [row for row in policies if row["condition"] == condition])
        row = {"condition": condition, "n": len(group)}
        for key in METRICS:
            values = [item[key] for item in group if item[key] is not None]
            complete = len(values) == len(group)
            row.update({
                f"{key}_n_defined": len(values),
                f"{key}_mean": float(np.mean(values)) if complete else None,
                f"{key}_sd": float(np.std(values, ddof=1)) if complete and len(values) > 1 else None,
                f"{key}_min": min(values) if complete else None,
                f"{key}_max": max(values) if complete else None,
            })
        rows.append(row)
    return rows


def paired_differences(policies):
    by_condition = {
        condition: sorted((row for row in policies if row["condition"] == condition),
                          key=lambda row: row["block"])
        for condition in CONDITIONS
    }
    for condition in CONDITIONS[1:]:
        for key in METRICS:
            n, mean, sd, low, high = paired_summary(
                [row[key] for row in by_condition[condition]],
                [row[key] for row in by_condition["C0"]],
            )
            yield {"contrast": condition + " − C0", "metric": key,
                   "n_defined_pairs": n, "n_total_pairs": BLOCKS, "mean": mean,
                   "sample_sd": sd, "ci95_low": low, "ci95_high": high}


def curve_rows(equity, exposure, hold):
    hold_equity, _ = hold
    timestamps = [datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat()
                  for ms in [FIRST_MS, *(TIMELINE + FOUR_HOURS_MS)]]
    for name, by_condition, reference in (
        ("curva-patrimonio", equity, hold_equity),
        ("curva-drawdown", {c: [drawdown(s) for s in equity[c]] for c in CONDITIONS},
         drawdown(hold_equity)),
        ("exposicion-media", exposure, None),
    ):
        fields = {"valuation_utc": timestamps}
        for c, values in by_condition.items():
            for label, series in zip(("p05", "median", "p95"),
                                      np.percentile(values, [5, 50, 95], axis=0), strict=True):
                fields[f"{c}_{label}"] = series
            if name == "exposicion-media":
                fields[f"{c}_mean"] = np.mean(values, axis=0)
        if reference is not None:
            fields["buy_and_hold"] = reference
        yield name, list(fields), (dict(zip(fields, row, strict=True))
                                   for row in zip(*fields.values(), strict=True))


def compute(dest):
    accepted, primary, reference, config = verified_inputs()
    initial = config["environment"]["initial_cash"]
    equity = {condition: [] for condition in CONDITIONS}
    exposure = {condition: [] for condition in CONDITIONS}
    policies = []
    audit_error = 0
    common_market = None
    for item in accepted:
        run = item["run"]
        condition, seed = run["condition"], run["seed"]
        opens, closes, values, weights = load_series(item, initial)
        if common_market is None:
            common_market = opens, closes
        elif not all(np.array_equal(a, b) for a, b in zip(common_market, (opens, closes), strict=True)):
            raise ValueError("Las trazas no comparten exactamente precios de apertura y cierre")
        metrics = summarize(values, weights)
        paired = primary[seed]
        audit_error = max(audit_error, check_match(
            metrics["sortino"], float(paired[f"{condition}_sortino_annualized"]), run["run_id"]
        ))
        policies.append({"block": int(paired["block"]), "seed": seed,
                         "condition": condition, **metrics})
        equity[condition].append(values)
        exposure[condition].append(weights)

    hold = reference_series(*common_market, config, reference)
    hold_metrics = summarize(*hold)
    reference_error = check_match(hold_metrics["sortino"], reference["sortino_annualized"], REFERENCE)
    check_match(hold_metrics["return_net"], reference["cumulative_net_return_fraction"], REFERENCE)
    policies.sort(key=lambda row: (row["block"], CONDITIONS.index(row["condition"])))
    summary = condition_summary(policies, hold_metrics)
    pairs = list(paired_differences(policies))

    dest.mkdir(parents=True, exist_ok=False)
    write_csv(dest, "metrics-by-policy.csv", list(policies[0]), policies)
    write_csv(dest, "summary-by-condition.csv", list(summary[0]), summary)
    write_csv(dest, "paired-differences.csv", list(pairs[0]), pairs)
    sortino = [{key: row[key] for key in ("block", "seed", "condition", "sortino")}
               for row in policies]
    sortino.append({"block": "", "seed": "", "condition": REFERENCE, "sortino": hold_metrics["sortino"]})
    write_csv(dest, "sortino-por-condicion.csv", list(sortino[0]), sortino)
    for name, fields, rows in curve_rows(equity, exposure, hold):
        write_csv(dest, name + ".csv", fields, rows)
    metadata = {
        "scope": SCOPE, "ledger_sha256": LEDGER_SHA, "paired_blocks_sha256": PAIRED_SHA,
        "buy_hold_result_sha256": REFERENCE_SHA, "config_sha256": CONFIG_SHA,
        "verified_traces": len(accepted), "verified_reports": len(accepted),
        "steps_per_policy": STEPS, "blocks": BLOCKS, "max_policy_sortino_abs_error": audit_error,
        "buy_hold_sortino_abs_error": reference_error, "sortino_abs_tolerance": 1e-12,
        "export_manifest_sha256": reference["export_manifest_sha256"],
        "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_resamples": BOOTSTRAP_SAMPLES,
        "numpy_version": np.__version__,
    }
    (dest / "integrity.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(metadata, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=EVIDENCE)
    args = parser.parse_args()
    compute(output_path(ROOT, args.output))
