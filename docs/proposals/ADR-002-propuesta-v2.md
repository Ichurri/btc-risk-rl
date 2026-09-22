# Propuesta ADR-002 v2: retorno finito común y riesgo de cola

**Estado: PROPUESTA PARA REVISIÓN, NO ADOPTADA.** Fecha: 22-09-2026 (UTC).
Base inspeccionada: H2, `cc913b629694641543e2b54375dbda5d55130544`.
Revisión documental de v1 (`082db3e`), conservada como antecedente.
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
| Corte interno de recolección m<H, continuación válida del mismo episodio | **Esperar y ensamblar H con política congelada**; no construir targets parciales. Tras ensamblar, b=c=1 a través del corte de memoria; b=c=0 solo en H | No mientras esté incompleto; sí tras completar H. Conservar cartera, reloj e identidad; no reset. H2 no emite actualmente este corte intermedio. |
| `segment_boundary` antes de H | Episodio censurado: no crear target cero ni bootstrap que invente continuidad. Rechazar todo el episodio para actor y crítico en este protocolo | No; error de índices/recolección, no una cola corta. Nunca unir al siguiente segmento. |
| `partition_boundary` antes de H | Igual rechazo; no completar con validación ni conjunto final | No. No reducir H según proximidad a frontera. |
| Final de validación continua, paso 2190 | Sin actualización, ventajas ni bootstrap de aprendizaje; conservar valoración y posición | El retorno total de 2190 pasos no es una muestra de R_H de entrenamiento. |

H2 ya exige H completo para rutas de entrenamiento, por lo que los dos casos de
censura temprana deberían ser fallos de integridad, no ocurrencias ordinarias.
Las mismas reglas de completitud se aplican a los lotes A (actor), Q (eta)
y B (auditoría) definidos en §6; ninguno puede contener retornos parciales.
Abortar y diagnosticar el lote evita sesgo por descartar selectivamente pérdidas;
no reemplazar silenciosamente una trayectoria que falló por sus acciones.
El final de objetivo y el motivo de corte pueden coexistir: registrar ambos.
La observación terminal es la real, nunca la observación de un autoreset.

## 6. Procedimiento concreto de actualización: lotes separados

### 6.1 Objetos distintos y gradiente

Se conserva el Lagrangiano K(theta,eta,lambda_r)=J(theta)−lambda_r(F_alpha(theta,eta)−d).
La formulación poblacional busca ascenso en theta/eta y descenso en lambda_r≥0;
no implica convexidad ni garantía de convergencia. La implementación propuesta
aproxima la maximización en eta por **minimización empírica exacta de F** en un
lote separado, sin tasa de aprendizaje de eta. Sustituye la elección abierta de v1.

Para un lote D de N pérdidas completas:

\[
\widehat F_D(\eta)=\eta+\frac{1}{\alpha N}\sum_{i\in D}(L_i-\eta)_+,
\qquad \widehat\rho_D=\min_\eta\widehat F_D(\eta).
\]

No confundir tres cantidades:

| Cantidad | Qué significa |
|---|---|
| rho_alpha(theta)=min_eta F_alpha(theta,eta) | Restricción **poblacional** bajo mu y la política finita; desconocida. |
| rho_hat_D | CVaR de la distribución **empírica** de D; eta ajustado en D. |
| F_hat_D(eta_Q) | Función variacional evaluada en D con umbral ajustado en **otro lote Q**; no es, en general, el CVaR empírico de D. |

Siempre rho_hat_D≤F_hat_D(eta_Q). Poblacionalmente rho_alpha(theta)≤F_alpha(theta,eta_Q).
La segunda desigualdad no convierte una estimación finita F_hat en cota superior
con confianza estadística. Condicional a theta y eta_Q, un D nuevo e independiente
estima F(theta,eta_Q) sin sesgo de muestreo; no estima necesariamente rho(theta)
sin sesgo. La incertidumbre y la precisión de cola quedan para pilotos.

