"""Update the local handoff report after a supervised OOS training session."""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from btc_risk_rl.pilots.oos_v12_training import (
    CAMPAIGNS,
    LA_PAZ,
    PROFILES,
    digest,
    read_budget,
)
from btc_risk_rl.pilots.p2_budget import state_hash
from btc_risk_rl.pilots.protocol import ROOT


def main():
    stamp = datetime.now(LA_PAZ).strftime("%d/%m/%Y %H:%M America/La_Paz")
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                            text=True, capture_output=True, check=True).stdout.strip()
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=ROOT,
                            text=True, capture_output=True, check=True).stdout.strip()
    lines = [f"# Reporte Codex — {stamp}", "", f"- Rama `{branch}`, commit `{commit}`."]
    for profile in PROFILES:
        root = CAMPAIGNS[profile]
        path = root / "ledger.jsonl"
        if not path.is_file():
            lines.append(f"- `{profile}`: sin ledger; no se inició una unidad.")
            continue
        previous = None
        for raw in path.read_text().splitlines():
            state = json.loads(raw)
            if (state.get("previous_hash") != previous
                    or state.get("state_hash") != state_hash(state)):
                raise ValueError(f"OOS report ledger hash chain corrupt: {path}")
            previous = state["state_hash"]
        accepted = len(state.get("units", []))
        lines.append(f"- `{profile}`: ledger `{state['status']}`, "
                     f"{accepted} unidades aceptadas, cursor {state['cursor']}, "
                     f"pending={state.get('pending') is not None}; "
                     f"SHA-256 ledger `{digest(path)}`.")
        charged = sum(day.get("charged_wall_seconds", 0.0)
                      for day in state.get("days", {}).values())
        lines.append(f"- `{profile}`: cargo propio medido en ledger "
                     f"{charged:.3f} s; última unidad "
                     f"{state['units'][-1]['seconds']:.3f} s."
                     if state.get("units") else
                     f"- `{profile}`: cargo propio medido en ledger {charged:.3f} s; "
                     "sin unidad aceptada.")
        if state.get("units"):
            last = state["units"][-1]
            checkpoint = last.get("checkpoint")
            if (checkpoint is None
                    or digest(Path(checkpoint) / "state.pt")
                    != last.get("checkpoint_sha256")):
                raise ValueError(f"OOS report checkpoint differs from ledger: {profile}")
            lines.append(f"- Último checkpoint `{profile}`: `{last.get('checkpoint')}`; "
                         f"estado SHA-256 `{last.get('checkpoint_sha256')}`.")
    prep = ROOT / "artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl"
    if prep.is_file():
        lines.append(f"- Bitácora de comprobaciones: `{prep}`; SHA-256 `{digest(prep)}`.")
    try:
        budget = read_budget("main-2018-2022")
        lines.append(f"- Presupuesto global del día: {budget['global_spent']:.3f} s "
                     f"cargados; {budget['remaining_before_reserve']:.3f} s "
                     "antes de la reserva de cierre de 2.700 s. "
                     f"Puerta: {'ready' if budget['ok'] else 'blocked'}.")
    except (OSError, ValueError) as exc:
        lines.append(f"- Presupuesto global no verificable: {exc}.")
    lines += ["- Validación 2023 y prueba final 2024–2025 permanecen cerradas.",
              "- Siguiente acción: consultar el ledger y el journal de `systemd --user`; "
              "reanudar solo un estado `ready` en la siguiente ventana con suite, Ruff, "
              "preflight vigilado y admisión nuevos. Un estado `failed`/`incomplete` "
              "no se reanuda.", "", "---", ""]
    report = ROOT / "reporte-codex.md"
    old = report.read_text() if report.exists() else ""
    temporary = report.with_name(f".{report.name}.{os.getpid()}.tmp")
    temporary.write_text("\n".join(lines) + "\n" + old)
    os.replace(temporary, report)


if __name__ == "__main__":
    main()
