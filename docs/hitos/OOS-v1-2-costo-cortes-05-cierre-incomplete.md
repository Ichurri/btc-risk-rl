# Cierre metodológico WF `...05`: `incomplete`

**Decisión conservadora del 03/11/2026:** el 02/11 cuenta como **segundo día
activo** de la campaña WF05. Se hicieron comprobaciones específicas de
reingreso, una suite completa, Ruff, preflight vigilado y cierre, aunque la
guarda de memoria impidió abrir una tercera sesión de campaña. La fecha ya
terminó en `America/La_Paz`; el máximo original de dos días impide iniciar
`wf-2022/Q0` en una fecha posterior. El estudio se informa
**`incomplete` (11/22 unidades)**. El ledger histórico permanece, sin
reescritura, en `ready`, `pending=null`; ese estado técnico de frontera no
equivale a una campaña completada ni autoriza reingreso. Ninguna de las
once unidades aceptadas se repitió.

## Evidencia conservada y permiso

La auditoría reproducida de la sesión 02 verifica cada uno de los once
reportes, checkpoints y manifiestos, la cadena del ledger, bitácora,
supervisor y fronteras. El mapa de 2.647 archivos de la raíz conserva
SHA-256 `0d034efccb2138c4fb975c86e504763ff69ce331f2a5fdbb9919f4e1d06931eb`.
El ledger conserva SHA-256
`218ae4d4efad8f3440bb898a1f30f6ca33a09a26045c2b0bff0fe15c0303c1ba`;
el último checkpoint `wf-2021/checkpoint-10/state.pt` conserva
`80626e96b6294492ca2ce116327f8ae32611f6419bede0219622cdb442f386cf`.
No existe checkpoint aceptado del corte 2022 ni unidad WF activa. Las
raíces `...01`–`...04` mantienen sus huellas anteriores.

El permiso operativo WF05 se cerró **prospectivamente** cambiando solo
`MARKET_EXECUTION_ENABLED` a `False`. El registro de aprobación original
queda intacto, SHA-256
`c2b287ec646a6d6a85c849474f1411f5be28fabb1f1c5701b65005e3374a3c59`;
su huella de código corresponde al ejecutor histórico aprobado, no al
código ya cerrado. El comando público y el trabajador devolvieron código
1 con `NOT AUTHORIZED` antes de abrir una solicitud o crear artefactos.
El código cerrado tiene SHA-256 de huella ejecutable
`d8e779354f6739221300cdc3cbfa6b74ebbb2f90f8f7f01e6300de09fc6f606b`.

## Conciliación sin doble cargo

La regla adoptada aquí cuenta **toda actividad de campaña** en su día
local: verificaciones, carga, ejecución, auditoría y cierre. El presupuesto
global es 10.800 s/día con reserva obligatoria de 2.700 s, por lo que hay
8.100 s antes de la reserva; los límites propios son 3.600 s/día y
5.400 s acumulados. Los cargos automáticos solo cubren el ledger y la
bitácora. La conciliación usa tanto duraciones registradas como intervalos
de pared conservadores; un intervalo que ya contiene una tarea no se
suma a esa tarea otra vez.

| Día La Paz | Cargo automático, medido | Trabajo medido fuera del cargo | Mínimo distinto verificable | Envolvente conservadora de pared | Tope propio diario |
| --- | ---: | ---: | ---: | ---: | ---: |
| 01/11 | 3.484,510403 s | Suite inicial anterior al ledger: 339,63 s | **3.824,140403 s** | 4.166 s, desde commit de aprobación hasta informe de sesión 02 | 3.600 s |
| 02/11 | 0 s informados por el contador | Suite: 390,45 s | **390,45 s** | 560 s, desde primera comprobación registrada hasta commit del bloqueo | 3.600 s |

El 01/11, el cargo automático es la unión de **3.482,644557 s** del
intervalo del ledger y **1,865846 s** de bitácora fuera de él. Incluye la
espera entre sesiones. Las suites posteriores del mismo día (338,85 s y
349,96 s) ocurrieron **dentro** de ese intervalo: se documentan, pero no
se añaden. La suite inicial de 339,63 s terminó antes del primer preflight
y del comienzo del ledger, por lo que sí se añade. El mínimo distinto
**supera el tope propio diario por al menos 224,140403 s**. El supervisor
admitió unidades usando el cargo automático incompleto; no se declara
retrospectivamente cumplido ese tope. La envolvente de 4.166 s incluye
esperas y cierre y **no** es tiempo de entrenamiento medido.

El 02/11, la primera lectura de hora del trabajo fue 17:22:39 local,
registrada en la conversación con resolución de un segundo. El preflight
observó 17:29:52,915844; el commit del informe bloqueado se fechó a las
17:31:59. El intervalo hasta preflight fue **433,915844 s**: contiene la
suite de **390,45 s** y **43,465844 s restantes** que no pueden repartirse
exactamente entre auditoría, Ruff, preflight y esperas. El intervalo de
preflight a cierre fue **126,084156 s**, con documentación y comprobaciones;
su reparto por proceso tampoco quedó registrado. Los dos intervalos suman
la envolvente conservadora de **560 s**. Es distinta del contador automático
de 0 s, que solo refleja que no se abrió una sesión de campaña. No se suman
otra vez los 390,45 s a los 560 s.

En ambos días, el gasto registrado de otras campañas fue 0 s en los
preflights. Las envolventes de 4.166 y 560 s quedan bajo los 8.100 s
globales por día antes de reserva, pero el **tope propio del 01/11 quedó
excedido en la conciliación**. El mínimo no solapado de los dos días es
**4.214,590403 s**; la suma de envolventes conservadoras es **4.726 s**,
con 674 s frente a 5.400 s. Esta última cifra incluye esperas, no es
duración de cómputo y no prueba un costo exacto. La duración individual de
las auditorías, Ruff, preflights y cierres no quedó instrumentada; sus
intervalos conjuntos sí están comprendidos en las envolventes. No se
infieren saldos íntegros del `global_spent=0` del 02/11.

La conciliación reproducible y las huellas se encuentran en
[`reconcile.py`](../evidence/oos-v1-2-wf-cost-05-closure-20261103/reconcile.py)
y [`results.json`](../evidence/oos-v1-2-wf-cost-05-closure-20261103/results.json).
La lectura de hora de 17:22:39 proviene de la salida de herramienta de la
conversación; los otros hitos proceden de preflights, ledger y commits.

## Alcance y verificación del cierre

La prueba focal posterior al cierre dio **24 passed**; la suite completa
dio **464 passed** y Ruff pasó. Los comandos directos del público y del
trabajador fueron rechazados con código 1. La auditoría tras esas pruebas
reprodujo el mismo JSON y las mismas huellas de raíz, ledger y checkpoint.
Ver [comandos](../evidence/oos-v1-2-wf-cost-05-closure-20261103/COMMANDS.md).

Solo hay una medición completa de costo del corte de desarrollo 2021: las
dos sesiones tuvieron 749,205481 s de pared sumada, mientras la fase D de
las diez actualizaciones registró 47,817987 s. El cargo de presupuesto es
mayor por la espera entre sesiones. **No existe una corrida medida del corte
2022**; WF05 no confirma la viabilidad temporal de la propuesta v1.2 ni
autoriza su evaluación. Esto es una medición de infraestructura y costos,
no un resultado financiero, de generalización ni de cumplimiento CVaR.
Validación 2023 y prueba final permanecieron cerradas.
