# P2R v2 — por qué D tardía supera al predictor cero

**Análisis descriptivo de artefactos existentes; sin trayectorias nuevas.**
Se cotejaron los nueve `unit-10.json` con los estados de checkpoint
SHA-256 anclados en el ledger. Las métricas completas A y D, antes y después
de actualizar el crítico, proceden de esos estados; el
[auditor](../evidence/p2r-late-mse-review/checks.py) solo agrega sumas
guardadas. [Resultados reproducibles](../evidence/p2r-late-mse-review/results.json)
y [comandos](../evidence/p2r-late-mse-review/COMMANDS.md). Temprano es
k={0,1,2}; tardío, k={7,8,9}. Cada celda agrupa 34.560 objetivos Monte
Carlo, uno por transición de cuatro horas de los tres lotes H180 de una
corrida; no son tres réplicas independientes.

La métrica adoptada es `R=MSE/(Z+10⁻¹²)`, con
`MSE=E[(V−G)²]` y `Z=E[G²]`; el predictor cero tiene `R≈1` donde Z es
informativo. `G` es retorno Monte Carlo completo de la misma política que
generó A o D. Para cada k, D usa una copia congelada de `π_k` y evalúa
`φ_k`/`φ_{k+1}` sobre **los mismos objetivos D**; A usa sus propios
objetivos y es el lote de ajuste del crítico. La siguiente tabla usa
únicamente métricas **post** de lotes completos y muestra también D **pre**
tardía. Los valores están redondeados; la auditoría conserva precisión plena.

| Semilla | Condición | R D post temprano → tardío | R A post tardío | R D pre → post tardío | MSE D post tardío | Z D tardío | Sesgo D post tardío |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 610031 | C0 | 1,4102 → 1,0465 | 0,8912 | 1,0310 → 1,0465 | 0,005940 | 0,005676 | −0,01375 |
| 610031 | C5 | 1,4102 → 1,0465 | 0,8912 | 1,0310 → 1,0465 | 0,005938 | 0,005674 | −0,01374 |
| 610031 | C10 | 1,4102 → 1,0465 | 0,8912 | 1,0310 → 1,0465 | 0,005938 | 0,005674 | −0,01375 |
| 610047 | C0 | 3,7135 → 1,1045 | 1,0097 | 1,1077 → 1,1045 | 0,005283 | 0,004783 | −0,00243 |
| 610047 | C5 | 3,7135 → 1,1046 | 1,0098 | 1,1078 → 1,1046 | 0,005283 | 0,004783 | −0,00243 |
| 610047 | C10 | 3,7135 → 1,1045 | 1,0097 | 1,1078 → 1,1045 | 0,005282 | 0,004782 | −0,00243 |
| 610081 | C0 | 1,5709 → 0,8592 | 0,7983 | 0,9067 → 0,8592 | 0,004503 | 0,005241 | −0,00361 |
| 610081 | C5 | 1,5709 → 0,8590 | 0,7981 | 0,9065 → 0,8590 | 0,004505 | 0,005244 | −0,00362 |
| 610081 | C10 | 1,5709 → 0,8591 | 0,7982 | 0,9066 → 0,8591 | 0,004504 | 0,005243 | −0,00361 |

Las seis corridas de 610031/610047 mejoran marcadamente entre las ventanas
temprana y tardía: **no** es ausencia total de aprendizaje. Sin embargo,
610031 termina con A tardía bajo el predictor cero y D por encima; en
610047 ambas quedan cerca o por encima de uno. Las tres iteraciones
tardías k=7,8,9 de cada una de esas seis corridas tienen R D post >1;
no es una sola iteración anómala. En 610031, la actualización del crítico
sube ligeramente el agregado D de 1,0310 a 1,0465 mientras mejora A;
en 610047 apenas baja D de 1,1078 a 1,1045/1,1046. Estas son
comparaciones sobre objetivos D fijos dentro de cada k, no pruebas de
causalidad entre las políticas de distintas iteraciones.

Las medias y dispersiones explican qué cambió entre ventanas y lotes. Se
ilustra con C0; las otras condiciones de la misma semilla difieren en la
cuarta decimal o menos, y el JSON conserva sus nueve valores completos.

| Semilla | Lote/ventana, post | Media V | Media G | SD V | SD G | Sesgo V−G |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 610031 | D temprana | −0,02777 | −0,01807 | 0,04614 | 0,06662 | −0,00969 |
| 610031 | A tardía | −0,03058 | −0,02771 | 0,02890 | 0,07323 | −0,00287 |
| 610031 | D tardía | −0,03169 | −0,01794 | 0,02931 | 0,07317 | −0,01375 |
| 610047 | D temprana | +0,01966 | −0,01803 | 0,11657 | 0,07041 | +0,03769 |
| 610047 | A tardía | −0,01830 | −0,01955 | 0,03332 | 0,06805 | +0,00125 |
| 610047 | D tardía | −0,01784 | −0,01541 | 0,03314 | 0,06742 | −0,00243 |
| 610081 | D temprana | −0,01911 | −0,02880 | 0,06992 | 0,06975 | +0,00969 |
| 610081 | A tardía | −0,03007 | −0,03089 | 0,03302 | 0,07022 | +0,00083 |
| 610081 | D tardía | −0,03062 | −0,02701 | 0,03177 | 0,06717 | −0,00361 |

