# P2 — evolución del crítico y diagnóstico independiente del aprendizaje

**PROPUESTA PARA REVISIÓN, NO AUTORIZADA PARA EJECUCIÓN.**
Base: cierre P1 `811d882`. [Configuración candidata](P2-candidate-v1.json).
Esta entrega solo diseña/documenta: no implementa ejecutor, registra permisos,
genera trayectorias, entrena ni accede a validación/final. Cuatro épocas son una
candidata provisional; no un parámetro confirmatorio adoptado.

## 1. Recomendación principal y fundamento

Proponer **K=10 iteraciones completas**, **tres semillas nuevas**, nueve corridas
C0/C5/C10, **cuatro épocas del crítico**, con **D=64 episodios diagnósticos por
iteración**. Mantener actor de dos épocas, arquitectura, tasas, N_A=64 y
N_Q=N_B=400 de P1. Diez puntos permiten distinguir el arranque de una evolución
posterior y fijar ventanas temprana/tardía sin elegirlas tras ver resultados.
No implican convergencia. Igual tamaño D/A facilita comparar sus medidas y limita
el costo; 64 no se presenta como tamaño con potencia o precisión demostrada.

P0 explicó que las alertas pueden coexistir con mejora del MSE y que lambda
positivo no garantiza shortfalls en A. P1 obtuvo reducciones post-A del 50.74%,
58.70% y 44.44% con cuatro épocas; todos sus post-A completos siguieron peor que
el predictor cero. Es evidencia **in-sample**, insuficiente para juzgar nuevas
realizaciones. Véanse [P0 diagnóstico](../hitos/P0-diagnostico.md) y
[P1](../hitos/P1-epocas-critico.md). Esto motiva observar más iteraciones y separar
ajuste de diagnóstico, sin modificar d para conseguir auditorías favorables.

No hay brazo de dos épocas en P2: cualquier evolución es descriptiva del proceso
con cuatro épocas, política cambiante y distintas muestras. No atribuir
causalmente mejoras posteriores a cuatro épocas ni combinar P1/P2 como contraste
pareado (cambian semillas, horizonte de entrenamiento y diagnóstico).

## 2. Configuración y orden propuestos

| Bloque/semilla | Orden secuencial de condiciones |
|---|---|
| 610031 | C0 → C5 → C10 |
| 610047 | C5 → C10 → C0 |
| 610081 | C10 → C0 → C5 |

Cada corrida completa K=10 antes de pasar a la siguiente, con pausas válidas si
corresponde. Sin concurrencia ni barajado retrospectivo. Semillas explícitas,
diferentes de P0/P1; comparten coordenadas aleatorias entre condiciones para
comparación por bloques, no representan nueve fuentes independientes de mercado.

Se conservan ADR-002 v2.1, Q/A/B, muestreo uniforme con reemplazo entre los 7048
inicios H1, entrenamiento 2018–2022, normalizador sin refit, segmentación,
particiones, observación H3, inicialización de cartera, H=180, gamma=1,
lambda_GAE=1, sin bootstrap final, costos, recompensa logarítmica neta y acción.
**d=−ln(0.90)=0.10536051565782628**, común C5/C10: referencia económica de 10% de
pérdida logarítmica H180, no cota individual ni de drawdown. CPU float64/un hilo;
Adam, tasas, clip y demás parámetros exactamente en la candidata. No CUDA.
No acceso a 2023 ni 2024–2025. No órdenes reales en un exchange.

## 3. Correspondencia entre política, crítico y lote D

Usar índices k=0,…,9 (primera iteración k=0). Antes de A_k guardar copias
inmutables **pi_k** y **phi_k**. El crítico posterior **phi_(k+1)** se ajusta con
A_k generado por pi_k, después de actualizar el actor a pi_(k+1). Por tanto,
el crítico posterior aprende retornos de **pi_k**, no necesariamente de pi_(k+1).

**Decisión recomendada:** una vez completado Q/A/B y la actualización dual,
generar D_k con la copia conservada de **pi_k**, y evaluar **ambos críticos**
phi_k y phi_(k+1) sobre ese mismo D_k. No usar automáticamente el actor más nuevo.
El retorno de cada episodio D es completo y el target en posición j es

    G^D_(i,j) = sum_{t=j}^{179} r^D_(i,t),  j=0,…,179.

