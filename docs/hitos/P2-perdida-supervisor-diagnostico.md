# P2: diagnóstico de la pérdida del supervisor

**Revisión documental de `a2014e4`; sin ejecutar P2 ni modificar sus artefactos.**
La evidencia nueva sitúa un **apagado del equipo** en el mismo segundo que el
último progreso de `run-05-C0`. Esto explica de forma mucho más sólida la
pérdida del supervisor que un error ordinario del algoritmo. No se pudo
determinar qué inició el apagado.

## Hechos comprobados

| Instante UTC, 30/09/2026 | Registro | Hecho |
|---|---|---|
| 06:19:30.457 | Ledger P2 | Cerró `run-05-C0`, unidad 1, en `after_dual_and_D`; 57 unidades cerradas en total. |
| 06:19:30.481 | Ledger P2 | Abrió unidad 2 de la misma corrida y permaneció en `running`. |
| 06:20:11.000 | Journal del usuario, GNOME | `endSessionDialog` consultó la sesión a `logind`. |
| 06:20:12.527 | Journal del usuario, GNOME | `Shutting down GNOME Shell`; comenzó el cierre de servicios de sesión. |
| 06:20:12.742 | `progress.json` | Unidad 2 en fase B: 1868 trayectorias de aprendizaje, 336240 transiciones, 16 pasos de actor y 32 de crítico **acumulados en esta corrida**; 64 D corresponden a la unidad 1. |
| 06:20:12 local 02:20:12 | `last -x -F`/wtmp | Registró `shutdown system down`; el arranque siguiente fue a las 16:06:59 UTC. |
| 06:20:16 | Journal del usuario | La sesión alcanzó `shutdown.target` y `exit.target`; la salida de aplicaciones y servicios fue general, no específica de P2. |
| 16:32:06.528 | Ledger P2 | Al inspeccionar de nuevo el estado, `CampaignLedger` marcó `failed`, razón `interrupted_supervisor_or_unit`. **Esta es la hora de detección**, no la hora del apagado. |

Los horarios GNOME y `progress.json` tienen precisión subsegundo; `last` muestra
segundos. El último progreso se escribió unos 0.215 s después del mensaje
`Shutting down GNOME Shell`: el worker aún pudo escribir mientras terminaba la
sesión. Los artefactos de la unidad 2 carecen de `closing-2.json`,
`unit-2.json`, `checkpoint-2` y `failure-2.json`; `worker-2.log` mide cero bytes.
El último evento del journal propio de la corrida es `in_unit`.

El código del supervisor lanza el worker con `PR_SET_PDEATHSIG=SIGKILL` y solo
registra su resultado cuando la llamada de supervisión retorna. La unidad
parcial no devolvió un resultado supervisado: el ledger quedó `running` hasta
su reapertura, y el bloque de cierre que acumula `active_seconds` no se ejecutó.
Un error Python ordinario del worker, de haber llegado al manejador, habría
dejado `failure-2.json`; su ausencia no prueba por sí sola la causa, pero es
coherente con terminación del proceso o del equipo. Tampoco se alcanzaron el
plazo de trabajo de 07:32:53 UTC ni el de cierre de 08:09:16 UTC. La última
unidad completa tuvo RSS pico de 387.8 MiB y la mayor de las 57 completas,
576.3 MiB; **no hay RSS medido de la unidad parcial**.

La cadena del ledger fallido conserva 176 estados y SHA256
`e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8`.
Los SHA256 del progreso, solicitud y journal parcial se registran en
[comandos y huellas](../evidence/p2-shutdown-investigation/COMMANDS.md). Ninguno
de esos archivos se editó ni se utilizó para reanudar.

## Inferencia, hipótesis y límites

**Inferencia principal, respaldada por dos registros independientes:** el
apagado del equipo interrumpió la sesión que alojaba al supervisor y dejó una
unidad sin frontera completa. La coincidencia temporal, el cierre general de
GNOME, el registro wtmp y la ausencia de retorno del supervisor apoyan esta
explicación. No hay evidencia de que un criterio de P2, un plazo o una alerta
del crítico haya solicitado la parada. El agotamiento del límite de uso del
chat coincidió en el tiempo, pero no demuestra que haya ordenado el apagado.

**Hipótesis no resueltas sobre el origen del apagado:** acción humana en el
escritorio o botón de encendido; política de energía o batería; orden de otro
servicio; otra causa externa. Los avisos de GNOME durante el desmontaje de la
sesión son posteriores al inicio del cierre y no identifican el desencadenante.
La presión de memoria u OOM no está demostrada: los picos de unidades cerradas
no son la memoria de la unidad parcial ni la del sistema completo. El journal
del sistema/kernel, que podría contener `logind`, energía, OOM o la orden de
apagado, no fue legible para este usuario; `sudo -n` requirió contraseña. No se
pidió elevar privilegios ni se infirió un motivo ausente de los registros.

**Datos faltantes:** iniciador y motivo de la orden de apagado, señal exacta
recibida por el supervisor/worker, RSS y tiempo final de la unidad parcial,
consumo diario total hasta la caída y log estructurado independiente de la
sesión. El ledger solo contabiliza unidades cerradas; el `active_seconds=0`
tras la caída no representa ausencia de trabajo. No se consultaron datos de
validación ni del conjunto final para explicar el apagado.

## Decisión de integridad

La campaña P2 en `artifacts/p2-approved-v1` continúa `failed`. La unidad 2 no
es una muestra completa de riesgo ni un checkpoint reanudable. Las cinco
corridas terminadas y la iteración cerrada de la sexta son descriptivas, pero
no satisfacen los criterios conjuntos de nueve corridas. No deben combinarse
con una nueva campaña para completar artificialmente la matriz. Una eventual
repetición completa exige protocolo, infraestructura y autorización nuevos;
véase la [propuesta P2R](../proposals/P2R-protocolo-v1.md).
