# Diagnóstico histórico y propuesta de tratamiento — 17 de septiembre de 2026

Estado: diagnóstico completado con causas parcialmente identificadas. Política propuesta, NO aplicada. Datos aún no aceptados. No se cambió configuración, fuente, particiones ni datos originales. No hubo entrenamiento ni acceso al test final.

## Conteos y reglas

Se esperan seis aperturas UTC por día (00, 04, 08, 12, 16, 20). Intervalos semiabiertos:

| Partición | Fechas UTC | Días | Esperadas | Recibidas | Ausentes | Cierre abreviado |
|---|---|---:|---:|---:|---:|---:|
| Calentamiento | 2017-12-01 → 2018-01-01 | 31 | 186 | 186 | 0 | 0 |
| Entrenamiento | 2018-01-01 → 2023-01-01 | 1826 | 10956 | 10940 | 16 | 20 |
| Validación | 2023-01-01 → 2024-01-01 | 365 | 2190 | 2190 | 0 | 0 |
| Total desarrollo | 2017-12-01 → 2024-01-01 | 2222 | 13332 | 13316 | 16 | 20 |

13332 = 2222 × 6 = 186 + 10956 + 2190. El año bisiesto 2020 está incluido.
Ausente: apertura esperada sin registro. Abreviado: campo 6 menor que apertura + 14400000 − 1 milisegundos. Son 36 intervalos distintos, sin superposición, agrupados en 20 bloques: cada bloque comienza con un cierre abreviado y puede continuar con huecos. Los 20 abreviados SÍ forman parte de las 13316 filas recibidas.

## Diagnóstico: evidencia frente a causa

- API: 36 reconsultas previas reprodujeron las anomalías (recheck.json); eso verifica persistencia, no causa.
- Archivos mensuales Binance: 18 ZIP con checksums verificados; las 16 aperturas también faltan allí. De las 20 filas abreviadas, 18 coinciden en los primeros 11 campos; dos difieren exclusivamente en close_time. OHLCV coincide en las 20.
- Diferencias de metadatos: 2018-02-08 00:00 tiene cierre API 00:28:14.788 y archivo 03:59:59.999; 2019-11-25 00:00 tiene cierre API 01:59:59.999 y archivo 03:59:59.999. No se sustituyó ningún valor.
- Contexto horario de la misma API: las 20 agregaciones OHLCV de 1h reproducen las velas 4h abreviadas. En los 16 huecos 4h no aparecen registros 1h. No se utilizó esa agregación para producir datos de entrenamiento.
- Esto aporta evidencia contra un error exclusivo de paginación o parseo del descargador. No prueba que los sistemas del proveedor carezcan de errores históricos. Archivo y API no son fuentes independientes: Binance documenta que los archivos kline proceden de su API [S1].
- Timestamps de este período: milisegundos Unix, apertura en campo 0 y cierre en campo 6; conversión explícita UTC y paso de 14400000 ms. No se detectó un desplazamiento de zona horaria. El cambio a microsegundos de archivos spot desde 2025 [S1] no afecta a este diagnóstico y no se leyó ese período.
- La regla actual de cierre exacto es un requisito del modelo de barras completas, no una prueba universal de corrupción. Una vela histórica finalizada durante una interrupción no es una vela actual todavía abierta. El texto genérico del validador mezcla ambas clases de irregularidad; se documenta aquí sin relajar el bloqueo.

### Documentación causal conservadora

| Bloque | Evidencia documental | Alcance de la conclusión |
|---|---|---|
| 2020-06-28 | Aviso oficial de suspensión spot desde 02:00 UTC [S2] | Evento programado coincidente con cierre 01:59:59.999. La duración estimada no demuestra hora efectiva de reapertura. |
| 2021-09-29 | Aviso oficial de actualización completada y reapertura 09:00 UTC [S3] | Interrupción documentada. La etiqueta 4h 08:00 no equivale a poder ejecutar a las 08:00. El contexto 1h reaparece a las 09:00. |
| 2019-11-13, 2019-11-25, 2020-04-25 | Canal oficial de anuncios API conserva referencias a avisos y finalización [S4] | Corroboración documental de eventos; no reconstrucción de horarios exactos. Algunos enlaces antiguos no devolvieron el artículo. |
| Demás 15 bloques del inventario | API, archivos y contexto horario; sin aviso causal plenamente verificado en esta entrega | Interrupción o característica del histórico del proveedor es una hipótesis compatible. Causa operativa específica no confirmada. |

No se declara que las 36 anomalías sean interrupciones demostradas ni que sean universalmente irrecuperables. No fueron recuperables por las vías consultadas. Un aviso de mantenimiento de atención al cliente, por sí solo, no demuestra suspensión spot. Tampoco se tomó una página genérica redirigida como evidencia de un evento.

