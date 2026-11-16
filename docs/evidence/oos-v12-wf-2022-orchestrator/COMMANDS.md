# Comandos y resultados del orquestador WF 2022

Rama `codex/oos-wf-2022-orchestrator`; base `cb6aeb8`. Se conservaron
`.python-version` eliminado localmente y las raíces WF históricas. Los
comandos de prueba usan `tmp_path`, sin permiso ni unidades de mercado.

```bash
git status --short --branch
git log -5 --oneline --decorate
uv run --frozen pytest -q tests/test_oos_wf_2022_orchestrator.py
uv run --frozen ruff check .
uv run --frozen pytest -q
python3 docs/evidence/oos-v12-wf-2022-cost-proposal/checks.py | sha256sum
test ! -e artifacts/oos-v12-wf-cost-only-2022-01 && \
  test ! -e docs/protocols/OOS-v1-2-wf-cost-2022-only-approval.json && \
  test ! -e artifacts/shared-pilot-budget/wf-2022-only-01-attempts.jsonl
grep -n '^MARKET_EXECUTION_ENABLED' \
  src/btc_risk_rl/pilots/wf_cost_replacement_05_exec.py \
  src/btc_risk_rl/pilots/wf_cost_2022_orchestrator.py
uv run --frozen python scripts/run_oos_wf_cost_2022.py --run
command -v strace
git diff --check
sha256sum src/btc_risk_rl/pilots/wf_cost_2022_orchestrator.py \
  tests/test_oos_wf_2022_orchestrator.py \
  scripts/run_oos_wf_cost_2022.py
```

Resultados observados con el código final:

- Prueba focal: **17 passed in 0.50s**. Antes de implementar, la prueba
  falló por módulo/atributos ausentes; las pruebas añadidas después
  detectaron las faltas de bitácora individual, admisión y cota posterior.
- Suite completa: **481 passed in 346.55s (0:05:46)**, código de salida 0.
- Ruff: `All checks passed!`, código de salida 0.
- `checks.py`: código de salida 0; SHA-256 de su JSON generado
  `5cb0298b58b00dc0b30401bc3c18f5bf60bb3ed159ba406508fc34a2d50cbd80`.
  Este script recalcula el mapa de 2.647 archivos WF05 y coteja su ledger,
  raíz, huellas y aprobación ausente de la nueva campaña. Es una auditoría
  **de solo lectura**; la salida coincide con la evidencia del protocolo.
- `test ! -e ...`: código de salida 0. Ni raíz, ni aprobación, ni bitácora
  de ejecución 2022 fueron creadas.
- Ambos archivos de perfil imprimieron `MARKET_EXECUTION_ENABLED = False`.
  La CLI nueva devolvió **código 1** con
  `WF 2022 market cost study NOT AUTHORIZED` antes de leer solicitudes.
- `command -v strace`: código 1; la vigilancia de aperturas queda pendiente
  para el futuro ejecutor histórico. `git diff --check`: código 0.
- El código de orquestador quedó en `422db7a`; SHA-256 del módulo
  `51ad1093f835712ef45cbb4a07d2b9b6efac6b69135f3bbfae4015f98f558f11`,
  de la prueba
  `20b9f392ae0611de0373e11f3d58df3e5084ad18dfb3f405f2d93a6326aa0634`
  y del comando público
  `16ca8878ce706a8ce468412abe5ef15cb74b1239cfad7b3b26fa3eca26933db3`.

La suite de **346.55 s** se ejecutó durante la implementación, fuera de
cualquier bitácora/campaña 2022 autorizada. Su duración es una observación
de pruebas de este hito, **no** un débito ni una estimación validada para
la futura campaña. No hubo optimización histórica, acceso deliberado a
validación 2023, prueba final o activación de v1.2.
