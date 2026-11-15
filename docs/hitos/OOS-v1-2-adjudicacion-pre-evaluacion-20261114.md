# Adjudicación previa al acceso de evaluación OOS v1.2

**Fecha:** 14/11/2026, `America/La_Paz`. **Estado:** decisión de trazabilidad
para abrir únicamente la comprobación técnica predefinida de 2023, sujeta a
permisos separados y preflight. No es una declaración de conformidad plena
de los cortes ni una selección de políticas.

## Entrenamiento principal y checkpoints

La auditoría del cierre [`57599b9`](../../reporte-codex.md) verificó 108/108
corridas, 36/36 ternas y 1.188/1.188 unidades aceptadas, sin pendiente.
El ledger principal tiene SHA-256
`c3e1d793997e6379739d01223876962260d988c892ed44c7b161878adfc81e6b`.
Se recalcularon las 1.188 huellas de `state.pt` y la cadena de 3.622 estados.
Los K10 están fijados por posición, sin mirar retornos de 2023 o 2024–2025.
La comprobación de roster de esta etapa volvió a confirmar esos 108 K10.

## Desviaciones heredadas

| Hecho | Evidencia | Tratamiento |
| --- | --- | --- |
| `wf-2021` original utilizó un bloqueo global anidado distinto del de preparación | [auditoría de ruta y presupuesto](OOS-v1-2-entrenamiento-ruta-presupuesto-20261111.md) | Sus 99 unidades y hashes se conservaron. 99/99 habrían cabido según reconstrucción, pero la exclusividad original no quedó demostrada. El corte se informa **solo como diagnóstico descriptivo**; no se usa como prueba de supervisión estricta ni para seleccionar K10. |
| El cargo conservador del 12/11 fue 51.223,830 s, 823,830 s sobre 50.400 s | [cierre principal](OOS-v1-2-entrenamiento-principal-cierre-20261114.md) | Los 38.973,205 s activos y la última unidad aceptada a las 13:09:39 no muestran una unidad admitida fuera de plazo. El exceso corresponde al cargo conservador hasta 16:34:51. Se conserva íntegro y se declara **desviación de presupuesto de cierre**, sin rebajar retrospectivamente el cargo. |

El perfil principal `main-2018-2022` no cargó pesos ni checkpoints de
`wf-2021`; su ledger, roster y fuente de entrenamiento exclusiva tienen
huellas independientes. Estas desviaciones no cambian el K10 fijado ni la
regla técnica de 2023. Sí limitan la afirmación de cumplimiento operativo
estricto de **toda** la campaña. Cualquier contraste final deberá mostrar
esta salvedad; no se presentará como protocolo ejecutado sin desviaciones.

## Puerta de 2023

Primero se autoriza, con huella de código y datos, una exportación exacta
de las 2.190 velas de 2023 y 43 velas de contexto desde H1; no se calcula
ninguna acción durante esa exportación. Un **segundo** permiso fija la huella
del manifiesto exportado y permite la comprobación técnica de las 108
políticas sobre un recorrido continuo cada una. Se usa el normalizador de
entrenamiento congelado. La puerta pasa únicamente si todos los recorridos,
acciones, patrimonio, costos, huellas y Sortino definido son íntegros. La
magnitud o signo de Sortino no decide qué checkpoint, semilla o configuración
conservar. Una falla cierra el paso a la prueba final y queda registrada.

La prueba final 2024–2025 sigue cerrada por un permiso independiente y por
la auditoría pendiente de su fuente. Esta adjudicación no afirma aún superioridad de C5/C10,
generalización temporal ni cumplimiento poblacional de CVaR.

## Comprobación documental de la tesis

Se leyó de modo **solo lectura** el documento de Drive
[`Santiago_Iturri_formato_UCB_preliminares`](https://docs.google.com/document/d/1dNp8MbiV0Zqpu6S9-5u6vnL-R-v4YbYaR8g6232EBQ8/edit),
versión mostrada con modificación `2026-11-15T02:19:19.634Z`. Sus secciones
2.7.2 y 3.8.4 ya describen 2023 como comprobación técnica de las 108
políticas, excluyen selección por rendimiento y reservan 2024–2025 para una
prueba confirmatoria separada. La sección 2.7.3 y la Tabla 4 explican que
los dos cortes cronológicos sustituyeron el CPCV inicialmente previsto; la
sección 3.8.5 fija K10, `sigmoid(μ)` y una cartera continua. Por tanto, la
armonización metodológica **del texto consultado** está presente. No se
editó el documento. El permiso final y la auditoría de su fuente continúan
siendo requisitos independientes.
