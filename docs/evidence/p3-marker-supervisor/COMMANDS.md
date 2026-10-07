# Comandos y resultados — marcador P3 / supervisor

Ejecutados desde la raíz del repositorio, sobre la rama
`codex/p3-marker-supervisor`. La eliminación local ajena de
`.python-version` no se preparó para commit.

| Comando | Resultado observado |
| --- | --- |
| `UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen pytest -q tests/test_p3_marker_supervisor.py` antes de crear la función | Error de importación por función/módulo ausente; prueba roja de la función nueva |
| El mismo comando tras implementar la función | 12 passed |
| El mismo comando tras añadir la matriz y antes de la guarda | 6 failed, 12 passed; el supervisor antiguo aceptaba reportes manipulados |
| `UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen pytest -q tests/test_p3_marker_supervisor.py tests/test_p2r_units.py` | 29 passed |
| `UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen pytest -q tests/test_p3_marker_supervisor.py` tras todas las pruebas nuevas | 23 passed |
| Primera `UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen pytest` | 311 passed, 1 failed; aserción heredada de solicitud falsificada P2R esperaba solo ausencia del ledger |
| `UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen pytest -q tests/test_p2r_historical_executor.py::test_market_worker_rejects_even_forged_request_before_reading_it tests/test_p3_marker_supervisor.py` | 24 passed tras actualizar solo la aserción |
| `UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen pytest > docs/evidence/p3-marker-supervisor/pytest.log 2>&1` | **312 passed in 225.10 s**; salida completa conservada en `pytest.log` |
| `python3 docs/evidence/p3-marker-supervisor/checks.py` | Anclas originales iguales; 99 reportes P2R retenidos |
| `UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check .` | All checks passed! |

La repetición completa se guarda literalmente en [pytest.log](pytest.log).
Las [anclas y recuentos](results.json) proceden de lectura de ledgers,
journal y reportes anteriores; el script solo escribe su propio
`results.json`. No se ejecutó ningún comando de campaña histórica,
preflight de mercado, validación ni prueba final.
