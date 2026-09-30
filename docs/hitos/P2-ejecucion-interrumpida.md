# P2 histórico: cierre por interrupción del supervisor

**Estado: campaña fallida e incompleta; criterios de P2 no evaluables.** La
ejecución autorizada empezó el 30/09/2026 sobre entrenamiento aceptado
2018–2022, desde la activación publicada en `18bc767`. Se mantuvieron las nueve
corridas previstas, K=10, crítico de cuatro épocas provisional, D=64, cota
`d=-ln(0.90)`, Q/A/B y los parámetros registrados. No hubo modificación del
algoritmo durante la campaña.

La sesión del supervisor desapareció durante `run-05-C0`, unidad 2. El último
estado completo se escribió a las 06:19:30.457 UTC. El progreso parcial, de
06:20:12.742 UTC, indica fase B; no existe `unit-2.json` ni `checkpoint-2`.
Al retomar la inspección a las 16:29 UTC, la sesión de ejecución ya no existía,
el bloqueo de campaña estaba libre y el ledger seguía en `running`. Se aplicó
el mecanismo de fallo del propio `P2Ledger`, que registró
`interrupted_supervisor_or_unit` a las 16:32:06.528 UTC. **No se lanzó otra
unidad, no se reanudó ni se repitió la parcial.** El límite de uso del chat
coincidió con la interrupción, pero los artefactos no prueban su causa precisa:
el log de la unidad parcial está vacío y no hay registro de excepción del worker.

## Resultados operativos realmente cerrados

| Corrida | Semilla | Estado | Iteraciones completas | Trabajo de unidades cerradas (s) | Pico RSS (MiB) | D medido (s) | Alertas del crítico: minibatch / A completo |
|---|---:|---|---:|---:|---:|---:|---:|
| C0 | 610031 | completa | 10 | 695.693 | 520.6 | 45.864 | 99/160; 8/10 |
| C5 | 610031 | completa | 10 | 702.693 | 574.3 | 46.471 | 99/160; 8/10 |
| C10 | 610031 | completa | 10 | 700.701 | 548.0 | 46.815 | 99/160; 8/10 |
| C5 | 610047 | completa | 10 | 733.862 | 562.1 | 50.269 | 121/160; 9/10 |
| C10 | 610047 | completa | 10 | 763.875 | 576.3 | 53.982 | 121/160; 9/10 |
| C0 | 610047 | fallida en unidad 2 | 1 | 99.118 | 387.8 | 4.934 | 16/16; 1/1 |
| C10/C0/C5 | 610081 | no iniciadas | 0 | 0 | — | 0 | — |

La tabla usa exclusivamente unidades confirmadas por el ledger; los tiempos
son de pared por unidad y no incluyen la parcial ni todos los costos de carga
y cierre. La primera D real consumió 4.604 s dentro de la primera iteración
C0/610031, bajo el subtope de 900 s. Las 51 iteraciones terminadas midieron
248.335 s de D en conjunto. Las cinco corridas completas más dos unidades de
la sexta suman 57 unidades y 3695.943 s de tiempo de pared supervisado, sin
inferir una duración total para el proceso interrumpido. La preparación del día
tenía un débito externo de 516.151 s. El inicio fue 05:17:53.076 UTC; el plazo
de trabajo configurado era 07:32:53.285 UTC y el de cierre 08:09:16.925 UTC.
El último progreso quedó antes de ambos. El tiempo exacto de terminación del
proceso no se pudo reconstruir, por lo que no se declara consumo diario total.
El campo `active_seconds=0` del ledger no representa duración nula: la
interrupción impidió ejecutar el cierre que lo actualiza. Para tiempos de
trabajo se usan las mediciones por unidad confirmada.

Los contadores **cerrados** son 46 464 trayectorias de aprendizaje, 8 363 520
transiciones, 3264 trayectorias D, 587 520 transiciones D, 408 pasos de actor
y 816 pasos de crítico. En la unidad parcial, `progress.json` reportó para la
sexta corrida 1868 trayectorias de aprendizaje acumuladas, 336 240 transiciones,
64 D acumuladas, 16 pasos de actor y 32 de crítico, aún en fase B. Frente al
checkpoint 1 de esa corrida, esto muestra trabajo adicional sin frontera
`after_dual_and_D`; no se agrega a los contadores cerrados ni se usa para
evaluación. Los archivos parciales originales permanecen en
`artifacts/p2-approved-v1/run-05-C0` fuera de Git.

En las cinco corridas completas hubo 581 advertencias del crítico, con
denominadores explícitos en la tabla. La sexta aporta 17 advertencias de su
primera iteración completa: 598 en las 57 unidades cerradas. Son diagnósticos
de ajuste, no fallos de integridad por sí mismos. En D, la MSE relativa
posterior de la primera/última iteración fue 1.510/1.052 para las tres
condiciones de 610031 y 7.542/1.176 para C5/C10 de 610047. Esas lecturas
siguen por encima del predictor cero en la última iteración respectiva; se
describen sin selección de checkpoints y sin inferencia entre semillas.

## Integridad y alcance de las conclusiones

El preflight posterior al commit verificó permiso, configuración, 7048 inicios
aceptados, huellas de datos y normalizador, recursos disponibles y 108
artefactos previos de P0/P1. Antes del mercado se ejecutaron 234 pruebas y
Ruff sin errores. El cierre **de solo lectura** validó la cadena completa de
176 estados del ledger, secuencia y recursos de 57 unidades, los hashes de sus
checkpoints, procedencia de entrenamiento y 3264 archivos D. El estado final
del ledger es `failed`, hash del archivo
`e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8`.
La unidad parcial no pasó ese cierre porque carece de checkpoint completo. No
se ejecutaron nuevas actualizaciones para comprobar el cierre.

El campo heredado `market_training_executed` aparece como `false` en los
informes P2 porque su condición de escritura solo reconoce P0/P1. Es un
defecto de **metadatos**, no prueba de que P2 no entrenó: el perfil
`authorized_p2_only`, los pasos de optimizador, el origen de entrenamiento y
los checkpoints verificados muestran las actualizaciones cerradas. No se
modificó el código operativo para corregirlo durante la campaña.

Los umbrales conjuntos predefinidos requieren las nueve corridas de las tres
semillas y las ventanas completas {0,1,2}/{7,8,9}. Por la interrupción, el
resultado es **no evaluable**, no un fracaso ni éxito del criterio del crítico.
No se puede afirmar generalización temporal, superioridad financiera o
cumplimiento poblacional de CVaR. D usa realizaciones nuevas del mismo
histórico de entrenamiento; no es validación 2023. No se accedió a validación
ni al conjunto final por el ejecutor P2; ninguno fue usado en el cierre. La
tesis no se modificó.

La siguiente decisión es metodológica y operativa: revisar la causa de la
pérdida del supervisor y definir un protocolo nuevo si se desea completar un
estudio comparable. El ledger fallido y las evidencias originales deben
preservarse; esta campaña no admite reanudación ni sustitución selectiva.

[Resultados auditados](../evidence/p2-execution/campaign-results/results.json),
[comandos y comprobaciones](../evidence/p2-execution/COMMANDS.md),
[autorización](../protocols/P2-market-approval-2026-09-30.md).
