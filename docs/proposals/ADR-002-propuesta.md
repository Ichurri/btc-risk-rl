# Propuesta para ADR-002: retorno finito común y riesgo de cola

**Estado: PROPUESTA PARA REVISIÓN, NO ADOPTADA.** Fecha: 22-09-2026.
Base inspeccionada: H2, `cc913b629694641543e2b54375dbda5d55130544`.
ADR-002 sigue abierto. Este documento no habilita agentes ni entrenamientos y
no cambia código, configuración, datos, observaciones o flags del simulador.

## 1. Recomendación y alcance científico

Adoptar para entrenamiento un objetivo de **H=180 transiciones contiguas de 4 h
(30 días), sin descuento, gamma=1**. PPO maximiza la esperanza del retorno
logarítmico neto de esa trayectoria; C5 y C10 restringen la cola de pérdidas del
**mismo retorno**. El final H es terminal para ese objetivo matemático, con valor
futuro cero, pero no obliga a liquidar BTC: la utilidad terminal usa patrimonio
marcado al cierre, como H2. Los costos de una venta hipotética posterior quedan
fuera de ese objetivo. Esta es una decisión económica explícita.

La afirmación investigable queda acotada a riesgo de retorno a 30 días bajo el
muestreo definido abajo. No equivale a optimizar riqueza anual, drawdown máximo,
riesgo durante interrupciones excluidas por B, ni una garantía financiera futura.
La evaluación continua será un ensayo operativo separado, con regla temporal
predefinida (§7). Si la tesis exige optimizar directamente la inversión indefinida,
esta recomendación debe rechazarse y desarrollarse la alternativa continua;
no basta cambiar gamma en una biblioteca.

## 2. Contrato existente contrastado

| Evidencia de H2 | Consecuencia para la propuesta |
|---|---|
| `env/trading.py:27–34`: entrenamiento completo de 180 pasos; validación completa | El recolector futuro puede reunir episodios completos sin alterar índices; no debe cortar validación. |
| `env/trading.py:36–54`: 10 características, peso BTC y log patrimonio relativo | No hay tiempo restante. Un objetivo finito requiere versionar la observación. |
| `env/trading.py:90–120`: siguiente apertura, recompensa neta, final `False, truncated` | Se preserva contabilidad; la terminalidad del objetivo requeriría otro contrato explícito. |
| `env/market.py:88–105`: contigüidad, fronteras y prioridad de motivo de corte | `end_reason` expresa procedencia, no completitud de la variable de riesgo. |
| `env/market.py:59–73`: aceptación y hashes de H1 | La migración posterior debe auditar manifiestos; no cambiar configuración y eludir incompatibilidades. |
| `configs/initial.toml`: `continuing_window_truncation`, sin gamma numérico | La opción recomendada cambia esa decisión; aún no está implementada. |

Rutas anteriores relativas a `src/btc_risk_rl/`. Los informes H1/H2 registran
7048 inicios aceptados de entrenamiento en 15 segmentos aptos y 2190 transiciones
continuas de validación. Son **resultados previos**, no una nueva auditoría del
mercado en esta tarea. No se cargaron productos de mercado para esta propuesta.

## 3. Alternativas

| Alternativa | PPO y CVaR | Ventanas y consecuencias |
|---|---|---|
| **A. Finita no descontada — recomendada** | Ambos usan R de 180 pasos, gamma=1. | H termina el objetivo; sin bootstrap en H; tiempo restante observable. Retorno financiero telescópico; alcance de 30 días. |
| B. Continua descontada con riesgo finito | PPO usa esperanza de suma infinita descontada; CVaR usa R observado de 180 pasos. | 180 es recolección para PPO y horizonte de riesgo. Es un objetivo mixto legítimo si se deriva como tal; no es el mismo retorno. Requiere gamma justificado y modelo de continuidad ante datos faltantes. |
| C. Finita descontada | Ambos usan suma de gamma^j r_j hasta H. | Alinea variables, pero ya no mide log(E_H/E_0). Requiere justificar preferencia temporal; conserva terminalidad y reloj de A. |

