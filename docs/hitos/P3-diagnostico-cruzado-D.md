# P3 v1.1 — diagnóstico cruzado de críticos sobre D tardía

**Alcance:** solo lectura de la campaña aceptada P3, sin nuevas trayectorias ni actualizaciones. La decisión original sigue siendo **`review`**. Este cruce fue autorizado después del [diagnóstico pareado](P3-diagnostico-pares.md) y **no** es una regla nueva de selección, un resultado fuera de muestra ni una repetición de P3.

## Contrato del cruce y procedencia

Para cada semilla y condición se fijaron `k=7,8,9`, sin seleccionar iteraciones por resultado. `D_k` fue generado por `π_k`, identificada en el checkpoint `k`; el crítico **posterior** se tomó del checkpoint completo `k+1`. En cada `k`, ese crítico de β=0 y el de β=1 se evaluaron sobre el D original de β=0 y sobre el D original de β=1. Dentro de cada columna ambos críticos reciben exactamente las mismas observaciones y objetivos Monte Carlo. Las diagonales reproducen la evaluación *on-policy* aceptada; las celdas cruzadas son evaluaciones **fuera de la política que generó el lote**, aunque siguen usando únicamente el histórico de entrenamiento 2018–2022.

`MSE=Σ(V−G)²/n`; `Z=ΣG²/n` es la MSE del predictor cero **del lote de esa columna**; `sesgo=Σ(V−G)/n`. Las métricas se agrupan por sumas de observaciones, nunca por media de razones. Cada lote D tiene 64 trayectorias completas por iteración, **192/192** en la ventana y **34.560/34.560** observaciones; cada celda de una matriz tiene esa cobertura. En cada par ambos brazos usan las mismas 189 rutas de mercado únicas entre 192 extracciones con reemplazo. Coincidencia de rutas no implica igualdad de exposición, patrimonio, observaciones ni retornos. En el [JSON reproducible](../evidence/p3-cross-diagnostic/results.json) constan también razón exacta `MSE/Z`, sesgo normalizado, acumuladores y resultados por iteración.

Antes de calcular MSE se cotejaron las huellas del ledger y cierre, los 18 reportes finales aceptados, las huellas de los checkpoints correspondientes a `k=7..10`, identidad de política y crítico, procedencia `accepted_train_collection_only`, y los SHA-256, rutas, reloj, horizonte, continuidad y targets de **3.456 archivos D**. No se abrió el derivado histórico, CSV H1 compartidos, validación ni conjunto final. Las 54 celdas diagonales por iteración (18 brazos × tres `k`) reprodujeron SSE, `ΣG²` y suma de errores de los reportes originales; las 18 diagonales agregadas coincidieron con el ledger decisorio. El script falla cerrado ante una entrada incompleta o incompatible.

## Las nueve matrices 2×2

En cada celda se muestra **MSE / sesgo**. `Z_D0` y `Z_D1` son las referencias del predictor cero, comunes a las dos filas de su columna. Las cifras redondeadas son solo para lectura; el JSON conserva precisión completa. Fila = crítico posterior; columna = política que generó D.

### 710031 · C0 — Z_D0=0,00563975; Z_D1=0,00564194

| Crítico | D de β=0: MSE / sesgo | D de β=1: MSE / sesgo |
| --- | ---: | ---: |
| β=0 | 0,00561811 / +0,00091120 | 0,00562076 / +0,00088932 |
| β=1 | 0,00565285 / +0,01145819 | 0,00565503 / +0,01143679 |

### 710031 · C5 — Z_D0=0,00563501; Z_D1=0,00563714

| Crítico | D de β=0: MSE / sesgo | D de β=1: MSE / sesgo |
| --- | ---: | ---: |
| β=0 | 0,00561335 / +0,00090346 | 0,00561595 / +0,00088168 |
| β=1 | 0,00564808 / +0,01145567 | 0,00565020 / +0,01143438 |

### 710031 · C10 — Z_D0=0,00563729; Z_D1=0,00563944

| Crítico | D de β=0: MSE / sesgo | D de β=1: MSE / sesgo |
| --- | ---: | ---: |
| β=0 | 0,00561560 / +0,00090775 | 0,00561821 / +0,00088593 |
| β=1 | 0,00565036 / +0,01145737 | 0,00565250 / +0,01143602 |

### 710047 · C0 — Z_D0=0,00586892; Z_D1=0,00586896

| Crítico | D de β=0: MSE / sesgo | D de β=1: MSE / sesgo |
| --- | ---: | ---: |
| β=0 | 0,00627033 / −0,00285353 | 0,00627025 / −0,00284816 |
| β=1 | 0,00625914 / +0,00925646 | 0,00625916 / +0,00926184 |

### 710047 · C5 — Z_D0=0,00587329; Z_D1=0,00587328

| Crítico | D de β=0: MSE / sesgo | D de β=1: MSE / sesgo |
| --- | ---: | ---: |
| β=0 | 0,00627460 / −0,00285940 | 0,00627447 / −0,00285430 |
| β=1 | 0,00626336 / +0,00925480 | 0,00626332 / +0,00925991 |

