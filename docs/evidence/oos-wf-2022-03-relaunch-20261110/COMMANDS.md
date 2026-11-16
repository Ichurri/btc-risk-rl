# Comandos realmente ejecutados — 10/11/2026

```bash
date '+%Y-%m-%d %H:%M:%S %Z'
systemctl --user show oos-wf-cost-2022-03-session-01.timer
systemctl --user show oos-wf-cost-2022-03-session-01.service
journalctl --user -u oos-wf-cost-2022-03-session-01.service --no-pager
systemctl --user list-units --type=service --state=running --no-legend
```

Tras el reinicio, el timer y el servicio originales estaban `not-found`, sin journal ni intento. Con memoria recuperada se lanzó:

```bash
systemd-run --user --wait --unit=oos-wf-cost-2022-03-session-02 --property=Restart=no /usr/bin/systemd-inhibit --what=sleep:idle --mode=block --why='WF 2022-03 supervised cost study' /usr/bin/bash -c 'cd /home/ichurri/Desktop/personal_projects/btc-risk-rl && /home/ichurri/.local/bin/uv run --frozen python scripts/launch_oos_wf_cost_2022_03_once.py'
```

Auditoría posterior, solo lectura:

```bash
journalctl --user -u oos-wf-cost-2022-03-session-02.service --no-pager -o short-iso
sha256sum artifacts/oos-v12-wf-cost-only-2022-03/{ledger.jsonl,sessions.jsonl,supervisor.jsonl}
sha256sum artifacts/oos-v12-wf-cost-only-2022-03/wf-2022/checkpoint-10/{state.pt,manifest.json}
sha256sum artifacts/shared-pilot-budget/wf-2022-only-03-{attempts,checks}.jsonl
python3 -m json.tool docs/evidence/oos-wf-2022-03-relaunch-20261110/closure-summary.json >/dev/null
git diff --check
```

La suite y Ruff se ejecutaron **dentro del servicio** mediante el lanzador; el journal conserva su salida. La auditoría de cada checkpoint y reporte se realizó con `python3`, leyendo los 11 registros del ledger y calculando SHA-256 de `state.pt`, `manifest.json` y `unit-N.json` sin modificar los artefactos.
