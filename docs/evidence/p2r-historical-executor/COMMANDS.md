# P2R v2 — comandos y resultados realmente ejecutados

Fecha local: 06/10/2026, America/La_Paz. Rama
`codex/p2r-historical-executor`, base `ccb010a`. Los comandos trabajaron
con código y pruebas sintéticas; el único acceso al histórico aceptado fue
el preflight **de solo lectura**, sin generar trayectorias. No se inició
ninguna unidad P2R histórica.

## Pruebas y estilo

```bash
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen pytest -q tests/test_p2r_units.py tests/test_p2r_historical_executor.py
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen pytest
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen ruff check .
git diff --check
```

Resultados observados: pruebas dirigidas `22 passed in 67.24s`; suite
completa `279 passed in 178.89s`; Ruff `All checks passed!` y
`git diff --check` sin errores. Antes de implementar las rutas nuevas se
observaron fallos esperados por módulo/función ausente, y antes del
checkpoint atómico se observó el fallo esperado por argumento inexistente.
Esas ejecuciones rojas fueron pruebas sintéticas, no campañas.

## Preflight de solo lectura

Se ejecutó `btc_risk_rl.pilots.p2r_market.inspect_preflight()` mediante
`UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen python -`, guardando
el retorno completo y el timestamp UTC en [preflight.json](preflight.json).
También se comprobó que las 50 huellas de código que contiene coincidían
con los archivos locales al cerrar. El preflight inspeccionó metadatos de
entrenamiento H1, 7048 inicios y el scaler persistido; no llamó a
`TrainingMarket.environment` ni realizó actualizaciones.

El cargador H1 verificó SHA-256 de archivos completos que también contienen
filas de 2023. Solo materializó el prefijo de entrenamiento; por eso «cero
observaciones de validación cargadas» no significa «cero bytes de esos
archivos leídos». Véase el límite señalado en el informe.

```bash
sha256sum artifacts/p0-approved-v1/ledger.jsonl artifacts/p1-approved-v1/ledger.jsonl artifacts/p2-approved-v1/ledger.jsonl
```

Huellas observadas: P0
`1d1ee72ca0ac49529f205b30942a68f381d86037e336091c490c624098339b8c`;
P1 `926eab40bc764e1cae88a74e6718ba70b50e2df0626e8e34964078cc4ba55755`;
P2 `e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8`.

## Bloqueo de campaña

```bash
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen python scripts/run_p2r_market.py
```

Salida en [blocked-command.txt](blocked-command.txt):
`P2R market campaign NOT AUTHORIZED`, código de salida 1. Se comprobó que
`artifacts/p2r-approved-v2` no existía después. Las pruebas también
rechazaron un JSON de aprobación falsificado y una solicitud de trabajador
con ruta ajena. **Este comando no lanzó entrenamiento.**

Una campaña futura requerirá otro commit con autorización/registro
específicos y un preflight vivo nuevo; este documento no los concede.