En B, usar gamma=1 en una suma infinita puede hacerla divergente; un criterio de
recompensa promedio sería otra formulación, con otro crítico. CVaR de un retorno
infinito tampoco se observa en una ventana de 180 pasos: añadir el valor esperado
del crítico no reconstruye su distribución de cola. Un descuento menor que uno
no resuelve la falta de transiciones durante interrupciones.

Un corte administrativo dentro de una trayectoria continua permite bootstrap
si se conserva su estado real y la semántica de continuación. Una frontera de
segmento no proporciona la transición al siguiente segmento. Evaluar V en el
último estado disponible sería una **extrapolación del modelo**, no evidencia de
esa continuación. En frontera de partición podría extrapolarse un crítico
entrenado sin leer la siguiente partición, pero seguiría faltando una definición
justificada de la tarea continua. Asignar cero allí convierte el problema en uno
finito de longitud variable. Ninguna de estas soluciones se adopta tácitamente.

## 4. Distribución, retorno y convención de riesgo

Propuesta de distribución inicial mu: elección uniforme con reemplazo entre los
7048 `episode_id` aceptados, independiente de theta. Cada trayectoria empieza
con 10000 USDT y cero BTC. Política estocástica congelada durante la recolección
de cada lote completo; todo episodio tiene 181 estados y 180 acciones/recompensas.
Los segmentos largos reciben mayor peso porque contienen más inicios. No se
balancean regímenes ni se sobremuestrean pérdidas sin cambiar mu y sus pesos.
Los inicios solapados reutilizan el mismo histórico: no representan 7048 períodos
económicos independientes. Los segmentos cortos excluidos de episodios siguen
siendo parte del ajuste del normalizador según H1; no se cambia esa regla.

Con j=0,...,H−1 y E_j posterior a la valoración del estado j:

\[
r_j=\log(E_{j+1}/E_j),\quad
R_H(\tau)=\sum_{j=0}^{H-1}r_j=\log(E_H/E_0),\quad
J(\theta)=\mathbb E_{I\sim\mu,\tau\sim\pi_\theta}[R_H].
\]

Definir pérdida L=−R_H: mayor L es peor; una ganancia produce pérdida negativa.
No usar valor absoluto, clipping en cero ni retornos simples en la restricción.
Alpha es **fracción de cola**, no confianza: C5 usa alpha=.05 (confianza .95),
C10 usa .10 (confianza .90). Para distribuciones con átomos:

\[
\rho_\alpha(L)=\min_{\eta\in\mathbb R}
F_\alpha(\theta,\eta),\qquad
F_\alpha=\eta+\frac1\alpha\mathbb E[(L-\eta)_+].
\]

El CVaR inferior de recompensa es C_alpha(R_H)=−rho_alpha(−R_H).
Eta es umbral de pérdida (VaR a confianza 1−alpha). La restricción común será
rho_alpha(L)≤d, equivalentemente C_alpha(R_H)≥−d. Tanto d como eta están en
**unidades de log pérdida a 30 días**. `1−exp(−d)` convierte un nivel de log pérdida
en pérdida simple, pero no convierte el CVaR logarítmico en CVaR simple.

C0 maximiza J sin restricción; C5/C10 maximizan J sujetos a su respectiva cola
con el mismo d. El valor de d requiere criterio económico previo y piloto de
factibilidad, no ajuste posterior para favorecer un resultado. Con la acción
siempre efectivo, interés cero y sin operaciones, R=0; por tanto d≥0 admite esa
referencia factible bajo el simulador. Un d<0 exige ganancia incluso en cola y
puede ser inviable. No se adopta una cota numérica aquí.

Para N pérdidas equiprobables ordenadas de mayor a menor, tomar exactamente
alpha*N unidades de masa: muestras completas y fracción de la siguiente. No
promediar todos los empates con el cuantil, ni redondear la cola a una muestra
como regla general. Esto implementa la distribución empírica, no una garantía de
precisión con pocos eventos extremos.

## 5. Valor, ventajas y tabla de cortes

