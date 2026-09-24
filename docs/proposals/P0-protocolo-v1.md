# P0-technical-v1 — PROPUESTA COMPLETA, NO AUTORIZADA

Base revisada H5 `1118129`; antecedente preservado:
[H5-P0-instrumentado](H5-P0-instrumentado.md). Este documento sustituye sus
pendientes técnicos por elecciones candidatas explícitas. No registra aprobación
ni habilita ejecución. [Configuración candidata](P0-candidate.json):
`authorized=false`, `executable=false`, `bound_selected=null`.
No modificar SyntheticSettings, initial.toml, ADR-002 ni el bloqueo run_pilot.py.

## 1. Objetivo, alcance y diseño propuesto

Medir viabilidad temporal y memoria, integridad del aprendizaje y estabilidad
numérica sobre entrenamiento aceptado 2018–2022. No estimar rentabilidad fuera de
muestra, seleccionar ganadores, calibrar d por factibilidad observada ni demostrar
CVaR poblacional. No acceder a validación o final. Una sola implementación Q/A/B.

Propuesta recomendada: **tres bloques de semillas × tres condiciones × dos
iteraciones completas** por corrida. Hay nueve corridas independientes; cada
condición recibe seis actualizaciones completas de política y seis del dual
(C0 mantiene lambda=0). Cada iteración contiene varios pasos Adam. Las dos
iteraciones permiten que la segunda use el multiplicador obtenido al cerrar la
primera. Si ese multiplicador queda en cero, se registra; no se altera d para
forzar actividad de riesgo ni se añaden iteraciones por ese resultado.

Alternativas consideradas: un solo bloque reduce trabajo pero deja la inspección
sujeta a una realización; una búsqueda de arquitecturas/tasas multiplica costo y
mezcla calibración técnica con selección. Se propone un diseño único con tres
bloques, sin búsqueda. Tres bloques no justifican inferencia confirmatoria.

| Bloque | Semilla raíz | Orden secuencial |
|---|---:|---|
| 1 | 410031 | C0 → C5 → C10 |
| 2 | 410047 | C5 → C10 → C0 |
| 3 | 410081 | C10 → C0 → C5 |

Semillas elegidas a priori, distintas de pruebas H4/H5; no exploradas para elegir
resultados. Cada condición ocupa cada posición una vez. Completar o pausar la
corrida actual antes de pasar a la siguiente; nunca intercalar corridas. Se
propone como máximo una corrida por día, aunque termine temprano. Una corrida
puede ocupar hasta tres sesiones diarias; no iniciar otra el mismo día. Límite
de campaña: 27 sesiones, hasta 3h cada una; es una cota de recursos, no una
predicción de duración. No se asegura que el diseño quepa: P0 debe medirlo.

Dentro de bloque, misma inicialización actor (seed) y crítico (seed+1), mismos
streams de rutas/acciones/minibatches por las coordenadas de H4. Identificadores
`P0-v1/bloque/condicion` distintos. Q/A/B independientes por rol; compartir semilla
entre condiciones empareja rutas y números base, no trayectorias después de
actualizar políticas. Repetir un inicio es válido bajo mu uniforme con reemplazo
sobre los 7048 ids; no descartar repeticiones ni confundirlas con mercados
independientes. Los auxiliares de C0 se registran sin intervenir en su actor,
RNG de A ni parada por rendimiento. Un fallo técnico invalida conforme a ADR.

## 2. Configuración candidata y justificación

