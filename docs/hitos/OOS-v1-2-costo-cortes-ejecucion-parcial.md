# Estudio de costos WF: Q0 aceptada y continuación bloqueada

**Estado metodológico:** medición parcial de desarrollo. El protocolo de
22 unidades fue autorizado para medir costos, sin adoptar la evaluación v1.2.
La ejecución se detuvo tras una sola Q0 y no ofrece tiempo medido de
Q/A/B+D ni costo completo de los dos cortes.

## Autorización y preflight

El registro específico
[`OOS-v1-2-wf-cost-approval.json`](../protocols/OOS-v1-2-wf-cost-approval.json)
fijó el alcance y las huellas SHA-256 del
[protocolo](../proposals/OOS-v1-2-costo-entrenamiento-cortes-v1.md)
`f6d81fd9f10938aee29480c701a1a52c0b84eba1db0ea42a21d2d84c3004cbe4`,
del [diseño](../protocols/OOS-v1-2-wf-cost-executor-v1.json)
`66109d4400e04440c9450d1f1c0c7cc4332b66b9079703e3a1e62596032b5ad0`
y del manifiesto H1 de solo entrenamiento
`62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9`.
La huella del propio registro es
`b36e32521f43af3f0b7b363f2555d1bee19fa5200c3cee30b5e8987068984369`.
El permiso se registró en el commit **`86e83ed`**, separado del código de
pausa Q0 (`0cdd264`). El registro histórico no se editó después del fallo.
El estado `infrastructure_only_not_authorized` del JSON de diseño es la
instantánea preaprobación fijada por su huella; la autorización se registró
en el archivo separado, sin reescribir ese diseño.

Los preflights vigilados
[`preflight-approved-20261026.json`](../evidence/oos-v1-2-wf-cost-executor/preflight-approved-20261026.json)
y [`preflight-launch-20261026.json`](../evidence/oos-v1-2-wf-cost-executor/preflight-launch-20261026.json)
fueron `ready`: gestor `running`, `Linger=yes`, CA, batería ≥50 %, memoria
≥4 GiB, disco ≥20 GiB, presupuesto compartido libre, entradas y hashes
íntegros, raíz ausente, 3.639/4.678 inicios de corte y ninguna apertura de
CSV H1 compartidos. El preflight inmediatamente antes del servicio fue a
las **02:38:19 UTC**, con batería 72 %, memoria disponible 8.437.854.208 B,
disco libre 152.827.473.920 B y gasto global registrado de 0 s. Son
mediciones de ese momento. El preflight tras Q0 volvió a dar `ready`; no
detectaba la discrepancia de tipos en el reingreso al ledger.

## Cronología y resultado medido

| Evento (UTC, 27/10/2026) | Evidencia |
| --- | --- |
| 02:38:42, sesión `oos-wf-cost-20261026-session-01.service` | `InvocationID=5c405d0855a14923bd4c9481fa73130e` |
| 02:38:44–02:39:11, `wf-2021/Q0` | 400 trayectorias, 72.000 transiciones; 0 pasos actor/crítico; 26,373 s entre begin/accept, 26,178 s de trabajador; RSS máximo trabajador 358.670.336 B |
| 02:39:11, auditoría de Q0 | `after_q0`, reporte y checkpoint coincidentes, cadena de ledger/journal íntegra; pausa `first_q0_audit`; servicio `Result=success` |
| 02:40:49, sesión `oos-wf-cost-20261026-session-02.service` | `InvocationID=6513bcb4dbf34444a38d8acc712cdafb` |
| 02:40:52, fallo antes de unidad 1 | `Campaign identity mismatch`, `Result=exit-code`, código 1; ninguna unidad nueva aceptada |

