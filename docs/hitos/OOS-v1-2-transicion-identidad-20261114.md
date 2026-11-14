# OOS v1.2 — transición de código operativo antes de la corrida 103

## Segundo intento, sin unidad nueva

La sesión `oos-v12-training.service` iniciada el 14/11/2026 a las 08:15:39
`America/La_Paz`, `InvocationID=a9afdbbc0ec242319f19b35614a465b4`,
pasó suite (861,489608 s), Ruff (0,042101 s) y preflight vigilado
(41,632520 s), pero terminó `Result=exit-code` antes de Q0 de la corrida
103. El supervisor registró `recovery_rejected`: `Campaign identity mismatch`.
El código v4 estaba verificado, pero el ledger conservaba por diseño la
identidad de código con la que comenzó la campaña. Este control impidió
silenciosamente mezclar identidades. La bitácora duró 1.105,433049 s y quedó
`failed`; el ledger no cambió: `ready`, cursor 103, 1.133 unidades,
`pending=null`, último checkpoint
`dff17b3504b95cf30ad16ab93df571e856397486c25d5b73ad59b484219097c1`.
No se recolectaron trayectorias ni se ejecutó un paso de optimizador.

## Adjudicación limitada y verificable

El [registro de transición](../protocols/OOS-v1-2-code-transition-20261114.json)
fija el hash exacto del segundo cierre fallido y de sus tres comprobaciones
`ready`. Se conserva la fila fallida. La recuperación solo procede si
el ledger sigue íntegro y en la misma frontera, y si la identidad científica
es idéntica. Se compararon las huellas de todos los archivos de código del
ledger con el checkout: **solo difieren**
`oos_v12_budget.py`, `oos_v12_launch.py`, `oos_v12_training.py` y
`wf_cost_session.py`, todos relativos a permiso, bitácora y supervisor.
Actor, crítico, recolector, entorno, recompensa, configuración, fuente,
normalizador, roster, orden y límites por unidad son los originales.

En el primer reingreso válido, el ledger conserva su identidad original y
**anexa** `operational_code_transitions` con cursor 103, número de unidades,
hash del estado anterior, hash del nuevo mapa de código, permiso y protocolo.
No reescribe filas antiguas. Los reportes y checkpoints nuevos registran la
procedencia efectiva del código nuevo. La corrida 103 comienza en Q0, sin
cargar un checkpoint de la identidad anterior. Una continuación posterior
solo admite ese mismo mapa de código y permiso. Cualquier cambio de código
del algoritmo o del diseño se rechaza.

El segundo intento se carga íntegro y se añade el intervalo conservador
registrado en el protocolo desde su cierre hasta la adjudicación. El timer
permanente se deshabilitó durante el diagnóstico para evitar un arranque
duplicado. El balance compartido de las 08:46 fue 23.954,341 s cargados y
23.745,659 s antes de la reserva, una medición de ese momento.

## Límite metodológico

Esto resuelve la trazabilidad de una modificación operativa entre corridas;
no convierte el entrenamiento en una evaluación confirmatoria. Se debe
informar el cambio de código y los dos intentos fallidos al presentar el
historial de entrenamiento. Validación 2023 y prueba final siguen cerradas.
