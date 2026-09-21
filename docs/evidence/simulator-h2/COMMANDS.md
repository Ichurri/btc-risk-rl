# Comandos y evidencia H2 — ejecución local

Base: 57e0885; se conservó fuera del commit la eliminación local de .python-version.
Entorno: Debian 13, Python 3.12.13, dependencias existentes de uv.lock.
Comandos uv con `UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache` para la caché escribible.
No se instalaron dependencias, no hubo descargas de mercado ni entrenamientos.

| Comando | Registro | Resultado |
|---|---|---|
| `uv run --frozen pytest tests/test_simulator.py -q` | accounting-red.log | módulo aún ausente (TDD) |
| mismo comando | accounting-green.log | 20 aprobadas |
| mismo comando con pruebas de entorno nuevas | environment-red.log | 12 fallan por módulo ausente, 20 aprobadas |
| mismo comando con entorno implementado | environment-green.log | 32 aprobadas; dos advertencias por Box infinito, posteriormente capturadas explícitamente |
| mismo comando con pruebas de loader nuevas | loader-red.log | 3 fallan por loader ausente, 33 aprobadas |
| mismo comando con loader implementado | loader-green.log | 36 aprobadas |
| `uv run --frozen pytest tests/test_simulator.py -q -k rollout_auditor` | auditor-red.log | script aún ausente |
| mismo comando con auditor implementado | auditor-green.log | 1 aprobada, 36 omitidas por filtro |
| `uv run --frozen ruff check src/btc_risk_rl/env scripts/verify_simulator.py tests/test_simulator.py --fix` y `ruff format` sobre esos archivos | salida en sesión | comprobación y formato correctos |
| `uv run --frozen python scripts/verify_installation.py --context local` | installation.log y verification-local/ | configuración válida, Ruff pasa, 100 aprobadas en 26.68 s; códigos 0 |
| `uv run --frozen python scripts/verify_simulator.py --context local --output artifacts/simulator-h2/real` | real-run.log y simulation-summary.json | passed; 7048 índices, 31 recorridos, 7590 pasos, códigos 0 |

`simulation-summary.json` contiene versiones, comando exacto, commit base,
estado Git, huellas de código y de entradas antes/después, resultados por recorrido
y hash del libro completo `artifacts/simulator-h2/real/ledger.csv`.
`independent-cases.json` presenta cuatro casos calculados por bisección Decimal
sobre flujos de caja. Los precios de esos casos y de las pruebas son sintéticos.

La revisión independiente de código no encontró defectos materiales abiertos.
Ejecutó por separado 36 pruebas en 9.08 s antes de agregar los últimos casos.
Sus recomendaciones (venta parcial con costos separados, aislamiento de carteras
y corte al fin de segmento) se incorporaron a las 100 pruebas finales.
Los logs de TDD con fallos se conservan íntegros; no son fallos abiertos.
