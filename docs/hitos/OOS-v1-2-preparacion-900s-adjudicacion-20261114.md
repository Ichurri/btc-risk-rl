# OOS v1.2 — adjudicación técnica del intento previo a unidad (14/11/2026)

## Hechos y alcance

La sesión `oos-v12-training.service` de las 07:41:08 (`America/La_Paz`),
`InvocationID=993794ee2b0d46abb5d350f063302211`, terminó con
`Result=exit-code` antes de iniciar otra unidad. La bitácora original cerró
`failed` a las 08:00:08,573568: **988,716483 s** medidos frente al límite
operativo de preparación de 900 s. Sus comprobaciones dieron `ready`:
suite 867,342799 s, Ruff 0,098453 s y preflight vigilado 44,072800 s.
La diferencia hasta 988,716483 s comprende carga, auditoría inicial y
contabilidad. El ledger principal quedó `ready`, cursor 103, **1.133/1.188**
unidades, `pending=null`; la última unidad aceptada y su checkpoint son
`run-102-C5-b0/10`, `state.pt` SHA-256
`dff17b3504b95cf30ad16ab93df571e856397486c25d5b73ad59b484219097c1`.
No hubo pasos de optimizador ni selección durante este intento. El sistema
rechazó el reingreso porque la bitácora genérica bloquea toda sesión `failed`.

## Decisión prospectiva limitada

La [adjudicación fijada](../protocols/OOS-v1-2-preunit-timeout-recovery-20261114.json)
reconoce **solo el hash del cierre fallido observado** si el mismo token tiene
suite, Ruff y preflight íntegros y `ready`. La fila `failed` permanece intacta;
el nuevo inicio registra `recovered_failed_sha256` en la cadena durable.
Otros fallos, sesiones huérfanas y ledgers `failed` o `incomplete` siguen
bloqueados. El tiempo original se carga íntegro. Además, se imputa de forma
conservadora todo el intervalo 08:00:08,573568–08:12:34 (745,426432 s) del
diagnóstico y corrección, sin duplicarlo con el ledger ni la bitácora.

El máximo **prospectivo de preparación** pasa a 1.200 s, a partir de los
988,716483 s observados y 211,283517 s de margen. El límite de la suite
individual es 1.050 s; un exceso total de preparación pasa a pausa previa
a unidad, conservando su cargo y exigiendo de nuevo las tres verificaciones.
No cambian 50.400 s globales por fecha, reserva de 2.700 s, máximos de Q0
(1.800 s) y Q/A/B+D (2.700 s), 20 días activos, orden, semillas, datos,
normalizador, parámetros ni criterios de análisis. La enmienda es operativa;
no valida resultados financieros ni habilita 2023 o 2024–2025.

## Huellas previas intocadas

| Evidencia | SHA-256 |
|---|---|
| Ledger principal antes y después del intento | `f2b8a639273f3fbdb2a3c7afa5d21d7a30dca6a16178b9748e87b47038b93215` |
| Bitácora del intento fallido | `786c2f0c3fe7fffcd75027ff09fb096c5571c01d029c6506e7761d3ac526f5eb` |
| Comprobaciones del intento | `39c05d395cc71b3818fb492ee536d848c3786d1121231e05e7d6060a9b77d957` |
| Último checkpoint aceptado | `dff17b3504b95cf30ad16ab93df571e856397486c25d5b73ad59b484219097c1` |

La decisión se aplica antes de admitir una nueva unidad. Repetir una unidad
aceptada o reanudar un estado parcial permanece prohibido.