| Elección | Propuesta | Motivo y límite |
|---|---|---|
| Mercado / normalizador | H1 train, sin refit; guardas H3 | Reutilizar exactamente los productos aceptados |
| Estado / acción / recompensa | 13 componentes, logística-normal H4, net log equity H3 | Sin cambio metodológico ni contable |
| Horizonte / retorno | H=180, gamma=1, lambda_GAE=1, MC completo; sin bootstrap final | ADR adoptado |
| N_A / N_Q / N_B | 64 / 400 / 400 | A permite 4 minibatches; Q/B dan masa de cola 20 (C5) o 40 (C10), sin afirmar precisión suficiente |
| Actor y crítico | Separados; 13→32 tanh→salida, una capa oculta | Capacidad inicial moderada y costo acotado; no búsqueda de ancho |
| Épocas / minibatch | 2 actor, 2 crítico; 16 trayectorias completas | 8 pasos Adam por red/iteración, reutilización limitada de A |
| Tasas | Actor 1e-4, crítico 1e-3, dual 0.1 | Punto inicial conservado de candidatos H4; crítico con paso mayor. Heurística a diagnosticar, no valor validado |
| PPO clip | 0.2 | Candidato H4 explícito, no justificado por ser default de biblioteca |
| Adam | betas=(0.9,0.999), eps=1e-8, weight_decay=0 | Mantener implementación verificada; no introducir otra variable |
| Fragmentos | 60 pasos, ensamblaje obligatorio de 180 | Ejercita continuidad sin cambiar objetivo |
| Regularización | Sin entropía, normalización de ventajas ni clipping de gradientes | Referencia adoptada |
| Runtime | CPU float64, torch/interop/BLAS=1 hilo, determinismo activado | Aislar variación por paralelismo; no presume ser configuración más rápida |
| Iteraciones | K=2 por corrida | Cubre uso del dual anterior, sin pretender convergencia |

Son elecciones propias para someter a revisión, no resultados publicados ni
herencia automática de SyntheticSettings. Igual configuración entre condiciones,
salvo alpha y mecanismo de riesgo. En C0 alpha=0 en el JSON **identifica ausencia
de restricción**, no se pasa 0 a funciones que dividen por alpha: para diagnósticos
auxiliares C0 se conserva alpha=0.05 como en H4, lambda exactamente cero.

Contabilidad prevista por corrida:
`400 + 2*(64+400+400) = 2128` trayectorias,
`2128*180 = 383040` transiciones, 16 pasos Adam actor y 16 crítico, dos duales.
Por condición (tres bloques): 6384 trayectorias, 1149120 transiciones y 48 pasos
por red. Campaña completa: **19152 trayectorias, 3447360 transiciones, 144 pasos
actor + 144 crítico**, 18 duales. Incluye Q0 y Q/B nuevos también en C0.
Contar aparte preflight, guardado, diagnósticos y consumo de corridas inválidas;
no borrar recursos fallidos para hacer coincidir el presupuesto válido.

## 3. Cota común: alternativas para decisión del investigador

PPO usa R=sum r=log(E180/E0); riesgo L=-R. Para alpha=.05 o .10:
`F_alpha(eta)=eta+E[(L-eta)+]/alpha`; restricción poblacional
`CVaR_alpha(L)=min_eta F_alpha(eta) <= d`. Misma d para C5/C10.
No identificar rho_B empírico, F_B(eta_Q) y restricción poblacional.

| Referencia económica simple l | d=-log(1-l) | Lectura y compromiso |
|---|---:|---|
| 5% | 0.05129329438755058 | Exigencia de cola más estricta; mayor posibilidad de lambda activa y de dificultad de optimización |
| 10% | 0.10536051565782628 | Opción intermedia para discusión; permite más pérdida de cola que 5%, menos que 20% |
| 20% | 0.22314355131420976 | Cota más permisiva; puede producir dual inactivo y menor contraste del mecanismo en P0 |

**Recomendación provisional para discutir: 10%. Elección pendiente, sin valor
operativo.** No se dispone aquí de una preferencia económica declarada que haga
óptima ninguna opción; escogerla requiere tu criterio sobre tolerancia a pérdida.
No se ha consultado validación ni resultados de entrenamiento para proponerlas.
Puedes escoger otra d positiva y justificarla antes de ejecutar; no probar las
tres para quedarse retrospectivamente con la que favorezca resultados.

