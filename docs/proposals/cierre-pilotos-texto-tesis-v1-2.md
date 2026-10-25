# Enmiendas exactas propuestas para la tesis — v1.2

**BORRADOR PARA REVISIÓN; NO APLICADO AL GOOGLE DOC.** Texto cotejado en
[la tesis vigente](https://docs.google.com/document/d/1dNp8MbiV0Zqpu6S9-5u6vnL-R-v4YbYaR8g6232EBQ8/edit?usp=sharing),
lectura 25/10/2026, modificación en Drive `2026-10-25T00:51:58.069Z`.
La [propuesta metodológica v1.2](cierre-pilotos-evaluacion-fuera-muestra-v1-2.md)
debe ser revisada antes de incorporar estas sustituciones. No alterar el
historial de resultados de Ingeniería del Proyecto.

## 1. Sustituir por completo §2.7.2

**La afirmación actual a retirar** es que validación 2023 «permite comparar
configuraciones y seleccionar una». La nueva función de 2023 no debe
describirse después como selección independiente.

### 2.7.2. Configuración previa y comprobación técnica de 2023

Los pilotos sobre entrenamiento 2018–2022 sirven para proponer una sola
configuración común a C0, C5 y C10. Antes de observar 2023 se registrarán
la configuración, las semillas, la regla de checkpoint terminal, la acción
de evaluación, el presupuesto, el efecto mínimo relevante y el análisis.
La ruta candidata usa crítico ordinario β=0, cuatro épocas y diez
iteraciones, sin que esos valores se consideren óptimos. La elección y
sus limitaciones se fundamentarán con los diagnósticos de desarrollo;
la partición 2023 **no** se usará para escoger hiperparámetros, semillas,
checkpoints o tratamientos.

Una sola consulta cronológica de 2023 verificará, bajo criterios fijados
antes, que todas las políticas completan su recorrido continuo con
contabilidad, acciones y retornos finitos, normalizador congelado,
huellas correctas y Sortino primario definido. Cualquier falla de
integridad o una desviación bajista nula detendrá el avance a 2024–2025.
El signo y tamaño del Sortino o de C5/C10 frente a C0 se informarán,
pero no actuarán como umbral para cambiar o repetir la configuración.
2023 no proporcionará el contraste principal ni una prueba CVaR
poblacional.

Si la comprobación técnica exige rediseñar, se conservará íntegramente
lo observado y se identificará cada decisión motivada por 2023. Este
período pasará a ser desarrollo observado y no volverá a describirse
como validación independiente del diseño nuevo. El período final
2024–2025 seguirá reservado; solo un protocolo ulterior, congelado
antes de abrirlo y autorizado por separado, podrá usarlo una vez.

## 2. Precisar §2.7.3 y Tabla 4 sin borrar la explicación bibliográfica

**La afirmación actual a retirar** es el cierre «Por este motivo se
adopta como mecanismo de control de sobreajuste del protocolo
experimental». CPCV puede explicarse como método de la literatura,
pero no atribuirse al diseño ejecutable de esta tesis.

**Sustituir el párrafo final de §2.7.3 por:**

> CPCV permite construir varios caminos de validación si se reentrenan
> políticas y transformadores en cada partición, se purgan las ventanas
> de información y se aplica un embargo. En este proyecto, la auditoría
> de índices encontró cobertura potencial para diez particiones, pero
> el costo y la reconstrucción exigida exceden el presupuesto candidato.
> Por ello se propone, como control auxiliar de **menor alcance**, un
> diagnóstico retrospectivo *walk-forward* de dos cortes exclusivamente
> en 2018–2022: ajustar 2018–2020 y examinar 2021, y ajustar 2018–2021
> y examinar 2022. Se purgarán ventanas solapadas, se separarán 180 velas
> antes del año examinado y se reajustarán normalizador y agentes por
> corte. Estos dos resultados descriptivos no reproducen los cuatro
> caminos nominales CPCV ni constituyen una validación independiente;
> tampoco sustituyen la evaluación final cronológica.

**Tabla 4:** conservar la fila CPCV como **alternativa teórica no
ejecutada**, eliminando cualquier marca que la declare adoptada.
Sustituir la fila genérica *Walk-forward* por:

| Esquema | Particiones | Controla la fuga temporal | Estimación que produce |
| --- | --- | --- | --- |
| Dos cortes *walk-forward* purgados de desarrollo | 2: ajuste anterior y examen posterior (2021, 2022) | Purga de información, separación de 180 velas y refit por corte | Dos diagnósticos retrospectivos descriptivos; no distribución CPCV ni prueba final. |

La explicación inmediatamente posterior a la tabla debe decir:
«CPCV ofrecería una distribución de caminos bajo su ejecución completa;
el control auxiliar propuesto aquí produce dos resultados cronológicos
de desarrollo. Se declara esta reducción de alcance y se mantiene
aparte la única prueba final reservada.»

## 3. Sustituir por completo §3.8.4

**Afirmaciones actuales a retirar:** «Los hiperparámetros comunes se
seleccionarán ... basada en validación» y «La CPCV se implementará ...
dentro ... 2018–2023». También se retira la descripción de entrenamiento
posterior a bloques evaluados, porque los dos cortes propuestos usan
solo información cronológicamente anterior.

### 3.8.4. Congelación previa, diagnóstico temporal y control de sobreajuste

Antes de consultar 2023 se propondrá y registrará una configuración
común a las tres condiciones, sin búsqueda basada en esa partición.
La candidata es β=0 para el crítico, cuatro épocas y diez iteraciones,
con el resto de ADR-002 y el simulador inalterado. El diseño de revisión
plantea 36 bloques nuevos de semillas, cada uno con C0, C5 y C10;
su efecto mínimo de interés es una diferencia de +0,50 unidades de
Sortino anualizado. Tanto las semillas como el número de bloques, el
presupuesto de tres horas globales diarias, la reserva, la acción
determinista, la frontera terminal y el procedimiento de fallos se
ratificarán y fijarán antes de entrenar. Las campañas P0–P3 no se
incorporarán como réplicas de este contraste.

El análisis temporal auxiliar se limita a 2018–2022 y emplea los dos
cortes de §2.7.3 con semillas de desarrollo separadas. Cada corte
reconstruirá segmentos y episodios elegibles, purgará ventanas de
información, aplicará una separación previa de 180 velas y reajustará
características, normalizador y agentes **solo** con su bloque anterior.
Se publicarán cobertura, exclusiones, resultados completos, costo y
fallos; no se compondrá una cartera ficticia al cruzar interrupciones.
Este análisis es retrospectivo y de desarrollo, **no CPCV** ni evidencia
confirmatoria de generalización temporal.

La consulta única de 2023 aplicará exclusivamente la puerta técnica de
§2.7.2 sobre políticas y normalizador congelados; no habrá gradientes,
selección de hiperparámetros, semillas o checkpoints. Si la puerta falla,
se detendrá el acceso final, se preservará todo lo visto y cualquier
rediseño reconocerá expresamente que 2023 ya participó en desarrollo.
Un resultado financiero desfavorable por sí solo no habilitará otra
búsqueda. La evaluación final 2024–2025 exige autorización separada y
el análisis pareado fijado antes de abrirla.

PBO solo se estimará con una matriz comparable de alternativas y una
regla auditada de selección dentro/fuera de muestra. DSR solo se
calculará si existen Sharpe, longitud, momentos y número efectivo de
ensayos; no corrige el Sortino primario. Si faltan los insumos se
informará «no estimable» y la causa, sin asignar cero ni fingir un
resultado CPCV.

## 4. Ajustes de coherencia necesarios si se adopta la v1.2

| Ubicación vigente | Ajuste propuesto, no aplicado |
| --- | --- |
| §3.5.2 | Sustituir la promesa de que `N` se fijará después de un piloto que estime variabilidad externa por: «Se propone `N=36` bloques pareados nuevos con sensibilidad explícita para SD supuesta 0,5/1,0/1,5; no existe aún una SD fuera de muestra medida. El tamaño se aprobará antes de consultar 2023 y no se aumentará por resultados.» |
| §3.9.2 | Fijar, si se ratifica, 19.999 remuestras con RNG 910031, remuestreo del bloque triplete, nula centrada por contraste, mismos índices para C5−C0 y C10−C0, prueba unilateral y Holm familiar 0,05. Aclarar que `δ=0,50` guía recursos, sin reemplazar la nula `E[Δ]≤0`. |
| §3.12.2 | Cambiar «configuración y costo de CPCV pendientes» por «decisión explícita sobre sustitución de CPCV por dos cortes purgados, implementación/refit por corte, costo medido, presupuesto y límites inferenciales pendientes de aprobación». |
| §4.3.3 y Tabla 15 | Mantener la auditoría histórica v1.1 como evidencia indexada. Añadir la **propuesta**, no una ejecución: 36 bloques principales, dos cortes auxiliares con tres semillas cada uno, costo mínimo ilustrativo de 17 días activos y tope propuesto de 20; 36 semillas por corte requerirían al menos 35 días bajo los supuestos. No escribir que *walk-forward* fue ejecutado o que CPCV dejó de existir como método teórico. |
| §3.8.5 | Mantener la puerta de prueba final; precisar que el checkpoint será solo el último K10 íntegro y la acción propuesta `sigmoid(μ)` se verificará antes de 2023. No declarar congelados esos valores mientras v1.2 esté en revisión. |

P2 `failed`, P2R `review` descriptivo y P3 `review` son hechos de
desarrollo, no observaciones fuera de muestra. La tesis solo debe
atribuir resultados *walk-forward*, 2023 o final **después** de su
ejecución autorizada y auditada.
