# P3 v1.1 — estudio pareado de regularización del crítico

**PROPUESTA PARA REVISIÓN; NO AUTORIZADA PARA IMPLEMENTACIÓN NI EJECUCIÓN.**
Esta revisión sustituye las reglas métricas imprecisas de la
[propuesta v1](P3-protocolo-v1.md), que se conserva como antecedente. No
modifica resultados ni reportes P2R. Las [diferencias exactas](P3-v1-1-cambios.md)
y el [resumen académico](../hitos/P3-v1-1-resumen-academico.md) acompañan
la propuesta completa.
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
mismas D de P2R daría razones tardías ≈0,941/0,978/0,837 por bloque de
semilla, según el cálculo retrospectivo con estabilizador de P2R;
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
**todavía provisionales**, Q0=400, cada k A64/Q400/B400 y D64. En cada
brazo, D se genera con su propia π_k congelada y un RNG separado. El
crítico **de ese mismo brazo**, antes y después de actualizarlo, se
evalúa sobre las mismas observaciones y objetivos Monte Carlo de su D.
La frase «ambos críticos» se refiere a esos dos estados del crítico
dentro de un brazo; no exige que β=0 y β=1 compartan trayectorias ni
objetivos D. D no alimenta ningún gradiente ni decisión de parada. C0
conserva Q/B auxiliares y λ=0; ambas β consumen idénticos tamaños y
número de pasos.
Totales si cierra la matriz: **162.720 trayectorias y 29.289.600
transiciones de aprendizaje**; **11.520 y 2.073.600 de D**; 1.440 pasos
de actor y 2.880 de crítico. Registrar costos de D y del nuevo término
por brazo, sin atribuir tiempos a componentes no medidos.

El RNG por semilla/rol/k permite cotejar inicios Q/A/B/D entre brazos en
la misma condición, sin garantizar que sus trayectorias coincidan. Antes
de actualizar el primer crítico deben coincidir
Q0, A inicial y actor después del primer paso de actor; comprobarlo
sintéticamente y en reportes. Desde k≥1 el crítico tratado altera las
ventajas y puede cambiar las políticas, trayectorias y objetivos de
β=0 y β=1: el contraste posterior mide el **efecto total** de adoptar
esa pérdida en el sistema,
no un efecto aislado del crítico bajo política fija. Cada D debe evaluar
la política π_k de su propio brazo. No mezclar resultados de P2R ni contar las
tres condiciones de una semilla como tres réplicas independientes.

## Métricas y decisión fijadas antes de ejecutar

Para cada semilla `s`, condición `c`, brazo `b∈{0,1}`, lote `X∈{A,D}`
y ventana `w`, reunir sobre observaciones individuales **post** los
acumuladores `n`, `SSE=Σ(V−G)²`, `Q=ΣG²` y `E=Σ(V−G)`; no promediar
razones de iteración ni de trayectoria. Las ventanas de iteraciones
temprana `k={0,1,2}` y tardía `k={7,8,9}` y los tres tercios disjuntos de
60 transiciones del H180 conservan etiquetas distintas. Cuando se
cruzan ventana y tercio, agregar solo las observaciones de esa
intersección. En cada conjunto no vacío:

    M = SSE/n,       Z = Q/n,       ē = E/n,
    R₀ = M/Z,        B₀ = ē/√Z                 si Z>0,
    Rε = M/(Z+ε),   ε = 10⁻¹²                  solo descriptivo.

`R₀` compara exactamente con el predictor constante cero **para los
targets del mismo brazo y conjunto**: su MSE es `Z`. El sesgo normalizado
`B₀` tiene signo; la puerta usa `|B₀|`. Si `Z=0`, `R₀` y `B₀` son
indefinidos, incluso si `M=0`. Si `0<Z≤ε`, son algebraicamente definidos,
pero **no elegibles para decidir** por señal de target insuficiente. No
reemplazar ese estado por `Rε`, cero ni infinito. Si `n=0` o hay valores
no finitos, no se calculan cocientes y se registra el fallo de integridad.
Se publican `M`, `Z`, `ē`, `R₀` y `B₀` donde estén definidos; `Rε` puede
publicarse junto a ellos como puente descriptivo con P2R, etiquetado
sin uso decisorio. Las comparaciones se hacen con sumas sin redondear;
el redondeo es solo para tablas.

Publicar además medias y desviaciones estándar de `V` y `G`, la
descomposición `M−Z=E[V²]−2E[VG]`, métricas pre, overlap, η/λ,
shortfalls A, gradientes de riesgo y auditorías B. Cada razón adicional
que se informe debe nombrar su numerador, denominador y conjunto de
observaciones. Los momentos medios usan `n>0`; una desviación estándar
muestral requiere `n≥2` y, si no, es indefinida. `M−Z` es diferencia
absoluta, no razón, y sigue definida con `Z=0` si `n>0`. No usar `Rε`
para inferir mejora frente a cero, diferencias pareadas ni brecha D−A.

