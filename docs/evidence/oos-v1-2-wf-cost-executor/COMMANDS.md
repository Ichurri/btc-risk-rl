# Comandos y resultados — infraestructura aislada WF costo

## Estudio autorizado del 26/10/2026, detenido tras Q0

El permiso específico quedó en
[`OOS-v1-2-wf-cost-approval.json`](../../protocols/OOS-v1-2-wf-cost-approval.json)
con SHA-256
`b36e32521f43af3f0b7b363f2555d1bee19fa5200c3cee30b5e8987068984369`.
La pausa obligatoria después de la primera Q0 se probó primero con una
prueba fallida por ausencia de la función y luego con 17/17 pruebas focales.
Tras registrar el permiso, las pruebas focales pasaron 18/18. Antes de
lanzar, la suite completa dio **378/378 en 261,37 s** y Ruff pasó.

Comandos de preflight y captura ejecutados (las salidas fueron `ready`, sin
bloqueos):

```bash
uv run --frozen python scripts/audit_oos_wf_cost_preflight.py \
  > /tmp/oos-wf-cost-preflight-approved-20261026.json
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-executor/checks_approved.py
uv run --frozen pytest -q tests/test_oos_wf_cost_executor.py
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen python scripts/audit_oos_wf_cost_preflight.py \
  > /tmp/oos-wf-cost-preflight-launch-20261026.json
sha256sum /tmp/oos-wf-cost-preflight-launch-20261026.json
```

SHA-256 del preflight aprobado: `ca4ec844028da895d3ea695dac20427b2c423d9081abf88951d3a82ca9fbf458`.
SHA-256 de la captura inmediatamente anterior al lanzamiento:
`1d05822bc8b125d7e4a0f57f11f8d2928ef14d92343f6c1a2018238222012291`.
Ambas registraron gestor `running`, CA, batería ≥50 %, memoria/disco sobre
los mínimos, huellas de entrada íntegras, presupuesto sin otra campaña y
raíz aún ausente. No abrieron CSV H1 compartidos.

Único lanzamiento de la primera sesión:

```bash
systemd-run --user --unit=oos-wf-cost-20261026-session-01 \
  --property=Type=exec --property=Restart=no \
  --property=WorkingDirectory=/home/ichurri/Desktop/personal_projects/btc-risk-rl \
  --property=RuntimeMaxSec=3600 \
  /home/ichurri/.local/bin/uv run --frozen python scripts/run_oos_wf_cost.py --run
```

La sesión `5c405d0855a14923bd4c9481fa73130e` cerró `Result=success` tras
Q0 y una pausa `first_q0_audit`, con ledger `ready`, una unidad aceptada y
sin `pending`. Se verificaron en solo lectura cadena de ledger y journal,
reporte, checkpoint, contadores, optimizadores y ausencia de unidad 1; el
resultado quedó en [`q0-audit.json`](q0-audit.json). El SHA-256 del ledger
en esa frontera fue
`b6bc9a30d25387813d664708edfa07347c21174d2df216fc6f6be2d844ec6af6`.

Tras la auditoría se repitió el preflight, también `ready`, con salida
[`preflight-after-q0-20261026.json`](preflight-after-q0-20261026.json)
(SHA-256 `25983e48c21b00e90004a5ffcc1101ce4ee73fae74823b6f8ebd2678d7d40a7c`).
Se lanzó **una sola** segunda sesión desde la frontera completa:

```bash
uv run --frozen python scripts/audit_oos_wf_cost_preflight.py \
  > /tmp/oos-wf-cost-preflight-after-q0-20261026.json
systemd-run --user --unit=oos-wf-cost-20261026-session-02 \
  --property=Type=exec --property=Restart=no \
  --property=WorkingDirectory=/home/ichurri/Desktop/personal_projects/btc-risk-rl \
  --property=RuntimeMaxSec=3600 \
  /home/ichurri/.local/bin/uv run --frozen python scripts/run_oos_wf_cost.py --run
journalctl --user -u oos-wf-cost-20261026-session-02.service \
  --output=short-iso-precise --no-pager
```

