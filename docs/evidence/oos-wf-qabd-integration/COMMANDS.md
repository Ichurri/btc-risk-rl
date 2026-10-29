# Comandos ejecutados — integración WF Q/A/B+D

Directorio de trabajo: `/home/ichurri/Desktop/personal_projects/btc-risk-rl`. Rama creada desde `3ee6ebc`; la eliminación local de `.python-version` quedó sin incorporar.

```bash
git status --short --branch
git log -4 --oneline
git switch -c codex/oos-wf-qabd-integration
uv run --frozen pytest -q tests/test_wf_permit_integration.py
uv run --frozen ruff check .
uv run --frozen pytest
git diff --check
```

La primera versión ampliada aprobó 10 pruebas sin requerir cambios operativos. Después se especificaron los motivos de rechazo y se añadió el caso de PID. La primera suite completa, iniciada antes de ese último caso, dio **441 passed en 284,43 s**. Se ejecutó de nuevo sobre el archivo final: **442 passed en 285,00 s**. La prueba focal final dio **14 passed en 6,52 s** y Ruff `All checks passed!`. Logs: `pytest-full.log`, `pytest-focal.log`, `ruff.log`.

La verificación final de solo lectura calculó SHA-256 de cada archivo de las raíces `artifacts/oos-v12-wf-cost-only-01/`, `...02/` y `...03/`; comparó `...01`/`...02` con `docs/evidence/oos-v1-2-wf-first-start-fix/hashes-before.json` y `...03` con `docs/evidence/oos-v1-2-wf-cost-03-campaign/audit-failure.json`. También leyó las tres constantes `MARKET_EXECUTION_ENABLED` y el hash del registro histórico `...03`. Resultado en `verification.json`; SHA-256 `a6c7bd49f245cec632b29c4a54b2317d4a25a32e5814438d0e0a1e4651b48704`.

No hubo comandos de campaña ni unidades `systemd --user`. La prueba nueva usa solo rutas fabricadas; la suite general conserva el alcance habitual de sus otras pruebas. No se consultó validación ni conjunto final para este hito.