En 610031, A tardía tiene objetivos más negativos que D tardía
(−0,02771 frente a −0,01794), mientras V queda alrededor de −0,031;
parte de la brecha A/D se manifiesta como sesgo en D. En 610047, el
sesgo D tardío es pequeño y su valor normalizado es −0,035, pero R D
sigue en 1,105. Los sesgos normalizados D tardíos son −0,183, −0,035 y
−0,050 para 610031/610047/610081, todos bajo el umbral |0,25| de P2R.
Por eso ni el sesgo ni la diferencia de medias A/D explican por sí solos
el fracaso frente al predictor cero.

## Descomposición verificable del exceso

Para un lote fijo, sin suponer independencia de retornos:

    MSE − Z = E[V²] − 2E[VG]
            = (Var(V) − 2Cov(V,G)) + (E[V]² − 2E[V]E[G]).

El auditor reconstruye los momentos a partir de SSE, `ΣG²`, conteo y
media/desviación poblacional de predicciones y objetivos; verifica la
identidad dentro de tolerancia numérica. En C0 como ejemplo representativo
de cada semilla, los agregados D post tardíos son:

| Semilla | Media V / G | SD V / G | E[V²] | 2E[VG] | Exceso MSE−Z | Componente centrada | Componente de medias |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 610031 | −0,03169 / −0,01794 | 0,02931 / 0,07317 | 0,001863 | 0,001599 | +0,000264 | +0,000397 | −0,000133 |
| 610047 | −0,01784 / −0,01541 | 0,03314 / 0,06742 | 0,001416 | 0,000916 | +0,000500 | +0,000731 | −0,000232 |
| 610081 | −0,03062 / −0,02701 | 0,03177 / 0,06717 | 0,001948 | 0,002686 | −0,000739 | −0,000022 | −0,000717 |

**Causa aritmética demostrada:** en 610031 y 610047, la covariación de
V con G es demasiado pequeña frente al segundo momento de V: `E[V²]`
supera `2E[VG]`. La parte **centrada** del exceso es positiva y mayor que
el exceso total; la contribución de las medias es negativa y lo compensa
parcialmente. Por tanto una explicación de «solo sesgo medio» es falsa,
particularmente en 610047, donde el sesgo medio es −0,00243. En 610081,
`2E[VG]` excede `E[V²]`; las medias negativas alineadas y mayor covarianza
permiten R<1. Una MSE absoluta menor entre semillas no garantiza R menor,
porque Z también cambia.

La dificultad se concentra hacia el final de las 180 transiciones. Para
610031, los tres tercios de D post tardía tienen R≈0,972 / 1,050 / 1,411;
para 610047, ≈0,995 / 1,176 / 1,484; incluso 610081, que pasa la regla
global, tiene ≈0,785 / 0,902 / 1,228. En el tercio final Z cae a
0,001895 / 0,001591 / 0,001470, respectivamente, y la dispersión de
predicciones sigue siendo material. **Hipótesis**, no hecho causal:
el menor horizonte restante reduce la señal predecible y el MSE entrenado
en A induce predicciones demasiado variables en rutas D nuevas. También
pueden intervenir ruido de retornos, diferencias de rutas/acciones y
capacidad/regularización del crítico; estos agregados no las separan.

## Comparabilidad y límites causales

Dentro de cada semilla, las tres condiciones comparten exactamente los
inicios de D en los diez k. Política y hash de objetivos D coinciden en
k=0,1, pero difieren desde k=2. El mecanismo de riesgo sí produjo
gradientes no nulos en C5/C10 tardíos (en 610031, 2/3 y 3/3 k;
en 610047, 3/3 y 3/3). La similitud de R entre C0/C5/C10 muestra que el
fenómeno **no requiere** activar el término de riesgo; no prueba que el
riesgo carezca de efecto causal. Son tres bloques de semilla, no nueve
réplicas. D comparte el histórico 2018–2022 con A/Q/B y puede solaparse;
no demuestra generalización temporal. Ni el sesgo, la fórmula de momentos
ni una sensibilidad algebraica de escala equivalente a `V/2` son una
política o un crítico entrenado. Esta última aparece en los resultados
solo para motivar una hipótesis de P3, sin reemplazar el resultado `review`
ni seleccionar checkpoints.
