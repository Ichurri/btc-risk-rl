# P3 histórico — autorización, preflight y primera sesión

Código base revisado: `51280c0`; rama `codex/p3-market-campaign`.
Permiso P3 separado: commit `618a08f`, registro SHA-256
`66675a4931ae8aea2175c20c1c38f2cba2d5db0512ecc84da61ef6dfeba54597`.
La eliminación local anterior de `.python-version` no se incluyó.

Comandos ejecutados antes de lanzar:

```bash
uv run --frozen pytest -q
uv run --frozen ruff check .
git diff --check
uv run --frozen python -
loginctl show-user ichurri -p Linger -p State -p Sessions
systemctl --user is-system-running
systemctl --user show -p ActiveState -p SubState default.target
systemctl --user list-units --all --type=service 'p3-*' --no-legend --no-pager
cat /sys/class/power_supply/ADP1/online
cat /sys/class/power_supply/BAT1/capacity
```

El último comando Python recibió por heredoc el programa conservado en
[preflight-stdin.py](preflight-stdin.py); solo se normalizó el orden de
sus imports al versionarlo para Ruff. La
redirección `< docs/evidence/p3-market-2026-10-08/preflight-stdin.py`
reproduce ese stdin con una **salida nueva** tras cambiar la ruta de
destino; no se volvió a ejecutar desde el archivo ni se sobrescribió
`preflight.json`.
La suite **antes de activar el permiso** dio 341 aprobadas en 235,94 s;
Ruff pasó. Después de fijar el registro, la comprobación directa de
`P3MarketPermit.require_campaign()` validó su SHA-256, raíz y 18
identidades; Ruff volvió a pasar. No se repitió la suite después del
cambio exclusivo de bandera/huella. El preflight aprobado produjo
`preflight.json`, con huellas, presupuesto, recursos y **cada ruta del
repositorio abierta**. La vigilancia rechazaba los CSV H1 compartidos;
hubo cero intentos, cero trayectorias y cero optimizaciones. Registro de
salida: `read_only_ready_campaign_enabled` a las 15:53:36 UTC.

Lanzamiento ejecutado **solo después** de todas esas guardas:

```bash
systemd-run --user --unit=p3-market-v1-session-01.service --service-type=exec \
  --description='P3 v1.1 approved historical development diagnostic' \
  --working-directory=/home/ichurri/Desktop/personal_projects/btc-risk-rl \
  --setenv=PYTHONUNBUFFERED=1 \
  /home/ichurri/Desktop/personal_projects/btc-risk-rl/.venv/bin/python \
  /home/ichurri/Desktop/personal_projects/btc-risk-rl/scripts/run_p3_market.py
systemctl --user show p3-market-v1-session-01.service \
  -p InvocationID -p MainPID -p ActiveState -p SubState -p Result -p ExecMainStatus
journalctl --user -u p3-market-v1-session-01.service -o short-iso-precise --no-pager
```

`systemd-run` devolvió `InvocationID=8b3d6b175bd34b78a655010d46cccf3d`.
La instantánea [first-units.json](first-units.json) conserva tiempos,
recursos, marcadores y huellas de Q0 y la primera iteración aceptadas.
Los ledgers, journals, logs y checkpoints completos están en la raíz
local `artifacts/p3-approved-v1`, fuera de Git. La sesión seguía activa
al redactar esta evidencia; `Result=success` mientras está `running`
no es un resultado final de systemd.