### 710047 · C10 — Z_D0=0,00587232; Z_D1=0,00587232

| Crítico | D de β=0: MSE / sesgo | D de β=1: MSE / sesgo |
| --- | ---: | ---: |
| β=0 | 0,00627370 / −0,00285890 | 0,00627359 / −0,00285374 |
| β=1 | 0,00626243 / +0,00925384 | 0,00626241 / +0,00925902 |

### 710081 · C0 — Z_D0=0,00475938; Z_D1=0,00476137

| Crítico | D de β=0: MSE / sesgo | D de β=1: MSE / sesgo |
| --- | ---: | ---: |
| β=0 | 0,00515353 / −0,00295762 | 0,00515510 / −0,00294631 |
| β=1 | 0,00520097 / +0,00747419 | 0,00520286 / +0,00748514 |

### 710081 · C5 — Z_D0=0,00475917; Z_D1=0,00476109

| Crítico | D de β=0: MSE / sesgo | D de β=1: MSE / sesgo |
| --- | ---: | ---: |
| β=0 | 0,00515326 / −0,00295935 | 0,00515476 / −0,00294848 |
| β=1 | 0,00520063 / +0,00747356 | 0,00520244 / +0,00748410 |

### 710081 · C10 — Z_D0=0,00475854; Z_D1=0,00476049

| Crítico | D de β=0: MSE / sesgo | D de β=1: MSE / sesgo |
| --- | ---: | ---: |
| β=0 | 0,00515285 / −0,00295630 | 0,00515438 / −0,00294525 |
| β=1 | 0,00520024 / +0,00747302 | 0,00520209 / +0,00748373 |

## Resumen por bloque de semilla

Para cada semilla se agruparon **descriptivamente** las tres condiciones: 576 trayectorias y 103.680 observaciones por columna/celda. El bloque, no cada condición, es la unidad de resumen; esta agregación no crea tres réplicas independientes ni un contraste inferencial.

| Semilla | Z_D0 | Z_D1 | β0→D0 MSE / sesgo | β1→D0 MSE / sesgo | β0→D1 MSE / sesgo | β1→D1 MSE / sesgo |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 710031 | 0,00563735 | 0,00563951 | 0,00561569 / +0,00090747 | 0,00565043 / +0,01145708 | 0,00561831 / +0,00088564 | 0,00565258 / +0,01143573 |
| 710047 | 0,00587151 | 0,00587152 | 0,00627288 / −0,00285728 | 0,00626164 / +0,00925503 | 0,00627277 / −0,00285207 | 0,00626163 / +0,00926026 |
| 710081 | 0,00475903 | 0,00476098 | 0,00515321 / −0,00295776 | 0,00520062 / +0,00747359 | 0,00515475 / −0,00294668 | 0,00520246 / +0,00748433 |

**Hechos medidos:** en 710031 y 710081 el crítico β=1 tiene MSE mayor que β=0 sobre **ambos** D fijos; en 710047 tiene MSE menor sobre ambos, por apenas ~0,000011. El signo se conserva en C0, C5 y C10. En 710031, β=0 queda ligeramente por debajo de `Z` en ambos D; β=1 queda ligeramente por encima. En 710047 y 710081, ambos críticos quedan por encima de `Z` en ambos D. El sesgo β=1 es positivo en los tres bloques, mientras β=0 es pequeño positivo en 710031 y negativo en 710047/710081. El cruce muestra que el signo de la comparación entre críticos **no depende solo de cambiar el lote D propio por el del otro brazo**. No establece la causa de esa diferencia.

**Límite decisivo:** el crítico de un brazo se entrenó junto a su propia política; su evaluación con el D del otro brazo puede estar fuera de su distribución de cartera, aun cuando las rutas de mercado sean las mismas. Además, el crítico y la política de cada brazo evolucionaron juntos desde `k≥1`. Por tanto, comparar filas en una columna no aísla un efecto causal puro de `β V²` bajo una política fija. Tampoco mide generalización temporal: ambos D proceden del mismo histórico de entrenamiento. No se aplican umbrales nuevos a la matriz, no se eligen checkpoints ni se revisa `review`.

## Reproducción y límites

El [script](../evidence/p3-cross-diagnostic/analyze.py), [results.json](../evidence/p3-cross-diagnostic/results.json), [verificador de tablas](../evidence/p3-cross-diagnostic/check_report.py) y [COMMANDS.md](../evidence/p3-cross-diagnostic/COMMANDS.md) contienen el cálculo, los acumuladores exactos, rutas y pruebas. Entradas ancladas: ledger SHA-256 `86b111b5365cda1760441d2f73d42e0463a4b4b2a7ddbc6e0e41f2a78751fcfe`; [cierre](../evidence/p3-market-2026-10-13/final-closure.json) SHA-256 `1d96dd5ed2cb4af27a0f3993501ea7c40ece67ccc5862fe0f9d7b0049c033c6d`. Todos los D y checkpoints permanecen en `artifacts/p3-approved-v1`, fuera de Git, sin modificaciones. El informe se detiene en este diagnóstico; cerrar pilotos o congelar evaluación fuera de muestra requiere revisión posterior.
