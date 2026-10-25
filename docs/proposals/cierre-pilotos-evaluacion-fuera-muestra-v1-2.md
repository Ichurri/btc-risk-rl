# Cierre de pilotos y evaluación fuera de muestra — propuesta v1.2

**PROPUESTA PARA REVISIÓN, NO ADOPTADA. NO AUTORIZA ENTRENAMIENTO NI EVALUACIÓN.**
Antecedentes preservados: [v1](cierre-pilotos-evaluacion-fuera-muestra-v1.md)
y [v1.1](cierre-pilotos-evaluacion-fuera-muestra-v1-1.md), commit `842fdd1`.
Base de código `886e3bc`: el permiso operativo P3 está cerrado. La
[tesis de Google Drive](https://docs.google.com/document/d/1dNp8MbiV0Zqpu6S9-5u6vnL-R-v4YbYaR8g6232EBQ8/edit?usp=sharing)
se cotejó **en lectura** el 25/10/2026; Drive marcó modificación
`2026-10-25T00:51:58.069Z`. El [texto de reemplazo propuesto](cierre-pilotos-texto-tesis-v1-2.md)
no fue aplicado a la tesis. P0–P3 y sus artefactos permanecen intactos.

## 1. Diseño candidato y estimando

Proponer **36 bloques nuevos de semillas**, cada uno con C0, C5 y C10:
**108 corridas completas** de entrenamiento 2018–2022. Una configuración
común se decidiría y fijaría antes de consultar 2023: crítico ordinario
`β=0`, cuatro épocas, `K=10`, actor y Q/A/B de ADR-002, horizonte 180,
`γ=1`, costos, recompensa y cota común `d=−ln(0,90)` ya establecidos.
Mantener Q/B auxiliares de C0 y D64 **solo observacional** para conservar
el contrato temporal y la frontera `after_dual_and_D`; D no alimenta
gradientes, selección de checkpoints ni el contraste primario. No
reutilizar corridas P3; P3 `review` y P2R `review` descriptivo siguen
siendo desarrollo, y P2 sigue interrumpido. Esta configuración es una
**ruta candidata por continuidad**, no óptima ni aprobada.

El estimando primario conserva `S_anualizado=√2190·S_4h`, retornos
simples netos de cuatro horas, MAR=0 y desviación bajista sobre **todos**
los períodos. La anualización es convención de reporte, sin presuponer
independencia temporal. El efecto mínimo de interés **propuesto** es
`δ=+0,50` unidades de Sortino anualizado para la diferencia media pareada
C5−C0 o C10−C0. No modifica la nula estadística `E[Δ]≤0`; es un umbral
de relevancia para planificar precisión y recursos, no una cifra publicada
para BTC ni derivada de 2023. Con igual desviación bajista, significa
una mejora de media convencional equivalente a media desviación bajista
anualizada. Con desviaciones distintas esa traducción deja de ser exacta.

La unidad de inferencia es el **bloque de semilla**, condicionado a un solo
histórico final; 108 corridas no son 108 réplicas independientes de
mercado. El Sortino superior no demuestra cumplimiento poblacional de
CVaR a 180 transiciones. Se informarán también fallos y todos los
resultados desfavorables, sin seleccionar una semilla o condición.

## 2. Semillas, orden, checkpoint y evaluación

El [cálculo versionado](../evidence/pilot-closure-v1-2/costs.py) genera
36 semillas principales mediante
`1 + int(SHA256("btc-risk-rl/oos-v1.2/main/" + i:02d)[0:8]) mod (2³¹−1)`,
para `i=00…35`, con los primeros ocho **bytes** del digest interpretados
como entero sin signo big-endian. El [JSON de resultados](../evidence/pilot-closure-v1-2/results.json)
contiene la lista íntegra en orden y su SHA-256 canónico
`74785abcea1f1517818d92f7402dd21035f720a0efa8540d482d9e48e7a8523d`.
Son semillas **candidatas aún no adoptadas**, fijadas por una cadena
pública antes de consultar 2023, sin descarte por desempeño. El mismo
índice `i` empareja C0/C5/C10; streams Q/B de C0 no modifican el stream
A ni la parada. Cada condición conserva RNG y checkpoints propios.

Orden propuesto: bloques `i=00…35`, sin concurrencia; para `i mod 3=0/1/2`
usar respectivamente `C0,C5,C10` / `C5,C10,C0` / `C10,C0,C5`.
Los dos cortes *walk-forward* usan **tres semillas nuevas y separadas**,
generadas con el espacio `walk-forward` en el mismo algoritmo: `57739409`,
`803999499`, `76375890`. Se comparten entre cortes y condiciones, pero
no son réplicas de la inferencia final. Ambas listas son disjuntas entre
sí y de las semillas P0–P3 registradas. Antes de ejecutar habría que
ratificar y fijar el JSON, orden, código, fuentes y huellas en un protocolo
adoptado; este documento no habilita un ejecutor ni reabre P3.

De cada corrida elegir **solo el checkpoint completo al final de K=10**,
`after_dual_and_D`, con huellas verificadas. No escoger por MSE, B,
patrimonio, Sortino o CVaR. En evaluación usar la mediana determinista
de la logística-normal `sigmoid(μ(o))`, calculada de forma numéricamente
estable en el contrato de acción `[0,1]`, sin clipping silencioso; un
valor no finito o saturación no justificada falla la integridad. Esta
regla requiere implementación y pruebas **antes** de cualquier consulta
de 2023. Evaluación cronológica continua, una sola cartera por política,
reloj `h=1`, normalizador de entrenamiento congelado y ningún paso de
optimizador; es transferencia operacional, no una garantía de CVaR H180.

## 3. Sensibilidad de precisión para 36 bloques

Los pilotos no proporcionan una desviación de diferencias de Sortino
**fuera de muestra**. Los tres valores siguientes son **supuestos**, no
estimaciones. La potencia usa una aproximación normal unilateral para
`δ=0,50` y `α=0,025` (primer umbral de Holm), con 80 % como referencia;
el semiancho usa `z₀․₉₇₅ σΔ/√n`. El bootstrap real puede diferir.

| SD pareada supuesta `σΔ` | Semiancho normal 95 % con 36 | Potencia normal aproximada con 36 | Bloques aproximados para 80 % |
| ---: | ---: | ---: | ---: |
| 0,5 | 0,163 | 99,997 % | 8 |
| 1,0 | 0,327 | 85,1 % | 32 |
| 1,5 | 0,490 | 51,6 % | 71 |

La ruta de 36 bloques solo supera 80 % bajo el escenario `σΔ≈1` o menor.
No se presentará como 80 % de potencia verificada; si la revisión exige
esa potencia incluso con `σΔ=1,5`, 36 bloques no bastan. El tamaño no se
ajustará después de observar 2023 o el final. La inferencia sigue
condicionada al único período final y a la variación entre entrenamientos.

## 4. Dos cortes temporales auxiliares y uso de 2023

Sustituir **expresamente**, si se aprueba, el CPCV prometido por dos
diagnósticos retrospectivos *walk-forward* dentro de 2018–2022:
(a) ajustar 2018–2020 y observar 2021; (b) ajustar 2018–2021 y observar
2022. Purga de intervalos de información y separación previa de **180
velas de cuatro horas**, sin cruzar interrupciones; normalizador,
características, índices y agentes se reconstruyen y auditan **por corte**.
El índice H1 deja respectivamente 3.639 y 4.678 inicios H180 para
aprender, y 1.979 y 2.190 transiciones en los años observados. Son
**coberturas indexadas**, no rutas evaluadas. Se proponen tres semillas
de desarrollo por corte y condición: **18 entrenamientos adicionales**,
sin usar estos años para seleccionar retrospectivamente hiperparámetros
del contraste principal. Las puertas de los cortes son de **integridad,
cobertura y correspondencia temporal**, no de signo o magnitud financiera:
un rendimiento bajo se informa, sin cancelar selectivamente una
condición. Si una incidencia técnica exige rediseño, registrar todo lo
observado y proponer nueva versión antes de entrenar las 36 réplicas
principales. Dos cortes no producen los cuatro caminos CPCV ni
demuestran generalización temporal; los años ya participaron en el
desarrollo histórico.

La partición 2023 tendría **una sola comprobación técnica predefinida**
de las 108 políticas finales, sin gradientes, refit, selección de
semillas, checkpoints o hiperparámetros. Verificar recorrido continuo
completo, acciones y contabilidad válidas, retornos finitos, normalizador
congelado, huellas y Sortino definido (`σ₋>0`) **en cada corrida**.
Una sola falla detiene acceso al final; Sortino negativo o C5/C10<C0
no lo detiene ni permite cambiar la configuración. Si 2023 motiva un
rediseño, publicar lo visto y llamarlo **desarrollo observado**, no
validación independiente renovada. La prueba final 2024–2025 permanece
cerrada hasta protocolo y autorización separados.

## 5. Presupuesto global: medido, escalado y asignado

El [cierre P3](../evidence/p3-market-2026-10-13/final-closure.json)
**midió** para nueve corridas `β=0` 6.542,420 s de pared de unidad,
726,936 s/corrida en promedio; D incluido sumó 429,329 s. La campaña
de ambos brazos debitó 13.273,772 s frente a 13.235,325 s de unidades:
la diferencia observada fue 38,446 s, no una tasa validada de campañas
futuras. Multiplicar 726,936 por otras corridas es **extrapolación**;
el entrenamiento de cortes más cortos, su refit y la evaluación nunca
se midieron. Cada partida marcada «tope» es una **asignación propuesta**,
no un tiempo observado ni una garantía de suficiencia.

| Partida candidata | Base | Segundos | Horas | Naturaleza |
| --- | --- | ---: | ---: | --- |
| Entrenamiento principal | 36×3=108 corridas | 78.509 | 21,81 | Tasa P3 β0 extrapolada; D incluido. |
| *Walk-forward* 2021 | 3×3=9 corridas | 6.542 | 1,82 | Tasa extrapolada, refit fuera de esta línea. |
| *Walk-forward* 2022 | 3×3=9 corridas | 6.542 | 1,82 | Tasa extrapolada, duración real desconocida. |
| Comprobación técnica 2023 | 108 recorridos | 10.800 | 3,00 | Tope propuesto, **no medido**. |
| Evaluación final 2024–2025 | 108 recorridos, solo si autorizada | 10.800 | 3,00 | Tope propuesto, **no medido**. |
| Auditoría, preflight, refit por corte, inferencia y cierre | Campaña completa | 21.600 | 6,00 | Tope propuesto, **no medido**. |
| **Trabajo previsto** | 126 entrenamientos + evaluaciones | **134.794** | **37,44** | Suma de extrapolaciones y topes. |
| Reserva de cierre obligatoria | 17 días mínimos × 2.700 s/día | 45.900 | 12,75 | Margen, **no trabajo consumido**. |
| **Partidas más reserva, escenario mínimo** | 17 días activos | **180.694** | **50,19** | 17 ventanas de 3 h suman 183.600 s. |

Se propone mantener el máximo **global** de 10.800 s (3 h) por día
`America/La_Paz` para toda la actividad, incluidas cargas, auditorías,
evaluaciones, guardado y trabajo de otras campañas; reservar **2.700 s
por día** para cierre y admitir unidades solo dentro de los **8.100 s
productivos** restantes. No concurrencia. El escenario anterior ocupa
**como mínimo 17 días activos** a tasa y topes supuestos: 45.900 s de
reserva agregada y 180.694 s de partidas más reserva; las 17 ventanas
diarias suman 183.600 s, con solo 2.906 s productivos sin asignar.
Recomendación para revisión: **tope duro de 20 días activos nuevos**,
216.000 s globales como máximo (60 h), de los cuales 54.000 s son
reserva obligatoria y 162.000 s máximo productivo. Quedarían 27.206 s
productivos de contingencia frente al plan; no se reasignan entre
partidas automáticamente. Cada día se resta el consumo ya registrado,
se registran timestamps UTC y se pausa solo en frontera completa. Si
una unidad no cabe con su reserva, no se inicia; si vence el tope de
días o de una partida sin terminar, estado `incomplete` y revisión,
sin reducir réplicas ni ampliar límites por conveniencia.

**Prueba de estrés de alcance:** exigir 36 semillas en **cada** corte
auxiliar elevaría *walk-forward* a 216 entrenamientos, ~157.018 s
extrapolados y **35 días mínimos** para toda la propuesta bajo los mismos
topes, más que los 20 días sugeridos. Por tanto, esa variante **no cabe**
en el presupuesto candidato. Tampoco cabe el diseño principal en los
tres días activos de P3; aquella autorización terminó con P3 y no se
traslada. Los nuevos topes deben aprobarse antes de implementar.

| Escenario de costo | Entrenamientos principal + auxiliar | Trabajo previsto, extrapolado + topes | Días mínimos a 8.100 s productivos/día | Relación con el tope candidato de 20 días |
| --- | ---: | ---: | ---: | --- |
| 36 principales + 3 semillas por corte | 108 + 18 | 134.794 s | 17 | Cabe solo si tasas y topes se sostienen. |
| 36 principales + 36 semillas por corte | 108 + 216 | 278.727 s | 35 | No cabe. |
| 12 principales + 3 semillas por corte | 36 + 18 | 82.455 s | 11 | Cabe como exploración, sin inferencia confirmatoria. |

**Alternativa si 20 días/60 h no son financiables:** declarar una campaña
**exploratoria**, con 12 bloques nuevos C0/C5/C10 y los mismos tres
bloques auxiliares por corte: 36+18=54 entrenamientos. La suma
extrapolada más topes de evaluación/auditoría sería ~82.455 s
productivos, **11 días mínimos**; un eventual tope de 14 días implicaría
42 h globales y 10,5 h de reserva. Bajo `σΔ=1`, su potencia normal
aproximada para `δ=0,50` es ~41 % (con `σΔ=1,5`, ~21 %). Es un
**diagnóstico de desarrollo**, no sustituto confirmatorio de los 36
bloques, no una prueba de superioridad y no permiso para abrir el final.
Si tampoco cabe, detener el plan en vez de cambiar K, D o semillas.

Antes de proponer autorización operativa deberán medirse de forma
separada, bajo un protocolo posterior, costo de refit, carga, política
determinista, recorridos, auditoría, memoria y disco; fijar admisión y
parada basadas en esas mediciones. Esta v1.2 no ejecuta dicha calibración.

## 6. Fallos, inferencia y controles condicionados

El calendario y presupuesto se fijarían antes de ejecutar. Pausa
planificada solo en checkpoint completo; interrupción dentro de una
unidad invalida la corrida/campaña conforme al supervisor. Conservar
ledger, unidad parcial y checkpoints anteriores como evidencia, **sin
reanudar una campaña fallida ni reemplazar selectivamente semilla o
condición**. Nueva campaña, si procede, requiere revisión, raíz y
repetición íntegra del diseño; no completar parejas con restos previos.
Si `σ₋=0`, Sortino es **indefinido**; patrimonio no positivo, retorno
no finito o recorrido incompleto son fallos distintos. No imputar
0/∞, eliminar bloques ni sustituir corridas. Si falta un Sortino finito
en cualquiera de los 36 bloques tripletes, no emitir contraste primario
confirmatorio; informar todos los casos y someter nuevo protocolo a
revisión. Esta regla severa sigue siendo propuesta, pendiente de ratificar.

Con 36 bloques íntegros: `Δ5,i=S5,i−S0,i` y
`Δ10,i=S10,i−S0,i`. Proponer **19.999 remuestras** con RNG independiente
de semilla fija `910031`; en cada remuestra usar los **mismos 36 índices
de bloque** para ambos contrastes. Para el contraste `j`, centrar
`Δj,i−mean(Δj)` bajo la frontera nula y remuestrear esos valores;
calcular `p_j=(1 + #{b: mean(Δ*_{j,0,b}) ≥ mean(Δ_j)})/20.000`, donde
`Δ*_{j,0,b}` es la remuestra centrada `b`.
Aplicar Holm paso a paso a los dos p-valores, con familia unilateral
`α=0,05`; reportar p crudos y ajustados, medias, dispersión, intervalos
descriptivos de diferencias originales y todas las semillas. No
escoger otro bootstrap por significancia. El bootstrap mide variación
entre entrenamientos sobre **un histórico final fijo**.

PBO requiere una matriz comparable de alternativas y una regla de
selección in-sample con rankings out-of-sample; una sola configuración
no basta. DSR requiere Sharpe, momentos/longitud y número efectivo
auditable de ensayos; no corrige Sortino. Declarar cada uno
`no estimable` si faltan insumos, sin reportar cero ni fabricar una
distribución CPCV. El diagnóstico *walk-forward* y 2023 no se mezclan
con el contraste final. El acceso a 2024–2025 requiere después de la
revisión: tesis armonizada, protocolo congelado, ejecutor verificado,
presupuesto autorizado y permiso final separado.

## 7. Decisiones pendientes antes de cualquier ejecución

| Decisión para revisión | Candidato v1.2 | Puerta |
| --- | --- | --- |
| Configuración común | β=0, crítico4, K10, D64 observacional y resto de ADR-002. No óptima. | Adoptar antes de entrenar nuevas réplicas. |
| Tamaño y relevancia | 36 bloques; `δ=0,50` anualizado; aceptar limitación si `σΔ=1,5`. | Antes de generar resultados o abrir 2023. |
| Semillas y orden | Lista y hash del JSON; 3 semillas auxiliares distintas; rotación sin concurrencia. | Congelar en protocolo/ejecutor nuevos. |
| Dos cortes | 2021 y 2022, 180 velas, refit por corte, 3 semillas diagnósticas. | Enmendar §2.7.3/Tabla 4/§3.8.4 de tesis. |
| Presupuesto | 3 h globales/día, 2.700 s de reserva/día, candidato 20 días activos. | Medir costos faltantes y aprobar admisión; P3 no autoriza. |
| Acción/checkpoint | `sigmoid(μ)`, reloj `h=1`, frontera terminal K10 sin selección. | Implementar y verificar **antes** de 2023. |
| Rol 2023 | Una puerta técnica, sin selección ni umbral económico. | Reemplazar §2.7.2 y §3.8.4 antes de consultar. |
| Fallos/Sortino indefinido | Sin sustitución selectiva; no contraste primario si falta un triplete válido. | Ratificar antes de campaña/final. |
| Inferencia | Bootstrap 19.999, semilla 910031, bloque pareado, Holm 0,05. | Congelar antes del final. |
| PBO/DSR | Solo con insumos reales, o `no estimable` justificado. | Informe final. |

**No se adoptó ninguna de estas decisiones por redactar la v1.2.**
No se entrenó ni evaluó ninguna política, no se abrieron validación ni
prueba final y no se modificó la tesis ni los artefactos P0–P3.
