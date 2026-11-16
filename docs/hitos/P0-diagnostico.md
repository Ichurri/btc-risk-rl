# P0 — diagnóstico de crítico y activación del riesgo

**Conclusión: comportamiento explicado, sin defecto operativo demostrado en los cálculos examinados.** El crítico mejora su MSE en el mismo A pero permanece peor que el predictor cero. C0/C5 de semilla 410031 coinciden porque la penalización del actor fue cero en ambas iteraciones, por motivos distintos. Persiste incertidumbre sobre generalización y aprendizaje prolongado; no se ejecutaron actualizaciones nuevas.

Base local/remota verificada: e0a2dfca508902c00d94848fa4ebbcb071fb5c25. Rama `codex/p0-diagnosis`. Se conserva `.python-version` eliminado previamente, sin incluirlo en commits. Algoritmo operativo, d, protocolo, tesis y evidencia P0 intactos.

## Procedencia y reconstrucción

Se leyeron los 27 checkpoints de frontera (Q0, después de iteración 0 y después de iteración 1) de las nueve corridas, sin escoger por rendimiento. Carga directa `torch.load(weights_only=True)` tras verificar hashes; no se invocó el cargador de reanudación, ni el ejecutor, ni sus journals. Se bloquearon Adam.step y SGD.step en el proceso diagnóstico. Autograd calculó derivadas con parámetros fijos, sin optimizadores.

Se reconstruyeron exclusivamente los 18 lotes **A originales** (1152 trayectorias, 207360 transiciones reproducidas para diagnóstico, no nuevas muestras de entrenamiento), mediante los mismos pesos, índices, semillas por rol/iteración y simulador. No se reconstruyeron Q/B: eta, lambda y auditorías se leyeron de sus registros. TrainingMarket mantiene acceso solo a 2018–2022; sin validación/final.

Correspondencia comprobada en los 18 lotes: rutas e identidades de realización/política exactas; diagnóstico agregado de recolección idéntico; **fixed_digest exacto** de observaciones, acciones, log-probabilidades, retornos, valores, ventajas, coeficientes y constantes. La pérdida del primer minibatch del actor coincide exactamente y su norma de gradiente coincide con tolerancia 1e-12. Los hashes de todos los archivos de campaña coinciden antes/después, al igual que código operativo y artefactos de cierre.

## Las 162 advertencias: momento y alcance

Cada corrida registra 18: nueve por iteración, 1 del lote A completo + 8 de minibatch. Hay 18 mediciones `targets` y 144 `critic`, todas con razón >1. Iteraciones **0 y 1** en tablas corresponden a primera y segunda actualización.

| Registro | Datos | Pesos evaluados | Momento del registro |
|---|---|---|---|
| targets / critic_mc_mse_before | A entero, 64×180 transiciones | Crítico de inicio, antes de actor y crítico | Antes de actualizar |
| critic / mc_mse, pasos 0…7 | 16 trayectorias completas ×180, dos épocas | Antes del paso Adam actual; ya incorporan pasos previos | Se añade al log después de Adam, pero loss.detach() conserva el valor anterior |
| post-A de este diagnóstico | El mismo A entero | Checkpoint después de los ocho pasos | Reconstruido ahora, no estaba en el log P0 |

MSE = media((G−V)²); denominador = media(G²)+1e-12. El denominador es el MSE del predictor cero más estabilizador, **no varianza**, ni pérdida total del episodio, ni escala reajustada. G son retornos restantes Monte Carlo en las 180 posiciones. Las mediciones de minibatch cambian tanto pesos como subconjunto/denominador: no deben interpretarse como curva de evaluación sobre una muestra fija. Los pesos intermedios no están guardados; no se reconstruyeron mediante pasos Adam. Por eso no se pueden recuperar sus predicciones completas ni vectores de gradiente exactos. Se conservan MSE/normas originales y se reconstruyen exactamente sus denominadores e índices.

