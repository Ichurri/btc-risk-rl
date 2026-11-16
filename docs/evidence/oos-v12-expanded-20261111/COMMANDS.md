# Comprobaciones y lanzamiento del 11/11/2026

Comandos realmente ejecutados en `codex/oos-v12-expanded-budget`:

```bash
uv run --frozen pytest -q tests/test_oos_v12_training.py::test_expanded_window_stops_at_midnight_with_reserve tests/test_oos_v12_training.py::test_expanded_budget_counts_old_day_conservatively_and_new_work
# RED: 2 fallos esperados antes del cambio
uv run --frozen pytest -q tests/test_oos_v12_training.py tests/test_oos_v12_budget_audit.py
# 38 passed
uv run --frozen pytest -q
# 587 passed, 2 advertencias de fork sintético, 570,02 s
uv run --frozen ruff check .
# All checks passed!
uv run --frozen python scripts/audit_oos_v12_training_preflight.py wf-2022 > docs/evidence/oos-v12-expanded-20261111/preflight.json
# status=ready; ninguna apertura protegida; 4.678 rutas
systemctl --user enable --now oos-v12-training.timer
systemctl --user start --no-block oos-v12-training.service
# una sesión iniciada 11:28:14 America/La_Paz; InvocationID 097bd51bfa774984a3913721e364f67e
```

El preflight del archivo `preflight.json` es una medición **anterior** a la sesión. El servicio repite suite, Ruff y preflight y no puede iniciar Q0 solo con esta captura. El informe de cierre debe consultar el journal de esta invocación, el ledger, la bitácora y los checkpoints. El timer diario quedó para 12/11 01:00 y no autoriza duplicar la sesión activa.

La medición de `wf-2021` y sus 99 checkpoints en `artifacts/artifacts/oos-v12-training-wf-2021-01/` no se alteraron. La eliminación local de `.python-version` permanece fuera de los commits.
