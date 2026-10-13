# P3 v1.1 — cierre histórico de diagnóstico de desarrollo

La campaña autorizada sobre el derivado H1 exclusivo de entrenamiento
2018–2022 terminó el **13/10/2026 a las 15:54:10 UTC**. El ledger quedó
`completed`, con 18/18 corridas K10 y 198/198 unidades aceptadas,
`pending=null`. La sesión 02
`p3-market-v1-session-02.service` (`InvocationID=629b6812dc79470e876a5ec7670e801a`)
salió con código 0 y `Result=success`. La sesión 01 había cerrado en
`ready` tras 116 unidades; la sesión 02 comenzó en `run-10-C0-b1`, unidad
6, y aceptó las 82 restantes. No se reutilizaron corridas P2R ni se
repitieron unidades por resultado.

El [preflight de sesión 02](../evidence/p3-market-2026-10-13/preflight-session02.json)
registró CA conectada, batería 100 %, memoria disponible 5.672.505.344 B,
disco libre 178.073.706.496 B, 10.800 s de presupuesto global del día,
7.048 inicios aceptados y cero aperturas de CSV H1 compartidos. Fue de
solo lectura: cero trayectorias y cero actualizaciones. La aprobación,
protocolo, configuración, código, derivado y ledgers previos pasaron las
guardas de huella. El preflight anterior del 09/10 quedó bloqueado por
alimentación y no consumió un día activo de P3.

La [auditoría de cierre](../evidence/p3-market-2026-10-13/final-closure.json)
comprobó íntegramente las cadenas de 601 estados de ledger y 3.609
eventos de journal, incluidos los prefijos originales de la sesión 01.
Cotejó las huellas de los 198 reportes y checkpoints completos, su orden,
sus contadores y el marcador `market_training_executed`: `false` en Q0,
`true` tras cada actualización. Recalculó la decisión a partir de los
reportes aceptados y obtuvo exactamente el resultado guardado. No hizo
pasos de optimizador ni abrió validación o prueba final. Los artefactos
voluminosos siguen en `artifacts/p3-approved-v1`, fuera de Git.

| Día America/La_Paz | Segundos globales debitados | Límite |
| --- | ---: | ---: |
| 08/10 | 8.016,088 | 10.800 |
| 13/10 | 5.257,683 | 10.800 |

La suma debitada fue 13.273,772 s en **dos días activos**, sin superar
las tres horas de ninguno. La pared de las 198 unidades sumó 13.235,325
s; las fases D de los 18 reportes finales sumaron 868,824 s. Son
mediciones de esta campaña, no extrapolaciones. Los contadores finales
fueron 162.720 trayectorias y 29.289.600 transiciones de aprendizaje;
11.520 trayectorias y 2.073.600 transiciones D; 1.440 pasos de actor y
2.880 del crítico. El máximo RSS de un trabajador registrado por el
supervisor fue 680.103.936 B. El journal de systemd de la sesión 02
informa un pico de cgroup de 4,1 G y 1 h 26 min 44,690 s de CPU;
representan alcances distintos de memoria.

La regla P3 v1.1 produjo **`review`**: ninguno de los tres bloques de
semilla superó conjuntamente las tres condiciones. Las nueve parejas
β=0/β=1 tuvieron `Z` elegible; en las nueve, el tratamiento no cumplió
la comparación exacta con el predictor cero en D tardía
`MSE≤0,95Z`, ni el límite de mejora pareada D tardía `ΔD≤−0,05`.
El resultado por pareja y cada puerta están en el cierre JSON. Las
advertencias de estabilidad de los 18 reportes finales sumaron 2.520
entradas (`critic_relative_mse`: 174 en `targets`, 2.346 en `critic`);
son diagnósticos, no fallos de integridad, y no se sumaron los reportes
intermedios que repiten advertencias acumuladas. Las tres condiciones de
una semilla **no** constituyen réplicas independientes.

`review` es un **diagnóstico de desarrollo sobre el mismo histórico de
entrenamiento**. No demuestra generalización temporal, rentabilidad,
superioridad frente a C0 ni cumplimiento poblacional de CVaR. Tampoco
autoriza elegir retrospectivamente checkpoints o modificar P3. La
evaluación confirmatoria y el conjunto final siguen pendientes de un
protocolo y autorización separados.

Huellas SHA-256 del cierre: ledger
`86b111b5365cda1760441d2f73d42e0463a4b4b2a7ddbc6e0e41f2a78751fcfe`;
journal supervisor
`3edba2fc24bbf6288423d6f0fad90e40d2d8db361dbf505ba9634f6738076b82`;
[cierre JSON](../evidence/p3-market-2026-10-13/final-closure.json)
`1d96dd5ed2cb4af27a0f3993501ea7c40ece67ccc5862fe0f9d7b0049c033c6d`.
