# Comandos ejecutados: WF `...02`, primera sesión fallida

Rama: `codex/oos-wf-cost-replacement-campaign`. Base: `59e7ae4`.
Autorización independiente: `743e51b`; cierre prospectivo: `279e6ab`.
La eliminación local de `.python-version` quedó fuera de todos los commits.

## Antes del servicio

```bash
uv run --frozen pytest tests/test_oos_wf_cost_replacement_executor.py -q
uv run --frozen pytest tests/test_oos_wf_cost_replacement_proposal.py -q
uv run --frozen pytest -q > /tmp/oos-wf-cost-02-pytest-verified.txt
uv run --frozen ruff check . > /tmp/oos-wf-cost-02-ruff-authorization.txt
systemctl --user is-system-running
loginctl show-user "$(id -u)" -p Linger --value
systemctl --user list-units --type=service --state=running --no-legend
uv run --frozen python -m scripts.audit_oos_wf_cost_replacement_preflight \
  > /tmp/oos-wf-cost-02-preflight-launch.json
sha256sum /tmp/oos-wf-cost-02-preflight-launch.json
```

La primera suite completa detectó una aserción obsoleta que esperaba la
ausencia del registro recién aprobado: **414 passed, 1 failed, 1 skipped**.
Se corrigió esa prueba; su prueba focal pasó **5/5** y la segunda suite
completa pasó **415/415**, con una omisión por la ventana de medianoche.
Ruff pasó. Las salidas finales se conservan en [`pytest-before-launch.txt`](pytest-before-launch.txt)
y [`ruff-before-launch.txt`](ruff-before-launch.txt). El preflight nuevo fue
`ready` sin bloqueos; su salida está en [`preflight-launch.json`](preflight-launch.json)
con SHA-256 `fdda73ba046a2fb247f6c26ffa5427b51e4bb9b77026acb8eed64c39186a9c9c`.

## Único lanzamiento

```bash
systemd-run --user --unit=oos-wf-cost-20261027-replacement-session-01 \
  --property=Type=exec --property=Restart=no \
  --property=WorkingDirectory=/home/ichurri/Desktop/personal_projects/btc-risk-rl \
  --property=RuntimeMaxSec=3600 \
  /home/ichurri/.local/bin/uv run --frozen python \
  scripts/run_oos_wf_cost_replacement.py --run
```

Resultado de `systemd-run`: unidad
`oos-wf-cost-20261027-replacement-session-01.service`,
`InvocationID=3bb524765d3c4b669fcad7f2ee4b18f4`.

## Auditoría y cierre

```bash
systemctl --user show oos-wf-cost-20261027-replacement-session-01.service \
  -p ActiveState -p SubState -p Result -p InvocationID \
  -p ExecMainStatus -p MemoryPeak -p CPUUsageNSec \
  -p ExecMainStartTimestamp -p ExecMainExitTimestamp
journalctl --user -u oos-wf-cost-20261027-replacement-session-01.service \
  --output=short-iso-precise --no-pager
find artifacts/oos-v12-wf-cost-only-02 -maxdepth 3 -type f
uv run --frozen python \
  docs/evidence/oos-v1-2-wf-cost-replacement-campaign/audit_failure.py \
  > docs/evidence/oos-v1-2-wf-cost-replacement-campaign/audit-failure.json
uv run --frozen python \
  docs/evidence/oos-v1-2-wf-cost-reentry/check_frozen_artifacts.py \
  > docs/evidence/oos-v1-2-wf-cost-replacement-campaign/original-campaign-frozen.json
uv run --frozen pytest tests/test_oos_wf_cost_replacement_executor.py \
  tests/test_oos_wf_cost_replacement_proposal.py -q \
  > docs/evidence/oos-v1-2-wf-cost-replacement-campaign/pytest-after-failure.txt
uv run --frozen ruff check . \
  > docs/evidence/oos-v1-2-wf-cost-replacement-campaign/ruff-after-failure.txt
uv run --frozen pytest -q \
  > docs/evidence/oos-v1-2-wf-cost-replacement-campaign/pytest-after-failure-full.txt
uv run --frozen python scripts/run_oos_wf_cost_replacement.py --run
uv run --frozen python -m btc_risk_rl.pilots.wf_cost_replacement_worker \
  /tmp/wf-nonexistent-request.json
systemctl --user is-system-running
```

`Result=exit-code`, `ExecMainStatus=1`; bitácora `end failed`,
`ledger_exists=false`, `units_started=0`, `checkpoints_accepted=0`.
Tras el cierre del gate, las pruebas focales pasaron **15/15** y Ruff pasó.
La suite completa posterior pasó **415/415**, con una omisión por la ventana
real de medianoche de La Paz.
Los comandos público y trabajador salieron con estado 1 y `NOT AUTHORIZED` antes de
abrir la solicitud inexistente o crear unidades.
La comprobación final del gestor devolvió `degraded` por la unidad fallida;
se conserva sin `reset-failed`.
Se preservaron el [journal de systemd](session-01-journal.txt), el
[estado del servicio](session-01-systemd.txt), la [bitácora](session-01-events.jsonl)
y la [auditoría](audit-failure.json). **No se lanzó otra sesión.**
El [cotejo original](original-campaign-frozen.json) mantuvo las cinco huellas
de `...01`.