Para eta fijo y baseline anterior al lote, el gradiente poblacional es

\[
\nabla_\theta K=\mathbb E\left[\sum_{j=0}^{H-1}\nabla\log\pi_\theta(a_j|x_j)
 \left(G_j-V_j-\frac{\lambda_r}{\alpha}(L-\eta)_+\right)\right].
\]

Supone soporte de política fijo, derivación bajo la esperanza válida y entorno/mu
independientes de theta. El prefijo desaparece del término de media por causalidad,
pero permanece en L del término de riesgo. Con eta estimado, esto es el gradiente
de **F a ese eta**, no necesariamente el gradiente exacto de rho. Ningún batch de
ventajas ni estimación del crítico reemplaza L observado. En eta minimizador
poblacional y bajo regularidad se recupera la derivada de CVaR; en puntos no
suaves se requiere tratamiento de subgradientes.

### 6.2 Umbral, empates y masa fraccionaria

Ordenar ascendentemente las pérdidas de Q y fijar
eta_Q=L_(ceil((1−alpha)N_Q)), con índices desde 1. Para alpha=.05/.10 está bien
definido. Es el menor cuantil empírico con CDF≥1−alpha. Si hay intervalo de
minimizadores, esta regla elige su extremo inferior; no interpolar valores por
una convención por defecto de biblioteca.

Para informar la cola, asignar peso 1 a pérdidas mayores que eta, peso 0 a las
menores y distribuir **por igual entre los empates** la masa restante
alpha*N_Q−n_mayores. Dividir la suma ponderada por alpha*N_Q. Esto equivale a
rho_hat_Q=F_hat_Q(eta_Q). Si alpha*N_Q<1, el máximo recibe masa fraccionaria;
la estimación existe aunque su precisión sea pobre. Conservar orden estadístico,
conteo de empates, masa y regla de igualdad exacta de pérdidas float64; no crear
empates mediante redondeo. El shortfall del actor es (L−eta_Q)+; los empates
aportan cero a ese shortfall, sin selección arbitraria de acciones en la cola.
Los pesos fraccionarios son para calcular CVaR empírico, no para sustituir el
shortfall por una máscara de selección en el gradiente.

### 6.3 Calendario y separación de muestras

A_k es el lote de actor/crítico de la política pi_k. Q_k estima eta_k bajo pi_k;
B_k audita pi_k con eta_k fijo. Cada lote contiene episodios completos de H,
con reloj descendente y reinicio inicial, usando solo inicios de entrenamiento
aceptados. **B no es la validación cronológica de 2023.**

Los flujos aleatorios de inicios y acciones para A/Q/B son separados. Pueden
sortear el mismo `episode_id` con reemplazo: independencia de simulaciones
condicional al histórico fijo no significa nuevos períodos de mercado.
No exigir inicios distintos mediante rechazo, porque alteraría mu y la
independencia declarada. No reutilizar la misma realización de trayectoria
entre roles. Un identificador de realización incluye corrida, iteración, rol y réplica.

Inicialización: fijar theta_0, phi_0 y lambda_0=0; congelar pi_0, recolectar Q_0,
calcular eta_0. C0 usa siempre lambda=0; C5/C10 empiezan también en cero. Durante
cada iteración:

1. Congelar pi_k, V_phi_k, eta_k, lambda_k. Recolectar A_k nuevo completo con pi_k.
2. Calcular G_ij por suma observada; A_ij=G_ij−V_phi_k(x_ij). Guardar logprob_old,
   shortfall_i=(L_i−eta_k)+ y D_ij=A_ij−lambda_k*shortfall_i/alpha.
3. Actualizar **solo actor** por épocas PPO sobre A_k. Minibatches de trayectorias
   completas, promediando por número de trayectorias y sumando sus H términos.
   Permanecen fijos pi_k como denominador, observaciones, G, V_old, A, eta_k,
   lambda_k, D, d, alpha y normalizador. No recomputar cuantiles por minibatch,
   ni normalizar ventajas/D con estadísticas del lote en esta referencia.