Observación propuesta x_j=(o_H2,j, h_j), con h_j=(H−j)/H. H2 aporta ya el retorno
acumulado mediante log(E_j/E_0), útil para la dependencia de riesgo del prefijo.
El reloj se entrega a actor y crítico, sin z-score ni ajuste con validación.
Tener el mismo mercado y cartera con un paso restante o con 180 puede requerir
decisiones distintas. El reloj elimina esa ambigüedad temporal; no demuestra que
las características financieras formen un estado Markov suficiente.

\[
V_j(x_j)=\mathbb E[\sum_{k=j}^{H-1}r_k\mid x_j],\quad V_H=0,
\quad G_j=\sum_{k=j}^{H-1}r_k,\quad \widehat A_j=G_j-V_j(x_j).
\]

Referencia recomendada: gamma=1 y lambda_GAE=1, retorno Monte Carlo completo con
baseline preactualización. Gamma define el objetivo; lambda_GAE controla el
estimador, y lambda_riesgo es otro parámetro. Una futura comparación con
lambda_GAE<1 debe declarar el sesgo por crítico imperfecto y aplicarse igual a
C0/C5/C10; no cambia la definición de R_H.

Para hacer explícitas las máscaras:

\[
\delta_j=r_j+\gamma b_jV_{j+1}-V_j,\qquad
\widehat A_j=\delta_j+\gamma\lambda_{GAE}c_j\widehat A_{j+1}.
\]

b permite bootstrap; c permite continuar la traza. No deducirlas únicamente de
`truncated`. Dentro del episodio observado b=c=1; en su final válido b=c=0.

| Situación observada | Bootstrap y ventajas propuestos | Elegibilidad CVaR / manejo |
|---|---|---|
| `collection_window` al completar H | b=0,c=0 en último paso; retorno completo hasta H | Sí, R_H observado. El objetivo finito terminó aunque exista mercado posterior. |
| `segment_boundary` exactamente en H | b=0,c=0; mismo retorno finito | Sí. La frontera posterior no invalida las 180 transiciones ya observadas. No se cruza el hueco. |
| `partition_boundary` exactamente en H de entrenamiento | b=0,c=0; sin valor ni recompensa de validación | Sí, todas las transiciones pertenecen a entrenamiento. |
| Corte interno de recolección m<H, continuación válida del mismo episodio | b=1 si se necesitara un objetivo parcial; c=0 en cálculo local del fragmento. **Referencia: esperar y ensamblar H con política congelada**, luego c=1 a través del corte de memoria | No mientras esté incompleto; sí tras completar H. Conservar cartera, reloj e identidad; no reset. H2 no emite actualmente este corte intermedio. |
| `segment_boundary` antes de H | Episodio censurado: no crear target cero ni bootstrap que invente continuidad. Rechazar todo el episodio para actor y crítico en este protocolo | No; error de índices/recolección, no una cola corta. Nunca unir al siguiente segmento. |
| `partition_boundary` antes de H | Igual rechazo; no completar con validación ni conjunto final | No. No reducir H según proximidad a frontera. |
| Final de validación continua, paso 2190 | Sin actualización, ventajas ni bootstrap de aprendizaje; conservar valoración y posición | El retorno total de 2190 pasos no es una muestra de R_H de entrenamiento. |

H2 ya exige H completo para rutas de entrenamiento, por lo que los dos casos de
censura temprana deberían ser fallos de integridad, no ocurrencias ordinarias.
Abortar y diagnosticar el lote evita sesgo por descartar selectivamente pérdidas;
no reemplazar silenciosamente una trayectoria que falló por sus acciones.
El final de objetivo y el motivo de corte pueden coexistir: registrar ambos.
La observación terminal es la real, nunca la observación de un autoreset.

## 6. Derivación técnica del mecanismo de riesgo (sin agente)

Propuesta de Lagrangiano, con lambda_riesgo≥0:

\[
K(\theta,\eta,\lambda_r)=J(\theta)
 -\lambda_r[F_\alpha(\theta,\eta)-d].
\]

Se busca punto silla: ascenso en theta y eta, descenso en lambda_r. Es una
formulación no convexa; no se afirma existencia de solución global ni ausencia
de brecha dual. Con eta fijo, entorno y mu independientes de theta, soporte de
política fijo y derivación bajo la esperanza válida, sea
S(τ)=sum_j grad_theta log pi_theta(a_j|x_j). Entonces:

