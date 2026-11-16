# Comandos ejecutados — WF `...04`, primera Q0 histórica

Directorio: `/home/ichurri/Desktop/personal_projects/btc-risk-rl`. Código
inicial y de la ejecución: `9a9ce9fa3b354dbf3571196c008484a57d4f5914`.
Rama local igual a origin; modificación previa ` D .python-version` excluida.

## Puertas previas

```bash
TZ=America/La_Paz date '+%Y-%m-%d %H:%M:%S %Z'
git status --short --branch
git rev-parse HEAD
git rev-parse origin/codex/oos-wf-cost-only-04-profile
test ! -e artifacts/oos-v12-wf-cost-only-04
cat /sys/class/power_supply/ADP1/online
cat /sys/class/power_supply/BAT1/capacity
awk '/MemAvailable:/{print $2*1024}' /proc/meminfo
uv run --frozen pytest -q > /tmp/oos-wf-04-20261030-pytest.log 2>&1
uv run --frozen ruff check . > /tmp/oos-wf-04-20261030-ruff.log 2>&1
uv run --frozen python -m scripts.audit_oos_wf_cost_04_preflight > /tmp/oos-wf-04-20261030-preflight.json
sha256sum /tmp/oos-wf-04-20261030-preflight.json
```

La primera consulta intentó `BAT0/capacity`, ausente en este equipo; se
enumeraron los sensores y se leyó `BAT1/capacity=97`. CA `ADP1/online=1`;
`MemAvailable=5.493.870.592 B` al inicio. Suite: **447 passed en 311,98 s**;
Ruff: `All checks passed!`. La [captura vigilada](preflight.json) dio
`ready` a las 05:48:54 UTC del 30/10, con 57 rutas abiertas, ninguna
protegida, cero trayectorias y pasos. SHA-256:
`b4af51dda7acb2dcc364623fa0bcb40165afe3542e6817eed7e816e405ebd789`.
Una comprobación en Python exigió explícitamente `ready`, raíz ausente,
recursos, presupuesto, huellas y aprobación coherentes y devolvió
`LAUNCH_GATES_READY` antes del lanzamiento.

## Única sesión

```bash
systemd-run --user --unit=oos-wf-cost-20261030-04-session-01 \
  --property=Type=exec --property=Restart=no \
  --property=WorkingDirectory=/home/ichurri/Desktop/personal_projects/btc-risk-rl \
  --property=RuntimeMaxSec=3600 \
  /home/ichurri/.local/bin/uv run --frozen python scripts/run_oos_wf_cost_04.py --run
systemctl --user show oos-wf-cost-20261030-04-session-01.service \
  -p Result -p ExecMainPID -p ExecMainStatus -p MemoryPeak \
  -p CPUUsageNSec -p ActiveState -p SubState -p InvocationID
journalctl --user -u oos-wf-cost-20261030-04-session-01.service \
  --no-pager -o short-iso-precise
```

`systemd-run` devolvió `InvocationID=9ea19b05c8584dcb8dc8cfccbcc2e032`.
La unidad terminó `Result=success`, `ExecMainStatus=0`, `inactive`.
[Journal](systemd-journal.txt) y [show](systemd-show.txt) conservados.
El journal del supervisor y la bitácora registran el mismo InvocationID.

## Auditoría de solo lectura

Se verificaron por Python las cadenas SHA-256 del ledger (`state_hash` y
`previous_hash`), bitácora de sesiones (`WFCostSessionJournal` en modo
`read_only=True`) y journal del supervisor (`P2RJournal`, solo lectura).
Se comprobó que el hash de `checkpoint-0/state.pt` coincide con manifiesto,
reporte y ledger; `torch.load(..., weights_only=True)` mostró frontera
`after_q0`, iteración 0 y cero pasos de ambos optimizadores. Se leyeron
los contadores, cargos y hashes de las tres raíces previas, cotejados con
las evidencias fijadas. El resultado está en [audit-q0.json](audit-q0.json).

**No ejecutado:** unidad 1, segundo servicio, evaluación fuera de muestra,
validación 2023 ni prueba final. No se escribió en las raíces `...01`–`...03`.