4. Congelar el nuevo actor pi_(k+1). Actualizar **después el crítico** con A_k y
   targets G fijos, mediante MSE promedio por transición. Actor y crítico tendrán
   parámetros separados; el ajuste del crítico no modifica el actor. El crítico
   aprende retorno medio sin penalización de riesgo. El baseline para la siguiente
   iteración se fija antes de observar su A nuevo.
5. Con pi_(k+1) congelada, recolectar Q_(k+1) nuevo y estimar eta_(k+1) con la regla
   anterior. Reemplaza eta_k; no suavizado ni gradiente de eta en esta referencia.
6. Con esa misma pi_(k+1), recolectar B_(k+1) independiente, después de fijar eta.
   Registrar F_hat_B(eta_(k+1)), rho_hat_B, rho_hat_Q, sus diferencias respecto de
   d y tamaños/masas de cola. No volver a ajustar eta usado por el actor con B.
7. Actualizar una vez el multiplicador, **para la iteración siguiente**:

\[
\lambda_{k+1}=\max\{0,\lambda_k+\beta_k[
\widehat F_{B_{k+1}}(\eta_{k+1})-d]\}.
\]

C0 o modo riesgo apagado: lambda_(k+1)=0 exactamente, ignorando la señal dual.
Una diferencia positiva es alarma empírica, no demostración de violación
poblacional. Tampoco una diferencia negativa certifica cumplimiento.
El gradiente dual usa F a eta fijo porque ese es el Lagrangiano especificado;
no lo sustituye por rho_hat_B, que minimiza sobre la misma muestra de auditoría.
No actualizar actor ni hacer selección/reintentos usando B dentro de esta iteración.
El siguiente actor recibe la señal de B únicamente mediante lambda_(k+1).
No parar por haber obtenido una auditoría favorable: usar K iteraciones fijadas
por presupuesto (salvo fallo técnico que invalide y registre la corrida).

El surrogate del actor queda definido por

\[
\widehat K_{clip}=\frac1{N_A}\sum_{i\in A_k}\sum_j
\min\{u_{ij}(\theta)D_{ij},\operatorname{clip}(u_{ij}(\theta),1-\epsilon,1+\epsilon)D_{ij}\},
\quad u_{ij}=\frac{\pi_\theta(a_{ij}|x_{ij})}{\pi_k(a_{ij}|x_{ij})}.
\]

### 6.4 Pseudocódigo completo — especificación, no agente implementado

```text
Entrada congelada: mu de entrenamiento, H=180, gamma=lambda_GAE=1,
                   d común, K, N_A/N_Q/N_B, épocas actor/crítico, clip, tasas,
                   semillas separadas por rol y condición; scaler H1 inmutable.
Inicializar actor theta_0 y crítico phi_0 separados; lambda_0=0.
Q_0 <- episodios_completos(pi_theta_0 congelada, mu, N_Q, flujo Q_0)
eta_0 <- cuantil_inferior(Q_0, confianza=1-alpha, empates exactos)
Para k=0,...,K-1:
    old <- copia inmutable de theta_k; V_old <- copia inmutable de phi_k
    A_k <- episodios_completos(pi_old, mu, N_A, flujo A_k)
    Verificar H, contigüidad, partición, versión de política e integridad.
    G <- sumas de rewards hasta H; ventajas <- G - V_old(observaciones)
    Si riesgo_apagado: D <- ventajas                  # igualdad exacta con C0
    Si no: D <- ventajas - lambda_k/alpha * max(-R_H(A_k)-eta_k, 0)
    Congelar D, G, ventajas, eta_k, lambda_k, logprob_old y datos de A_k.
    theta_(k+1) <- épocas PPO actor en A_k con estos valores fijos
    Congelar theta_(k+1).
    phi_(k+1) <- épocas MSE crítico en A_k contra G (actor no compartido)
    Q_(k+1) <- episodios_completos(pi_theta_(k+1), mu, N_Q, flujo Q_(k+1))
    eta_(k+1) <- cuantil_inferior(Q_(k+1), confianza=1-alpha)
    Congelar eta_(k+1).
    B_(k+1) <- episodios_completos(pi_theta_(k+1), mu, N_B, flujo B_(k+1))
    f <- eta_(k+1) + media(max(L(B_(k+1))-eta_(k+1),0))/alpha
    Registrar f-d, CVaR_empirico(B_(k+1))-d, CVaR_empirico(Q_(k+1)),
              masas/empates, versiones, semillas y recursos consumidos.
    Si riesgo_apagado: lambda_(k+1) <- 0
    Si no: lambda_(k+1) <- max(0, lambda_k + beta_k*(f-d))
    Conservar eta_(k+1) para el próximo A; no replay de A/Q/B para otro actor.
    Si hubo trayectoria inválida: abortar y diagnosticar; no reemplazo selectivo.
Salida: theta_K fijado por presupuesto; no elegir checkpoint mediante B.
Evaluación cronológica separada: una cartera continua, pi_theta_K(o,h=1),
    sin actualización de actor/crítico/eta/lambda/scaler; semillas predefinidas.
```

