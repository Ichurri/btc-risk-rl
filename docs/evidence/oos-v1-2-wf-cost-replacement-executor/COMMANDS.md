# Comandos de verificación del ejecutor WF `...02`

Base: `37cc06e58b3c9d3d92f4b1c38cb438d7bae52e95`.
Rama: `codex/oos-wf-cost-replacement-executor`.
Commit de código probado: `baf382a`.
Todas las pruebas de Q0/reingreso usan raíces temporales sintéticas. Ningún
comando lanzó unidades históricas ni creó `artifacts/oos-v12-wf-cost-only-02/`.

| Comando ejecutado | Resultado |
| --- | --- |
| `uv run --frozen pytest tests/test_oos_wf_cost_replacement_executor.py -q` | 9 passed; incluye Q0→pausa→otro proceso→admisión 1, rechazo de roster y fallos previos al ledger |
| `uv run --frozen pytest tests/test_oos_wf_cost_executor.py tests/test_oos_wf_cost_replacement_proposal.py tests/test_oos_wf_cost_replacement_executor.py tests/test_oos_wf_session_journal.py -q` | Ver [`pytest-focused.txt`](pytest-focused.txt) |
| `uv run --frozen pytest -q` | Ver [`pytest-full.txt`](pytest-full.txt): 414 passed, 1 skipped (ventana real de medianoche La Paz), 259,05 s |
| `uv run --frozen ruff check .` | Ver [`ruff.txt`](ruff.txt) |
| `uv run --frozen python -m scripts.audit_oos_wf_cost_replacement_preflight > docs/evidence/oos-v1-2-wf-cost-replacement-executor/preflight.json` | `blocked` solo por permiso ausente; 30 archivos observados; ningún CSV compartido/validación/final abierto; 0 trayectorias/pasos |
| `uv run --frozen python docs/evidence/oos-v1-2-wf-cost-reentry/check_frozen_artifacts.py > docs/evidence/oos-v1-2-wf-cost-replacement-executor/frozen-artifacts-check.json` | `frozen_historical_study_verified`, ledger `ready`, una Q0, 5 huellas iguales |
| `git diff --check` | Sin errores |

SHA-256 de [`preflight.json`](preflight.json):
`b7a182b3703f9e6973fba2be92cfa4f1ff12f811bce2352e05e21a52d9be6ba6`.
SHA-256 de [`frozen-artifacts-check.json`](frozen-artifacts-check.json):
`6747b9865bb2a76f0beea1d45d1917ae306d146fb6f38d569c794132faa00b27`.

El preflight leyó ocho productos del derivado
`data/processed/p2r-training-h1/` (incluido su manifiesto), documentos de
protocolo/configuración y las cinco piezas congeladas del estudio `...01`.
`fold_metadata` registra 3.639/4.678 episodios y 5.764/7.703 filas de ajuste
en 2021/2022. La salida conserva la lista exacta de rutas y huellas.

La eliminación local de `.python-version` quedó fuera de los commits.