El journal del primer servicio informa 30,553 s de CPU y 465,6 MB de pico
de memoria de servicio; el segundo, 4,140 s de CPU y 395,9 MB de pico. Son
medidas de `systemd` distintas del intervalo de Q0 del ledger. No se
extrapolan a las diez iteraciones ni al corte 2022. La primera sesión
terminó con 1/22 unidades; el ledger registra 26,714 s de pared cargada
para ese día. El tiempo fuera del ledger de preflight, auditoría y segunda
sesión debe contarse en cualquier análisis de recursos; no se le asigna aquí
una duración total inventada. El journal de `systemd` sitúa la segunda sesión
entre 02:40:49,873 y 02:40:52,833 UTC (aprox. 2,96 s de pared), pero el
ledger quedó con la misma huella anterior: ese fallo previo a abrir el ledger
**no se debitó allí**. Es una brecha de instrumentación del presupuesto para
sesiones fallidas en preflight, aunque este caso quedó muy por debajo del tope.

## Diagnóstico y adjudicación

La reconstrucción de la identidad de campaña, **sin trayectorias ni pasos de
optimizador**, halló una sola diferencia: `identity.roster` es `list` de
listas en el ledger JSON y `tuple` de tuplas al reabrirlo. Los demás campos
coinciden, y las identidades son iguales después de serializar la segunda a
JSON. [`session-02-identity-diff.json`](../evidence/oos-v1-2-wf-cost-executor/session-02-identity-diff.json)
documenta la comprobación. Es un defecto de reanudación demostrado, no una
hipótesis sobre entrenamiento. La prueba sintética previa había ejercitado
reapertura tras **22 unidades completas**, pero no reapertura desde la
primera Q0 aceptada. Su cobertura fue insuficiente para este caso.

La segunda sesión no creó `checkpoint-1` ni `unit-1.json`. El ledger quedó
`ready`, `units=1`, `pending=null`, con SHA-256
`b6bc9a30d25387813d664708edfa07347c21174d2df216fc6f6be2d844ec6af6`,
idéntico al de la auditoría Q0. El estado operativo, sin embargo, es
**detenido por fallo de reingreso**, no una pausa presupuestaria admisible.
No se corregirá el código bajo esta raíz: cambiarlo modificaría la huella
congelada del checkpoint, y no se forzará equivalencia retrospectiva.
El permiso de código se cerró prospectivamente (`MARKET_EXECUTION_ENABLED=False`)
y ambos comandos rechazan otra ejecución antes de leer una solicitud de
trabajo. El JSON de autorización sigue activo solo como registro histórico;
no habilita el código. Cualquier estudio de reemplazo requeriría diseño,
prueba sintética de Q0→reingreso, raíz y autorización nuevos. No se repetirá
selectivamente la unidad fallida ni se llamará completo a este estudio.

Tras el fallo, `systemctl --user is-system-running` devuelve `degraded`
porque la unidad 02 permanece en estado `failed`. No se ejecutó
`systemctl reset-failed`: su estado y journal se preservan como evidencia.
El preflight `ready` anterior al lanzamiento fue válido para ese instante;
no describe el estado actual del gestor ni concede un nuevo lanzamiento.

## Integridad y límites

La [auditoría Q0](../evidence/oos-v1-2-wf-cost-executor/q0-audit.json)
fijó SHA-256 de `state.pt`
`22f9f60484db6ae5a04b7b35f4ebe2149debb16ac357437536c24f571bf8bca7`
y del reporte
`1ba4d95998624d0f0c8a46cdc37ddb51b8a2e04a32c5a14d85eff4f6639a934f`.
Las huellas seguían iguales después del fallo. Los cinco ledgers P0/P1/P2/
P2R/P3 coincidieron con sus huellas anteriores; `.python-version` permanece
como eliminación local ajena sin incorporar al commit. No se abrió
validación 2023 ni prueba final.

Los [comandos ejecutados](../evidence/oos-v1-2-wf-cost-executor/COMMANDS.md),
los journals originales en `artifacts/oos-v12-wf-cost-only-01/` y sus copias
pequeñas versionadas permiten revisar las horas y hashes. La suite previa al
lanzamiento pasó 378/378 y Ruff; después del cierre, las pruebas focales
pasaron 18/18, la suite completa 378/378 y Ruff volvió a pasar.
Este resultado mide solo Q0 del primer corte. No permite afirmar que el
presupuesto de 20 días propuesto para v1.2 baste, ni comparar C0/C5/C10,
rentabilidad, generalización o cumplimiento de CVaR.