### Comparación sobre A fijo, por corrida e iteración

| Corrida | Semilla | k | MSE antes | MSE después | Denominador | Razón antes → después |
|---|---:|---:|---:|---:|---:|---|
| run-00-C0 | 410031 | 0 | 0.03927896 | 0.01766925 | 0.00605263 | 6.4896 → 2.9193 |
| run-00-C0 | 410031 | 1 | 0.01883558 | 0.00988183 | 0.00474408 | 3.9703 → 2.0830 |
| run-01-C5 | 410031 | 0 | 0.03927896 | 0.01766925 | 0.00605263 | 6.4896 → 2.9193 |
| run-01-C5 | 410031 | 1 | 0.01883558 | 0.00988183 | 0.00474408 | 3.9703 → 2.0830 |
| run-02-C10 | 410031 | 0 | 0.03927896 | 0.01766925 | 0.00605263 | 6.4896 → 2.9193 |
| run-02-C10 | 410031 | 1 | 0.01883558 | 0.00988183 | 0.00474408 | 3.9703 → 2.0830 |
| run-03-C5 | 410047 | 0 | 0.09093033 | 0.04338899 | 0.00460969 | 19.7259 → 9.4126 |
| run-03-C5 | 410047 | 1 | 0.03917358 | 0.01724370 | 0.00892136 | 4.3910 → 1.9329 |
| run-04-C10 | 410047 | 0 | 0.09093033 | 0.04338899 | 0.00460969 | 19.7259 → 9.4126 |
| run-04-C10 | 410047 | 1 | 0.03917358 | 0.01724370 | 0.00892136 | 4.3910 → 1.9329 |
| run-05-C0 | 410047 | 0 | 0.09093033 | 0.04338899 | 0.00460969 | 19.7259 → 9.4126 |
| run-05-C0 | 410047 | 1 | 0.03917358 | 0.01724370 | 0.00892136 | 4.3910 → 1.9329 |
| run-06-C10 | 410081 | 0 | 0.08553469 | 0.03684419 | 0.00493065 | 17.3476 → 7.4725 |
| run-06-C10 | 410081 | 1 | 0.04052538 | 0.01798767 | 0.00536399 | 7.5551 → 3.3534 |
| run-07-C0 | 410081 | 0 | 0.08553469 | 0.03684419 | 0.00493065 | 17.3476 → 7.4725 |
| run-07-C0 | 410081 | 1 | 0.04052538 | 0.01798767 | 0.00536399 | 7.5551 → 3.3534 |
| run-08-C5 | 410081 | 0 | 0.08553469 | 0.03684419 | 0.00493065 | 17.3476 → 7.4725 |
| run-08-C5 | 410081 | 1 | 0.04052538 | 0.01798767 | 0.00536399 | 7.5551 → 3.3534 |

### Predicciones y targets (medias por transición)

Las tres condiciones coinciden aquí para cada semilla/k: primera iteración usa lambda=0; el segundo A se genera antes de la primera actualización que puede llevar riesgo activo. El crítico separado usa ese A original y targets sin penalización. Las diferencias del actor al final de k=1 todavía no generan otro A en K=2.

| Semilla | k | Media G | Media V antes | Media V después |
|---|---:|---:|---:|---:|
| 410031 | 0 | -0.014388 | 0.110040 | 0.034547 |
| 410031 | 1 | -0.014766 | 0.050564 | -0.014334 |
| 410047 | 0 | -0.016338 | -0.252044 | -0.173018 |
| 410047 | 1 | -0.034472 | -0.166647 | -0.100713 |
| 410081 | 0 | -0.023785 | 0.103945 | 0.040979 |
| 410081 | 1 | -0.004223 | 0.029386 | -0.007765 |