La conversión expresa una referencia económica en escala logarítmica; no afirma
que CVaR simple sea igual al CVaR logarítmico. Si la restricción se cumpliera en
la distribución objetivo, acotaría la media de pérdidas logarítmicas de su cola,
con masa fraccionaria en empates; equivale a un umbral de media geométrica del
cociente de patrimonios en esa cola, no a un máximo de pérdida individual.
No es un límite de drawdown ni una garantía en evaluación continua. C5 considera
una cola más extrema que C10. La referencia de efectivo total del simulador no
prueba factibilidad del actor logística-normal, que no representa exactamente
acción cero. Dos iteraciones no prueban cumplimiento ni su imposibilidad.

## 4. Calendario por corrida y persistencia

1. Inicializar redes independientes, lambda0=0; congelar pi0. Q0 de 400 episodios
   completos estima eta0 con menor cuantil empírico y masa fraccionaria adoptados.
2. Para k=0,1: A_k nuevo de pi_k congelada; 64 episodios completos. Congelar G,
   V_old, old logprob, ventajas, coeficientes de riesgo, eta y lambda.
3. Actualizar actor durante dos épocas/minibatches; congelar pi_(k+1). Actualizar
   crítico separado después durante dos épocas con MC sin penalización.
4. Pi_(k+1) genera Q_(k+1) nuevo (400); fijar eta nuevo. B_(k+1) independiente
   (400) estima F_B a ese eta y rho_B diagnóstico. Actualizar lambda una vez
   para iteración siguiente. C0 fuerza lambda=0.
5. Guardar checkpoint completo `after_q0` y tras **cada** `after_dual`, cualquiera
   que sea el resultado de riesgo; cerrar en K=2. No escoger el mejor checkpoint.

La pausa solo ocurre en fronteras completas. No reemplazar una realización
fallida ni ensamblar fragmentos de políticas distintas. Solo el checkpoint más
reciente y journal coherente permiten reanudar una pausa planificada. Fallo,
watchdog, proceso interrumpido o salida sin journal coherente invalidan la corrida.
Se detiene la campaña para diagnóstico; no se completa el bloque repitiendo solo
la condición fallida. Cualquier repetición exige nueva revisión/versionado y
conserva las corridas originales; no se oculta como continuación.

## 5. Primera medición temporal, sin duración inventada

**Situación actual:** H5 no tiene estimación de iteración de aprendizaje de mercado,
ni watchdog duro ni presupuesto diario reanudable. No convertir tiempos sintéticos
ni los tres episodios congelados H5 en estimaciones. El siguiente procedimiento
es una ampliación técnica propuesta que deberá implementarse y probarse después
de la autorización; hoy el ejecutor sigue cerrado.

Se elige calibrar dentro de las primeras corridas previstas, evitando corridas
auxiliares o semillas adicionales. Sus transiciones/actualizaciones ya están
incluidas arriba. El reloj inicia antes de carga/preflight; máximo 180 minutos
por día, 15 para preflight, hasta 135 adicionales de trabajo, 30 de cierre.
Si preflight termina antes, no se amplía la ventana de trabajo: fin de trabajo
como máximo en `min(fin_preflight+135 min, inicio_dia+150 min)`.

**Arranque sin estimación: excepción de medición explícita, no truco para poner
una estimación igual a cero.** En la primera corrida de cada condición se admite
una medición Q0 con tope 30 min y una primera iteración completa con tope 45 min.
Son límites de exposición computacional propuestos, no predicciones de duración.
Ambos deben caber íntegros en la ventana de trabajo antes de lanzarse; si no,
pausa en frontera y medición al día siguiente. Si exceden su tope, se invalida y
para la campaña. No reintentar hasta lograr un tiempo favorable.

