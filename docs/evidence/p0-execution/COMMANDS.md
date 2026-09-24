# P0 aprobado — comandos realmente ejecutados

Base 7a379b7; autorización e0e3495; rama codex/p0-approved-execution.
Prefijo usado en comandos uv: UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache.

## Antes de mercado

| Comando después de `uv run --frozen` | Log | Resultado |
|---|---|---|
| pytest tests/test_p0_budget.py -q | budget-red.log / budget-green.log | API inexistente, luego 7 pasan |
| pytest tests/test_p0_integration.py -q | integration-red.log / integration-green.log | API inexistente, luego 3 pasan |
| pytest tests/test_p0_budget.py tests/test_p0_integration.py -q | synthetic-first.log | 15 pasan |
| pytest | pytest-first.log | 179 pasan antes de revisión |
| pytest tests/test_p0_integration.py::test_c0_checkpoint_risk_flag_allowed_but_c5_c10_cannot_disable -q | c0-resume-red.log | Reproduce fallo C0 |
| pytest tests/test_p0_integration.py -q | integration-review-green.log | 8 pasan |
| pytest | pytest-final.log | 182 pasan antes de revisión de cierre |
| pytest tests/test_p0_budget.py::test_checkpoint_can_use_closing_reserve_without_extending_work tests/test_p0_budget.py::test_supervisor_separates_work_and_save_deadlines tests/test_p0_integration.py::test_late_invocation_preserves_paused_or_completed_campaign -q | closing-red.log | 4 fallos reproducidos |
| pytest tests/test_p0_budget.py tests/test_p0_integration.py -q | closing-green.log | 21 pasan, 1 fallo intermedio corregido |
| pytest | **pytest-verified.log** | **186 pasan, 63.77 s** |
| ruff check . | **ruff-verified.log** | **All checks passed** |

Se aplicaron Ruff format/check --fix para imports. Fallos intermedios conservados,
no vigentes. accepted_synthetic fabrica sus productos; ningún fixture carga
mercado. Dos corridas pequeñas sintéticas reales prueban la orquestación con un
launcher adaptado; watchdog se prueba aparte con procesos reales. La prueba de
guarda C0 simula el lease. Los tiempos ficticios no estiman mercado.
No se atribuyen los resultados históricos H5 a esta ejecución. Véase REVIEW.md.

## Campaña autorizada

Comando canónico, sin overrides de parámetros/semillas/raíz/presupuesto:

```bash
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python scripts/run_pilot.py --protocol docs/protocols/P0-approved-v1.json
```

Estado y checkpoints en artifacts/p0-approved-v1; schema p0_complete_boundary_v2.
Unidades: Q0 y dos iteraciones completas, guardado tras cada frontera. La
exportación pequeña usa solo logs/manifiestos, nunca OHLC ni evaluación:

```bash
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python scripts/report_p0.py --output docs/evidence/p0-execution/campaign-results
```

El log y resultados de campaña se registrarán por separado. Destinos nuevos,
sin sobrescribir evidencia. La eliminación previa de .python-version no se incluye.