## Inventario íntegro (UTC)

Todas las marcas siguientes son UTC. El CSV adjunto incluye cierre nominal y regla por registro.

| Apertura UTC | Tipo | Cierre recibido UTC |
|---|---|---|
| 2018-01-04 00:00:00 | Abreviado | 2018-01-04 03:00:14.838 |
| 2018-02-08 00:00:00 | Abreviado | 2018-02-08 00:28:14.788 |
| 2018-02-08 04:00:00 | Ausente | — |
| 2018-02-08 08:00:00 | Ausente | — |
| 2018-02-08 12:00:00 | Ausente | — |
| 2018-02-08 16:00:00 | Ausente | — |
| 2018-02-08 20:00:00 | Ausente | — |
| 2018-02-09 00:00:00 | Ausente | — |
| 2018-02-09 04:00:00 | Ausente | — |
| 2018-06-26 00:00:00 | Abreviado | 2018-06-26 01:59:59.999 |
| 2018-06-26 04:00:00 | Ausente | — |
| 2018-06-26 08:00:00 | Ausente | — |
| 2018-07-04 00:00:00 | Abreviado | 2018-07-04 00:22:25.551 |
| 2018-07-04 04:00:00 | Ausente | — |
| 2018-10-19 04:00:00 | Abreviado | 2018-10-19 05:59:59.999 |
| 2018-11-14 00:00:00 | Abreviado | 2018-11-14 01:59:59.999 |
| 2018-11-14 04:00:00 | Ausente | — |
| 2019-03-12 00:00:00 | Abreviado | 2019-03-12 01:59:59.999 |
| 2019-03-12 04:00:00 | Ausente | — |
| 2019-05-15 00:00:00 | Abreviado | 2019-05-15 02:59:59.999 |
| 2019-05-15 04:00:00 | Ausente | — |
| 2019-05-15 08:00:00 | Ausente | — |
| 2019-08-15 00:00:00 | Abreviado | 2019-08-15 01:59:59.999 |
| 2019-08-15 04:00:00 | Ausente | — |
| 2019-11-13 00:00:00 | Abreviado | 2019-11-13 01:59:59.999 |
| 2019-11-25 00:00:00 | Abreviado | 2019-11-25 01:59:59.999 |
| 2020-02-19 08:00:00 | Abreviado | 2020-02-19 11:35:32.286 |
| 2020-02-19 12:00:00 | Ausente | — |
| 2020-04-25 00:00:00 | Abreviado | 2020-04-25 01:59:59.999 |
| 2020-06-28 00:00:00 | Abreviado | 2020-06-28 01:59:59.999 |
| 2020-12-21 12:00:00 | Abreviado | 2020-12-21 13:47:20.521 |
| 2021-02-11 00:00:00 | Abreviado | 2021-02-11 03:40:54.773 |
| 2021-04-20 00:00:00 | Abreviado | 2021-04-20 01:59:59.999 |
| 2021-04-25 04:00:00 | Abreviado | 2021-04-25 04:00:58.146 |
| 2021-08-13 00:00:00 | Abreviado | 2021-08-13 01:59:59.000 |
| 2021-09-29 04:00:00 | Abreviado | 2021-09-29 06:59:59.999 |

## Política recomendada: B, cuarentena y segmentos para entrenamiento

Conservar todos los originales; crear posteriormente una máscara derivada que identifique los 16 huecos, 20 abreviados y las 20 primeras velas posteriores a esos bloques. Excluir estas últimas es una precaución uniforme ante reaperturas internas, no una afirmación de que todas estén mal. Reiniciar el cálculo de indicadores al comenzar cada segmento y prohibir transiciones entre segmentos. Mantener missing_bar_policy=fail hasta acordar e implementar una ruta explícita de preparación segmentada.

Alternativa A: excluir solo las 36 anomalías. Gana poca cobertura y deja el problema de la vela de reapertura. No se recomienda para ejecución estricta a apertura siguiente.

### Impacto cuantificado en entrenamiento

| Escenario | Barras retenidas | Segmentos | Transiciones tras calentamiento | Inicios de 180 pasos | Segmentos aptos | Ventanas sin solapamiento |
|---|---:|---:|---:|---:|---:|---:|
| Rejilla ideal contrafactual | 10956 | 1 | 10956 | 10777 | 1 | 60 |
| A: 36 intervalos | 10920 | 21 | 10073 | 7063 | 15 | 46 |
| B: 56 intervalos | 10900 | 21 | 10054 | 7048 | 15 | 46 |

La rejilla ideal es una referencia aritmética, no un dataset rellenado. Las ventanas sin solapamiento tampoco son observaciones independientes de mercado.