Un supervisor externo al trabajador, con reloj monotónico, registra el estado
running antes de lanzar la unidad y vigila tiempo/RSS cada segundo. Límite de
unidad = menor entre tope aplicable y fin de trabajo diario. Al límite pide
terminación; tras 10 s sin salida fuerza terminación. No acepta pesos/episodios
parciales ni los usa para estimar duración de una unidad completa. La reserva
absorbe latencia de terminación y registro. No se promete un límite físico
infalible frente a bloqueo del SO; registrar cualquier incumplimiento. Las
señales de parada y supervisor deben probarse sintéticamente antes de mercado.

Después de obtener unidades completas para la **misma condición/configuración/
máquina/hilos/código**, definir:
`estimacion_unidad = 1.5 * max(tiempos_completos_observados_unidad)`.
Registrar lista de tiempos, muestra n y factor. El margen 50% es una decisión de
prudencia para revisar, no un intervalo de confianza. Estimaciones nunca decrecen
ni se comparten automáticamente entre condiciones. La primera observación es
provisional; la segunda iteración de la misma corrida comprueba su utilidad.
Unidades medidas incluyen journal y preparación/targets dentro de Q0 o iteración;
el guardado se mide por separado y usa la reserva. No omitir tiempos no atribuidos.

Para unidades siguientes, iniciar solo si su estimación cabe antes del fin de
trabajo y sigue quedando la reserva diaria de cierre. De lo contrario, checkpoint
y pausa planificada, sin reducir K o lote. Si la duración real supera la estimación,
registrar desviación; no abortar por el mero error de predicción mientras no
exceda el tope técnico: 30 min Q0 / 45 min iteración en todas las sesiones.
Actualizar máximo tras completar. Si la estimación conservadora supera el tope
o ya no cabe en una sesión vacía, parar campaña como diseño inviable hasta revisión.

Al llegar a sesión 3 sin K=2 completo, terminar como **incompleta por presupuesto**,
con evidencia; no presentar una iteración como réplica válida ni añadir días
silenciosamente. Si todas completan, resultan tres Q0 y seis iteraciones medidas
por condición; informar tiempos individuales, rango y máximos, no solo media.
No presentar ese pequeño conjunto como garantía temporal futura.

### Reanudación entre días

Proponer dos registros enlazados e inmutables: consumo acumulado de corrida
(trayectorias/transiciones/Adam/segundos de trabajo+guardado) y sesión diaria
(id/fecha/inicio/deadlines/consumo). Nueva sesión solo tras pausa planificada y
checkpoint coherente, sin retroceder contador acumulado. Impedir dos sesiones el
mismo día y no transferir minutos sobrantes. Máximo tres sesiones/corrida.
Un reinicio del proceso durante la misma sesión conserva el deadline; no crea
otras tres horas. Registrar días de descanso sin consumo.

Esto **no existe aún en H5**: su TimeBudget acumulado no se debe resetear ni
reemplazar al cargar. Antes de ejecutar P0, añadir controlador diario alrededor
del presupuesto acumulado, versionar checkpoint/protocolo y probar conservación
con relojes ficticios. No cambiar Q/A/B ni reusar checkpoints H5 incompatibles.

## 6. Integridad, diagnóstico y parada concretos

**Entrada por sesión:** protocolo autorizado con d seleccionada, hashes de código,
lock, H1 y scaler; CPU float64 y número de hilos fijos; 7048 ids; guardas de
train/normalizador; al menos 2 GiB disponibles y 5 GiB libres en disco. Si falla,
no lanzar trabajo. Anclar H1 al manifiesto versionado, no a un JSON arbitrario.
No modificar costos, particiones, características ni reloj. Solo otra prueba
sintética del supervisor y de la integración autorizada será condición técnica
previa; no se declara cubierta por estos cálculos estáticos.