En C0 se recolectan igualmente Q/B para diagnóstico y contabilidad de recursos;
se pueden informar ambas colas .05/.10, sin utilizarlas para aprender. Ninguna
función aquí descrita se implementa en esta entrega.

### 6.5 Reutilización, sesgo y auditoría

| Muestra | Reutilización definida | Límite estadístico |
|---|---|---|
| A_k | Todas las épocas del actor y luego ajuste del crítico | PPO usa varias veces las mismas acciones; después del primer punto theta_k no es un gradiente on-policy exacto. Clipping no garantiza la restricción. |
| Q_k | Su eta se usa en B_k y en A_k, no sus realizaciones para gradientes | A/B nuevos evitan ajustar y evaluar eta sobre la misma muestra. Eta sigue teniendo error y puede sesgar respecto del gradiente de rho, aunque el gradiente de F a eta fijo sea correcto. |
| B_(k+1) | Auditoría de pi_(k+1) y una actualización dual | Es diagnóstico fuera del lote actor, pero forma parte del aprendizaje por lambda. No es un conjunto confirmatorio independiente del proceso completo. |
| Validación cronológica | Solo evaluación declarada; sin actualización | Si luego sirve para selección de hiperparámetros, deja de ser evidencia confirmatoria independiente. |

Condicional a theta_k, eta_k, lambda_k y V_old, A nuevo da el estimador score de K
con eta fijo en el punto theta_k. El ajuste previo del crítico sobre A_(k−1) no
usa las acciones de A_k. Q/B no eliminan sesgo de selección histórica, error de
eta ni aproximación PPO. El valor esperado de F con eta estimado es al menos
rho poblacional para theta fijo, pero una realización de F_hat_B puede quedar
por debajo. Minimizar y evaluar en un mismo lote da un CVaR empírico cuyo valor
esperado puede ser inferior al poblacional: no reportarlo como cota conservadora.

Ejemplo exacto: L=.2 con probabilidad .25 y L=−.1 con .75; alpha=.5. Rho=.05.
Con Q de una muestra, eta=.2 o −.1; F poblacional respectivo=.2 o .05;
E_Q F=.0875. En cambio E[rho_hat_Q]=−.025. Un B independiente estima F al eta
elegido, no corrige automáticamente esa diferencia. Es un ejemplo algebraico
con tamaño deliberadamente insuficiente, no un tamaño recomendado.

### 6.6 Equivalencia y presupuesto común

Con riesgo apagado, D se copia de las ventajas sin operar sobre shortfalls;
lambda permanece cero incluso si B viola d. Igualar pesos iniciales, streams
de A, arquitectura separada, estados de optimizadores, minibatches, épocas y
tasas recuperará el mismo actor/crítico C0. Streams Q/B no consumen el RNG de A
ni cambian tasas, parada, selección o normalización. Esta es una obligación de
la implementación futura; los cálculos actuales solo verifican la identidad
algebraica y el orden de la especificación.

