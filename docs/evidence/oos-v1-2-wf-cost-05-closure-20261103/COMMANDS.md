# WF05: comandos reales de conciliación y cierre

Ejecutados desde `/home/ichurri/Desktop/personal_projects/btc-risk-rl`
el 03/11/2026 (`America/La_Paz`). La eliminación local de
`.python-version` quedó fuera de los commits. No se inició `systemd-run`,
ningún trabajador histórico ni otra unidad.

## Lectura previa

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse origin/codex/oos-wf05-profile
date '+%Y-%m-%dT%H:%M:%S%:z %Z'
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-05-session-02-20261101/audit.py > /tmp/wf05-closure-before.json
cmp /tmp/wf05-closure-before.json docs/evidence/oos-v1-2-wf-cost-05-session-02-20261101/audit.json
sha256sum /tmp/wf05-closure-before.json
```

El `cmp` pasó: SHA-256 del JSON previo
`9b5426f58d065feae02ea8e00c05e77dd3665ff6773ef8d908dfcc5d76b9275a`.
El ledger siguió `ready`, 11/22, `pending=null`.

## Cierre de gate y pruebas

Se cambió solo el gate del perfil 05 a `False`; no se editó su aprobación.
Se ajustaron y ampliaron las pruebas de rechazo. Se ejecutaron:

```bash
uv run --frozen pytest -q tests/test_oos_wf_cost_05_profile.py tests/test_wf_permit_integration.py > /tmp/wf05-close-focused.log 2>&1
uv run --frozen pytest -q > /tmp/wf05-close-full.log 2>&1
uv run --frozen ruff check . > /tmp/wf05-close-ruff.log 2>&1
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-05-closure-20261103/reconcile.py > /tmp/wf05-closure-reconciliation.json
```

Salidas: **24 passed in 22.46s**, **464 passed in 328.61s** y
`All checks passed!`. La conciliación de solo lectura pasó y produjo
`results.json`, SHA-256
`6c917610e10375a639ed67be3ae41d23beb80d1f34d5b064cad590f0165b0d0d`.
Las salidas están copiadas en esta carpeta. El script fija sus fuentes,
reproduce la aritmética y coteja los once checkpoints y todas las huellas
de la raíz con la auditoría anterior.

Después del commit de cierre del gate, se ejecutó directamente:

```bash
uv run --frozen python scripts/run_oos_wf_cost_05.py --run > /tmp/wf05-close-public.log 2>&1
uv run --frozen python -m btc_risk_rl.pilots.wf_cost_replacement_05_worker /tmp/wf05-forged-request-does-not-exist.json > /tmp/wf05-close-worker.log 2>&1
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-05-closure-20261103/reconcile.py > /tmp/wf05-closure-reconciliation-after.json
cmp /tmp/wf05-closure-reconciliation-after.json docs/evidence/oos-v1-2-wf-cost-05-closure-20261103/results.json
systemctl --user list-units 'oos-wf-cost*' --state=running --no-legend --no-pager
```

Ambas entradas devolvieron **código 1** y `NOT AUTHORIZED`. El segundo
`cmp` pasó; no apareció unidad WF activa ni cambió archivo de la raíz.
Se conservaron `public-rejection.log` y `worker-rejection.log`.

La aritmética de fechas usa estas fuentes: `sessions.jsonl` y
`ledger.jsonl` originales; los cuatro logs versionados de pytest del
01–02/11; los tres preflights del 01/11 y el del 02/11; commits
`cacf6a9`, `4e2ab6a` y `2f25d6a`. La primera hora observada del 02/11,
17:22:39 local, está en la salida de herramienta de esa conversación,
con resolución de un segundo; no se presenta como duración individual
de ningún proceso.