| Regla propuesta | Acción |
|---|---|
| Hash/config/scaler/identidad incompatibles; observación fuera de train; episodio !=180 o discontinuo, terminalidad/reloj H3 incorrectos | Invalidar corrida y detener campaña |
| No finitud de estados, pérdidas, logprob, gradientes, ratios, eta, lambda o parámetros; acción saturada 0/1 | Invalidar, nunca clipping/resampling correctivo |
| max abs(old logprob recalculada−almacenada)>1e-10 | Invalidar por inconsistencia de política |
| abs(sum r−log(E180/E0))>1e-10, E<=0 o contadores distintos de lo planificado | Invalidar; investigar sin usar pesos parciales |
| Política/targets/coefs cambian fuera de su fase; lambda C0!=0; B reutiliza realización Q/A | Invalidar; no es una fluctuación estadística |
| RSS proceso trabajador >10 GiB; supervisor/proceso falla; tiempo supera tope de unidad | Invalidar corrida, registrar recursos parciales y detener campaña |
| Estimación no cabe y frontera coherente | Pausa planificada y checkpoint; no es un fallo |
| Tres sesiones consumidas sin completar K=2 | Incompleta por presupuesto; detener campaña, no resultado comparable |

Diagnósticos **sin detener corridas ni modificar hiperparámetros**: registrar
cada minibatch/fase y marcar advertencia si se cumple cualquiera:

- Ratio fuera de [0.5,2] o fracción de clip PPO activo >0.5.
- Norma L2 de gradiente >100 (sin recorte); error relativo del crítico
  `MSE(G,V)/(mean(G²)+1e-12)>1`, referencia predictor cero.
- Más de 1% de acciones en `(0,1e-6)` o `(1−1e-6,1)`; los extremos exactos
  siguen siendo fallos de representación, no advertencias.
- `abs(rho_Q−rho_B)>0.05` log unidades, masa alpha*N<20 o lambda>1.

Umbrales propios de alerta inicial, no pruebas estadísticas ni garantías de
convergencia. Registrar exposición media/rango, costos, recompensas, critic MSE,
ratios y fracción fuera del intervalo PPO por separado de clip activo, eta,
empates/masa fraccionaria, rho_Q/rho_B/F_B, F_B−d, lambda antes/después.
Q/B discrepantes no permiten atribuir precisión poblacional ni independencia
histórica: los episodios se solapan. No se propone bootstrap de cola en P0;
la evaluación formal de precisión se diseñaría para P1 con autorización aparte.

Al completar los nueve casos: puerta verde técnica solo si todos íntegros,
K=2 y sin advertencias. Si hay advertencias, informe de estabilidad pendiente y
propuesta de revisión común antes de P1; no borrar casos ni elegir ganadores.
F_B>d o rho_B>d se informan sin parar ni seleccionar: la meta P0 es técnica,
no factibilidad. F_B<=d tampoco autoriza salida temprana. Un Sortino superior
no demuestra CVaR; P0 no calcula Sortino de validación ni cambia inferencia ADR.

## 7. Entrega esperada y decisiones

En cada corrida: protocolo/hash/autorización, runtime/hilos, tiempos de cada fase,
CPU/RSS, tiempos totales sin atribuir y guardado, contadores acumulados/diarios,
identidades de realizaciones/rutas/políticas, diagnósticos anteriores, checkpoints
de todas las fronteras y journal. Datos/checkpoints voluminosos fuera de Git;
manifiestos, huellas, resúmenes y fallos versionados. No reescribir evidencias.

Pendiente de tu respuesta: **elegir d común** y **aprobar o ajustar este diseño P0**
(configuración/semillas/orden, topes, excepciones de medición y sesiones). Esa
aprobación debe precisar si autoriza implementación del ejecutor/supervisor y
posterior P0 acotado; mientras no ocurra, ambos siguen bloqueados. Los valores
podrán congelarse en una versión autorizada tras esa respuesta, nunca tomando
esta propuesta como permiso implícito. No se modificó la tesis.