Cada condición debe consumir, para K iteraciones y tamaños constantes,

\[
N_{tray}=N_Q+K(N_A+N_Q+N_B),\qquad
N_{trans}=180N_{tray}.
\]

Incluye Q_0, Q/B auxiliares, también en C0; añadir por separado todos los recorridos
continuos de evaluación y pilotos. Presupuesto primario iguala K, N_A/N_Q/N_B y
épocas en C0/C5/C10, con d idéntico para las dos condiciones de riesgo. El cálculo
de colas puede hacerse en C0 para diagnóstico pero no para actualizar. Informar
además tiempo, memoria y pasos de optimización: igualdad de datos no es igualdad
de costo computacional. No regalar trayectorias de auditoría a C5/C10 ni dar más
actualizaciones a C0 en el contraste principal. Una comparación secundaria por
tiempo requeriría protocolo aparte. Tasas, tamaños y K siguen pendientes de pilotos;
la separación de roles y el orden anterior quedan definidos en esta propuesta.

## 7. Evaluación continua: decisión previa a resultados y Sortino

### 7.1 Diferencia de soporte y recomendación

**Mantener el horizonte móvil h=1 únicamente como prueba de transferencia
operacional**, con una cartera continua, sin reinicios periódicos. Esta elección
se realiza por criterios metodológicos antes de leer resultados de validación.
Conservar H=180/gamma=1 y la distribución inicial fija del entrenamiento. Se
acepta deliberadamente la limitación siguiente; no se declara resuelta por usar
la misma red ni por mantener el reloj constante.

Sea w el peso BTC, z=log(E/E_0) y m las diez características. En entrenamiento:

\[
P_{train}((w,z)=(0,0)\mid h=1)=1.
\]

En despliegue pi_despliegue(a|m,w,z)=pi_theta(a|m,w,z,h=1), después de operar
puede haber w≠0 o z≠0. Esas combinaciones conjuntas tienen probabilidad cero
bajo el soporte de entrenamiento condicionado a h=1. Aunque (w,z) se haya visto
con h<1, eso no identifica la respuesta en (h=1,w,z). La invariancia de escala
contable no fuerza a una red a ignorar z. Además, el z de entrenamiento acumula
como máximo 180 pasos; en continuo se ancla al inicio del recorrido completo.
No rebasar z a cero, falsificar w ni normalizar cartera para ocultar la diferencia.

Ejemplo con precio sintético 100 y E_0=10000 (estados contables, sin afirmar
que procedan de operaciones H2 ni de una política entrenada):

| Contexto ilustrativo | h | E | BTC | Efectivo | w | z |
|---|---:|---:|---:|---:|---:|---:|
| Reset de entrenamiento | 1 | 10000 | 0 | 10000 | 0 | 0 |
| Estado posterior finito | .5 | 11000 | 55 | 5500 | .5 | log(1.1) |
| Misma cartera, evaluación móvil | 1 | 11000 | 55 | 5500 | .5 | log(1.1) |
| Evaluación tras pérdida | 1 | 9000 | 67.5 | 2250 | .75 | log(.9) |
| Evaluación de nuevo en efectivo | 1 | 11000 | 0 | 11000 | 0 | log(1.1) |

Las últimas tres filas no satisfacen el soporte en h=1. La cuarta muestra que
no solo importan ganancias; la quinta que vender todo tampoco recupera z=0.
Un contraejemplo de identificabilidad: dos funciones de acción pueden coincidir
en todos los relojes de entrenamiento y diferir en h=1,w>0. Sea g(h)=0 para los
valores h≤179/180 y g(h)=180h−179 entre 179/180 y 1. Las funciones f=.25 y
f'=.25+.5*g(h)*w coinciden en el soporte temporal de entrenamiento (incluido
h=1,w=0), pero en h=1,w=.5 dan .25 y .50. Este ejemplo **no es un agente** ni
una afirmación sobre PPO: demuestra que acertar en el soporte no determina la
transferencia. Las pruebas ampliadas comprueban esta diferencia, no rendimiento.