La segunda sesión, `InvocationID=6513bcb4dbf34444a38d8acc712cdafb`,
terminó `Result=exit-code`, código 1, por `Campaign identity mismatch`
**antes de iniciar unidad 1**. La reconstrucción de solo lectura mostró que
únicamente `identity.roster` difería en tipo `tuple`/`list`; normalizada a
JSON, toda la identidad coincidía. Ese resultado quedó en
[`session-02-identity-diff.json`](session-02-identity-diff.json).
Tras cerrar prospectivamente el permiso, se ejecutaron:

```bash
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-executor/audit_after_failure.py \
  > docs/evidence/oos-v1-2-wf-cost-executor/audit-after-failure.json
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-executor/audit_identity_mismatch.py \
  > docs/evidence/oos-v1-2-wf-cost-executor/identity-recheck-after-closure.json
uv run --frozen python scripts/run_oos_wf_cost.py --run
uv run --frozen python -m btc_risk_rl.pilots.wf_cost_worker \
  /nonexistent/forged-request.json
uv run --frozen pytest -q tests/test_oos_wf_cost_executor.py
uv run --frozen ruff check .
sha256sum artifacts/oos-v12-wf-cost-only-01/ledger.jsonl \
  artifacts/oos-v12-wf-cost-only-01/wf-2021/checkpoint-0/state.pt
```

Ambos comandos operativos devolvieron código 1 con `NOT AUTHORIZED` antes de
leer una solicitud o iniciar otra unidad; las pruebas focales pasaron 18/18,
Ruff pasó y los hashes de ledger/checkpoint siguieron iguales. La auditoría
después del cierre usa los bytes del código de autorización fijados en Git
para reconstruir su identidad histórica: el flag prospectivamente cerrado
no se confunde con el código que produjo Q0. La suite completa posterior
al cierre pasó **378/378 en 259,54 s** con el permiso desactivado.

---

## Preflight posterior a `swaync` (evidencia nueva)

El archivo `/tmp/oos-wf-cost-preflight-after-swaync.json` ya existía al
iniciar esta revisión. Se incorporó byte por byte como
`preflight-after-swaync.json`; no se volvió a ejecutar el preflight ni se
sobrescribió `preflight.json`. Comandos ejecutados:

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/codex/oos-wf-cost-executor
sha256sum /tmp/oos-wf-cost-preflight-after-swaync.json \
  docs/evidence/oos-v1-2-wf-cost-executor/preflight.json
systemctl --user is-system-running
systemctl --user is-enabled swaync.service
systemctl --user --failed --no-pager
loginctl show-user "$USER" -p Linger -p State
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-executor/checks.py
cp /tmp/oos-wf-cost-preflight-after-swaync.json \
  docs/evidence/oos-v1-2-wf-cost-executor/preflight-after-swaync.json
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-executor/checks_after_swaync.py
uv run --frozen ruff check docs/evidence/oos-v1-2-wf-cost-executor/checks_after_swaync.py
sha256sum docs/evidence/oos-v1-2-wf-cost-executor/preflight-after-swaync.json
git diff --check
```

Antes de la incorporación, HEAD y origin coincidían en `813c647` y solo
figuraba la eliminación local previa de `.python-version`. SHA-256 de la
nueva evidencia: `875f56ba04d5f4f3146aebe62edce337ca7d15c57f032b9ba55a2dd645a870f5`;
la anterior conservó `79e9b0a0b3d7633b62b51e5d2895be573fd4b6f1df24503b295fe992cfa176eb`.
`systemctl --user is-system-running` devolvió `running` (0);
`is-enabled swaync.service` devolvió `masked` (1, salida esperada para una
unidad enmascarada), y `--failed` mostró cero unidades. `Linger=yes`.
El nuevo JSON reporta `blocked` únicamente por falta de aprobación, permiso
inactivo, raíz ausente, cero trayectorias y pasos, y ninguna apertura de CSV
H1 compartidos. La comprobación estática de ambos JSON y las huellas de
código, entradas y ledgers devolvió `passed_read_only`; Ruff y
`git diff --check` pasaron. No se repitió la suite de entrenamiento ni se
inició una unidad.

---

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
