# P3 — comandos y evidencia del ejecutor sin campaña

Rama de trabajo `codex/p3-historical-infrastructure`, desde
`a1d9032`. La eliminación local previa de `.python-version` no se
versionó. Todos los ensayos de unidades/optimizadores usan
`SyntheticMarket` o sobres fabricados; el único acceso al derivado H1
fue el preflight de lectura.

## Comandos ejecutados

```bash
uv run --frozen pytest -q tests/test_p3_protocol_metrics.py tests/test_p3_market_guard.py tests/test_p3_unit_algorithm.py tests/test_p3_supervisor.py tests/test_p2r_training_shard.py
uv run --frozen pytest -q tests/test_p2r_training_shard.py::test_registered_synthetic_preflight_opens_only_metadata_and_shard
uv run --frozen python scripts/audit_p3_preflight_opens.py --output docs/evidence/p3-historical-infrastructure/preflight-opens.json
uv run --frozen python docs/evidence/p3-marker-supervisor/checks.py
test ! -e docs/protocols/P3-market-approval.json && test ! -e artifacts/p3-approved-v1 && uv run --frozen python scripts/run_p3_market.py
uv run --frozen ruff check .
uv run --frozen pytest -q
git diff --check
```

El primer ensayo amplio terminó con **26 aprobados, 1 fallido**: una
prueba preexistente de vigilancia de archivos dependía de la memoria
disponible del host, que en ese instante era inferior a 4 GiB. La
primera corrección del test señaló el módulo equivocado y el ensayo
focalizado falló por `NameError`; el import se corrigió. El ensayo
focalizado final dio **1 aprobado**. El test ahora sustituye solo el
control de recursos en esa prueba de aperturas; las pruebas operativas
de recursos conservan su umbral. No se cambió el ejecutor P2R ni sus
artefactos.

El auditor registró `accepted_starts=7048`, cero aperturas intentadas de
CSV H1 compartidos, cero trayectorias y cero pasos de optimizador. Su
archivo [preflight-opens.json](preflight-opens.json) conserva las rutas
del repositorio abiertas y sus recuentos, incluidas las importaciones
Python; los productos de datos abiertos fueron únicamente el derivado
de entrenamiento y `data/processed/segmented-B-h1/manifest.json`. La
huella SHA-256 del archivo de evidencia es
`97e654ce791c0d2b516ca1d9fdb19db549fdc4758408edfddf367a05edecb70f`.
La
medición UTC `2026-10-08T03:48:24.114983+00:00` dio
`read_only_resources_blocked`: memoria disponible 3.294.134.272 bytes,
disco libre 178.840.850.432 bytes, alimentación conectada y batería
100 %. El presupuesto compartido del día local 07/10/2026 había cargado
6.893,095675 s de P2R y mostraba 3.906,904325 s restantes. Es una
lectura del momento, no una estimación de ejecución P3.

El auditor de artefactos imprimió `Original artifact anchors unchanged;
99 P2R reports retained`. El comando público devolvió código 1 con
`P3 market campaign NOT AUTHORIZED`, resultado **esperado**, y los
controles `test ! -e` confirmaron ausencia de aprobación y raíz P3.
Ruff informó `All checks passed!`; `git diff --check` pasó.

La suite completa final dio **340 aprobados, 1 omitido en 267,38 s**. La
omisión corresponde a la ventana de medianoche real de La Paz en
`tests/test_p2.py:467`, que no deja admisión Q0 aprobada. Ruff terminó
sin observaciones y `git diff --check` pasó. Ningún ejemplo sintético
es validación de rendimiento de un agente sobre mercado. No se abrió
validación 2023 ni prueba final.
