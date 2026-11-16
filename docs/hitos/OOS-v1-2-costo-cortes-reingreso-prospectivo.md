# Corrección prospectiva del reingreso WF

**Alcance:** infraestructura y pruebas sintéticas. La campaña histórica
`artifacts/oos-v12-wf-cost-only-01/` permanece detenida después de una Q0;
su permiso operativo sigue cerrado. No se reanudó, repitió ni usó para
validar esta corrección. La evaluación fuera de muestra v1.2 permanece sin
adoptar.

## Causa reproducida y corrección

La [ejecución parcial](OOS-v1-2-costo-cortes-ejecucion-parcial.md) mostró
que el ledger serializa `identity.roster` como listas JSON, mientras que
`run_units` reconstruye tuplas Python. `CampaignLedger` compara la identidad
completa con `==`; después de Q0, esa diferencia de tipo bloqueaba el
reingreso. La prueba de proceso nuevo reprodujo el fallo antes de editar
el código.

La corrección se restringe a `WFCostLedger.__init__`: si la identidad incluye
roster, valida que sea una secuencia de filas `(corte: str, semilla: int,
condición: str)` y crea una copia con listas JSON. El resto de la identidad
se entrega sin normalizar a `CampaignLedger`, cuya comparación íntegra y
cadena de hashes permanecen iguales. Una semilla, condición, orden o número
de filas diferente continúa produciendo `Campaign identity mismatch`;
secuencias mal formadas se rechazan. No se cambió el algoritmo Q/A/B+D,
el calendario, los datos, los límites de admisión ni la fuente histórica.

## Verificación sintética

Dos procesos Python independientes operaron solo sobre `tmp_path`:

1. El primero creó un ledger sintético, aceptó un checkpoint Q0 fabricado
   en `after_q0` y cerró el proceso con `status=ready`, una unidad y
   `pending=null`.
2. El segundo reconstruyó la misma identidad, abrió el ledger y obtuvo
   `admit_unit("2021", 1, ...) == "start"`. No comenzó aprendizaje ni
   creó una trayectoria de mercado.
3. Procesos nuevos con semilla, condición, orden o longitud de roster
   alterados fueron rechazados. En cada caso, los SHA-256 del ledger y del
   checkpoint Q0 sintéticos quedaron idénticos y no apareció checkpoint 1.

El ensayo rojo de reingreso falló con `Campaign identity mismatch`; tras la
corrección, pasaron las cinco variantes nuevas. La ejecución focal terminó
con **23 passed en 6,79 s**, la suite completa con **383 passed en 264,16 s**,
y `uv run --frozen ruff check .` con **All checks passed!** El archivo
[`pytest-focused.txt`](../evidence/oos-v1-2-wf-cost-reentry/pytest-focused.txt)
contiene la ejecución focal. La suite completa y Ruff se consignan en
[`COMMANDS.md`](../evidence/oos-v1-2-wf-cost-reentry/COMMANDS.md).

## Tiempo perdido antes de abrir el ledger

La segunda sesión histórica falló en el constructor de `WFCostLedger`,
después de que `P2RSharedBudget` registrara `entered` y el journal del
supervisor registrara `supervisor_started`, pero antes de persistir un
`supervisor_exit` o un cargo al ledger. El SHA-256 del ledger quedó igual.
El journal de `systemd` mide aproximadamente 2,96 s entre inicio y fallo,
que **no figuran** en `charged_wall_seconds`. Además, `run_units` define
`entered = time.time()` después de reconstruir las dos fuentes, por lo que
esa carga previa tampoco queda cubierta por el intervalo del ledger.

Para un futuro estudio, el registro debe empezar después del permiso y del
contexto de servicio pero **antes** de la carga de fuentes. Una bitácora
durable independiente del ledger de campaña debe guardar `InvocationID`,
inicio/fin UTC, tiempo monotónico transcurrido, día `America/La_Paz`,
estado y motivo de salida, incluso si falla el constructor del ledger.
La admisión global deberá cargar ese intervalo junto al tiempo del ledger
sin duplicar su intersección; un inicio sin cierre verificable exigirá un
débito conservador y bloqueará la siguiente unidad. Las sesiones que crucen
medianoche requieren atribución por día. Los eventos `entered/exited`
actuales de `P2RSharedBudget` no incluyen duración y no cierran por sí solos
esta brecha. **Esta instrumentación presupuestaria queda propuesta, no
implementada en este hito**; debe probarse antes de autorizar otro estudio.

## Integridad y límite de la conclusión

[`frozen-artifacts.json`](../evidence/oos-v1-2-wf-cost-reentry/frozen-artifacts.json)
verifica en solo lectura las huellas publicadas del ledger, checkpoint Q0,
reporte, journal y registro histórico. El gate continúa
`MARKET_EXECUTION_ENABLED=False`; el registro de autorización conserva su
hash, pero no habilita ejecución. `.python-version` sigue como eliminación
local ajena. Las pruebas nuevas no abrieron validación 2023 ni prueba final,
no ejecutaron entrenamiento histórico y no demuestran que el costo total
de 22 unidades quepa en el presupuesto.