Se elige mantener la prueba porque conserva el retorno financiero finito común,
las exclusiones B y el recorrido operacional exigido, sin introducir nuevas
carteras iniciales fabricadas ni asumir continuidad en huecos. El precio de esa
elección es restringir las conclusiones. La alternativa de reloj cíclico sigue
teniendo h=1 con cartera heredada cada ciclo y agrega una fase arbitraria; la
alternativa de bajar hasta h=0 y mantenerlo usa un estado terminal sin acciones
de entrenamiento; ninguna elimina automáticamente el problema. Aleatorizar
carteras iniciales cambiaría mu, las colas y sus interpretaciones y requeriría
justificar su distribución. Una tarea continua alineada con despliegue resolvería
otra pregunta, pero exige rediseñar objetivo/estimador y los cortes históricos.
No se adopta ninguna de estas modificaciones en v2.

### 7.2 Qué mide el contraste principal

Mantener como contraste principal **la diferencia de Sortino fuera de muestra
entre los procedimientos completos C5/C10 y C0**, incluyendo esta regla común de
despliegue, a presupuesto igual. No describirlo como verificación de la cota CVaR
ni como estimación directa del objetivo J. El desplazamiento de soporte puede
interactuar de forma diferente con cada condición; una regla común no cancela
ese efecto. Una mejora apoyaría transferencia operacional del procedimiento en
el período y semillas evaluados, no identificaría por sí sola el control de la
cola a 30 días como causa aislada de la mejora.

Para evitar ambigüedad proponemos esta convención operacional, sujeta a revisión
académica (el módulo de evaluación del repositorio aún está reservado): con
u_t=E_(t+1)/E_t−1, retornos simples netos de cada 4 h, MAR m=0 por período,

\[
DD=\sqrt{T^{-1}\sum_{t=0}^{T-1}\min(u_t-m,0)^2},\qquad
S=\frac{T^{-1}\sum_t(u_t-m)}{DD},\qquad
\Delta S_c=S_c-S_{C0}.
\]

Es Sortino por período, **sin anualización automática**. El denominador usa los
T retornos, no solo los negativos. MAR cero es referencia común a efectivo sin
interés de H2, no cota d ni cuantíl de CVaR. Si DD=0, registrar ratio indefinido,
numerador y DD; no añadir epsilon ni asignar una victoria por infinito. Congelar
el tratamiento de esas réplicas y la inferencia antes del contraste. El ejemplo
(.02,−.01,.01,−.02) tiene S=0; (.03,−.01,.01,−.02) tiene S≈.2236068. No hay una
implicación algebraica de ese aumento hacia rho_alpha(R_180)≤d.

La unidad de comparación es la réplica completa emparejada por semillas, con
una cartera por recorrido; no tratar los 2190 retornos correlacionados ni las
ventanas solapadas como réplicas independientes. La inferencia temporal y la
multiplicidad de C5/C0 y C10/C0 requieren protocolo congelado, con pilotos solo
en desarrollo. No seleccionar reloj, d, checkpoint ni fórmula de Sortino tras
ver validación. Si 2023 se utiliza para seleccionar hiperparámetros, su contraste
es de desarrollo, no una prueba confirmatoria independiente; la evaluación
final seguirá bloqueada hasta autorización y protocolo separados.

### 7.3 Regla de recorrido y afirmaciones permitidas

Una sola cartera de 10000 USDT al inicio; 2190 transiciones continuas de 2023,
sin leer ahora sus precios o resultados. Política estocástica fija y semillas
emparejadas; h=1 en cada decisión, w/z reales respecto de esa cartera inicial;
sin reajuste del normalizador, eta, crítico, multiplicador ni actor. El último
paso no recibe un horizonte más corto por conocer la fecha de corte. No se
liquida forzosamente; el patrimonio terminal conserva valoración H2.

