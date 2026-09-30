# P2R: repetición íntegra tras apagado, propuesta para revisión

**PROPUESTA PARA REVISIÓN; NO AUTORIZADA PARA IMPLEMENTACIÓN NI EJECUCIÓN.**
Antecedente: P2 `a2014e4` quedó `failed` a mitad de una unidad y la
[investigación](../hitos/P2-perdida-supervisor-diagnostico.md) encontró un
apagado del equipo en el mismo segundo. Esta propuesta no reactiva el permiso
P2, no reutiliza su raíz ni convierte sus cinco corridas completas en parte de
una nueva matriz. Validación 2023 y final 2024–2025 siguen excluidos.

## 1. Alternativas y decisión recomendada

| Alternativa | Ventaja | Límite | Recomendación |
|---|---|---|---|
| Repetir **las nueve corridas enteras** con semillas, orden y método P2 en raíz nueva | Mantiene una comprobación de reproducibilidad determinista y no selecciona qué condiciones repetir | Consume de nuevo recursos y las primeras cinco son resultados de desarrollo ya observados | **Sí, P2R** |
| Nueve corridas con semillas nuevas | Aporta otro bloque de realizaciones | Cambia la pregunta experimental y no reconstruye el diseño interrumpido; también sigue siendo desarrollo sobre el mismo histórico | Solo en otro protocolo |
| Retener las cinco P2 y ejecutar las cuatro faltantes | Ahorra cómputo | Selecciona supervivientes de una campaña fallida, mezcla sesiones/procedencias y oculta la unidad parcial | **Rechazar** |

P2R empezaría desde Q0 para **todas** las condiciones en una raíz exclusiva,
con un ledger y permiso nuevos. Las cinco corridas P2 previas pueden servir
como referencia de reproducibilidad y tiempos, nunca como observaciones de la
matriz P2R ni como criterio para elegir checkpoints. Si P2R también se
interrumpe, se cierra como fallida: no hay derecho automático a P2R2.

## 2. Contrato científico congelable

P2R conserva literalmente el diseño y configuración algorítmica de
`P2-infrastructure-v1.json` (SHA256
`d5fa2f2726cd6458df3c290e7b58c591f11310c7a9b645c47a5fb6bd419e5238`):
ADR-002 v2.1, C0/C5/C10, política logística-normal, actor y crítico
separados, Q/A/B, `d=−ln(0.90)=0.10536051565782628` común C5/C10, H=180,
`gamma=lambda_GAE=1`, recompensa logarítmica neta, costos, contabilidad y
observaciones H3. No se interpreta d como tope individual o de drawdown.

| Bloque | Orden sin concurrencia | K | Q0 | Cada k=0,…,9 |
|---|---|---:|---:|---|
| 610031 | C0 → C5 → C10 | 10 | 400 Q | 64 A + 400 Q + 400 B + 64 D |
| 610047 | C5 → C10 → C0 | 10 | 400 Q | 64 A + 400 Q + 400 B + 64 D |
| 610081 | C10 → C0 → C5 | 10 | 400 Q | 64 A + 400 Q + 400 B + 64 D |

El crítico conserva cuatro épocas **provisionales**, actor dos, minibatch 16,
red oculta 32/tanh, Adam, tasas y clipping del JSON citado. Q/B auxiliares de
C0 se conservan para igualar recursos y no alterar RNG de A. D usa la copia
congelada de `pi_k` que produjo A_k y RNG independiente; ambos críticos se
evalúan contra los mismos retornos Monte Carlo completos. D no ajusta ninguna
variable, no cambia Q/A/B y no excluye solapamientos de mercado; se reportan.
Muestreo uniforme con reemplazo entre 7048 inicios H1, normalizador persistido
sin refit, solo entrenamiento aceptado [2018-01-01, 2023-01-01) UTC. Huellas de
manifiesto y scaler de H1 se fijarán al aprobar el ejecutor; toda diferencia
de identidad impide iniciar. No se usará validación ni prueba final.

Presupuesto esperado **por contrato**, no por estimación: 81360 trayectorias
de aprendizaje/14644800 transiciones, 5760 D/1036800 transiciones,
720 pasos actor y 1440 crítico para nueve corridas completas. Una unidad
Q/A/B+D no se divide ni se trata como muestra CVaR si falta D. Las únicas
fronteras reanudables son `after_q0` y `after_dual_and_D`. No se eligen
checkpoints por rendimiento.

## 3. Protección frente a pérdida de sesión y apagado