Las siguientes puertas de información se exigen **por separado en cada
brazo** de cada par `(s,c)`:

    Z(D,post,temprana,b) > ε;
    Z(D,post,tardía,b)  > ε;
    Z(A,post,tardía,b)  > ε;
    Z(D,post,tardía,tercio 3,b) > ε.

La última puerta no se deduce de `Z(D,post,tardía,b)>ε`: un último
tercio sin señal puede quedar oculto por los dos anteriores. No se exige
una puerta para A temprana, que no interviene en la regla conjunta; si se
publica su razón o sesgo, se aplican los mismos casos indefinidos. D
temprana se conserva para interpretar evolución, aun cuando no integra
un contraste de avance. Las puertas no son pruebas estadísticas.

Definir **sin ambigüedad** las diferencias pareadas usando `R₀` calculado
con el `Z` propio de cada brazo, porque las políticas y por tanto los
targets pueden divergir después de `k=0`:

    ΔD = R₀(D,post,tardía,β=1) − R₀(D,post,tardía,β=0);
    ΔD₃ = R₀(D,post,tardía,tercio 3,β=1)
          − R₀(D,post,tardía,tercio 3,β=0);
    ΔA = R₀(A,post,tardía,β=1) − R₀(A,post,tardía,β=0);
    H₁ = R₀(D,post,tardía,β=1) − R₀(A,post,tardía,β=1).

La pareja es una misma semilla y condición con sus dos brazos completos;
no restar MSE absolutas ni reutilizar el `Z` de un brazo para el otro.
`H₁` es una brecha descriptiva entre lotes diferentes, no una estimación
de generalización temporal. Si falla una puerta de `Z`, el contraste
que la requiere queda **no informativo**, no se le asigna un número ni
se lo sustituye por otra ventana.

El único criterio de avance técnico de P3 es conjunto:

1. Las 18 corridas K10 y todos los D64/checkpoints cierran íntegros;
   marcador de mercado y guardas del supervisor correctos, sin no finitos,
   acceso prohibido, selección de checkpoint ni reintentos selectivos.
2. Para al menos **dos de tres bloques de semilla**, en **cada una de sus
   tres condiciones**, se cumplen las cuatro puertas `Z>ε` en **ambos**
   brazos y simultáneamente:
   `M(D,post,tardía,β=1)≤0,95 Z(D,post,tardía,β=1)`,
   `ΔD≤−0,05`, `ΔD₃≤−0,10`, `ΔA≤0,10`,
   `|B₀(D,post,tardía,β=1)|≤0,25` y `H₁≤0,5`.

La primera desigualdad es una comparación **exacta** contra el predictor
cero y, con `Z>ε`, equivale a `R₀≤0,95`. Un crítico idénticamente nulo
tiene `M=Z>0`, por lo que la incumple. En cambio,
`Rε=Z/(Z+ε)≤0,95` puede cumplirse incluso con `Z>ε`; el estabilizador
de v1 no descarta ese predictor. Los umbrales 0,95/0,05/0,10/0,25/0,5
son objetivos de ingeniería **elegidos tras ver P2R y antes de P3**,
no significancia estadística. El bloque de semilla, no el par
condición-brazo, es la unidad de resumen; exigir las tres condiciones
del bloque evita contar nueve réplicas independientes.

Si se cumplen ambas puertas, estado `advance_to_discussion`; si hay 18
corridas íntegras pero una puerta informativa falla o una desigualdad
no se alcanza, `review`, indicando cada métrica no informativa. Una
corrida incompleta o fallo de integridad da `not_evaluable` para P3 y
**detiene** la campaña; nunca se repite por resultado desfavorable.
Publicar todas las métricas de ambos brazos, incluidos fallos. Ningún
criterio demuestra generalización temporal, rentabilidad o cumplimiento
CVaR poblacional.

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

## Corrección prospectiva del marcador: requisito previo, no implementación

Antes de implementar la ruta histórica de **un futuro ejecutor P3**,
resolver y verificar el marcador y el rechazo por el supervisor; este
documento solo especifica el requisito. Definir la semántica de
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
frontera. La verificación sintética previa a la integración histórica y
al permiso debe probar la matriz
Q0/iteración × fuente sintética/entrenamiento, incluyendo un `false`
malicioso en una unidad con pasos positivos, y confirmar fallo cerrado
sin ledger aceptado. Congelar código, tests, protocolo y huellas después
de esa verificación; solo entonces solicitar permiso separado de P3 y
repetir preflight del host. No se modifica el ejecutor P2R ni se reescribe
un solo reporte histórico en este hito.
