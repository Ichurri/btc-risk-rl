# Integración prospectiva del permiso WF

**Alcance:** código y verificación sintética después del fallo de Q0 de `...03`. No hubo campaña, unidad histórica, permiso nuevo ni modificación de las raíces `...01`–`...03`. La rama es `codex/oos-wf-permit-integration` y el commit de código y pruebas es `803abc1`.

## Causa y guardas revisadas

El trabajador `wf_cost_replacement_03_worker.main` construía el permiso específico de `...03` y llamaba a `complete_unit`. El permiso hereda de `wf_cost.WFCostPermit`, pero el comparador `type(permit) is WFCostPermit` lo rechazaba. La revisión de la ruta encontró otras dos listas de tipo exacto que tampoco incluían los perfiles `...02`/`...03`:

| Etapa | Guarda previa | Cambio |
| --- | --- | --- |
| `p2_runner.complete_unit` | Solo `WFCostPermit` original | Tipos exactos `...01`/`...02`/`...03`; `permit.validate` y raíz `CAMPAIGN/run_id` antes de crearla |
| `trainer.SyntheticExperiment` | Parejas fuente/configuración/permiso solo con tipo WF original | Añade las dos parejas específicas a los conjuntos exactos; conserva `permit.validate` |
| `p2.Diagnostic.bind` | Solo tipo WF original | Añade los dos tipos específicos; conserva `permit.validate_d` |

La lista única está en `src/btc_risk_rl/pilots/wf_permits.py`; se compara con `type`, no con `isinstance`. Un subtipo inventado o un objeto con métodos `validate`/`validate_d` no queda autorizado. Los permisos listados no activan campañas: cada `validate` y `validate_d` sigue exigiendo su gate, aprobación registrada, lease pendiente con token y PID, identidad de corrida/fuente y datos de entrenamiento aceptados. La raíz ajena falla antes de `mkdir`.

## Prueba de integración

`tests/test_wf_permit_integration.py` llama a `wf_cost_replacement_03_worker.main` sin reemplazar `complete_unit`, `SyntheticExperiment`, `Diagnostic.bind`, `run`, `save_checkpoint` ni `_verify_completion`. La fuente tiene tipo `TrainingMarket` para recorrer las guardas de mercado, pero sus rutas y precios provienen de `SyntheticMarket` en un directorio temporal. El fixture reduce Q a dos trayectorias y desactiva **solo dentro de la prueba** la aprobación externa y la comprobación de parámetros congelados, para no iniciar una campaña. Mantiene reales la validación de solicitud, hash, token, PID, ledger, semilla, condición, procedencia del lote controlado y raíz de ejecución.

Q0 termina en `after_q0`; la prueba compara el SHA-256 de `state.pt` con el manifiesto, verifica contadores sin pasos de actor/crítico y pasa el verificador real `_verify_completion`. También rechaza token falso, raíz ajena, semilla y condición alteradas, un subtipo de permiso no listado y el gate cerrado. El test positivo atravesó las tres guardas que faltaban; por diseño no ejecuta D ni Q/A/B+D, ni prueba recursos, `systemd` o costo del histórico.

La primera ejecución roja del test llegó al mismo `PermissionError` de `p2_runner.py:79` que detuvo `...03`. Una equivocación inicial del fixture al parchear una importación interna se corrigió antes de esa reproducción. Después del cambio, las pruebas focales terminaron **52 passed** y la suite completa **435 passed en 287,40 s**; Ruff y `git diff --check` pasaron. Los comandos y logs están en [COMMANDS.md](../evidence/oos-wf-permit-integration/COMMANDS.md).

## Preservación y límite de interpretación

La [auditoría de solo lectura](../evidence/oos-wf-permit-integration/verification.json) comparó los archivos de cada raíz con sus referencias congeladas: `...01` 15/15, `...02` 2/2 y `...03` 10/10 idénticos. Los tres `MARKET_EXECUTION_ENABLED` permanecen `False`. Los tres trabajadores públicos devolvieron código 1 con `NOT AUTHORIZED` antes de leer una solicitud inexistente. La huella del JSON histórico de aprobación `...03` se conserva; el código actual tiene otra huella y no reutiliza esa aprobación.

Esto corrige la incompatibilidad de permisos demostrada, **sin convalidar retrospectivamente** el preflight de `...03` ni convertir su ledger `failed` en reanudable. Tampoco establece el costo de Q0 histórica o de 22 unidades. Una medición posterior requeriría una raíz limpia y una autorización independiente, precedidas de su propio preflight.