Sin bootstrap, recompensas netas originales. D tiene 64 trayectorias de H=180,
misma distribución inicial que A; se excluye la observación terminal como punto
de predicción. La política permanece congelada durante todo D. Se evalúa cada
estado alcanzado, incluidos reloj y cartera reales, contra su retorno restante.

| Medición | Política generadora/target | Crítico | Interpretación |
|---|---|---|---|
| A_k antes/después | pi_k | phi_k / phi_(k+1) | Ajuste sobre el lote utilizado para aprender |
| D_k antes/después | pi_k, misma muestra para ambos | phi_k / phi_(k+1) | Adaptación sobre realizaciones no usadas para ajustar; política del target fija |
| D_k post, medida principal | pi_k | phi_(k+1), entrenado con pi_k | Correspondencia entre política del ajuste y del target |
| D_k pre, medida auxiliar | pi_k | phi_k, normalmente entrenado con pi_(k−1) | Incluye desfase del crítico ante la política vigente; en k=0 es inicialización |

La comparación pre/post en D mantiene fijo el target y la política generadora.
El pre no se etiquetará como error puro del crítico para su política anterior.
No incluir un lote pi_(k+1) como medida principal: mezclaría adaptación del crítico
con cambio de política. Evaluarlo sería una pregunta distinta y requeriría otro
protocolo. Entre iteraciones cambian política, distribución de estados y targets:
ni siquiera la serie post-D es una prueba aislada de progreso causal del crítico.

Los targets Monte Carlo tienen ruido de realización; el MSE también contiene
variabilidad de retornos condicionales, no solo error de la función de valor.
Informar denominadores y distribución de G impide atribuir una caída de razón
únicamente a mejor predicción cuando puede cambiar la escala del retorno.

## 4. Independencia, secuencia y uso prohibido del diagnóstico

Crear un namespace diagnóstico propuesto y versionado, separado de A/Q/B:
`SeedSequence([seed, 7002, k, 0])` para inicios y `[seed,7002,k,1]` para acciones.
No consumir RNG global ni modificar las coordenadas actuales A/Q/B. La condición
comparte coordenadas dentro del bloque de semilla, deliberadamente; D es
independiente de flujos de aprendizaje dentro de una corrida, no independiente
entre condiciones pareadas. Identidad: campaña/corrida/semilla/k/rol D/réplica,
route_id, hash de pi_k y hashes de ambos críticos. No confundir ruta con realización.

Secuencia propuesta (pseudocódigo, **no ejecutor**):

    Inicializar; ejecutar Q0/eta0 exactamente como ADR; guardar frontera Q0.
    Para k=0,…,9:
        Capturar pi_k y phi_k inmutables antes de A_k.
        Ejecutar A_k → actor → crítico → Q_(k+1) → B_(k+1) → dual sin cambios.
        Congelar phi_(k+1); registrar A fijo pre/post y contadores Q/A/B.
        Generar los 64 D_k completos con pi_k conservada y RNG exclusivo D.
        Calcular G^D y métricas de phi_k y phi_(k+1), sin gradientes aplicados.
        Registrar solapamiento, tiempos, muestras, hashes y diagnósticos.
        Verificar finitud y ausencia de mutaciones; guardar after_dual_and_D.
        Solo entonces admitir la siguiente iteración o pausar.

D no ajusta actor, crítico, eta, multiplicador, normalizador, tasa ni parada por
rendimiento. No se recicla D como A/Q/B, ni se recomputan cuantiles con él. No se
reutiliza un D entre iteraciones: nuevos flujos k, sin elegir realizaciones.
No hay evaluación diagnóstica extra elegida por una alerta. Futuros cambios
motivados por D lo convierten inequívocamente en **diagnóstico de desarrollo**,
no evidencia confirmatoria ni conjunto reservado de prueba.

Pruebas futuras deberán comparar Q/A/B con diagnóstico encendido/apagado sobre
datos sintéticos: mismos lotes, parámetros, Adam, eta/lambda y RNG de aprendizaje.
Registrar D no debe alterar gradientes existentes. Estas pruebas no se ejecutan
en la presente propuesta.

## 5. Solapamiento y límites de generalización

