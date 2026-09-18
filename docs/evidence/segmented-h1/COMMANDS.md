# Registro de comandos locales

Todos ejecutados en el repositorio abierto, con
`UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache`. No hubo instalación adicional ni red.
El estado inicial de Git era 108847e con eliminación previa de .python-version.

| Comando | Registro | Resultado observado |
|---|---|---|
| `uv run --frozen pytest tests/test_segmentation.py -q` | tdd-core-red.log | Fallo esperado: módulo nuevo ausente |
| mismo comando | tdd-core-green.log | 13 pasan |
| mismo comando, nuevos casos pipeline | tdd-pipeline-red.log | 5 fallan por módulos ausentes, 13 pasan |
| mismo comando, pipeline implementado | tdd-pipeline-green.log | 18 pasan, advertencias de comparación de nulos corregidas después |
| `uv run --frozen pytest tests/test_segmentation.py -q -k 'cli_exposes or one_millisecond'` | tdd-cli-exact-red.log | 2 fallan: comandos ausentes y tolerancia de 1 ms |
| `uv run --frozen ruff check` sobre archivos cambiados, con `--fix`, y `ruff format` | salida en sesión | Imports/formato; un import indirecto eliminado causó el fallo siguiente |
| `uv run --frozen pytest -q` | tests-first-full.log | 6 fallan, 46 pasan; import FEATURES corregido para apuntar a su módulo propietario |
| `uv run --frozen btc-risk prepare-segmented-development --output data/processed/segmented-B-h1` | prepare-real.log | Import falló antes de acceder a datos |
| `uv run --frozen pytest -q` | tests-second-full.log | 52 pasan |
| `uv run --frozen btc-risk prepare-segmented-development --output data/processed/segmented-B-h1` | prepare-real-retry.log | accepted, código 0 |
| `uv run --frozen pytest -q` | tests-review-cases.log | 59 pasan; incluye casos pedidos en revisión |
| `uv run --frozen btc-risk verify-segmented-development --prepared data/processed/segmented-B-h1` | audit-real.log | passed, código 0 |
| `uv run --frozen btc-risk prepare-segmented-development --output artifacts/segmented-h1/reproduction` | reproduction.log | accepted, código 0 |
| `uv run --frozen python scripts/verify_installation.py --context local` | installation-final.log y verification-local/ | configuración válida, Ruff pasa, 59 pruebas en 13.85 s; código 0 |

`verification-run.json` registra comandos finales, códigos, plataforma, versión,
commit base y huellas de código y de fuentes antes/después. La comparación de
los hashes de todos los derivados entre los dos destinos fue exacta.
La fecha `created_at_utc` del manifiesto no se exige idéntica entre ejecuciones.
Los fallos de desarrollo se conservan por transparencia, no son fallos abiertos.