El retorno de 42 barras requiere 43 cierres para la primera observación válida. Dentro de un segmento nuevo, primera observación en índice 42 y primera transición valorable en índice 43. Así, un segmento aislado necesita 223 barras para 180 transiciones; hay max(0, n−222) inicios. El contexto contiguo previo a la frontera de entrenamiento/validación puede calentar indicadores sin puntuar retornos fuera de la partición. Por eso diciembre de 2017 evita perder los primeros 43 objetivos de enero de 2018. Los límites start/end de impact.json describen el segmento de contexto; raw_partition_bars y usable_transitions están recortados a cada partición. Ninguna ventana de entrenamiento cruza 2023-01-01.

B retiene 99.49% de las barras nominales; permite 91.77% de transiciones. Se pierden 902 objetivos: 56 por cuarentena/ausencia y 846 por contexto insuficiente. Frente a la rejilla ideal hay 3729 inicios menos (34.60%). Los seis segmentos cortos aportan 321 transiciones que no entran en episodios completos; la unión de objetivos alcanzables por episodios de 180 pasos es 9733 (88.84% del calendario nominal). No confundir 7048 inicios solapados con 7048 historias independientes. Los 186 registros de calentamiento original se conservan.

### Evaluación y carteras

Validación 2023 permanece íntegra: 2190 barras y 2190 transiciones posibles usando contexto previo. Una cartera nueva al inicio, un solo recorrido, valoración final sin venta obligatoria. No se reinicia cada 180 pasos. Esto es viabilidad temporal, no resultados de una estrategia.

En entrenamiento, cada episodio comenzaría explícitamente con 10000 USDT y cero BTC, como ya se propuso. No se construirá una curva de rentabilidad de 2018–2022 concatenando episodios ni reiniciando carteras entre segmentos sin declarar. Esos datos representarían ventanas de períodos contiguos elegibles; el riesgo durante interrupciones queda fuera y puede haber sesgo de selección. El tamaño de muestra baja de forma desigual por período.

No se acepta excluir huecos de una evaluación y anualizar como si se hubiese negociado todo el calendario. Si una futura partición de evaluación tiene interrupciones, se bloqueará su evaluación continua hasta especificar contabilidad y tiempo real; no se elegirán nuevas fechas mirando rendimiento, no se imputará retorno cero ni se reiniciarán carteras automáticamente. Una evaluación por segmentos, si se acordara, se reportaría por segmento con exposición temporal y cobertura, sin llamarla rentabilidad continua. El test final sigue sin inspeccionarse.

### Qué falta para aceptar y programar el simulador

La aprobación metodológica de B debe quedar registrada antes de aplicarla, por solicitud expresa del usuario. Después: máscara con motivo y segmento, características causales por segmento, normalizador ajustado exclusivamente a observaciones elegibles de entrenamiento con criterio de ajuste explícito, índice de episodios, verificación de no cruce y reporte de cobertura. La auditoría realizada se centra en las 36 anomalías detectadas: no certifica que toda vela con cierre nominal carezca de interrupciones internas ni asegura negociabilidad en cada milisegundo de apertura.

CVaR-PPO continúa bloqueado por ADR-002. La selección de segmentos no resuelve descuento, horizonte y bootstrap.

## Fuentes consultadas el 17-09-2026

- [S1: Binance Public Data](https://github.com/binance/binance-public-data): esquema, procedencia de klines, checksums y posible revisión de archivos.
- [S2: aviso de actualización spot de 28-06-2020](https://www.binance.com/en/support/articles/a9d34695cd9345c7a648a882fcd3bcc0): suspensión programada desde las 02:00 UTC.
- [S3: actualización completada de 29-09-2021](https://www.binance.com/en/support/announcement/detail/f72eb94584fa47a586127ff5149ef83c): reapertura anunciada a las 09:00 UTC.
- [S4: canal Binance API Announcements](https://t.me/s/binance_api_announcements?before=33): referencias históricas conservadas; se usa solo para los eventos mencionados, no horarios inferidos.

## Evidencias reproducibles

- inventory/inventory.csv: 36 filas, reglas y cierres exactos.
- inventory/impact.json: conteos y 21 segmentos por escenario.
- archive-comparison.json: hashes, presencia y diferencias de campos de 18 meses.
- hourly-comparison.json: 20 consultas y agregaciones diagnósticas.
- offline-verification.json: reproducción exacta del inventario/impacto y hashes de 38 archivos diagnósticos.
- data/diagnosis/: respuestas y ZIP originales de corroboración, incluidos en el paquete y fuera de Git ordinario.
- Scripts de diagnóstico no generan características aceptadas ni entrenan.
