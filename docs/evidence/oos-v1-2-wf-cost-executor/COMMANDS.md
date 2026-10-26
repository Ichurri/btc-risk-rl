# Comandos y resultados — infraestructura aislada WF costo

Rama `codex/oos-wf-cost-executor`. Código verificado en `e0f843c`.
La evidencia corresponde al 26/10/2026, America/La_Paz; el preflight
registró `2026-10-26T17:39:26.920499+00:00`.

## Verificación del código, sin unidades de entrenamiento

```bash
uv run --frozen pytest -q tests/test_oos_wf_cost_executor.py
uv run --frozen pytest -q
uv run --frozen ruff check .
git diff --check
```

Las pruebas focales terminaron **16/16**; la suite final, sobre código ya
fijo, terminó **376/376 en 299,18 s**; Ruff y `git diff --check` pasaron.
Hubo dos pasadas de suite anteriores con una falla de procedencia en pruebas
P2R/P3 mientras los archivos fuente se editaban simultáneamente; la prueba
afectada pasó al repetirla sobre código estable y la suite final pasó
completa. Esas pasadas no se usaron como verificación final.

## Preflight y aperturas

```bash
uv run --frozen python scripts/audit_oos_wf_cost_preflight.py \
  > /tmp/oos-wf-cost-preflight-final.json
cp /tmp/oos-wf-cost-preflight-final.json \
  docs/evidence/oos-v1-2-wf-cost-executor/preflight.json
sha256sum docs/evidence/oos-v1-2-wf-cost-executor/preflight.json
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-executor/checks.py
systemctl --user --failed --no-pager --plain
```

La salida de `checks.py` fue `passed_read_only`; el JSON tiene SHA-256
`79e9b0a0b3d7633b62b51e5d2895be573fd4b6f1df24503b295fe992cfa176eb`.
El preflight abrió 29 archivos locales registrados, entre ellos el derivado
H1 exclusivo de entrenamiento y los ledgers previos; **ningún CSV H1
compartido, archivo de validación ni final**. La reconstrucción en memoria
dio inicios/filas de ajuste 2021 `3639/5764` y 2022 `4678/7703`.

Estado medido: CA conectada, batería 95 %, memoria disponible
`7.938.338.816` B, disco libre `152.870.371.328` B, `Linger=yes`, gasto
global registrado hoy `0` s. `systemd --user is-system-running` devolvió
`degraded`; `systemctl --user --failed` mostró `swaync.service` fallida.
El permiso específico permanece inactivo. La raíz reservada no existe.
Estas condiciones del equipo son una foto de ese momento.

## Rechazos observados

```bash
uv run --frozen python scripts/run_oos_wf_cost.py --run
uv run --frozen python -m btc_risk_rl.pilots.wf_cost_worker \
  /nonexistent/forged-request.json
```

Ambos comandos devolvieron código **1** con `WF cost market study NOT
AUTHORIZED`. El trabajador rechazó antes de abrir la ruta inexistente; no
se creó la raíz ni se recolectaron trayectorias.

## Conservación de campañas anteriores

```bash
sha256sum artifacts/p0-approved-v1/ledger.jsonl \
  artifacts/p1-approved-v1/ledger.jsonl \
  artifacts/p2-approved-v1/ledger.jsonl \
  artifacts/p2r-approved-v2/ledger.jsonl \
  artifacts/p3-approved-v1/ledger.jsonl \
  data/processed/p2r-training-h1/manifest.json
uv run --frozen python docs/evidence/p3-permit-closure/audit_artifact_tree.py
```

Los seis SHA-256 coinciden con el cierre anterior: P0
`1d1ee72ca0ac49529f205b30942a68f381d86037e336091c490c624098339b8c`,
P1 `926eab40bc764e1cae88a74e6718ba70b50e2df0626e8e34964078cc4ba55755`,
P2 `e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8`,
P2R `fe443e5e32d26a7de075fa6e34771c8f20651bbe566f9097bfdb367d17d0b866`,
P3 `86b111b5365cda1760441d2f73d42e0463a4b4b2a7ddbc6e0e41f2a78751fcfe`
y derivado H1
`62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9`.
La auditoría de P3 recorrió 47.487 archivos, 5.326.594.447 B, y dio
`73949350733bf3f8e3939e2dfcf7a28920668e738b0e5d910bd070a010fdcbec`,
igual a la huella ya publicada. No se modificaron artefactos de campañas.