El MSE cae en **18/18** comparaciones sobre A fijo, entre 47.5% y 56.9%, pero todas las razones posteriores siguen >1. Las medias iniciales muestran desajuste de escala/sesgo respecto a G; no basta mirar la media: por ejemplo semilla 410031, k=1, las medias se acercan pero la razón sigue 2.083. El JSON incluye desviación estándar, extremos y segundo momento de predicciones/targets.

**Evidencia:** aprendizaje del crítico reduce error in-sample en estas fronteras; las 162 alertas son compatibles con mejora y no prueban divergencia. **Hipótesis pendiente:** dos épocas/ocho pasos por iteración pueden ser insuficientes para este ajuste inicial. No se ha demostrado que aumentar épocas mejore generalización, varianza del actor o resultados económicos. No hay comparación fuera de muestra.

## Riesgo del actor y coincidencia C0/C5

Se verificó D_ij = (G_ij−V_ij) − (lambda/alpha) max(L_i−eta,0), L_i=−G_i0. Eta/lambda se leen de la frontera **anterior**, no de la auditoría que viene después del actor. B puede exceder d aunque A no tenga pérdidas mayores que eta: son lotes diferentes y d no es el umbral de shortfall.

En la primera iteración lambda=0 en todas las condiciones, aunque haya shortfalls. En la segunda:

| Corrida | lambda utilizado | eta | n shortfall /64 | Penalización máxima | Norma Δgradiente riesgo¹ | Cambio actor L2² |
|---|---:|---:|---:|---:|---:|---:|
| run-00-C0 | 0.000000000 | 0.234530612 | 0 | 0.000000000 | 0.000000000 | 0.005073736 |
| run-01-C5 | 0.017980103 | 0.234530612 | 0 | 0.000000000 | 0.000000000 | 0.005073736 |
| run-02-C10 | 0.014594454 | 0.199310909 | 4 | 0.004754791 | 0.006633975 | 0.005068684 |
| run-03-C5 | 0.015397907 | 0.211233570 | 6 | 0.035712615 | 0.094912622 | 0.004821504 |
| run-04-C10 | 0.011512138 | 0.182405719 | 9 | 0.016668846 | 0.046036712 | 0.004837099 |
| run-05-C0 | 0.000000000 | 0.211233570 | 6 | 0.000000000 | 0.000000000 | 0.004850584 |
| run-06-C10 | 0.014312546 | 0.163651295 | 11 | 0.015648105 | 0.046380357 | 0.006108263 |
| run-07-C0 | 0.000000000 | 0.198910931 | 5 | 0.000000000 | 0.000000000 | 0.006096688 |
| run-08-C5 | 0.018253964 | 0.198910931 | 5 | 0.027042061 | 0.063449415 | 0.006108596 |

¹ Diferencia de gradientes de la pérdida PPO con/sin penalización, sobre A entero y pesos de **inicio** congelados; es un diagnóstico reconstruido, no un paso original ni toda la trayectoria de Adam. Los ocho registros originales por iteración de pérdida/norma/clipping y el primer gradiente comprobado se incluyen en JSON. ² Diferencia real entre checkpoints de inicio/fin; no actualización realizada por este diagnóstico.

Para **C5/410031**, lambda=0.01798010270375307, eta=0.23453061174429735 y **máximo L de A=0.23189034740200398 < eta**. Los 64 shortfalls son cero: D coincide exactamente con las ventajas y la contribución de riesgo al surrogate es cero para cualquier peso durante todas las épocas, porque D permanece congelado. La primera iteración también coincide con C0 por lambda=0.

La igualdad no se deduce solo del hash final: se verifican parámetros del actor y estados Adam idénticos C0/C5 en **las tres fronteras**, todos los registros de pérdida/norma/clipping de los 16 pasos originales iguales y el primer gradiente reconstruido idéntico. Los actores sí cambiaron respecto de su inicio; C5 no quedó inactivo como optimizador. No se dispone de vectores de todos los gradientes intermedios: su igualdad se explica por los mismos inputs, pesos iniciales, Adam y orden determinista; las normas originales y fronteras la respaldan.