Reportar exposición, costos, patrimonio y frecuencia de combinaciones fuera del
soporte condicionado a h=1 como diagnóstico futuro, sin usarlos para cambiar la
regla después de ver resultados. No asumir un umbral de distancia que certifique
transferencia. Los retornos móviles de 180 pasos pueden ser diagnósticos de cola
con cartera heredada y solapamiento, no muestras de mu de entrenamiento. La
restricción estática inicial no es una garantía condicional a cada estado ni
una garantía dinámica al replanificar. Un Sortino mejor tampoco certifica
cumplimiento CVaR ni protección frente a las interrupciones excluidas por B.

## 8. Decisiones propuestas y parámetros que requieren pilotos

Todo lo siguiente sigue pendiente de aprobación metodológica, no operativo.

| Estructura resuelta en v2 | Pendiente de pilotos/protocolo previo a comparación |
|---|---|
| H=180, gamma=1, lambda_GAE=1; mismo retorno para media y cola | Tamaños N_A/N_Q/N_B, precisión de cola y número K de iteraciones |
| Q independiente estima eta por cuantil empírico, sin tasa ni suavizado | Tasas actor/crítico/dual, clip y épocas; arquitectura con parámetros separados |
| A actor, luego crítico, Q nuevo, B nuevo, después dual con F_B a eta fijo | Diagnóstico de sensibilidad al error de eta y estabilidad de la aproximación PPO |
| C0 sin riesgo; C5/C10 fracciones .05/.10 y una cota común d | Valor de d, motivación económica y factibilidad; nunca elegirlo retrospectivamente por ganador |
| Igual presupuesto incluyendo auxiliares, regla de evaluación idéntica | Semillas, réplicas, análisis de incertidumbre y multiplicidad; manejo de Sortino indefinido |
| Sortino continuo evalúa transferencia operacional; h=1 y cartera única | Protocolo confirmatorio futuro; validación usada en selección se declara de desarrollo |

Una cola con masa N*.05 pequeña sigue siendo imprecisa aunque se calcule
exactamente. La independencia de sorteos no crea nueva historia económica.
No queda abierta la elección entre eta alternado sobre A y muestra independiente:
se elige Q independiente; la actualización dual se hace con B independiente de Q.
El crítico no comparte parámetros con el actor en esta referencia. Entropía y
normalización de ventajas están desactivadas en la referencia matemática;
cualquier regularización futura deberá ser común y explícita, fuera de R_H.

## 9. Cambios posteriores a aprobación — no realizados

1. Versionar ADR/configuración de objetivo finito, reloj como componente 13 y
   observaciones diferenciadas de entrenamiento/despliegue, sin modificar
   las diez características ni reajustar su normalizador.
2. Separar terminalidad del objetivo de procedencia del corte. Entrenamiento
   finito terminal en H sin liquidación; validación truncada al final de datos.
   No reinterpretar automáticamente `truncated` de H2. Revalidar manifiestos
   compatibles manteniendo originales, máscara B, índices y particiones.
3. Verificar integración de reloj/cartera, máscaras, fronteras coincidentes,
   fragmentos ensamblados y cartera continua. Auditar identificación de soporte
   sin confundir esos tests con generalización de una política.
4. Solo con autorización posterior, implementar estimador con identidad de roles
   y políticas, registro de muestras/recursos, eta fraccionario, auditoría B y
   equivalencia bit a bit con C0 en modo riesgo apagado. Probar gradientes y
   congelación efectiva antes de autorizar entrenamientos.

## 10. Evidencia, alcance y respuesta a la revisión

Se conserva v1 y su evidencia sin sobrescribirla. La reproducción coincidente
por el chat académico es un **resultado comunicado por el usuario**; esta entrega
no le atribuye logs locales nuevos. Las dos observaciones se resuelven así:

- **Distribución/evaluación:** se demuestra la diferencia del soporte conjunto,
  se mantiene explícitamente transferencia operacional y se limita el significado
  del contraste principal de Sortino. Se comparan alternativas sin proclamarlas
  soluciones automáticas. Los ejemplos de cartera y funciones coincidentes en
  entrenamiento muestran por qué verificar solo un reloj no prueba transferencia.
- **Eta/multiplicador:** se fija separación Q/A/B, políticas generadoras, orden,
  parámetros congelados, regla de cuantiles/empates, señal dual, reutilización y
  contabilidad de recursos. Se distingue rho empírico, F a eta dado y rho
  poblacional. La pseudocodificación completa está en §6.4.

[Checks v2](../evidence/adr002-proposal-v2/checks.py),
[resultados](../evidence/adr002-proposal-v2/results.json) y
[comandos](../evidence/adr002-proposal-v2/COMMANDS.md) separan:

1. **Cálculos algebraicos:** los cuatro grupos algebraicos de v1; nuevos
   contrastes de cuantil/masa, F frente a rho y aritmética de Sortino.
2. **Pruebas de especificación:** cortes/reloj de v1 con aclaración de que la
   rama parcial b=1 de v1 no se usa en v2; nuevos ejemplos de soporte,
   congelación/identidad de lotes y contabilidad de recursos. No implementan
   un recolector, optimizador ni red. No verifican transferencia de una política.
3. **Pruebas H2:** suite existente intacta, con fixtures sintéticos. Sus resultados
   se registran aparte. No se presentan como pruebas del agente propuesto ni
   como una nueva auditoría de mercado real.

El resultado v2 incluye hashes de código/configuración/pruebas/scripts/lock
comparados con cc913b6, además de huellas de los documentos y scripts comprobados.
No se cargan datos de entrenamiento, validación ni del conjunto final.

## 11. Fuentes primarias y separación entre evidencia y diseño propio

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

7. [Ross, Gordon y Bagnell (AISTATS 2011), §2](https://proceedings.mlr.press/v15/ross11a/ross11a.pdf).
   Formaliza la distribución de estados inducida por una política en aprendizaje
   secuencial. Es evidencia conceptual del problema de distribución, no un teorema
   sobre este PPO: no usamos sus garantías de imitación ni implementamos DAgger.
8. [Nassar y Ephrem (2020), §2, investigación original](https://arxiv.org/pdf/2007.06460).
   Contrasta retorno y riesgo a la baja mediante Sortino. Nuestra convención
   discreta, frecuencia, MAR cero y no anualización son decisiones propias;
   no trasladamos resultados de sus estrategias a BTC.

La referencia histórica Sortino y Price (1994), DOI
[10.3905/joi.3.3.59](https://doi.org/10.3905/joi.3.3.59), devolvió 403 al intentar
leerla; no se atribuyen a su texto ecuaciones específicas que no se pudieron
verificar. La fórmula operacional se declara expresamente como propuesta aquí.

Pardo justifica distinguir tiempo intrínseco y corte de recolección; no demuestra
transferencia de h=1 con cartera heredada. Rockafellar/Uryasev fundamenta la
representación variacional y los átomos; no garantiza precisión de una cola
empírica pequeña. Tamar aporta la derivada con umbral y sus supuestos; Q separado
no vuelve exacto el gradiente de rho con eta estimado. PPO aporta el surrogate
local, no un certificado de restricción. IJCAI-22 inspira la relajación, pero
no prescribe este calendario de lotes ni una cota congelada.

**Decisiones propias v2:** conservar transferencia móvil con alcance limitado,
Q/A/B y su orden, eta por cuantil exacto, dual sobre F_B, presupuesto con auxiliares,
convención de Sortino y prohibición de seleccionar retrospectivamente la regla.
No se ha encontrado ni se invoca un resultado publicado que garantice que esta
combinación cumple CVaR a 30 días al desplegarse continuamente.

Siguiente paso: revisión académica de v2. ADR-002 permanece abierto; ninguna
propuesta de este documento cambia el contrato H2 ni autoriza entrenamientos.