Antes de considerar una autorización de mercado se necesita una **infraestructura
P2R nueva** y pruebas sintéticas. El supervisor debe ejecutarse como servicio
local administrado por `systemd --user`, independiente de la sesión de Codex o
de un terminal; el journal de la unidad y un registro propio deben conservar
mensajes de inicio, señales, parada y salida. Si la persistencia del gestor de
usuario tras cerrar sesión no está configurada y verificada, el preflight falla;
no se cambiará la configuración del sistema de forma implícita. El apagado
físico siempre puede detener un servicio: esta medida reduce la dependencia
del chat, **no garantiza** continuidad ante pérdida de energía.

El supervisor escribirá con sincronización durable un heartbeat cada ≤5 s:
UTC, tiempo monotónico, día La Paz, campaña/corrida/unidad, fase, PID/cgroup,
último contador y estado de alimentación. Un manejador de `SIGTERM`/`SIGINT`
intentará registrar el motivo antes de salir. Si hay señal **entre** unidades,
persistirá pausa válida y no iniciará otra. Si llega **dentro** de Q0 o
Q/A/B+D, marcará campaña fallida, guardará progreso/log/parcial y nunca
convertirá esa unidad en checkpoint. Si muere sin manejador o se apaga la
máquina, el primer preflight posterior cotejará heartbeat, bloqueo y journal,
marcará interrupción como fallo y se detendrá sin lanzar worker. Un worker no
debe sobrevivir a su supervisor; conservar el cierre por cgroup y la guarda
de muerte del padre. No se genera un nuevo D para sustituir uno parcial.

Como **guardas de disponibilidad**, no como explicación retrospectiva del
apagado P2: alimentación AC conectada y batería legible ≥50 % al preflight;
antes de cada unidad, AC y batería ≥40 %, memoria disponible ≥4 GiB y disco
libre ≥10 GiB. Sensor ausente o lectura incoherente: no iniciar. Si falla una
guarda entre unidades, pausa completa con motivo; si ocurre dentro, intentar
terminar la unidad únicamente mientras el watchdog y la reserva permitan
guardarla, después pausar. Una orden de apagado o pérdida del worker a mitad
de unidad es fallo permanente. Estas guardas se deben verificar con fixtures
y lectura local **antes** de cualquier permiso; no se derivan como causa del
P2 anterior. No se modifica CUDA ni drivers.

## 4. Presupuesto global y admisión predefinidos

Máximo **10800 s por día America/La_Paz**, compartidos con toda campaña del
repositorio e incluyendo preparación, carga, preflight, aprendizaje, D,
instrumentación, guardado y cierre; timestamps UTC. Hasta **tres días activos**,
tres sesiones por corrida y 27 sesiones de campaña, sin concurrencia ni
reinicio del contador al cambiar proceso o corrida. Se conserva una reserva de
1800 s para cierre; preflight ≤900 s y trabajo ≤8100 s/día, además del saldo
real `10800 − débitos externos − tiempo consumido − reserva`. Si el saldo no
cubre la estimación admisible de la **unidad siguiente**, pausar antes de
comenzarla. La medianoche local no concede una unidad en curso más tiempo.
El 30/09/2026 La Paz queda excluido para P2R: el tiempo de cierre del P2
interrumpido no se puede medir con precisión. Para cualquier otro día con una
campaña previa de débito incompleto se asignarán conservadoramente los 10800 s
como consumidos y no se iniciará P2R ese día.

Primera Q0 de cada condición: reserva de admisión 1800 s; primera unidad
Q/A/B+D: 2700 s, con subtope D=900 s dentro de ella. Para las siguientes de
la misma condición y runtime, exigir `1.5 × máximo tiempo completo medido`
sin rebajar la estimación por una unidad rápida; si supera el tope o saldo,
pausar o cerrar para revisión, nunca ampliar límites automáticamente. Un
exceso de tope, RAM 10 GiB del worker, reloj discontinuo >2 s o cierre fuera
de reserva es fallo, no pausa. La primera unidad mide D real sin corrida de
calibración extra. Los valores P2 ya medidos —cinco corridas completas entre
695.693 y 763.875 s de unidades, D total 243.401 s en esas cinco— orientan
factibilidad, **no validan** el costo del nuevo supervisor ni sustituyen la
admisión conservadora. Los 282 MiB por corrida observados tampoco garantizan
uso futuro de disco. Sin medición del costo nuevo, no se promete día de cierre.

