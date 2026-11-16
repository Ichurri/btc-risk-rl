# P3 — estudio pareado de regularización del crítico

**PROPUESTA PARA REVISIÓN; NO AUTORIZADA PARA IMPLEMENTACIÓN NI EJECUCIÓN.**
P3 sería una campaña nueva de **diagnóstico de desarrollo**, no una
continuación, reparación o repetición selectiva de P2/P2R. No se crea raíz,
registro de permiso ni comando habilitado en este hito. La motivación es el
[exceso de MSE D tardía](../hitos/P2R-error-valor-tardio.md) documentado
en P2R; por ello P3 tampoco aportaría evidencia confirmatoria.

## Hipótesis e intervención única

En P2R, el exceso `MSE_D−Z_D` de 610031/610047 se explica
aritméticamente por `E[V²]>2E[VG]`, sobre todo en el último tercio de
H180. Se **hipotetiza** que reducir la energía de salida del crítico
mejorará el error en D nueva del mismo histórico sin perder señal útil.
Comparar dos brazos nuevos; dentro de **cada brazo**, los dos términos de
su pérdida usan el mismo lote A y sus targets Monte Carlo congelados:

    β=0 (control): Lφ = mean_A[(Vφ(o)−G)²]
    β=1 (tratamiento): Lφ = mean_A[(Vφ(o)−G)² + Vφ(o)²]

La penalización se calcula en los mismos minibatches A del crítico, solo
durante sus cuatro épocas. No toca el actor, su pérdida, los coeficientes
de riesgo, el descuento gamma=1, el retorno H180, D ni el calendario
Q/A/B. Para un predictor funcional irrestricto, el óptimo de esa pérdida
sería `E[G|o]/(1+β)`; eso explica por qué β=1 es una prueba clara de
contracción, **no** promete que una red finita entrenada con Adam reduzca
sus predicciones a la mitad. La sensibilidad algebraica `V/2` sobre las
mismas D de P2R daría R tardía ≈0,941/0,978/0,837 por bloque de semilla;
es cálculo **retrospectivo**, no un agente reentrenado ni prueba de P3.
Los resultados P2R motivaron β=1 y los umbrales: P3 sigue siendo
exploración de desarrollo. No se probarían varios β ni se ajustaría β
durante la campaña.

Se descartó para este estudio aumentar de nuevo las épocas: P1 ya mostró
mejor ajuste sobre A, pero P2R con cuatro épocas mantuvo D débil. Doblar
el tamaño A cambiaría simultáneamente el muestreo del actor y el costo,
complicando una intervención centrada en la salida del crítico.

## Matriz, invariantes y comparabilidad

Tres **semillas nuevas** `710031`, `710047`, `710081`; en cada una C0,
C5 y C10 con los dos brazos β=0/1: **18 corridas K=10, 198 unidades**
completas (Q0 y diez Q/A/B+D por corrida), sin concurrencia. El orden
propuesto queda congelado antes de cualquier resultado:

| Semilla | Orden de condiciones | Orden de brazos dentro de cada condición |
| ---: | --- | --- |
| 710031 | C0 → C5 → C10 | C0: 0→1; C5: 1→0; C10: 0→1 |
| 710047 | C5 → C10 → C0 | C5: 1→0; C10: 0→1; C0: 1→0 |
| 710081 | C10 → C0 → C5 | C10: 0→1; C0: 1→0; C5: 0→1 |

Ambos brazos usan el derivado H1 exclusivo de entrenamiento 2018–2022,
7.048 inicios uniformes con reemplazo, normalizador fijo, mismo H3,
costos/recompensa, ADR-002, d=`−ln(0.90)` común a C5/C10, actor y
arquitectura 32/tanh, tasas, minibatch16, actor2 épocas, crítico4 épocas
**todavía provisionales**, Q0=400, cada k A64/Q400/B400 y D64. D conserva
π_k congelada, RNG propio, ambos críticos sobre los mismos objetivos,
y no alimenta ningún gradiente ni decisión de parada. C0 conserva Q/B
auxiliares y λ=0; ambas β consumen idénticos tamaños y número de pasos.
Totales si cierra la matriz: **162.720 trayectorias y 29.289.600
transiciones de aprendizaje**; **11.520 y 2.073.600 de D**; 1.440 pasos
de actor y 2.880 de crítico. Registrar costos de D y del nuevo término
por brazo, sin atribuir tiempos a componentes no medidos.

El RNG por semilla/rol/k permite cotejar inicios Q/A/B/D entre brazos en
la misma condición. Antes de actualizar el primer crítico deben coincidir
Q0, A inicial y actor después del primer paso de actor; comprobarlo
sintéticamente y en reportes. Desde k≥1 el crítico tratado altera las
ventajas y puede cambiar las políticas, acciones y objetivos: el contraste
posterior mide el **efecto total** de adoptar esa pérdida en el sistema,
no un efecto aislado del crítico bajo política fija. D de cada brazo debe
corresponder a su propia π_k. No mezclar resultados de P2R ni contar las
tres condiciones de una semilla como tres réplicas independientes.

## Métricas y decisión fijadas antes de ejecutar

