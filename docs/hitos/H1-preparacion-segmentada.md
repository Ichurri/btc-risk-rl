# H1: preparación segmentada de desarrollo bajo B

Fecha: 17 de septiembre de 2026. Ejecución local Debian; no resultados remotos.
Estado: **datos aceptados técnicamente para desarrollo bajo ADR-004**. Este hito
no implementa el simulador, no entrena y no resuelve ADR-002.

## Entradas y aceptación

Solo se utilizaron los originales de `data/raw/development`, de
[2017-12-01, 2024-01-01) UTC. Se conservaron las 14 páginas y su manifiesto, cuya
huella SHA-256 es `5608f59ca77d73c2afe564f94a0eddc50d26a477f73b6d3e38a47d930a9fb807`.
La ruta compara esta identidad, las huellas de cada página y los timestamps/cierres
exactos contra el inventario versionado y las reaperturas del diagnóstico.
No se descargó ni modificó mercado; la rejilla de máscara no contiene precios
fabricados. `prepare-development` mantiene su rechazo estricto original.

La aceptación exige:

1. Mismas fuentes e inventario aprobado; sin anomalías adicionales ni OHLCV inválido.
2. Máscara exacta, segmentación contigua y características con reinicio y calentamiento.
3. Observaciones finitas, muestra de ajuste explícita y transformación recargada sin refit.
4. Índices exhaustivos de transiciones/episodios y validación cronológica completa.
5. Productos persistidos verificados, huellas válidas y cobertura idéntica al diagnóstico.

La preparación escribe estado pendiente, audita los CSV/JSON recargados y solo
entonces marca `accepted`. Cualquier fallo deja rechazo y evidencia del error.
`verify-segmented-development` vuelve a verificar en modo de solo lectura, sin fit.

## Resultados reales y comparación

| Medida | Entrenamiento | Validación |
|---|---:|---:|
| Barras nominales | 10956 | 2190 |
| Recibidas originales | 10940 | 2190 |
| Ausencias en máscara | 16 | 0 |
| Cierres abreviados en cuarentena | 20 | 0 |
| Reaperturas en cuarentena | 20 | 0 |
| Barras retenidas | 10900 | 2190 |
| Segmentos que intersectan la partición | 21 | 1 |
| Transiciones utilizables | 10054 | 2190 |
| Inicios posibles de 180 transiciones | 7048 | 2011 (solo diagnóstico) |
| Segmentos con al menos 180 transiciones | 15 | 1 |
| Ventanas de 180 sin solapamiento | 46 | 12 (solo diagnóstico) |

Los 186 registros originales de diciembre de 2017 siguen disponibles como contexto.
Las 56 exclusiones son intervalos: 16 no tenían fila; se ponen en cuarentena 40
filas recibidas. La máscara cubre 13332 aperturas, no 13332 barras inventadas.
Se conservan 13276 barras reales entre calentamiento, entrenamiento y validación.

**No hay diferencias respecto a los conteos ni a los límites de los segmentos del
escenario B del diagnóstico.** `diagnosis_comparison.json` registra `matched` y
una lista vacía de diferencias. El total de 7048 corresponde a ventanas solapadas,
no a muestras de mercado independientes. Sus objetivos distintos cubren 9733
transiciones; 321 transiciones de seis segmentos cortos no caben en episodios
completos. La aceptación no concatena esas ventanas en una rentabilidad continua.

Validación mantiene sus 2190 objetivos en un solo recorrido, con observación inicial
al cierre de la barra anterior. Los 2011 inicios y 12 ventanas son comparadores
aritméticos del diagnóstico; **no se generan episodios de evaluación de 180 pasos**.

## Características, ajuste y contrato para el futuro simulador

La primera observación finita de un segmento está en índice 42 (43 cierres);
la primera transición puntuable tiene objetivo en índice 43. Se requieren 223
barras para 180 transiciones y 181 estados. No se pasan interrupciones al cálculo
de indicadores ni al índice de episodios. Las características se calculan en float64.

La muestra de ajuste es `fit_observations.csv`: **10073 observaciones** con timestamp
en [2018-01-01, 2023-01-01), diez características finitas y una sola aparición por
fecha, incluidos segmentos cortos y estados terminales. El número supera en 19
las 10054 transiciones porque 19 segmentos reiniciados tienen una primera
observación finita antes de su primer objetivo puntuable; el segmento de 29 barras
no alcanza el calentamiento. El primer segmento ya dispone del contexto de 2017.
No se ajusta por frecuencia de uso en episodios ni se usan observaciones de validación.

`scaler.json` contiene medias, desviaciones poblacionales, columnas, fronteras y
conteo. Las columnas constantes usan escala 1. No hay clipping. La auditoría
comprueba esos momentos directamente y reutiliza el objeto persistido para
transformar; no llama a `fit`. Modificar validación en una prueba sintética no
cambia las características ni la muestra de entrenamiento.

Cada episodio contiene `segment_id`, observación inicial, primer/último objetivo
y 180 transiciones; todas sus fechas puntuadas pertenecen a entrenamiento. La
observación/contexto anterior a una frontera no puntúa retornos fuera de la partición.
Las barras originales, características y observaciones tienen timestamps explícitos:
no se debe interpretar su concatenación física en un CSV como continuidad temporal.

## Evidencia y reproducción

Producto real: `data/processed/segmented-B-h1/` (fuera de Git, incluido en el ZIP).
Evidencia pequeña versionada: `docs/evidence/segmented-h1/`.

```bash
uv run --frozen btc-risk prepare-segmented-development --output data/processed/segmented-B-h1
uv run --frozen btc-risk verify-segmented-development --prepared data/processed/segmented-B-h1
uv run --frozen btc-risk prepare-segmented-development --output artifacts/segmented-h1/reproduction
uv run --frozen python scripts/verify_installation.py --context local
```

Los destinos de preparación deben ser nuevos. En esta ejecución se configuró
`UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache`; no se instaló ninguna dependencia adicional.
La evidencia incluye logs de desarrollo (incluidos fallos corregidos), verificación
final, versiones, huellas de código, fuentes y derivados. La reproducción en otro
destino produjo productos idénticos byte por byte; solo la fecha del manifiesto
cambia. Las huellas originales coincidieron antes y después y con el diagnóstico.

Las pruebas adicionales usan precios **sintéticos**: exclusiones exactas, rechazos,
causalidad, calentamiento 222/223 barras, ajuste sin filtración, fronteras, protección
final antes de leer páginas, adulteración de archivos y fallos de aceptación.
La revisión independiente de código no encontró defectos materiales abiertos;
sus recomendaciones de casos de prueba y precisión documental se incorporaron.
Verificación local final: configuración válida, Ruff sin errores y **59 pruebas
aprobadas en 13.85 s**, todas con código de salida 0. Son 27 pruebas adicionales
respecto a las 32 del hito previo. La ejecución registra el commit base 108847e
y las huellas del código previo al commit de cierre.

## Límites y siguiente paso

La aceptación es de preparación temporal para desarrollo bajo B. No demuestra
negociabilidad de cada apertura ni causalidad operativa de todas las anomalías.
Persiste el sesgo de selección y la ausencia de exposición durante interrupciones.
No hay métricas de rentabilidad, piloto ni entrenamiento. El conjunto final no fue
leído, descargado o utilizado. Se preservan C0/C5/C10 y las particiones.

El siguiente hito es diseñar e implementar el simulador causal con contabilidad
float64, costos exactos y pruebas, usando los índices aceptados. No se comenzó aquí.
PPO/CVaR-PPO y entrenamientos continúan bloqueados por ADR-002.