\[
\nabla_\theta K=
\mathbb E\!\left[\sum_j\nabla\log\pi_\theta(a_j|x_j)
 \left(G_j-V_j-\frac{\lambda_r}{\alpha}(L-\eta)_+\right)\right].
\]

El baseline V_j depende solo de información previa a la acción y se trata como
constante en esta derivada. El prefijo de recompensa se elimina del término de
media por causalidad; **no** se elimina del shortfall de trayectoria. Todas las
acciones reciben el término de riesgo de su trayectoria completa. En regiones
regulares, al minimizar F en eta esta derivada representa la derivada del CVaR;
en átomos se usa la representación variacional y subgradientes, no una fórmula
condicional que ignore masa en el cuantil.

Fuera de empates: dK/deta=−lambda_r[1−P(L>eta)/alpha]. La actualización dual
lambda_r←max(0,lambda_r+paso*(F_alpha−d)) aumenta penalización ante violación.
Eta estimado con la misma muestra introduce error de estimación; el futuro
protocolo debe fijar actualización alternada o muestra independiente, y medir
sesgo/varianza. Las ecuaciones poblacionales no garantizan insesgadez del plug-in.

Una adaptación PPO podría fijar eta, lambda_r y estadísticas del lote, y usar
D_ij=A_ij−lambda_r*(L_i−eta)_+/alpha en el surrogate:

\[
\widehat K_{clip}=\frac1N\sum_i\sum_j
\min\{u_{ij}(\theta)D_{ij},
\operatorname{clip}(u_{ij}(\theta),1-\epsilon,1+\epsilon)D_{ij}\},
\quad u=\pi_\theta/\pi_{old}.
\]

En theta_old, antes de clipping activo, su gradiente coincide con el estimador
anterior. Lejos de theta_old los cocientes por acción no son cocientes de
trayectoria completa; varias épocas/clipping producen una aproximación, **no**
un certificado de factibilidad CVaR. Auditar violaciones con nuevas trayectorias
on-policy completas. No presentar esto como reproducción literal del CPPO de
IJCAI-22 ni trasladar sus garantías de horizonte descontado a gamma=1.

Mantener la escala por trayectoria: dividir por H solo es un escalado común si
se aplica a todos los términos correspondientes y se documenta. No normalizar
media y riesgo por separado, recalcular colas por minibatch, ni calcular CVaR de
ventajas, rewards individuales, retornos del crítico o muestras de políticas
mezcladas sin corrección. Con lambda_r=0 fijo, el mismo código y lote deberían
producir exactamente el gradiente, pérdida y actualización C0. Esta identidad
necesitará pruebas del agente futuro; aquí solo se verifica algebraicamente.

## 7. Validación continua y límites de transferencia

Propuesta operativa concreta: una cartera, un reset inicial, 2190 pasos, sin
actualizar política, crítico, eta, multiplicador ni normalizador. Usar la misma
política estocástica y semillas de evaluación emparejadas en las tres condiciones.
Se recomienda **horizonte móvil**: antes de cada acción presentar h=1 (180 pasos
por delante); aplicar pi_despliegue(a|o)=pi_theta(a|o,h=1). Mantener el peso BTC y
log(E/E_inicial_validación) reales de H2, sin reiniciar riqueza cada 180 pasos ni
liquidar en cortes de calendario. El último paso tampoco recibe un horizonte
acortado usando la fecha final como señal de trading. No hace falta observar los
180 pasos futuros para decidir; h expresa planificación, no datos disponibles.

Esta regla convierte la política finita en un controlador de horizonte móvil.
**No es la misma ley de trayectorias usada para entrenar**, donde h desciende.
La cartera heredada y el log patrimonio también difieren de los reinicios de
entrenamiento. Su rendimiento continuo mide transferencia operacional; no prueba
que se optimizó el objetivo anual ni que rho_alpha≤d se cumpla en validación.
La restricción estática de cola al inicio tampoco asegura una restricción
condicional en cada estado ni consistencia dinámica al replanificar.