D usa los mismos 7048 inicios con reemplazo. No rechazar coincidencias para
fabricar un holdout: cambiaría la distribución mu. Registrar, por iteración:

- IDs de inicios D, duplicados internos (conteo/64) y porcentaje con inicio exacto
  en A_k y, por separado, en todo aprendizaje observado hasta ese momento:
  Q0, A_0…A_k, Q_1…Q_(k+1), B_1…B_(k+1).
- Intersección de tiempos UTC de transiciones en cada segmento: ocurrencias de
  transiciones D compartidas con la unión de aprendizaje / (64×180). Informar
  además fracción sobre timestamps únicos, con ambos numeradores/denominadores.
  No confundir coincidencia de inicio con ventanas que se solapan parcialmente.
- Al cerrar, resumen retrospectivo del solapamiento con todo el aprendizaje de
  la corrida, sin usarlo para filtrar muestras o decisiones durante ejecución.

Una misma ruta puede producir distintas acciones/carteras/retornos; una nueva
realización no es un período de mercado nuevo. La independencia de RNG es
condicional al histórico fijo y no elimina dependencia temporal entre ventanas.
No afirmar generalización temporal, eficacia en 2023 o comportamiento en 2024–2025.
No usar transiciones excluidas para completar muestras o comparar ventanas.

## 6. Métricas con denominadores explícitos

Para X=A_k o D_k, con N=64 y H=180, y cada versión del crítico:

    MSE_X = sum((V_ij − G_ij)^2)/(N H)
    Z_X   = sum(G_ij^2)/(N H)
    R_X   = MSE_X/(Z_X + 1e−12)
    bias_X = sum(V_ij − G_ij)/(N H)
    normalized_bias_X = bias_X/sqrt(Z_X + 1e−12)

Z es segundo momento, **no varianza**. R usa la convención P1, aproximación a
comparar con predictor cero. Si Z<=1e−12: conservar MSE/Z/R numéricos, marcar razón
no informativa para decisiones; clasificar el criterio como pendiente de revisión,
no éxito por estabilizador. Guardar media, desviación estándar, min/max de V/G,
número de trayectorias y transiciones; también resumen por tercios fijos del
horizonte (j=0–59,60–119,120–179) para ver reloj sin tratar estados como réplicas.

En cada k: MSE/R/bias A y D pre/post; diferencia post(D−A), y reducción pre→post
si el MSE pre>0 (en cero, porcentaje indefinido). No comparar el log prepaso de
un minibatch con post-A completo como si fueran la misma observación.

Ventanas predefinidas **temprana k={0,1,2}** y **tardía k={7,8,9}**. Agregar
sumas de errores cuadrados y G² sobre las tres muestras, dividir por 3×64×180
y aplicar las fórmulas anteriores. No promediar razones con distintos denominadores.
La unidad para resumir avance es semilla/condición, no transición ni condición
repetida. Publicar las diez iteraciones y los nueve recorridos, sin omitir negativos.

Riesgo: conservar eta_Q y su política, lambda usado en A y lambda después de B,
conteo de L_A>eta_Q /64, magnitud de shortfalls, coeficientes alterados /64,
norma del componente de gradiente de riesgo y del total en pesos iniciales,
normas/clipping originales, F_B(eta_Q), rho_B, rho_Q, F_B−d y masas/empates de cola.
D no interviene. C0 conserva Q/B auxiliares y lambda=0. Una violación en B no implica
activación de shortfalls en A; gradiente de riesgo nulo con lambda=0 es esperado.

## 7. Reglas propuestas antes de resultados

Son **umbrales técnicos propuestos para revisión**, no pruebas estadísticas con
nivel de significancia ni promesas de CVaR. No aplicar bootstrap/Holm confirmatorio
sobre estos diagnósticos ni evaluar Sortino fuera de muestra.

**Avance a discusión de siguiente protocolo**, solo al completar las nueve corridas
sin fallos: en al menos **dos de tres semillas de cada condición**, simultáneamente:

1. R_D,post,tardía <=1 y <=0.8×R_D,post,temprana.
2. |normalized_bias_D,post,tardía| <=0.25.
3. R_D,post,tardía − R_A,post,tardía <=0.5.
4. Z de las ventanas usadas >1e−12, identidades/RNG y controles íntegros.