Para cada corrida, agregar SSE, `ΣG²`, suma de errores y conteo de D/A
post sobre k={0,1,2} y k={7,8,9}, sin promediar razones. Publicar
`MSE`, `Z`, `R=MSE/(Z+10⁻¹²)`, sesgo normalizado, medias/SD de V y G,
tercios H180 y `MSE−Z=E[V²]−2E[VG]`, además de métricas pre, overlap,
eta/λ, shortfalls A, gradientes de riesgo y auditorías B. Z de D temprana,
D tardía y A tardía debe ser **>10⁻¹² por separado**. Los pares β=0/1
se comparan dentro de semilla y condición. El único criterio de avance
técnico de P3 es conjunto:

1. Las 18 corridas K10 y todos los D64/checkpoints cierran íntegros;
   marcador de mercado y guardas del supervisor correctos, sin no finitos,
   acceso prohibido, selección de checkpoint ni reintentos selectivos.
2. Para al menos **dos de tres bloques de semilla**, en **cada una de sus
   tres condiciones**, el brazo β=1 cumple simultáneamente:
   `R_D,post,tardía≤0,95`, diferencia pareada
   `R_β1−R_β0≤−0,05`, mejora del último tercio D tardío
   `R_β1−R_β0≤−0,10`, `R_A,post,tardía(β1)−R_A,post,tardía(β0)≤0,10`,
   `|sesgo_normalizado_D,post,tardía(β1)|≤0,25` y
   `R_D−R_A≤0,5` en β=1.

El margen `R≤0,95` exige mejoría material frente a cero y evita que un
crítico trivialmente nulo pase solo por no excederlo. Los umbrales de
0,05/0,10 son objetivos de ingeniería **propuestos antes de P3**,
informados por P2R y no significancia estadística. El bloque de semilla,
no el par condición-brazo, es la unidad de resumen. Si se cumplen ambas
puertas, estado `advance_to_discussion`; si hay 18 corridas íntegras pero
no, `review`. Una corrida incompleta o fallo de integridad da
`not_evaluable` para P3 y **detiene** la campaña; nunca se repite por
resultado desfavorable. Publicar todas las métricas de ambos brazos,
incluidos fallos. Ningún criterio demuestra generalización temporal,
rentabilidad o cumplimiento CVaR poblacional.

## Presupuesto, admisión y parada

Máximo **3 h globales por día** America/La_Paz, timestamps UTC, hasta
**tres días activos**, descontando campañas ajenas del mismo día; no se
reinicia el saldo al cambiar de corrida o proceso. Preflight ≤900 s,
trabajo ≤8.100 s/día y reserva de cierre 1.800 s/día. Mantener
admisión Q0=1.800 s e iteración=2.700 s antes de medición; D≤900 s
dentro de Q/A/B+D. Después, admitir solo si cabe 1,5×el máximo completo
observado del mismo tipo/condición **entre ambos brazos**, sin reducir
estimación por una unidad rápida ni elevar topes. Hasta tres sesiones por
corrida y 54 de campaña; un proceso a la vez, sin concurrencia. Conservar
umbrales P2R de CA, batería, memoria, disco, RSS, heartbeat y reloj.

P2R **midió** 6.893,096 s de débito global para 99 unidades en un día;
duplicarlo da 13.786,192 s como **escenario aritmético**, no estimación
validada de P3. El costo del término β, 18 corridas, cargas, pausas y
distribución diaria no se ha medido. La primera unidad programada mide
tiempo real y D; no se añade calibración con mercado ni se cambia el
diseño según esa medición. Si no cabe la siguiente unidad más reserva,
pausar **antes** de abrirla en `after_q0` o `after_dual_and_D`. Si se
agotan tres días/sesiones sin completar la matriz, `incomplete`, sin
ampliar límites. Señal, watchdog, heartbeat >5 s, no finito, identidad
incompatible, unidad parcial o pérdida de supervisor durante una unidad
dejan `failed` irreversible; conservar artefactos y no reanudar por tener
checkpoint anterior. P0/P1/P2/P2R siguen inmutables.

## Corrección prospectiva del marcador: condición previa, no implementación

Antes de congelar **un futuro ejecutor P3**, definir la semántica de
`market_training_executed` como «fuente aceptada de entrenamiento **y**
pasos de optimizador completados», no como pertenencia a una lista
incompleta de nombres de campaña. Q0 debe ser `false` porque solo recoge
Q/eta; cada Q/A/B+D histórica aceptada debe ser `true`. Un campo
separado podría registrar colección de trayectorias históricas Q0 para
evitar ambigüedad. La implementación candidata es una función pura
`marker(source_profile, actor_updates, critic_updates)` que exige
`accepted_train_collection_only` y ambos contadores positivos. Los
estados de optimizador y recursos del checkpoint deben concordar con los
contadores; un valor del marcador nunca reemplaza esa evidencia.

En el supervisor P3, `_verify_completion` deberá rechazar un reporte
Q0 con marcador `true` y un reporte de iteración con `false`, cotejando
perfil, unidad, deltas de recursos y checkpoint **antes** de aceptar la
frontera. El preflight sintético previo al permiso debe probar la matriz
Q0/iteración × fuente sintética/entrenamiento, incluyendo un `false`
malicioso en una unidad con pasos positivos, y confirmar fallo cerrado
sin ledger aceptado. Congelar código, tests, protocolo y huellas después
de esa verificación; solo entonces solicitar permiso separado de P3 y
repetir preflight del host. No se modifica el ejecutor P2R ni se reescribe
un solo reporte histórico en este hito.