Alternativa descartada para esta propuesta: repetir un reloj 180→1 cada 30 días
sin reset de cartera. Introduce fase de calendario y saltos de reloj; no elimina
la diferencia de distribución inicial. No elegir entre ambas reglas mirando
cuál obtiene mejor validación. La elección de horizonte móvil debe revisarse
junto con la afirmación científica limitada de §1.

Se puede informar retorno total continuo, costos, drawdown y distribución de
retornos móviles observados de 180 pasos, etiquetada como diagnóstico distinto
(con dependencia por solapamiento y carteras heredadas). No contar el residuo
final como trayectoria completa ni transformar validación en episodios con
reinicio. Ningún indicador modifica d o el objetivo después de congelarlos.

## 8. Consistencia experimental y parámetros pendientes

| Definido dentro de esta propuesta, pendiente de aprobación | Requiere piloto o protocolo posterior |
|---|---|
| R_H neto logarítmico; H=180, gamma=1; pérdidas −R; fracciones .05/.10 | N trayectorias completas por lote, precisión y masa efectiva de cola; incertidumbre por solapamiento |
| Misma mu, H1, costos, acción, reloj, particiones y reglas de corte | Cota común d: tolerancia económica y factibilidad; congelarla antes de comparación |
| Referencia lambda_GAE=1; mecanismo apagado equivale a C0 | Arquitectura, optimizadores, clip PPO, épocas, tasas de eta/dual; lambda_GAE<1 solo como aproximación explícita |
| Misma evaluación continua de horizonte móvil | Semillas de piloto separadas de comparación, número de réplicas y presupuesto común de transiciones/actualizaciones |
| C0 sin restricción; C5/C10 solo difieren en mecanismo y fracción de cola | Criterios de precisión/violación y parada, actualización de eta y dual, estabilidad e inferencia estadística |

Un lote con N=400 tendría solo 20 unidades de masa en la cola .05 y 40 en .10:
es un ejemplo de contabilidad de muestra, **no** una recomendación de tamaño.
Exigir métricas de incertidumbre; más solapamientos no crean más historia.
No adaptar d individualmente por condición. Registrar esfuerzo computacional:
el costo del mecanismo puede variar aunque se igualen datos y presupuesto.
Si se añade entropía al actor, documentarla como regularización común (cero en
la referencia matemática), nunca incluirla en el retorno financiero de CVaR.

## 9. Cambios necesarios si se aprueba, no realizados ahora

1. Adoptar explícitamente esta formulación en ADR-002 y versionar configuración
   de horizonte finito; mantener prohibición de entrenamiento hasta su autorización.
2. Añadir reloj determinista como componente 13, con contratos diferenciados
   de entrenamiento y evaluación; conservar las 10 características y su scaler.
3. Exponer `objective_terminal`/completitud y procedencia separadamente. Un modo
   finito de entrenamiento devolvería terminalidad en H (sin liquidación);
   validación seguiría truncando al final de datos. Probar ambas semánticas y
   evitar doble cómputo por flags. No reinterpretar H2 silenciosamente.
4. Revalidar manifiestos/configuración en una migración versionada: preservar
   originales, máscara B, particiones, índices y parámetros del normalizador.
   El reloj no requiere refit. Documentar huellas antes/después y compatibilidad.
5. Antes del agente: pruebas de integración de máscaras, tiempo, fronteras
   coincidentes, ensamblaje de fragmentos y validación continua. Después, con
   autorización separada, implementar y verificar estimador/gradientes y
   equivalencia exacta C0/riesgo apagado antes de cualquier entrenamiento.

## 10. Ejemplos sintéticos y evidencia ejecutable

[Comprobaciones independientes](../evidence/adr002-proposal/checks.py) usan solo
la biblioteca estándar, constantes sintéticas y enumeración; no importan el
simulador, agentes ni datos de mercado. [Resultados](../evidence/adr002-proposal/results.json)
y [comandos](../evidence/adr002-proposal/COMMANDS.md) registran su ejecución local.
Son comprobaciones de la propuesta, no validación de un agente implementado.

- Rewards (.1,−.1): R=0; descuento .99 da .001. Descontar cambia el objeto medido.
  Con gamma=.99, el último reward de H=180 pesa aproximadamente .165, no uno.
