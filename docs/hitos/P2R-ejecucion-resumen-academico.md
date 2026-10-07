# P2R v2 — resumen para Ingeniería del Proyecto

P2R v2 se ejecutó **solo como diagnóstico de desarrollo** sobre el derivado
H1 de entrenamiento 2018–2022. Se hicieron nueve corridas nuevas y separadas
de P2, con semillas 610031/610047/610081, orden rotado C0/C5/C10, K=10,
crítico de cuatro épocas provisional, D=64, `d=−ln(0.90)` y calendario
Q0, Q/A/B+D sin modificación. No se usó validación 2023 ni prueba final.

Las 99 unidades y checkpoints cerraron íntegros el 07/10/2026 en tres
sesiones `systemd --user` del mismo día La Paz. Dos pausas por disponibilidad
de recursos ocurrieron **después** de completar unidades; no se aceptó ni
repitió una unidad parcial. Se cargaron 6.893,096 s de 10.800 s diarios.
La primera Q/A/B+D histórica tardó 66,286 s de pared, con 4,725 s de D;
las 90 D sumaron 445,994 s. Se contabilizaron por separado 81.360
trayectorias de aprendizaje y 5.760 diagnósticas. El auditor verificó las
cadenas de ledger/journal, 99 checkpoints, 5.760 archivos D y 1.547
intervalos de heartbeat, cuyo máximo fue 4,228 s.

El cálculo **numérico** de la regla conjunta predefinida da `review`:
solo 610081 cumple en cada condición, 1/3 frente a 2/3 exigidos. En
610031 y 610047, la MSE relativa D tardía sigue por encima del predictor
cero; hubo 69/90 advertencias D/post de esa métrica. D usa trayectorias
nuevas, pero del mismo histórico: 2.823/5.760 inicios y
1.036.590/1.036.800 ocurrencias de transición coincidieron con muestras
de aprendizaje. Esto **no** prueba generalización temporal.

La aceptación metodológica formal requiere revisión: los 99 reportes
conservan `market_training_executed=false`, porque el marcador heredado
solo reconoce P0/P1, aunque los contadores, artefactos y perfiles muestran
aprendizaje P2R de mercado. El protocolo exigía corregir/verificar ese
campo antes de congelar el ejecutor. No se alteran reportes ni se repite la
campaña para ocultarlo. Tres commits documentales aparecen en metadatos de
checkpoint durante la corrida, pero las huellas de **código** fueron
idénticas en todos. Ningún resultado es confirmatorio ni demuestra
rentabilidad o cumplimiento poblacional de CVaR.

[Informe completo](P2R-ejecucion-historica-v2.md),
[comprobaciones y resultados](../evidence/p2r-market-2026-10-07/results.json),
[comandos](../evidence/p2r-market-2026-10-07/COMMANDS.md).
