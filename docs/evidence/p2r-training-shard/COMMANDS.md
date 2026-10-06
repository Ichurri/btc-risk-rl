# Comandos y resultados — aislamiento P2R y señal sintética

Fecha: 06/10/2026 UTC. Todos los comandos se ejecutaron en
`codex/p2r-historical-executor`. No se activó el permiso histórico ni se
generaron trayectorias de mercado. El cache de uv se ubicó en `/tmp`.

## Prueba de aperturas y regresión

```bash
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen pytest -q tests/test_p2r_training_shard.py
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen pytest -s -q tests/test_p2r_training_shard.py::test_preflight_requires_registered_training_shard_without_opening_h1_tables tests/test_p2r_training_shard.py::test_registered_synthetic_preflight_opens_only_metadata_and_shard > docs/evidence/p2r-training-shard/access-trace.txt
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen pytest -q tests/test_p2r_training_shard.py tests/test_p2r_historical_executor.py tests/test_p2r_units.py
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen ruff check .
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen pytest
```

Se observaron primero **dos fallos esperados**: preflight antiguo abría
`data/processed/segmented-B-h1/bars.csv` y `TrainingMarket` todavía no
admitía un derivado. Tras implementar la barrera, cinco pruebas nuevas
del derivado pasaron; la traza verificable registró cero aperturas de
archivos H1 de datos reales en el preflight bloqueado. El preflight
sintético abrió solo el manifiesto padre y los ocho archivos del derivado
(incluido su manifiesto); el test lanza un error si se intenta abrir un
CSV compartido. La regresión dirigida cerró en **28 passed in 77.42s** y
Ruff informó `All checks passed!`.

## Sondas de señal

```bash
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen python scripts/probe_p2r_optimizer_signal.py --output artifacts/p2r-synthetic-optimizer-signal-07 --summary docs/evidence/p2r-optimizer-signal-07/results.json
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen python scripts/probe_p2r_optimizer_signal.py --output artifacts/p2r-synthetic-optimizer-signal-08 --summary docs/evidence/p2r-optimizer-signal-08/results.json
sha256sum -c docs/evidence/p2r-optimizer-signal-08/SHA256SUMS.txt
```

La 07 devolvió error de aserción del **controlador**: su envoltorio salió
0 aun cuando ledger y supervisor marcaron `failed`. Se conservó la raíz
07 y se versionó su [diagnóstico](../p2r-optimizer-signal-07/diagnostic.json).
Tras corregir solo ese envoltorio, la 08 devolvió
`{"status":"failed","accepted_units":1,...}` con código 0 del
controlador y código 1 del supervisor interrumpido. El ledger registró
`interrupted_supervisor_or_unit`; la huella previa y posterior de Q0 fue
idéntica. Las ocho verificaciones de `SHA256SUMS.txt` respondieron `OK`.

Se releyeron sin modificar los ledgers P0/P1/P2 y sus SHA-256 siguieron:
`1d1ee72ca0ac49529f205b30942a68f381d86037e336091c490c624098339b8c`,
`926eab40bc764e1cae88a74e6718ba70b50e2df0626e8e34964078cc4ba55755`
y `e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8`.
La verificación del manifiesto de la sonda 06 anterior respondió `OK`.

La suite completa cerró en **284 passed in 193.77s**. `git diff --check`
no informó errores. Estas cifras pertenecen a esta ejecución, no a P0,
P1, P2 ni a las sondas anteriores.
