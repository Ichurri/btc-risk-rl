# Evaluación fuera de muestra: prórroga y armonización pendiente

**PROPUESTA PARA REVISIÓN ACADÉMICA; NO ADOPTADA.** Preparada el 06/11/2026.
Santiago eligió **prorrogar la evaluación confirmatoria** para conservar los
36 bloques principales y los límites presupuestarios de la [v1.2](cierre-pilotos-evaluacion-fuera-muestra-v1-2.md).
No se toma el 16/11 como permiso para reducir semillas, omitir controles o
abrir anticipadamente la prueba final. La fecha extendida concreta debe
acordarse con el tutor. Esta decisión de calendario no adopta por sí sola
las decisiones científicas de la v1.2.

## Estado que debe conocer el tutor

La [tesis en Drive](https://docs.google.com/document/d/1dNp8MbiV0Zqpu6S9-5u6vnL-R-v4YbYaR8g6232EBQ8/edit?usp=sharing),
modificada por última vez el **06/11/2026 a las 19:08:42 UTC** según Drive,
todavía presenta en §2.7.2 la validación como medio de comparar y seleccionar
configuraciones; en §2.7.3 conserva CPCV como control considerado. §3.8.4
describe expresamente dos rutas, la inicial y la v1.2 aún no adoptada. §4.4
declara pendiente el objetivo 4. Esas afirmaciones son coherentes con el
estado actual, pero tendrían que cambiar **antes** de tratar 2023 como puerta
técnica y de sustituir CPCV por dos cortes *walk-forward*.

La v1.2 prevé 108 entrenamientos principales (36 semillas × C0/C5/C10),
18 auxiliares de desarrollo (3 semillas × 2 cortes × 3 condiciones), una
comprobación técnica 2023 y la prueba final 2024–2025. Usa una configuración
común candidata `β=0`, cuatro épocas de crítico, `K=10`, `D=64`
observacional; checkpoint completo final y acción determinista
`sigmoid(μ)`. Su estimando primario es la diferencia pareada del Sortino
anualizado. P2R y P3 `review` siguen siendo diagnóstico de desarrollo, no
evidencia confirmatoria. La medición real del costo 2022 todavía está
bloqueada por alimentación desconectada; no se ha iniciado ninguna unidad.

El cálculo v1.2 tiene **134.794 s** de trabajo extrapolado o asignado y
requiere al menos **17 fechas activas** a 8.100 s productivos por fecha,
dejando 2.700 s de reserva dentro de las 3 h globales. Hasta el 16/11 hay
como máximo 11 fechas locales contando el 06/11. La prórroga preserva el
diseño; no convierte estas extrapolaciones en tiempos medidos ni garantiza
que 20 fechas activas basten. El costo del corte 2022 debe actualizar esa
cuenta antes de fijar el calendario definitivo.

## Cambios académicos concretos a decidir

| Sección actual | Cambio propuesto antes de abrir 2023 o la prueba final | Condición |
| --- | --- | --- |
| §2.7.2 | Mantener la explicación general de selección con validación, pero aclarar que **este estudio** fijará una sola configuración con evidencia de desarrollo 2018–2022 y usará 2023 solo para una puerta técnica predefinida, sin elegir hiperparámetros, semillas ni checkpoints. La prueba final sigue reservada. | Aprobación expresa del tutor; no describir 2023 como validación independiente reutilizable tras rediseño. |
| §2.7.3 y Tabla 4 | Conservar CPCV como método de referencia, eliminar cualquier promesa de ejecutarlo en este estudio y declarar su sustitución por dos cortes retrospectivos purgados 2021/2022. Los dos cortes no entregan caminos CPCV ni validación temporal independiente, porque sus años ya formaron parte del desarrollo. | Registrar alcance reducido y costo de reentrenamiento; revisar la tabla comparativa y cualquier referencia a CPCV ejecutado. |
| §3.8.4 | Sustituir las dos rutas condicionales por una regla cerrada: tres semillas auxiliares disjuntas, refit de normalizador y agente por corte solo con el pasado, separación de 180 velas, cobertura y correspondencia temporal como puertas; resultados financieros de los cortes no seleccionan la configuración. | Ratificar los detalles de v1.2 antes de ejecutar más réplicas. |
| §3.8.5 y §3.9 | Fijar código/datos/semillas/orden, checkpoint `K=10`, acción `sigmoid(μ)`, continuidad de cartera, métrica primaria, fallos, bootstrap pareado unilateral 19.999 remuestras y Holm 0,05. PBO/DSR solo con insumos reales; de lo contrario `no estimable`. | Congelar antes de observar 2023; acceso final separado tras auditoría de integridad y presupuesto. |
| §4.3–§4.4 | Informar el costo 2022 y las futuras corridas como evidencia de ejecución, manteniendo P2R/P3 en `review`. Hasta existir contraste final, el objetivo 4 y la hipótesis principal siguen pendientes. | No convertir pilotos o costo en rentabilidad o cumplimiento CVaR. |

El [texto de tesis v1.2 ya propuesto](cierre-pilotos-texto-tesis-v1-2.md)
sirve como base de edición. Debe cotejarse con la versión actual del Drive
antes de aplicarlo; esta nota **no modifica** la tesis.

## Puertas de aceptación del protocolo confirmatorio

1. Tutor y tesista aceptan el reemplazo explícito de CPCV, el papel técnico
   de 2023 y la prórroga. Se registra la versión adoptada sin reescribir las
   propuestas previas.
2. El estudio exclusivo 2022 termina con ledger íntegro o se informa
   `incomplete/failed`; su costo observado y sus reservas se incorporan al
   presupuesto sin escoger resultados de rendimiento.
3. Se congelan 36 semillas principales, tres auxiliares, configuración,
   reglas de fallos, métricas, inferencia, código, índices, normalizadores y
   acciones **antes** de abrir 2023. Ninguna condición pierde corridas por
   un resultado desfavorable.
4. Se verifica la ruta de evaluación continua con datos sintéticos y luego
   la única puerta técnica 2023, sin gradientes ni selección. Un fallo de
   integridad o Sortino indefinido detiene el acceso al final; el signo del
   rendimiento no lo detiene.
5. La prueba final 2024–2025 se abre una sola vez, bajo permiso propio,
   después de cerrar el protocolo y el presupuesto. Si cualquier resultado
   posterior motiva rediseño, se declara exploratorio y no una nueva prueba
   independiente.

**Decisión pendiente del tutor:** aprobar o corregir los cambios de
§2.7.2, §2.7.3/Tabla 4 y §3.8.4, junto con una fecha de entrega extendida.
Hasta esa decisión, la evaluación confirmatoria no se declara iniciada.