En las otras **cinco corridas C5/C10**, k=1 tiene shortfalls, coeficientes distintos de las ventajas y diferencia de gradiente de riesgo no nula al inicio. Se verifica activación real del término, no se infiere del incumplimiento de B. Esto no demuestra que la actualización reduzca CVaR. Para 410047/410081, C0/C5 son iguales hasta checkpoint-1 y distintos en parámetros y Adam al final.

## Conclusión y límites

- **Comportamiento explicado:** igualdad C0/C5/410031 por shortfall nulo en A y lambda inicial cero; no defecto demostrado de cableado del riesgo.
- **Comportamiento explicado:** alertas del crítico evalúan error relativo al predictor cero; caen los errores sobre A fijo pero permanecen altos. El momento de escritura del log no convierte la pérdida en postactualización.
- **Limitación instrumental demostrada:** no se guardaban MSE final sobre A fijo, predicciones detalladas ni pesos de minibatch. Este diagnóstico recupera fronteras/targets, sin atribuir reconstrucciones a mediciones originales.
- **Incertidumbre pendiente:** precisión del crítico fuera de A, eficacia poblacional del riesgo, evolución más allá de K=2. No hay convergencia ni cumplimiento CVaR demostrado; d se conserva.

## P1 candidato — no autorizado ni ejecutado

Intervención única propuesta: comparar **2 frente a 4 épocas del crítico**, manteniendo actor, arquitectura, tasas, N_A=64/N_Q=N_B=400, K=2, gamma, calendario, d y demás reglas P0. Hipótesis: más pasos del crítico reducen el error sobre A fijo; no se presume beneficio financiero ni generalización. Instrumentar antes/después sobre el mismo A, medias/dispersiones de V/G, denominadores y conteos de shortfall/coefficient delta/gradiente inicial de riesgo.

Diseño candidato acotado: semillas nuevas 510031/510047/510081; bloques C0-C5-C10 / C5-C10-C0 / C10-C0-C5; dos brazos por condición en orden 2→4 para semillas primera/tercera y 4→2 para segunda. Total 18 corridas, K=2; pares con mismas semillas/streams, sin concurrencia. Ambos brazos mantienen el mismo presupuesto de trayectorias, pero el brazo 4 consume el doble de pasos del crítico: contabilizarlo explícitamente, no declararlo igual cómputo. Aplicar presupuesto global 3h/día, límites/márgenes P0 y primera medición conservadora de la nueva unidad; no extrapolar un tiempo garantizado.

Criterio técnico prepropuesto: al terminar la **primera** actualización (mismo A en ambos brazos), reducción de MSE post-A de al menos 20% respecto al brazo 2 en al menos dos de tres semillas, sin no-finitos ni fallo de integridad. Comprobar igualdad del actor tras esa primera actualización como control negativo. Las tres condiciones comparten esa comparación por construcción: no contarla como nueve réplicas independientes. Registrar k=1 como diagnóstico secundario; no usar B para seleccionar checkpoints. Si el criterio no se cumple, rechazar esta hipótesis acotada; si se cumple, solo acredita mejora in-sample, no autoriza experimento confirmatorio. No variar d, N_A ni otros parámetros para forzar shortfalls. Cualquier ejecución P1 requiere autorización aparte.

## Evidencias y comprobaciones

[Reconstrucción y resultados](../evidence/p0-diagnosis/results.json), [162 métricas](../evidence/p0-diagnosis/metrics.csv), [script](../evidence/p0-diagnosis/reconstruct.py) y [comandos](../evidence/p0-diagnosis/COMMANDS.md). Se ejecutaron 16 pruebas algebraicas/analíticas sin pasos de optimizador. No se ejecutó la suite completa, porque incluye actualizaciones de aprendizaje excluidas por esta solicitud.