Exigir adecuación relativa al cero responde al límite pendiente de P1; la caída
20% exige evolución adicional; sesgo 0.25 y brecha 0.5 son tolerancias de ingeniería
propuestas, no derivadas de un test publicado ni escogidas con P2. Los tres criterios
se juzgan juntos por bloque, sin seleccionar semillas distintas para cada uno.
No asumir independencia de tres condiciones ni declarar un ganador financiero.

**Revisión**, si no se cumple ese criterio completo o una razón es no informativa.
Describir qué falló, sin incrementar K/épocas/tamaño de D en la misma campaña.
Si A mejora y D no, es evidencia de una brecha de ajuste/desarrollo; no identifica
por sí sola sobreajuste frente a ruido, cambio de política o composición de rutas.

**Advertencias (no parada por desempeño):** R>1, |sesgo normalizado|>0.25,
brecha post D−A>0.5; conservar además umbrales P0/P1 de ratios PPO, gradientes,
clipping, lambda, cola y diferencias Q/B. Dar tasas por familia y alcance:
10 oportunidades para cada métrica full-A/full-D pre o post por corrida;
160 minibatches del crítico (4 épocas×4 minibatches×10); 80 del actor;
10 auditorías B. Activación de riesgo: número de iteraciones activas /10 y,
adicionalmente, /9 para k>=1; shortfalls por lote /64. No sumar esas poblaciones
para comparar condiciones. Si hay fallo, denominador = mediciones efectivamente
completadas, y mostrar aparte las previstas/faltantes.

**Parada de integridad inmediata:** cualquier valor no finito, hash/cartera/tiempo
incoherente, mezcla de políticas, trayectoria parcial/censurada, cruce de segmento
u otra partición, RNG de aprendizaje alterado por D o cualquier actualización con D.
Abortar campaña y conservar lote/parcial/log; no reemplazo selectivo ni reintento
para ocultar fallo. Lo mismo ante watchdog de tiempo/RSS o corrupción/reanudación
incompatible. Falta de presupuesto antes de una unidad es pausa, no fallo.
Límite global/días/sesiones agotado: cerrar incompleto, no extender automáticamente.
Nunca parar antes por métricas favorables/desfavorables ni elegir checkpoint mejor.

## 8. Presupuesto, calibración y reanudación

Evidencia temporal **medida**, solo configuración y máquina anteriores:

| Antecedente | Q0 mediana/rango s | Iteración mediana/rango s |
|---|---|---|
| P0 (9 Q0,18 iteraciones) | 30.079 / 28.283–31.447 | 60.417 / 56.675–65.732 |
| P1 brazo4 (9 Q0,18 iteraciones) | 27.954 / 27.779–28.155 | 58.457 / 55.511–59.260 |

Proxy de planificación, **no tiempo medido P2 ni admisión de unidades**:
9×(mediana Q0 P1 +10×mediana iteración P1) ≈5512.723 s (91.879 min) para
aprendizaje. Con máximos observados ≈5586.813 s (93.114 min); multiplicar ese
último por 1.5 da ≈8380.219 s (139.670 min). No es intervalo de confianza.
**Costo D, nuevas copias, almacenamiento e instrumentación no medido**: no asignar
un número inventado ni prometer terminar en un día. P2 se propone con hasta
**tres días activos**, nunca más de 3h global/día, tres sesiones por corrida y
27 sesiones de campaña. Prioridad es presupuesto fijado, no completar a cualquier costo.

| Recurso | Por corrida | Nueve corridas |
|---|---:|---:|
| Aprendizaje Q0+10(A+Q+B) | 9040 trayectorias | 81360 |
| Transiciones de aprendizaje | 1627200 | 14644800 |
| Diagnóstico 10D | 640 trayectorias | 5760 |
| Transiciones diagnósticas | 115200 | 1036800 |
| Total trayectorias / transiciones | 9680 / 1742400 | 87120 / 15681600 |
| Pasos actor / crítico | 80 / 160 | 720 / 1440 |

Mismo presupuesto de aprendizaje y diagnóstico por condición (tres semillas).
D no incrementa contador de entrenamiento: registrar ambos más el total real.
No abaratar C0 suprimiendo Q/B. Persistir CPU/tiempo por fase, RSS, bytes de
artefactos y tiempo de cargar/copiar/diagnosticar/guardar/cerrar, no solo optimización.