Se registrarán intervalos medidos por fase y totales, RSS pico del worker y
del proceso supervisor, disco, D y débito compartido. `active_seconds` no
podrá interpretarse como cero si hay unidades cerradas o heartbeats tras un
apagado; ante esa discrepancia se informa rango inferior y tiempo faltante.

## 5. Criterios, advertencias y decisión al final

**Entrada obligatoria:** permiso P2R propio en commit separado, ejecutor y
servicio probados sintéticamente, código/configuración/protocolo congelados y
publicados, P0/P1 y P2 original con huellas intactas, datos/scaler coincidentes,
ninguna otra campaña activa, host y presupuesto aptos, raíz nueva y guardas de
train-only verificadas antes de cargar trayectorias. El registro P2 anterior no
es permiso P2R. Cualquier fallo de entrada bloquea el inicio; no se corrige
modificando umbrales durante la campaña. El metadato heredado
`market_training_executed=false` deberá corregirse y probarse sin cambiar
salidas Q/A/B+D antes de congelar el código nuevo.

**Integridad por unidad:** 180 transiciones por trayectoria; políticas,
targets y RNG coherentes; todas las muestras Q/A/B/D, eta, dual, redes,
optimizadores y contadores completos; finitud; hashes de datos, normalizador,
código, artefactos D y checkpoint; no cruce de segmento/partición ni acceso
prohibido; D sin gradientes ni mutaciones. La comparación sintética con D
encendido/apagado debe demostrar Q/A/B idéntico y la reanudación desde ambas
fronteras debe reproducir una ejecución continua. El ledger y heartbeat
deben tolerar cierre planificado, medianoche, suspensión de sesión y rechazo
de estado corrupto; una señal en unidad debe dejarla inválida.

**Parada de campaña:** cualquier no finito, violación de identidad o integridad,
trayectoria incompleta, watchdog, señal/apagado durante unidad, checkpoint
incompatible o imposibilidad de conciliar presupuesto ⇒ `failed`, evidencia
preservada, sin reintento ni sustitución selectiva. Agotar días/sesiones ⇒
`incomplete`, sin ampliación automática. Advertencias de PPO/crítico/riesgo
se publican con numerador y denominador, pero no adelantan parada por
desempeño favorable o desfavorable. Tampoco se ajusta d, K, D, épocas o
semillas durante la campaña.

**Resultado técnico**, solo si nueve corridas K10 cierran íntegramente: para
cada condición, al menos dos de las tres semillas deben cumplir **juntas**
las reglas P2 originales sobre D posterior: ventanas temprana k={0,1,2}
y tardía k={7,8,9}, `Z>1e−12`, `R_D,tardía≤1`, `R_D,tardía≤0.8 R_D,temprana`,
`|sesgo_normalizado_D,tardía|≤0.25` y
`R_D,tardía−R_A,tardía≤0.5`. Agregar sumas SSE/targets/errores y
denominadores antes de formar razones, como en P2. Si las nueve cierran pero
la regla no se cumple, resultado `review`; si falta alguna, `not_evaluable`.
Se publican además MSE absoluta/relativa en A y D, sesgo, terceros del
horizonte, solapamiento, eta/lambda, shortfalls en A, gradiente de riesgo y
auditorías B. Ningún resultado de desarrollo se convierte en inferencia
confirmatoria, rendimiento financiero o garantía poblacional de CVaR.

## 6. Evidencia, cierre y decisiones requeridas

Conservar íntegros P0/P1/P2 y la unidad parcial P2. P2R escribirá en raíz
versionada por nombre y **nunca existente**; checkpoints y trayectorias fuera
de Git, con manifiestos y hashes pequeños en Git. Publicar comando exacto,
versiones, huellas, journal del servicio, ledger, heartbeats, pausas/fallos,
tiempos por fase, recursos, métricas por corrida, advertencias por oportunidad
y cierre de solo lectura. Antes de autorizar, se revisará en particular el
comportamiento del servicio ante logout y apagado sintético, sin mercado. No
usar validación ni final para elegir infraestructura o checkpoints. La tesis
permanece sin cambios.

**Para revisión del usuario:** (1) aceptar o ajustar la repetición completa
de las mismas tres semillas, sin mezclar P2; (2) aceptar las guardas de
alimentación y el servicio de usuario como condición de entrada; (3) aprobar
por separado la implementación/verificación sintética y, posteriormente,
la ejecución histórica. Este documento no concede ninguna de esas
autorizaciones.