- Rewards (.02,−.01,.03) y V=(.04,.025,.01,0): G=(.04,.02,.03),
  A=(0,−.005,.02). La recurrencia GAE con gamma=lambda_GAE=1 coincide con
  suma directa. Añadir V_H=.7 filtraría .7 a todas las ventajas.
- Cortar ese ejemplo después de dos rewards y bootstrap con V_2=.01 produce
  target inicial .02, frente al retorno completo .04. El bootstrap es una
  estimación; no se debe presentar como retorno financiero realizado de cola.
- Pérdidas (.2,.1,−.02,−.1), alpha=.375: masa de cola 1.5, CVaR=1/6.
  La minimización variacional y la integración fraccionaria coinciden, también
  con empates y alpha=.05/.10.
- Enumeración de dos resultados: R_malo=−.2 con p=.25, R_bueno=.1 con 1−p,
  alpha=.5. J=.1−.3p y rho=.6p−.1. Con p=sigmoid(theta),
  dJ/dtheta=−.05625 y drho/dtheta=.1125. Para lambda_r=.4,
  dK/dtheta=−.10125. Diferencias finitas, fórmula cerrada y score de trayectoria
  coinciden. Lambda_r=0 recupera dJ/dtheta. No se ejecuta optimización.
- Una trayectoria completa es admisible con cualquiera de los tres motivos;
  una frontera antes de H se rechaza. El fragmento interno espera completitud.

## 11. Fuentes primarias y alcance de su uso

1. [Schulman et al., PPO (2017), §§3 y 5, ecuaciones 7 y 10–12](https://arxiv.org/pdf/1707.06347).
   Distingue surrogate de política, valor y recolección truncada. Fundamenta la
   comparación local del surrogate; sus hiperparámetros no justifican los nuestros.
2. [Schulman et al., GAE (ICLR 2016), §3, ecuaciones 16–18](https://arxiv.org/pdf/1506.02438).
   Distingue descuento y lambda; explica la relación Monte Carlo/baseline y el
   compromiso sesgo-varianza. Nuestra especialización es finita con valor terminal cero.
3. [Pardo et al., Time Limits in Reinforcement Learning (ICML 2018), §§2–3](https://proceedings.mlr.press/v80/pardo18a/pardo18a.pdf).
   Distingue límite integrante de la tarea y corte externo de recolección;
   respalda reloj para horizonte finito y bootstrap para continuación válida.
   No autoriza unir observaciones separadas por ausencia de datos.
4. [Rockafellar y Uryasev, Conditional Value-at-Risk for General Loss Distributions (2002), teorema 10](https://sites.math.washington.edu/~rtr/papers/rtr187-CVaR2.pdf).
   Proporciona representación variacional compatible con distribuciones discretas.
   Aquí alpha denota masa de cola: se sustituye su nivel de confianza por 1−alpha.
5. [Tamar, Glassner y Mannor, Optimizing the CVaR via Sampling (AAAI 2015), proposiciones 1–2](https://cdn.aaai.org/ojs/9561/9561-13-13089-1-2-20201228.pdf).
   El gradiente de cola requiere el umbral VaR, no un baseline arbitrario dentro
   de la cola. Sus supuestos de regularidad no se trasladan automáticamente a
   empates; usamos la formulación variacional para los ejemplos discretos.
6. [Towards Safe Reinforcement Learning via Constraining Conditional Value-at-Risk (IJCAI 2022), §§2 y 4](https://www.ijcai.org/proceedings/2022/0510.pdf).
   Formula media con restricción sobre cola de retorno y relajación lagrangiana;
   emplea retorno descontado y propone modificar la cota durante aprendizaje.
   Aquí se propone horizonte finito no descontado y cota común congelada: es
   adaptación metodológica explícita. Su alpha es confianza; C5/C10 son masa de
   cola. Sus resultados de robustez no certifican este mercado ni esta variante.

Las decisiones de mu, horizonte, validación móvil y cota congelada son propuestas
propias para este repositorio, no mandatos de esas fuentes. Revisión documental
realizada sin entrenamiento ni acceso al conjunto final. El siguiente paso es
revisar conjuntamente la formulación finita y el alcance de la evaluación antes
de cambiar el contrato H2.