Descontar **todo consumo ya registrado** de campañas del mismo día local; no
reiniciar por proceso/corrida. La fecha es America/La_Paz, timestamps UTC; cortar
antes de medianoche si no cabe unidad más reserva. Incluir preparación/verificaciones
futuras con intervalos medidos y cierre. Reserva 1800 s; preflight <=900 s;
trabajo <=8100 s y además limitado por saldo compartido. Watchdog RSS 10GiB,
memoria disponible inicial >=2GiB/disco libre >=5GiB, como P1.

**Calibración integrada, sin corrida extra:** primer Q0 de cada condición admite
el tope no estimado 1800 s. Primera unidad combinada Q/A/B+D admite 2700 s totales
de trabajo, con subtope D=900 s dentro de esos 2700, más reserva de guardado. Si no
caben esos topes en saldo, pausar antes, no usar 58 s de P1 como permiso. Medir
separadamente Q/A/B, D, inferencia y E/S en esa primera unidad programada; no cambiar
N_D/K tras medir. Un exceso del tope una vez iniciado es fallo, no pausa selectiva.
Unidades siguientes: estimación admisible 1.5×máximo completo P2 de la misma
condición/config/runtime, incluyendo D/carga/instrumentación, sin reducirla por
una muestra rápida. Si supera tope, cerrar y revisar, no ampliarlo. Guardado en
reserva sin ampliar la ventana de trabajo. Descontar también comprobaciones y cierre.

**Fronteras reproducibles propuestas:** after_q0 y after_dual_and_D. El Q/A/B
completo seguido de D es una unidad atómica de trabajo; no iniciar aprendizaje
siguiente ni una pausa planificada si D está pendiente. Conservar pi_k/phi_k hasta
completar D y sus hashes; checkpoint completo al final con actor/crítico actuales,
Adam, eta/lambda, siguiente k, RNG por rol/versionado, contadores separados,
telemetría, versión de normalizador/datos/código y ledger global. Guardar D numérico
fuera de Git y su huella; resume no genera D otra vez ni vuelve a usarlo para ajustar.
Muerte a mitad de D invalida unidad/campaña; no reanudar selectivamente desde dual
para sustituir diagnóstico. Mantener todos los checkpoints, terminal K=10 fijado.

## 9. Trabajo pendiente y decisiones para revisión

**No implementado:** perfil/permiso P2, recolector D y snapshots, esquema de frontera
compuesta, resume/RNG/contadores D, solapamiento y reglas agregadas. El supervisor
actual tiene supuestos K=2 y solo roles A/Q/B: no basta editar un JSON para ejecutar
esta candidata. No cambiar registries/hashes operativos en esta entrega.

Decisiones pendientes, con recomendación concreta:

1. Aprobar o ajustar K=10, tres semillas/orden y D=64 en cada iteración con pi_k;
   cuatro épocas siguen provisionales, sin brazo2 ni afirmación causal.
2. Aprobar los umbrales conjuntos de §7 y ventanas fijas; si se ajustan, congelarlos
   antes de cualquier ejecución P2, sin mirar resultados de P2.
3. Aprobar máximo tres días activos, límites compartidos y unidad Q/A/B+D con
   subtope D=900 s. La calibración puede concluir que el diseño no cabe, sin ejecutarlo
   con parámetros reducidos por cuenta del agente.
4. Autorizar por separado implementación/verificación sintética y, si pasan,
   ejecución del protocolo finalmente congelado. Esta solicitud **no lo autoriza**.

Aceptación previa de infraestructura futura: Q/A/B idéntico con D encendido/apagado
sobre sintéticos; políticas/targets alineados; ninguna mutación por D; MC correcto;
identidad de reanudación y contadores; presupuestos compartidos/medianoche/fallos;
solapamiento comprobado con intervalos sintéticos conocidos; estados no finitos y
particiones prohibidas rechazados; verificación de umbrales con casos algebraicos.
La presente entrega verifica solo consistencia documental/aritmética, no ese ejecutor.

[Resumen académico](P2-resumen-academico-v1.md) ·
[Comprobaciones estáticas/algebraicas](../evidence/p2-proposal/COMMANDS.md).
