"""Audited, read-only tables of complete OOS training runs."""

from __future__ import annotations

import hashlib
from pathlib import Path

from btc_risk_rl.reporting.oos_progress import summarize_state

EXPECTED_RUNS = {"wf-2021": 9, "wf-2022": 9, "main-2018-2022": 108}
RESOURCE_KEYS = ("trajectories", "actor_updates", "critic_updates",
                 "diagnostic_trajectories")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def completed_run_rows(profile: str, state: dict, expected_roster,
                       *, root: Path) -> list[dict]:
    """Verify accepted checkpoint bytes and omit incomplete runs from tables."""
    if profile not in EXPECTED_RUNS:
        raise ValueError("Unknown OOS profile")
    roster = tuple(tuple(row) for row in expected_roster)
    if (len(roster) != EXPECTED_RUNS[profile] or len(set(roster)) != len(roster)
            or state.get("identity", {}).get("profile") != "oos_v12_market_units"
            or state["identity"].get("roster") != [list(row) for row in roster]):
        raise ValueError("OOS frozen roster identity mismatch")
    summary = summarize_state(profile, state, expected_runs=len(roster))
    root = Path(root).resolve()
    grouped: dict[str, list[dict]] = {}
    for unit in state["units"]:
        checkpoint = Path(unit["checkpoint"]).resolve()
        if not checkpoint.is_relative_to(root):
            raise ValueError("OOS checkpoint outside campaign root")
        if _sha256(checkpoint / "state.pt") != unit["checkpoint_sha256"]:
            raise ValueError("OOS accepted checkpoint hash mismatch")
        grouped.setdefault(unit["run_id"], []).append(unit)
    rows = []
    for index in range(summary["completed_runs"]):
        seed, condition, beta = roster[index]
        run_id = f"run-{index:02d}-{condition}-b{beta}"
        units = grouped.get(run_id)
        if units is None or len(units) != 11:
            raise ValueError("OOS completed run differs from roster")
        recorded = state.get("runs", {}).get(run_id, {}).get("resources", {})
        resources = {}
        for key in RESOURCE_KEYS:
            values = [unit.get("resources", {}).get(key) for unit in units]
            if (any(type(value) is not int or value < 0 for value in values)
                    or recorded.get(key) != sum(values)):
                raise ValueError("OOS run resource counters disagree with accepted units")
            resources[key] = sum(values)
        rss = [unit.get("supervisor", {}).get("rss_peak_bytes") for unit in units]
        if any(type(value) is not int or value <= 0 for value in rss):
            raise ValueError("OOS run memory measurement missing")
        rows.append({"run_id": run_id, "seed": seed, "condition": condition,
                     "units": 11, "unit_seconds": sum(row["seconds"] for row in units),
                     "checkpoint_sha256": units[-1]["checkpoint_sha256"],
                     "peak_rss_mib": max(rss) / 1024**2, **resources})
    if len(rows) != summary["completed_runs"]:
        raise ValueError("OOS completed run count mismatch")
    return rows


def render_markdown_table(rows: list[dict], *, profile: str,
                          ledger_sha256: str) -> str:
    """Training time and provenance only; no financial outcome is inferred."""
    if profile not in EXPECTED_RUNS or len(ledger_sha256) != 64:
        raise ValueError("OOS table provenance invalid")
    lines = [f"## {profile}: corridas completas", "",
             f"Fuente: ledger de `{profile}` SHA-256 `{ledger_sha256}`. "
             "Tiempos medidos solo de unidades aceptadas; entrenamiento, "
             "sin evaluación fuera de muestra.", "",
             "| Corrida | Semilla | Condición | Unidades | Tiempo (s) | "
             "Trayectorias A/Q/B | Trayectorias D | Pasos actor | Pasos crítico | "
             "Pico RSS (MiB) | Checkpoint K10 SHA-256 |",
             "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for row in rows:
        seconds = f"{row['unit_seconds']:.3f}".replace(".", ",")
        rss = f"{row['peak_rss_mib']:.1f}".replace(".", ",")
        lines.append(f"| {row['run_id']} | {row['seed']} | {row['condition']} | "
                     f"{row['units']} | {seconds} | {row['trajectories']} | "
                     f"{row['diagnostic_trajectories']} | {row['actor_updates']} | "
                     f"{row['critic_updates']} | {rss} | `{row['checkpoint_sha256']}` |")
    if not rows:
        lines.append("| Sin corrida completa | — | — | 0 | — | — | — | — | — | — | — |")
    lines.extend(["", "Las unidades parciales o pendientes no son comparaciones completas.", ""])
    return "\n".join(lines)
