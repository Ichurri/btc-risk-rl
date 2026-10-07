# Estado vigente — P2R descriptivo adjudicado; P3 solo propuesto

El usuario autorizó el 07/10/2026 la campaña P2R v2 como **diagnóstico de
desarrollo** exclusivo de entrenamiento 2018–2022. El registro y permiso
fijados están en `38fc54b`; se repitieron preflight, huellas, suite completa
(289 pruebas) y Ruff antes de lanzar la raíz nueva
`artifacts/p2r-approved-v2`. Tres sesiones `systemd --user` terminaron
con `Result=success`: dos pausaron entre unidades completas por guarda de
recursos, y la tercera cerró las nueve corridas. El ledger marca
`completed`, cursor 9, **99 unidades aceptadas**, ninguna pendiente; cargó
6.893,096 s de 10.800 s el 07/10/2026 La Paz. La primera Q/A/B+D midió
66,285994 s de pared y 4,724537 s de D. El auditor releyó las cadenas,
99 checkpoints y 5.760 archivos D; todas las huellas de código de
checkpoints coinciden. Ver el
[informe de cierre](hitos/P2R-ejecucion-historica-v2.md) y los
[comandos/evidencias](evidence/p2r-market-2026-10-07/COMMANDS.md).

La [revisión de solo lectura del metadato](hitos/P2R-metadato-entrenamiento-revision.md)
demostró que el generador heredado excluye `authorized_p2r_only`: los 99
reportes marcan `false`, aunque las 90 unidades Q/A/B+D tienen pasos de
optimizador y cambios de pesos respaldados por checkpoints. El supervisor
no verificaba ese campo. La
[adjudicación](protocols/P2R-adjudicacion-metadato-v1.md) reconoce que
faltó la verificación previa, mantiene el resultado numérico `review` y
limita P2R a diagnóstico **descriptivo de desarrollo**. No declara
cumplido retrospectivamente el preflight ni aceptación confirmatoria.
El [análisis tardío](hitos/P2R-error-valor-tardio.md) y su evidencia
fundamentan la [propuesta P3](proposals/P3-protocolo-v1.md), todavía
**no autorizada para implementación ni ejecución**.

**Siguiente tarea:** revisión académica del diseño P3, su intervención y
criterio antes de autorizar implementación. La corrección prospectiva del
marcador y su rechazo por el supervisor son condiciones de entrada de
P3; no se implementaron aquí. No reabrir P2R ni repetir corridas o editar
sus reportes. P2 permanece `failed` y separado; validación y final siguen
protegidas. `.python-version` continúa eliminado solo localmente.

---

# Estado anterior — presupuesto P2R analizado, campaña bloqueada

El [análisis temporal P0/P1/P2](hitos/P2R-analisis-presupuesto-P0-P1-P2.md)
usa solo ledgers y JSON de unidades completas, con huellas verificadas.
P2 midió 6 Q0 y 51 Q/A/B+D cerradas (medianas 29,038 y 69,067 s),
incluidas 51 D por 248,335 s; no aporta tiempo global fiable después de
la interrupción ni costo del nuevo supervisor P2R histórico. Los
[escenarios](evidence/p2r-budget-analysis/results.json) contrastan 99
unidades con 24.300 s máximos de trabajo en tres días, separando tiempos
medidos de sobrecostos supuestos. El
[resumen académico](hitos/P2R-presupuesto-resumen-academico.md) conserva
los límites de interpretación.

**Siguiente tarea:** revisión académica del análisis de factibilidad.
No se activó `MARKET_EXECUTION_ENABLED`, no se creó raíz/registro P2R y
no hubo entrenamiento. Una campaña posterior exige autorización separada;
su regla de presupuesto sigue siendo admisión por unidad, pausa antes de
abrir una que no cabe y fallo irreversible si se interrumpe una activa.
P0/P1/P2 y las sondas permanecen intactos; `.python-version` continúa
eliminado solo localmente.

---

# Estado anterior — preparación final P2R v2 revisada, campaña bloqueada

La [revisión final](hitos/P2R-preparacion-final-v2.md) desde `dc6285c`
ejecutó 288 pruebas y Ruff, cotejó el manifiesto derivado con el ancla
`cd6b686`, verificó los 12 hashes H1 y las huellas P0/P1/P2, y repitió el
[preflight vigilado](evidence/p2r-final-readiness/preflight-opens.json):
cero aperturas de CSV H1 compartidos, cero trayectorias y cero
actualizaciones. El hash H1 completo fue una lectura de integridad separada
del preflight. Las lecturas de alimentación, recursos, Linger y presupuesto
están fechadas y son instantáneas. El informe contiene el procedimiento de
lanzamiento/parada **para revisión, no ejecutado** y los límites que pueden
impedir completar nueve corridas.

**Siguiente tarea:** revisión humana del informe y, solo si se decide
autorizar la campaña, registrar permiso específico en un commit separado y
repetir el preflight inmediatamente antes de cualquier unidad. Actualmente
`MARKET_EXECUTION_ENABLED=False`, sin registro ni raíz P2R histórica. No
reanudar P2; validación y prueba final protegidas. La eliminación local
previa de `.python-version` permanece sin versionar.

---

# Estado anterior — derivado H1 exclusivo de entrenamiento P2R auditado

La [exportación auditada](hitos/P2R-training-shard-export.md) creó
`data/processed/p2r-training-h1` sin filas de 2023, conservando el
calentamiento y las 7.048 rutas aceptadas. La lectura puntual de los CSV H1
compartidos se limitó a hashes y cotejo byte/fila del prefijo, autorizados
para este hito. La [segunda auditoría](evidence/p2r-training-shard-export/re-audit.json)
confirmó recuentos, exclusiones, segmentos, rutas y normalizador sin refit.
El manifiesto derivado quedó fijado en `cd6b686`; el
[preflight con vigilancia de aperturas](evidence/p2r-training-shard-export/preflight-opens.json)
registró cero aperturas de los cinco CSV H1 compartidos, cero trayectorias,
cero actualizaciones y estado `read_only_ready_campaign_disabled`.

**Siguiente tarea:** revisión del informe, código y evidencias del
derivado. El permiso P2R sigue inactivo y la campaña requiere autorización
y registro separados, más preflight repetido en ese momento. No reanudar
P2 fallido ni ejecutar unidades por este hito. H1, P0/P1/P2 y sondas
anteriores permanecen intactos. La eliminación local de `.python-version`
sigue sin versionarse. Validación y prueba final permanecen protegidas.

---

# Estado anterior — preflight P2R aislado y sonda de optimizador sintética

Desde `93515ef` se corrigió la ruta P2R que antes verificaba hashes de
CSV H1 completos con filas de 2023. El ejecutor y su preflight exigen
ahora un [derivado exclusivo de entrenamiento](protocols/P2R-training-shard-contract-v1.md)
con hashes propios y ancla H1. **El derivado histórico no existe ni tiene
huella registrada**: preflight falla cerrado antes de abrir los CSV
compartidos. La vigilancia de aperturas y los rechazos de enlaces se
verificaron solo con fixtures sintéticos. Una [sonda sintética de señal
durante cálculo de gradientes](hitos/P2R-preflight-optimizer-signal.md)
terminó `failed`, conservó Q0 por hash y no aceptó la unidad parcial.
La raíz 07 muestra un error del envoltorio de prueba; la 08 verificó la
salida 1. El [resumen académico](hitos/P2R-preflight-optimizer-resumen-academico.md)
y las evidencias pequeñas están versionados.

**Siguiente tarea:** revisar el contrato de exportación y la sonda.
Una exportación auditada del prefijo H1, el registro de su hash y una
autorización independiente de campaña son pasos pendientes; este hito
no los concede. P0/P1/P2 y sondas 01–06 intactos. No reanudar campañas
fallidas, no ejecutar P2R histórico ni consultar validación o prueba
final. La eliminación local de `.python-version` sigue sin versionarse.

---

# Estado anterior — ejecutor P2R v2 integrado, campaña bloqueada

La autorización posterior a la sonda 06 permitió **solo** implementar y
verificar el ejecutor histórico P2R. El supervisor común enlaza nueve
corridas de entrenamiento aceptado con Q0 y Q/A/B+D, roster, D64,
preflight, presupuesto compartido, ledger/journal durables y checkpoints
atómicos. El [informe](hitos/P2R-ejecutor-historico-v2.md),
[resumen académico](hitos/P2R-ejecutor-resumen-academico.md) y
[preflight de solo lectura](evidence/p2r-historical-executor/preflight.json)
documentan la implementación y sus límites. No se ejecutó ninguna unidad
histórica ni se generaron trayectorias de mercado. El permiso de campaña
P2R permanece **inactivo en código**; no existe registro aprobado.
El preflight no cargó observaciones de validación, pero el cargador H1
calculó huellas de archivos completos que incluyen filas de 2023; revisar
esta distinción antes de cualquier permiso histórico.

**Siguiente tarea:** revisar ejecutor, huellas, pruebas y preflight. Solo
una autorización posterior puede registrar/activar el permiso P2R en otro
commit y considerar la primera unidad histórica. Antes de hacerlo se debe
repetir el preflight vivo; el snapshot de este hito no concede presupuesto
futuro. P2 y las sondas 01–06 permanecen intactos. La eliminación local de
`.python-version` sigue sin versionarse. Validación y final bloqueados.

---

# Estado anterior — sonda sintética P2R 06 cerrada

Desde `d840d6a`, una única unidad `systemd --user` nueva completó Q0 con
checkpoint `after_q0`; recibió SIGTERM al proceso principal mientras estaba
activa la primera unidad Q/A/B+D. [Informe](hitos/P2R-signal-QABD-06.md) y
[evidencia](evidence/p2r-signal-qabd-06/results.json): ledger `failed`,
systemd `Result=exit-code`, ninguna aceptación de la unidad interrumpida y
SHA-256 de `checkpoint-0` exactamente igual antes y después. La señal cayó
durante la espera sintética supervisada, antes de los cálculos Q/A/B+D; no
prueba interrupción dentro de un optimizador ni apagado físico. El checkpoint
se conserva como evidencia y **no autoriza reanudar** la campaña fallida.
Las raíces 01–05, P0/P1 y P2 siguen intactas; `.python-version` permanece
eliminado solo localmente, fuera de los commits.

**Siguiente tarea:** revisión de esta evidencia y de las brechas restantes
del P2R v2 adoptado. No implementar ni lanzar el ejecutor histórico por esta
sonda; validación y conjunto final siguen bloqueados.

---

# Estado anterior — P2R v2 adoptado como diagnóstico de desarrollo

La revisión académica adoptó metodológicamente P2R v2 tras la precisión
registrada en `36ed24d`: `Z_D,temprana`, `Z_D,tardía` y `Z_A,tardía` deben
superar `10⁻¹²` **cada uno** en la regla conjunta. El
[registro de adopción](protocols/P2R-adopcion-metodologica-v2.md) delimita el
alcance. Se conservan las nueve corridas nuevas, semillas y orden rotado,
Q0/Q/A/B+D, fronteras, presupuesto global, datos solo de entrenamiento y
separación absoluta de P2. Es diagnóstico de desarrollo, no evaluación
confirmatoria.

**No hay permiso para implementar el ejecutor histórico ni para lanzar P2R
de mercado.** Validación y final continúan bloqueados. En ese momento
seguían pendientes las comprobaciones de checkpoint previo ante fallo
posterior y señal durante Q/A/B+D bajo systemd, además de identidad de
datos/código/normalizador, preflight y permisos separados de implementación
y campaña. La sonda 06 atiende parcialmente las dos primeras brechas, con el
límite indicado arriba. Las sondas 01–05 y sus huellas permanecen intactas;
`.python-version` sigue eliminado solo localmente, fuera del commit.

**Siguiente tarea:** revisión de las brechas para una eventual autorización
de implementación histórica, sin comenzar ese trabajo por esta adopción.

---

# Estado anterior — P2R v2 propuesta, sin permiso histórico

Desde `af14af2` se consolidaron [P2R v1](proposals/P2R-protocolo-v1.md),
su anexo y las sondas sintéticas 01–05 en la
[propuesta P2R v2](proposals/P2R-protocolo-v2.md),
**PROPUESTA PARA REVISIÓN, NO ADOPTADA**. Se conservaron v1, anexo y
artefactos originales. La [síntesis académica](proposals/P2R-v2-resumen-academico.md)
y las [diferencias](proposals/P2R-v2-cambios.md) separan lo verificado de lo
pendiente. No se ejecutaron unidades ni entrenamientos en este hito.

La repetición propuesta mantiene nueve corridas nuevas, semillas
610031/610047/610081, C0/C5/C10, Q0 y Q/A/B+D, ambas fronteras, 3 h
globales/día hasta tres días y solo entrenamiento H1. P2 sigue `failed` y
absolutamente separado. La prueba 02 observó `Linger=yes` y Q0 tras logout
completo sin suspensión hasta el reingreso; 03 corrigió la cadencia y 04/05
probaron SIGTERM en Q0. Faltan señal bajo systemd durante Q/A/B+D,
conservación por huellas de un checkpoint previo ante fallo posterior,
ejecutor histórico train-only, permiso propio y preflight de campaña. Un
servicio de usuario no resiste un apagado físico.

**Siguiente tarea:** revisión académica de la v2. Solo después de una
decisión expresa correspondería definir implementación histórica y
autorización de ejecución **separadas**. No usar validación ni prueba final;
no reanudar P2. La eliminación local previa de `.python-version` continúa
fuera de los commits.

---

# Estado anterior — señal durante Q0 P2R sintética verificada

En `codex/p2r-unit-integration`, las sondas nuevas 04/05 enviaron SIGTERM
al proceso principal durante una Q0 sintética activa. El ledger quedó
`failed` por `interrupted_supervisor_or_unit`, con cero unidades y cero
checkpoints aceptados. La sonda 04 descubrió que la CLI terminaba con código
0 pese al fallo; `08c0fda` corrigió esa salida y la repetición acotada 05
terminó `Result=exit-code`, estado 1. El
[informe](hitos/P2R-signal-Q0-sintetica.md) y las
[evidencias](evidence/p2r-signal-q0/results.json) distinguen las dos
ejecuciones y conservan las raíces 01–05 intactas. La suite dio 267 pruebas
pasadas y Ruff pasó; hashes 01–03 revalidados. La eliminación local previa
de `.python-version` no se versionó.

**Siguiente tarea:** revisión metodológica del protocolo P2R y de los
requisitos para un ejecutor histórico train-only, sus huellas, guardas y
permiso explícito de campaña. Esta sonda no habilita P2R histórico ni la
reanudación de P2. No se accedió a validación ni prueba final. La señal
durante Q0 no demuestra conservación de un checkpoint anterior ni reacción
ante apagado físico.

---

# Estado anterior — cadencia P2R corregida y verificada solo en sintético

Desde `76757ed`, `run_synthetic_units` solicita heartbeats con margen de
4 s y rechaza una unidad si el intervalo **registrado** supera 5 s. La
[sonda 03](hitos/P2R-cadencia-heartbeat-03.md), una única Q0 sintética breve
bajo `systemd --user`, terminó `ready`, `Result=success` y checkpoint
`after_q0` íntegro. Sus seis intervalos entre siete heartbeats fueron
≤5 s (máximo 4.143739 s UTC). La prueba con sondeo tardío provocó ledger
`failed`, sin checkpoint aceptado. Ruff pasó; 28 pruebas P2R y 266 pruebas
totales pasaron. Las huellas de los artefactos 01/02 siguen intactas; la
raíz 03 es nueva. El cambio de reloj no modifica algoritmo ni datos.

**Siguiente tarea:** revisar el informe y decidir por separado la sonda de
señal durante unidad, la adopción del protocolo P2R, el ejecutor histórico
train-only, sus huellas/preflight y una autorización de mercado propia. La
sonda 03 no demuestra cumplimiento temporal bajo cualquier carga, no
autoriza P2R histórico ni reanudar P2. Validación y prueba final siguen
bloqueadas. La eliminación local previa de `.python-version` permanece
fuera de los commits.

---

# Estado anterior — logout sintético Q0 02 aprobado; mercado P2R bloqueado

La [sonda 02](hitos/P2R-logout-Q0-02-cierre.md) del 05/10/2026 terminó
`ready`, `Result=success` y checkpoint `after_q0` íntegro. Desde la retirada
de la sesión interactiva 40 (15:57:37.582970 UTC) hasta el ingreso de la 54
(16:51:58.504184 UTC) hubo 139 heartbeats P2R del mismo `InvocationID`
durante Q0 y **cero eventos de suspensión** en el journal de logind. Las
raíces originales 01 y 02 permanecen intactas; sus hashes están versionados
en los respectivos informes. El supervisor terminó antes del reingreso, por
lo que los heartbeats no cubren todo el intervalo; la ausencia de suspensión
se establece por logind.

**Límite pendiente:** todos los 174 intervalos entre heartbeats de Q0 02
superaron el tope ≤5 s de P2R (máximo 5.212391 s). Hay que corregir y
verificar esa cadencia sintéticamente. También faltan una prueba separada de
señal durante unidad, revisión/adopción del protocolo P2R, ejecutor histórico
train-only, huellas y preflight completos, y autorización de mercado propia.
La prueba sintética **no autoriza** campaña P2R ni reanudar P2. No usar
validación/final. La eliminación local previa de `.python-version` continúa
fuera de los commits.

**Siguiente tarea:** revisar el [informe de cierre](hitos/P2R-logout-Q0-02-cierre.md)
y decidir los trabajos de infraestructura pendientes. No lanzar otra sonda
ni entrenamiento por este cierre documental.

---

# Estado anterior — logout sintético Q0: continuidad comprobada, suspensión detectada

El 05/10/2026, `p2r-logout-q0-review-01.service` terminó Q0 sintética
`ready`, con checkpoint `after_q0` y `Result=success` después de retirar la
última sesión interactiva. Sus 156 heartbeats tras el logout acabaron antes
de Q0. El equipo se suspendió a las 15:13:47 UTC, después de Q0 y antes del
nuevo login: **la condición «sin suspensión» falló**. Los artefactos y el
ledger 01 conservan sus hashes. El temporizador de 900 s del greeter GDM es
la causa más probable, pero falta identificar el llamador con journal
privilegiado. Ver [diagnóstico](hitos/P2R-logout-Q0-diagnostico.md).

**Siguiente tarea:** revisar el contexto privilegiado del journal y la
corrección propuesta para el greeter; no se modificó el host. Si se aplica
la corrección, hacer preflight nuevo y considerar la [repetición 02, solo
sintética](protocols/P2R-logout-Q0-synthetic-review-02.md), con unidad y
raíz nuevas. Esta repetición está preparada, **no iniciada**. No ejecutar
P2R histórico, no reanudar P2 ni acceder a validación/final.

---

# Estado anterior — prueba de logout P2R preparada, no iniciada

En `codex/p2r-unit-integration` quedó preparado el
[procedimiento exacto](protocols/P2R-logout-Q0-synthetic-review.md) para una
unidad `systemd --user` exclusivamente sintética. Una espera acotada de 900 s
dentro del child supervisado deja tiempo para logout y reingreso; después
Q0 produce un checkpoint `after_q0`. La unidad **no se lanzó** y nadie cerró
la sesión. `InvocationID` aún no existe: se captura inmediatamente después
del lanzamiento manual y antes de salir. El journal P2R incluirá ese ID.

El usuario informó `Linger=yes` y gestor `running`. La última lectura de
solo recursos dio `MemAvailable=3981492224` bytes, por debajo de 4 GiB;
la guarda bloqueó el preflight. No se bajaron umbrales ni se alteró systemd.
Repetir el preflight al decidir la prueba. No hay permiso histórico P2R;
P0/P1 y la campaña fallida P2 siguen intactos. La eliminación local previa
de `.python-version` permanece fuera de los commits.

**Siguiente tarea:** cuando el host cumpla recursos, ejecutar manualmente
las secciones A y B del procedimiento, cerrar todas las sesiones y luego
seguir C. Si no se identifica un intervalo sin sesiones con heartbeats de la
misma invocation, declarar logout no verificado. No lanzar P2R histórico ni
acceder a validación/final.

---

# Estado anterior — P2R Q0/Q/A/B+D integrado solo en sintético

Base `e1e98dd`; rama `codex/p2r-unit-integration`. La autorización actual
integra el supervisor independiente con el worker sintético existente de P2:
Q0 y Q/A/B+D, contadores de trayectorias/transiciones/actualizaciones,
checkpoints `after_q0` y `after_dual_and_D`, reanudación desde frontera
completa y fallo permanente si se interrumpe una unidad. La CLI mantiene un
rechazo temprano del perfil histórico. No hay permiso P2R de mercado ni se
generaron trayectorias del histórico. P0/P1 y el ledger/unidad parcial de P2
permanecen intactos. La eliminación local previa de `.python-version` se
conserva fuera de los commits.

Ver [informe de integración](hitos/P2R-unidades-sinteticas.md),
[comprobaciones](evidence/p2r-unit-integration/COMMANDS.md) y
[procedimiento separado para el host](protocols/P2R-host-preflight-review.md).
La prueba automatizada de señal **no equivale** a logout completo; el último
estado documentado fue `Linger=no`, y la lectura actual de `loginctl` quedó
bloqueada por el entorno de herramientas. No se modificó systemd ni se
rebajaron umbrales.

**Siguiente tarea:** revisar las evidencias y verificar por separado
`Linger=yes`, logout completo y recursos reales aptos. Una futura campaña
histórica requeriría autorización específica, permiso y ejecutor train-only
separados, huellas congeladas y nuevo preflight. No reanudar P2 ni iniciar P2R
histórico, validación o final. No modificar la tesis.

---

# Estado anterior — infraestructura P2R sintética; mercado bloqueado

Base `d7f253b`; rama `codex/p2r-infrastructure`. El usuario autorizó
implementar y verificar **solo infraestructura sintética** de P2R. El servicio
`systemd --user` probó separación del proceso lanzador y señal durante una
unidad; el ledger y los artefactos de P2 conservan sus huellas. La CLI P2R
rechaza mercado, validación y final antes de crear artefactos. No se generaron
trayectorias históricas ni hubo actualizaciones de aprendizaje. La propuesta
P2R v1 permanece sin autorización de ejecución.

El gestor de usuario está activo pero `Linger=no`; no se efectuó logout
completo. La memoria disponible observada fue menor que 4 GiB, de modo que
un preflight de mercado tampoco pasaría en este estado. Las pruebas usan
fixtures de recursos y una ventana de reloj ficticia solo para ensayar señales
cerca de medianoche. Ver [informe](hitos/P2R-infraestructura.md),
[ajustes para revisión](proposals/P2R-infraestructura-addendum-v1.md) y
[comandos/evidencia](evidence/p2r-infrastructure/COMMANDS.md).

**Siguiente tarea:** revisar el informe y decidir ajustes del protocolo.
Antes de una eventual ejecución histórica se necesitan autorización separada,
permiso nuevo, runner integrado con P2 Q/A/B+D, huellas y preflight, verificación
de continuidad tras logout y recursos disponibles. No reanudar P2, no modificar
la tesis, no acceder a validación ni final. La eliminación local previa de
`.python-version` sigue fuera de los commits.

---

# Estado anterior — apagado identificado; propuesta P2R para revisión

Base `a2014e4` verificada local/origin; rama documental
`codex/p2-shutdown-diagnosis-proposal`. Una investigación posterior de solo
lectura encontró cierre de GNOME y registro de apagado del equipo a las
06:20:12 UTC del 30/09/2026, coincidente con el último progreso de la unidad
2 de `run-05-C0`. La pérdida del supervisor se explica por la salida de la
sesión/equipo; **no consta quién ni qué ordenó el apagado**. El ledger P2
permanece `failed`, SHA256
`e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8`,
y la parcial se conserva fuera de Git. No hubo reanudación, entrenamientos
nuevos ni acceso a validación/final.

[Diagnóstico](hitos/P2-perdida-supervisor-diagnostico.md) y
[evidencia de comandos](evidence/p2-shutdown-investigation/COMMANDS.md).
La [propuesta P2R](proposals/P2R-protocolo-v1.md) recomienda repetir **las
nueve corridas completas** en una raíz y permiso nuevos, con supervisor
independiente del chat, controles de alimentación, mismo diseño científico y
reglas de presupuesto/interrupción fijadas antes de ejecutar. Está
**PROPUESTA PARA REVISIÓN, NO AUTORIZADA** para implementación o mercado.

**Siguiente tarea:** revisión del diagnóstico y de P2R por el usuario. Una
eventual implementación sintética y la ejecución histórica requerirán
autorizaciones posteriores y separadas. No reutilizar resultados P2 como
corridas P2R, no modificar la tesis ni tocar validación/final. La eliminación
local previa de `.python-version` sigue sin incluirse en commits.

---

# Estado anterior — P2 histórico interrumpido, campaña cerrada por fallo

Rama `codex/p2-execution`. La autorización y activación se publicaron en
`18bc767`. El preflight activo y la integridad de P0/P1 pasaron. La campaña
alcanzó cinco corridas K10 completas y una sexta (`run-05-C0`, semilla 610047)
con Q0 e iteración 1 completas. Durante la iteración 2 se perdió la sesión del
supervisor; el último progreso conservado está en fase B, sin checkpoint de esa
unidad. El 30/09/2026 a las 16:32:06 UTC el ledger registró
`interrupted_supervisor_or_unit` y estado **failed**. No se reanudó ni repitió
ninguna unidad.

El cierre de solo lectura verificó la cadena de 176 estados, 57 unidades
completas, sus checkpoints y 3264 archivos D. La unidad parcial queda fuera de
los contadores cerrados; su progreso se conserva localmente. La causa precisa
de la desaparición del proceso no está demostrada. Los umbrales conjuntos de P2
no son evaluables con nueve corridas incompletas. Las advertencias del crítico
y la marca heredada `market_training_executed=false` se documentan sin cambiar
el código operativo ni inferir ausencia de aprendizaje.

**Siguiente tarea:** revisar [informe de cierre](hitos/P2-ejecucion-interrumpida.md),
[resumen académico](hitos/P2-ejecucion-resumen-academico.md) y
[evidencia](evidence/p2-execution/COMMANDS.md). Decidir un protocolo nuevo antes
de cualquier ejecución adicional; no reparar ni relanzar esta campaña por
resultado. Validación 2023, final 2024–2025 y tesis permanecen intactos. La
eliminación local previa de `.python-version` sigue fuera de los commits.

---

# Estado anterior — P2 histórico autorizado, preflight previo a ejecución

Base de integración `2f01d6c` comprobada contra origin el 30/09/2026. Rama
`codex/p2-execution`. El usuario autorizó un permiso específico para las nueve
corridas P2 sobre entrenamiento aceptado 2018–2022; el registro está en
[P2-market-approval-2026-09-30.md](protocols/P2-market-approval-2026-09-30.md).
Se conserva el diseño P2, d, ADR-002, Q/A/B, crítico4 provisional y D64.
Validación 2023, final 2024–2025 y campañas posteriores siguen bloqueadas.

Antes de iniciar: verificar permiso y commit separado, 108 huellas P0/P1,
configuración/datos/scaler, ausencia de otra campaña y presupuesto diario La Paz.
La campaña debe pausar en frontera completa si no cabe una unidad. Fallo de
integridad invalida la corrida/campaña sin reintento selectivo. Checkpoints y
evidencia se guardan localmente; los resultados pequeños se versionarán.
La eliminación local previa de `.python-version` permanece fuera de commits.

**Siguiente tarea:** ejecutar preflight activo; solo si pasa, iniciar el comando
canónico P2 y medir D real dentro de sus topes. Al pausar o cerrar, comprobar
ledger/checkpoints sin nuevas actualizaciones y publicar informe, resumen OE3
y estado de integridad. No modificar la tesis.

---

# Estado vigente — P2: perfil histórico integrado, campaña bloqueada

Base `5e81594` verificada contra `origin/codex/p2-infrastructure`; nueva rama
`codex/p2-market-integration`. La autorización vigente cubre integración,
fixtures sintéticos y preflight histórico de **solo lectura**. La campaña P2,
trayectorias históricas nuevas y actualizaciones con mercado NO están autorizadas.

El perfil conecta `TrainingMarket` con 7048 inicios H1, normalizador persistido y
las particiones protegidas. Conserva nueve corridas K10, semillas y orden P2,
crítico4 provisional, D64 y Q/A/B común. El registro de campaña está inactivo y
anclado por hash; el comando público rechaza mercado antes de cargar datos o
crear salidas. D exige un permiso de supervisor y generador propio. El preflight
leyó únicamente entrenamiento y huellas, sin solicitar rutas/episodios. La
suite final: 234 pruebas y Ruff aprobados. La
eliminación local previa de `.python-version` sigue ajena a los commits.

**Siguiente tarea:** revisar [informe](hitos/P2-integracion-historica.md),
[resumen académico](hitos/P2-integracion-resumen-academico.md) y
[evidencias/comandos](evidence/p2-market-integration/COMMANDS.md). Después se
necesita autorización explícita y un commit de activación del permiso para medir
el costo D y, solo entonces, ejecutar P2 dentro de los topes aprobados. Ni el
JSON ni la CLI por sí solos activan la campaña. No repetir P0/P1, no acceder a
validación/final, no modificar tesis. Cuatro épocas siguen provisionales.

---

# Estado vigente — P2: infraestructura sintética, mercado bloqueado

Rama `codex/p2-infrastructure`, base `7357aa1` verificada local/origin. El usuario
aceptó el diseño P2 (9 corridas, K10, semillas 610031/610047/610081, crítico4
provisional, D64, umbrales §7, hasta3 días/3h globales por día). Autorizó únicamente
implementación y pruebas sintéticas. **NO autoriza P2 histórico**, validación2023
ni final2024–2025. P0/P1 cerrados y sus evidencias se conservan.

Implementación: D independiente con pi_k de A y ambos críticos sobre los mismos
MC; métricas/solapamientos/criterios conjuntos; fronteras after_q0 y
**after_dual_and_D**; checkpoint, reanudación, contadores y presupuesto global
persistentes. Q/A/B se conserva en una implementación común. Código `41fcef3`;
221 pruebas pasadas (94.31 s), Ruff y 282 huellas históricas verificados.
La CLI rechaza mercado
antes de cargar datos. No hay P2Permit ni bandera que habilite campaña.

**Siguiente tarea:** revisar [informe y límites](hitos/P2-infraestructura.md),
[resumen académico/OE3](hitos/P2-resumen-academico.md),
[contrato y permisos](protocols/P2-infrastructure-v1.md) y
[pruebas ejecutadas](evidence/p2-infrastructure/COMMANDS.md).
La ejecución histórica requiere autorización posterior y registrar/conectar el
perfil de mercado al supervisor antes de la calibración acotada. No inferirla de
la aceptación de infraestructura ni congelar cuatro épocas como confirmatorias.

El comando futuro está documentado **NO EJECUTADO como campaña**; actualmente
bloqueado. No repetir P0/P1 ni modificar la tesis. La eliminación local previa de
`.python-version` sigue fuera de los commits. Sin ZIP.

---

# Estado vigente — propuesta P2 para revisión, NO autorizada

Antecedente P1 cerrado 811d882, verificado local/origin; rama `codex/p2-proposal`.
Solo diseño/documentación y comprobaciones estáticas/algebraicas. Sin cambios de
src/scripts/configs, registros de permisos o ejecutores; sin nuevas trayectorias,
entrenamiento, validación 2023 ni conjunto final. Evidencias P0/P1 conservadas.

**Recomendación:** nueve corridas K=10, semillas 610031/610047/610081, cuatro épocas
provisionales del crítico; D=64 por iteración con RNG separado y pi_k que generó A_k.
Evaluar phi_k y phi_(k+1) sobre el mismo D_k, alineando el post con su política de
ajuste. Mantener d, Q/A/B, normalizador y todos los demás parámetros P1.
Tres semillas, no nueve réplicas independientes; no afirmar generalización temporal.

**Siguiente tarea:** revisar K/D/semillas, umbrales técnicos y presupuesto máximo de
tres días activos con 3h global/día; después decidir autorización explícita de
implementación/pruebas y ejecución. Esta propuesta NO autoriza esos pasos ni
congela cuatro épocas para confirmación. No usar la configuración candidata en
un ejecutor ni registrar su hash como permiso.

[Protocolo y decisiones pendientes](proposals/P2-protocolo-v1.md),
[configuración NO ejecutable](proposals/P2-candidate-v1.json),
[resumen académico](proposals/P2-resumen-academico-v1.md),
[comprobaciones y límites](evidence/p2-proposal/COMMANDS.md).
La eliminación local previa de .python-version sigue fuera de commits. Tesis intacta.

---

# Estado vigente — P1 cerrado, criterio cumplido

Rama `codex/p1-critic-epochs`. Aprobación 7eb9738, ejecutor 7617d84;
18 corridas K=2 completadas sin fallos/reintentos/pausas. Criterio primario
cumplido en **3/3 semillas**: reducción MSE post-A con cuatro épocas de
50.74%, 58.70% y 44.44%. A inicial/actor posterior idénticos en todos los pares;
condiciones repetidas como controles, no nueve réplicas independientes.

**Siguiente tarea:** revisión académica de P1 y definición explícita del próximo
protocolo. No ejecutar P2, validación/final ni congelar automáticamente cuatro
épocas como parámetro definitivo. La mejora es in-sample; sigue MSE relativo >1
en todos los A completos. 465 alertas del crítico; no otras alertas predefinidas.

Recursos: 38304 trayectorias, 6894720 transiciones, 288 pasos actor/432 crítico.
Brazo2: 144 pasos crítico; brazo4: 288, con iguales trayectorias.
P1: 2650.523 s (44m10.523s). Total diario P0+preparación+P1: 5424.038 s
(1h30m24.038s), dentro de 3h. Día 24/09/2026 La Paz, timestamps UTC.

198 pruebas sintéticas/Ruff aprobados antes de mercado. Cierre de solo lectura
verifica 72 artefactos, 18 pares de hashes actor/crítico, presupuesto, recursos
y P0 intacto. No se accedió a validación/final; tesis intacta.
[Informe](hitos/P1-epocas-critico.md), [resumen académico](hitos/P1-resumen-academico.md),
[resultados](evidence/p1-execution/campaign-results/results.json),
[comandos](evidence/p1-execution/COMMANDS.md). Checkpoints completos locales.
La eliminación local previa de .python-version sigue fuera de commits.

---

# Estado vigente — P1 aprobado, preparación de ejecución

Autorización de usuario desde diagnóstico 42152c3; registro 7eb9738.
Rama `codex/p1-critic-epochs`. [Protocolo aprobado](protocols/P1-approved-v1.md)
y configuración JSON congelada: 18 corridas, K=2, semillas nuevas,
crítico 2/4 épocas; demás parámetros P0 intactos, d=-ln(.90).

Ejecutor Q/A/B común, métricas de A fijo antes/después, control de igualdad
inicial de A/actor. Bloqueo GLOBAL compartido y débito de otras campañas del día.
Conserva 3h/día La Paz/UTC, reserva, topes y 27 sesiones máximas de campaña.
Solo entrenamiento 2018–2022; P0/diagnóstico conservados; sin validación/final.

Siguiente paso autorizado: ejecutar P1 después de cerrar las pruebas sintéticas
y registrar resultados en informe/evidencia P1. No modificar parámetros durante
la campaña ni repetir fallos. No inferir generalización/CVaR del criterio primario.
Se conserva la eliminación local previa de .python-version fuera de commits.

---

# Estado vigente — diagnóstico P0 cerrado

Base P0 e0a2dfc verificada contra origin; rama `codex/p0-diagnosis`.
**Comportamiento explicado; sin defecto operativo demostrado en lo examinado.**
Reconstrucción congelada de los 18 A originales con hashes de cálculo exactos;
sin pasos de optimizador, reejecución P0 ni acceso a validación/final.

Las 162 alertas del crítico son 18 mediciones preactualización sobre A entero y
144 sobre minibatches antes de su paso actual, aunque se escriben después.
MSE post-A reconstruida disminuye en 18/18 casos, todavía peor que predictor cero.
C0/C5 de semilla 410031 coinciden porque lambda=0 al inicio y el segundo A tiene
cero shortfalls pese a lambda positivo. Las otras cinco corridas C5/C10 sí tienen
penalización y gradiente de riesgo no nulos en la segunda iteración.

**Siguiente paso:** revisión académica del diagnóstico y de la propuesta acotada
P1 (2 frente a 4 épocas del crítico). P1 no autorizado ni ejecutado; no cambiar d,
repetir P0 ni iniciar otras corridas. No se puede concluir generalización/CVaR.

[Informe](hitos/P0-diagnostico.md),
[resumen académico](hitos/P0-diagnostico-resumen-academico.md),
[evidencias y comandos](evidence/p0-diagnosis/COMMANDS.md).
16 pruebas analíticas sin aprendizaje y comprobaciones de correspondencia pasan;
Ruff pasa. Todos los hashes de campaña/código operativo se conservan. La
eliminación previa de `.python-version` sigue fuera de commits. Tesis intacta.

---

# Estado vigente — P0 completado con advertencias

Campaña `artifacts/p0-approved-v1`: **completed**, nueve corridas K=2, sin fallos
ni reintentos. Rama `codex/p0-approved-execution`; ejecutor publicado 0838ac8,
aprobación e0e3495. El código ejecutado permanece intacto en este cierre documental.

**Siguiente tarea:** revisar las advertencias del crítico y la señal de riesgo con
las evidencias existentes antes de proponer seguimiento. P0 ya terminó: no volver
a ejecutarlo. No se autoriza P1, validación, conjunto final ni evaluación confirmatoria.

Tiempo global supervisado 1385.677 s (23 min 5.677 s), día 2026-09-24 La Paz.
19152 trayectorias / 3447360 transiciones / 144 actualizaciones por red;
pico RSS trabajador 358.44 MiB. Una sesión por corrida, límites conservados.
186 pruebas y Ruff aprobados antes de mercado; comprobación posterior de registros,
contadores, límites y hashes aprobada. 162 advertencias critic_relative_mse:
cierre operativo completo, estabilidad pendiente de revisión. F_B y rho_B de C5/C10
superaron d; dos iteraciones no demuestran convergencia ni cumplimiento CVaR.

[Informe P0](hitos/P0-ejecucion.md), [resumen académico](hitos/P0-resumen-academico.md),
[resultados](evidence/p0-execution/campaign-results/results.json),
[comandos](evidence/p0-execution/COMMANDS.md). Checkpoints locales fuera de Git;
hashes y evidencia pequeña versionados. Se conserva la eliminación local previa
de `.python-version` fuera de commits. Tesis intacta.

---

# Historial conservado

# Handoff — P0 aprobado, ejecutor verificado

Base aprobada 7a379b7; aprobación registrada en e0e3495. Rama
`codex/p0-approved-execution`. [Protocolo vigente](protocols/P0-approved-v1.md)
y [configuración congelada](protocols/P0-approved-v1.json). Propuesta original
conservada debajo y en docs/proposals.

Autorización: ejecutar P0 en train 2018–2022 tras pruebas sintéticas, d=-ln(.90),
K=2, tres semillas y orden rotado aprobado. Varias corridas secuenciales comparten
3h GLOBAL/día America/La_Paz, timestamps UTC; no reiniciar límites ni escoger
checkpoints por resultado. Validación/final/campañas posteriores bloqueados.

Implementado: ledger canónico append-only con lock, deadlines diarios persistentes,
contadores por corrida/campaña, subprocess por frontera completa, watchdog
monotónico/RSS y terminación del hijo si muere el supervisor. Perfil P0 requiere
protocolo registrado y lease del supervisor. Algoritmo Q/A/B único.
Checkpoint v2 conserva actor/crítico/Adam/estado/RNG; ledger enlaza las fronteras
y las sesiones. Un proceso interrumpido invalida campaña, sin reintento selectivo.

Verificación nueva: 186 pruebas pasan, Ruff pasa; incluye C0/C5 reanudados exactos,
dos corridas sintéticas en un día, presupuestos/reinicio/midnight, corrupción,
watchdog tiempo/memoria y muerte de supervisor. La revisión encontró y corrigió
rechazo del flag risk_enabled=False al reanudar C0; C5/C10 no pueden apagar riesgo.

Comando canónico autorizado (sin overrides de parámetros/output):
`uv run --frozen python scripts/run_pilot.py --protocol docs/protocols/P0-approved-v1.json`.
Ledger y checkpoints: artifacts/p0-approved-v1. Repetir el mismo comando únicamente
tras pausa planificada; campaña failed/incomplete requiere diagnóstico y nueva
revisión, no borrar el ledger. Si no cabe unidad, continuar otro día con igual
autorización. Conservar .python-version eliminado previamente fuera de commits.

Estado/resultados de la ejecución se registrarán al finalizar o pausar la campaña.
No atribuir a estas pruebas resultados de mercado.

---

# Handoff — propuesta P0 pendiente de decisión

H5 revisado, base **1118129**. Se preparó el protocolo concreto
[P0-technical-v1](proposals/P0-protocolo-v1.md) y su
[configuración candidata NO AUTORIZADA](proposals/P0-candidate.json), en rama
`codex/p0-protocol-proposal`. Se conserva debajo la entrega H5.

Propuesta: tres bloques de semillas, orden C0/C5/C10 rotado, dos iteraciones
Q/A/B completas por corrida, N_A=64 y N_Q=N_B=400; CPU float64/un hilo.
Referencia d común de 5%, 10% o 20% convertida a pérdida logarítmica: selección
pendiente; 10% se recomienda solo para discusión, sin adoptarla.

Siguiente paso: respuesta del investigador sobre **d y aprobación/ajustes de P0**,
incluidos topes de primera medición, supervisor y hasta tres sesiones de 3h por
corrida. La medición inicial tiene límites propuestos, ninguna duración inventada.
Antes de ejecutar se necesita una autorización explícita y adaptar/probar el
ejecutor cerrado, watchdog y contadores diarios/acumulados. No resetear
TimeBudget H5 ni inferir permiso desde un JSON.

Ocho comprobaciones estáticas/algebraicas y Ruff dirigidos pasaron:
[comandos y límites de evidencia](evidence/p0-proposal/COMMANDS.md). No se
repitieron verificaciones H5, no se leyó mercado ni se ejecutó aprendizaje.
Guardas, ADR, código operativo, configuración H3 y tesis intactos; la eliminación
local previa de .python-version sigue fuera del commit.

---

# Handoff — entrega H5 conservada

Repositorio [GitHub](https://github.com/Ichurri/btc-risk-rl), origin.
Rama [codex/h5-infrastructure](https://github.com/Ichurri/btc-risk-rl/tree/codex/h5-infrastructure).
Base H4 local/remota verificada 19fa2e6; implementación H5 **3cbd342**.
El commit documental posterior añade evidencias y este handoff. La eliminación
local previa de .python-version se mantiene fuera de commits. Sin force push.

**Vigente:** ADR-002 v2.1 adoptado, sin cambios metodológicos. H5 autoriza
infraestructura, aprendizaje pequeño sintético e integración 2018–2022 sin
optimización. Pilotos, entrenamientos de mercado y evaluación confirmatoria
siguen bloqueados. PyTorch CPU existente; sin CUDA/drivers ni cambios de tesis.

Entregado: adaptador AcceptedMarket de entrenamiento (7048 inicios), checkpoint
completo after_q0/after_dual con journal contra rollback, reanudación exacta
sintética, diagnósticos y control preventivo de tiempo con reserva. Q/A/B único.
No se habilitó el ejecutor de mercado: run_pilot.py rechaza antes de abrir datos.

Nueva verificación: **164 pruebas y Ruff aprobados**; integración real acotada
de 3 episodios/540 transiciones con política congelada, **0 actualizaciones**.
Normalizador/productos H1 invariantes; sin observaciones de validación cargadas
ni acceso al conjunto final. Los hashes verifican archivos H1 compartidos en
bytes completos; no equivale a evaluación de validación. No extrapolar tiempos
de estas comprobaciones a entrenamiento.

## Siguiente tarea

Revisar H5 y [P0 instrumentado](proposals/H5-P0-instrumentado.md). Antes de cualquier
piloto, el investigador debe fijar especialmente la **cota económica común d**,
configuración/semillas/tamaños/tasas, criterios de precisión/parada, calibración
temporal y protocolo autorizado de hasta 3h diarias. Habilitar pilotos requerirá
un cambio revisado; no basta pasar un JSON con authorized=true. No convertir
SyntheticSettings ni candidatos H4 en decisiones definitivas.

Leer [informe H5](hitos/H5-infraestructura.md),
[resumen académico](hitos/H5-resumen-academico.md) y
[comandos/resultados](evidence/infrastructure-h5/COMMANDS.md).
H1/H3, guardas, contabilidad y tesis intactos. No ZIP rutinario.

---

## Historial conservado: entrega H4

# Handoff — entrega histórica H4

Repositorio [GitHub](https://github.com/Ichurri/btc-risk-rl), remoto origin.
Rama de entrega: [codex/h4-agents-collector](https://github.com/Ichurri/btc-risk-rl/tree/codex/h4-agents-collector).
Base H3 verificada local/remota 8f027c5; alcance/dependencias 31b4c87;
implementación H4 a6c391a. La eliminación previa de .python-version sigue fuera
de los commits. No hubo retroceso de ramas ni sobrescritura de cambios previos.

**Vigente:** ADR-002 v2.1 adoptado. H4 autoriza agentes/recolector y actualizaciones
pequeñas exclusivamente sintéticas; NO mercado, pilotos o evaluación confirmatoria.
AGENTS refleja esta autorización. PyTorch 2.8.0+cpu instalado y fijado, sin CUDA.
H3 y los productos H1 se conservan; no se leyeron datos reales en H4.

Implementado: actor logística-normal y crítico separados, política congelada,
identidades de realización/ruta/política, fragmentos completos de 180, MC,
calendario Q/A/B, eta/masa fraccionaria, dual F_B y equivalencia exacta riesgo
apagado/C0. Los fallos invalidan la corrida, sin reemplazo selectivo.
NPZ de trayectorias versionado para auditoría; no checkpoint/reanudación de
optimizadores. El ejecutor solo acepta rutas fabricadas en código.

Verificación nueva: Ruff pasa; **149 pruebas aprobadas**, 32 nuevas H4.
Evidencias y actualización sintética adicional en
[COMMANDS](evidence/agents-h4/COMMANDS.md).
Leer [informe](hitos/H4-agentes-recolector.md),
[resumen académico](hitos/H4-resumen-academico.md) y
[propuesta de pilotos](proposals/H4-pilotos-3h.md).

## Siguiente tarea

Revisar H4 y la propuesta de pilotos; autorizar alcance separado antes de mercado.
Resolver adaptador de índices aceptados, checkpoint integral/reanudación
determinista y diagnósticos; después calibrar tiempos con presupuesto máximo de
3h/día. Cerrar cota económica común, tamaños, tasas, arquitectura y presupuesto
antes de comparar condiciones. No extrapolar tiempos sintéticos ni seleccionar
por B favorable. El conjunto final sigue bloqueado.

Los valores SyntheticSettings NO son hiperparámetros de pilotos. La configuración
initial.toml conserva el perfil histórico H3 y training_enabled=false para mercado.
No tomar los antiguos «sin agentes» del historial como estado vigente.
No modificar la tesis ni generar ZIP rutinario.

---

# Historial conservado anterior a H4

# Handoff — estado vigente H3 (22-09-2026)

Repositorio en [GitHub](https://github.com/Ichurri/btc-risk-rl), remoto origin.
Rama de entrega: [codex/adopt-adr002-v2-1](https://github.com/Ichurri/btc-risk-rl/tree/codex/adopt-adr002-v2-1).
Base revisada e4e2e8f; adopción 10d92fa; código H3 ebb3914.
Git local y remoto coincidían en la base; no había commits posteriores.
La eliminación local previa de .python-version se conserva fuera de los commits.

**Vigente:** ADR-002 v2.1 ADOPTADO por autorización explícita del usuario.
Simulador H3: schema 2, observación 13 con reloj, H=180/gamma=1,
terminalidad finita sin bootstrap en H; evaluación continua con cartera única
y h=1. Cortes internos esperan completitud; rutas cortas se rechazan.
H1 permanece aceptado bajo B; productos originales, scaler, cuentas H2,
costos y recompensa conservados. Propuestas anteriores y evidencia intactas.

Verificación local nueva: Ruff pasa, **117 pruebas aprobadas**.
Auditor de desarrollo: **7048 índices, 31 recorridos y 7590 transiciones**,
incluida validación continua de 2190 con un reset. Datos/scaler sin cambios.
Regresión contable exacta frente a H2. Son acciones prefijadas y fixtures
sintéticos, no resultados de agentes. Sin entrenamiento ni acceso final.

Leer [ADR vigente](decisions/ADR-002-risk-horizon.md),
[informe H3](hitos/H3-contrato-ADR002.md),
[resumen académico](hitos/H3-resumen-academico.md) y
[comandos/evidencia](evidence/simulator-h3/COMMANDS.md).

## Siguiente tarea

Solicitar autorización de alcance antes de implementar agentes y recolector:
identidad y congelación de políticas, ensamblaje H completo, Monte Carlo,
Q/A/B, eta/empates/masa fraccionaria, señal dual F_B y equivalencia exacta con C0.
Cerrar protocolo de pilotos antes de ejecutarlos; congelar parámetros comunes
antes de comparar condiciones y parámetros inferenciales antes de confirmación.
La adopción actual NO autoriza agentes, entrenamientos o evaluación confirmatoria.

No reabrir automáticamente las decisiones adoptadas ni interpretar los estados
«abierto/no adoptada» del historial siguiente como vigentes. No modificar la tesis.
Compartir rama/commit y evidencia desde GitHub; ya no se requieren ZIP por entrega.

---

# Historial conservado (estado anterior a H3)

# Traspaso entre este chat y Codex local/remoto

Leer AGENTS.md y los ADR. Consultar git status y git log antes de editar.
El paquete inicial se entrega como repositorio Git local con historial. No existe
remoto configurado. El usuario elegirá proveedor/cuenta y añadirá el remoto.

Git es la fuente de verdad del código; la tesis se actualiza en el otro chat.
Un chat no envía automáticamente su conversación a otro proceso Codex.
Para continuar, compartir URL/rama/commit o un paquete actualizado y este archivo.

Al terminar tarea: commit, comandos ejecutados, salida relevante, artefactos,
estado del conjunto final y siguiente tarea. No atribuir a Debian local las
pruebas ejecutadas en el entorno de construcción del paquete.

## Estado de entrega
- H0 código: b215268, repositorio/configuración/reglas.
- H1 código: f92574e, datos/características/controles/reconsulta.
- 28 pruebas pasan; Ruff pasa. Evidencia en docs/evidence/ y docs/hitos/.
- Datos reales rechazados: 16 huecos, 20 cierres abreviados; persisten en reconsulta.
- No hay simulador, agente o entrenamiento. Test final sin acceso.

## Siguiente tarea para Codex local o remoto
Leer ADR-003 y los informes de calidad/reconsulta. Investigar el tratamiento
de interrupciones de Binance sin rellenar precios y sin unir segmentos.
Diseñar una regla documentada para segmentos/calentamiento y sus criterios de
aceptación; conservar el dataset original y las fechas de partición.
No debilitar la guarda de prueba final. No implementar el simulador hasta
resolver esta aceptación. No implementar agentes hasta cerrar ADR-002.

## Mensaje mínimo para continuar en otro entorno
«Trabaja sobre el commit actual de btc-risk-rl. Lee AGENTS.md, docs/HANDOFF.md,
docs/hitos/H1-datos.md y ADR-003. Continúa la tarea de calidad de datos indicada.
No entrenes ni accedas al conjunto final. Registra decisiones, pruebas y commit».

Sin remoto configurado: este chat no puede acceder automáticamente a cambios
en tu disco. Para revisar cambios, proporcionar repo/rama/commit accesibles o
un archivo actualizado. Los resultados locales deben indicar máquina y versiones.

## Actualización: diagnóstico, iteración 02

El estado anterior de 28 pruebas queda como evidencia histórica. Ahora hay 32
pruebas remotas aprobadas y Ruff pasa. Revisar docs/DIAGNOSTICO-HISTORICO.md,
docs/DEBIAN.md y docs/hitos/H1-diagnostico.md.

36 anomalías en 20 bloques; 18 archivos mensuales corroboran los huecos, con dos
diferencias exclusivas de close_time. No afirmar causa verificada para todos.
Política B propuesta: 36 intervalos más 20 reaperturas en cuarentena, segmentos
contiguos. 7048 inicios posibles de 180 pasos; NO se aplicó la política.
Próximo paso: registrar la decisión metodológica del usuario y después implementar
preparación segmentada, verificar características y aceptar datos antes del simulador.
Verificación Debian local pendiente de resultados del usuario. Sin entrenamientos.

## Verificación local: 17 de septiembre de 2026

Ejecutada en el repositorio abierto del equipo local, sobre el commit
`d097f5c948f4f2250e04682c5cc47b9bf5932fb2`. Debian 13.7 (trixie),
kernel `6.12.107+deb13-amd64`, Python 3.12.13 y uv 0.11.18.
La eliminación previa de `.python-version` se conservó; el árbol no estaba limpio.

- `uv sync --frozen`: completado, 21 paquetes instalados desde el lock.
  El primer intento falló por caché de solo lectura y el segundo por DNS en
  el entorno restringido. El reintento con acceso de red terminó con código 0.
  Se utilizó `UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache` para sync y verificación.
- `uv run --frozen python scripts/verify_installation.py --context local`:
  código 0; config-check válido, Ruff sin errores y **32 pruebas aprobadas
  en 1.24 s**. Son resultados locales nuevos, separados de la evidencia remota.
- Evidencia: [verification.json](evidence/local-20260917T083436Z/verification.json),
  [versiones](evidence/local-20260917T083436Z/versions.json), logs `0.log`,
  `1.log`, `2.log` y logs de instalación en esa misma carpeta. Originales en
  `artifacts/verification-local-20260917T083436Z/` y
  `artifacts/local-installation-20260917/` (excluidos de Git).

No se modificaron código, configuración, lock ni decisiones metodológicas.
No se instalaron PyTorch/CUDA ni se modificaron drivers. No se ejecutaron
entrenamientos ni se accedió al conjunto final. Las pruebas sintéticas no
constituyen aceptación de datos de mercado.

Al terminar esa verificación, B seguía propuesta y pendiente de aprobación.

## Decisión local: aprobación de B, 17 de septiembre de 2026

El usuario confirmó explícitamente: «Si, apruebo la politica B.» Se registró
la aprobación metodológica en [ADR-004](decisions/ADR-004-segment-proposal.md).
Este estado reemplaza las referencias anteriores a B como propuesta pendiente;
la política todavía no está implementada ni aplicada y los datos no están aceptados.

Siguiente paso técnico: implementar preparación segmentada conforme a ADR-004,
con máscara de motivos, calentamiento causal por segmento, normalizador ajustado
solo en entrenamiento, índice de episodios y verificación de cobertura y fronteras.
Mantener el bloqueo estricto de la ruta actual hasta disponer de la ruta explícita.
El alcance de esta actualización es documental; no se ejecutaron nuevas pruebas
de código. Se conserva la evidencia de verificación local anterior, sobre d097f5c.
ADR-002 sigue abierto. Sin entrenamientos ni acceso al conjunto final.

## Cierre documental local

Antes del commit se repitió el verificador local: configuración válida, Ruff
sin errores y 32 pruebas aprobadas en 1.17 s, con código de salida 0.
Evidencia nueva en [verification.json](evidence/local-20260917T084415Z/verification.json)
y sus tres logs. El registro identifica el commit base d097f5c y los cambios
documentales presentes durante la ejecución. El commit de cierre incorpora
la evidencia local y la aprobación de B; excluye la eliminación previa de
`.python-version`. El siguiente trabajo sigue siendo la preparación segmentada.

## H1 cerrado: preparación segmentada B, 17 de septiembre de 2026

La ruta explícita `prepare-segmented-development` aplica ADR-004 y
`verify-segmented-development` audita los productos sin modificarlos ni reajustar
el normalizador. `missing_bar_policy = "fail"` y la ruta estricta se conservan.
Los datos de desarrollo están **aceptados técnicamente bajo B**, con las
limitaciones del [informe del hito](hitos/H1-preparacion-segmentada.md).

- Máscara exacta: 16 ausencias, 20 cierres abreviados y 20 reaperturas; sin imputación.
- Entrenamiento: 10900 barras retenidas, 21 segmentos, 10054 transiciones,
  7048 episodios posibles de 180 transiciones en 15 segmentos aptos.
- Ajuste: 10073 observaciones finitas de entrenamiento, una vez por timestamp;
  incluye segmentos cortos y estados terminales. Validación solo transforma.
- Validación: 2190 transiciones continuas, sin episodios de evaluación de 180 pasos.
- Coincidencia exacta con el escenario B del diagnóstico, incluidos límites
  por segmento. Reproducción en otro destino: mismos hashes de derivados.
- Verificación local final: configuración válida, Ruff pasa y 59 pruebas
  aprobadas en 13.85 s. Originales intactos, hashes antes/después verificados.

Evidencias, versiones y comandos: [docs/evidence/segmented-h1](evidence/segmented-h1/COMMANDS.md).
Producto fuera de Git: `data/processed/segmented-B-h1/`. El ZIP académico incluye
los archivos versionados, el producto, las páginas originales de desarrollo y
un Git bundle; el descriptor de entrega identifica el commit y los hashes.
La evidencia de ejecución referencia 108847e como base previa al commit del hito
y registra huellas de los archivos ejecutados. Se conserva fuera del commit la
eliminación local de `.python-version`.

Siguiente hito: simulador causal float64 con contabilidad y costos exactos sobre
los índices aceptados. **No se inició el simulador en esta entrega.** ADR-002
sigue pendiente; no hay PPO/CVaR-PPO ni entrenamientos. Conjunto final sin acceso.

## H2 cerrado: simulador causal, 21 de septiembre de 2026

Implementados `env/accounting.py`, `env/market.py` y `env/trading.py`:
observaciones float64 de 10 características y 2 variables de cartera, objetivo
BTC posterior a costos marcado a apertura de referencia, ejecución en apertura
siguiente con comisión sobre precio ejecutado, deslizamiento adverso y recompensa
logarítmica neta que incluye el gap. Sin clipping de acciones o saldos.

El cargador exige aceptación y auditoría H1. Entrenamiento solo por índice
aceptado de 180 transiciones; validación mantiene 2190 pasos y una sola cartera.
Los cortes devuelven observación final y truncación, sin venta obligatoria.
Se distingue fin de ventana, segmento y partición. ADR-002 permanece abierto:
no se decide descuento, bootstrap ni estimador de riesgo.

Verificación local real: configuración válida, Ruff pasa y **100 pruebas pasan
en 26.68 s**. Casos sintéticos con oráculo Decimal independiente de 60 dígitos,
incluidos 120 portafolios aleatorios deterministas. Comprobación funcional real:
7048 índices revisados, 30 episodios extremos de los 15 segmentos aptos y una
validación continua; 31 recorridos y 7590 transiciones. Acciones prefijadas sin
aprendizaje ni selección por resultados. Error máximo de efectivo 3.64e-12 USDT;
error telescópico máximo 1.67e-15. Fuentes y normalizador intactos.

Informe: [H2-simulador.md](hitos/H2-simulador.md). Evidencias y comandos:
[simulator-h2/COMMANDS.md](evidence/simulator-h2/COMMANDS.md). Libro completo:
`artifacts/simulator-h2/real/ledger.csv`, incluido en el ZIP académico junto con
código, evidencia, datos de desarrollo y Git bundle. La evidencia registra
57e0885 como commit base y hashes del código ejecutado; DELIVERY.json del ZIP
identifica el commit de cierre. `.python-version` sigue eliminado localmente,
fuera de este commit, por el cambio previo del usuario.

Siguiente paso: resolver metodológicamente ADR-002 antes de agentes o entrenamientos.
No se instaló PyTorch/CUDA, no se modificaron drivers y no se accedió al test final.

## Propuesta ADR-002 para revisión — 22 de septiembre de 2026 (UTC)

Sobre H2 `cc913b629694641543e2b54375dbda5d55130544` se preparó
[la propuesta metodológica y técnica](proposals/ADR-002-propuesta.md), todavía
**NO ADOPTADA**. Recomienda H=180 finito, gamma=1 y CVaR sobre la misma suma neta
logarítmica; distingue completitud de trayectoria y procedencia del corte,
requiere tiempo restante y propone validación continua con horizonte móvil.
Explicita que esa evaluación mide transferencia operacional, no garantiza la
restricción de entrenamiento ni optimiza el retorno anual. Incluye alternativas,
fuentes primarias, gradiente de riesgo, parámetros pendientes y migración futura.

Evidencia nueva: [comandos y resultados](evidence/adr002-proposal/COMMANDS.md).
Seis grupos sintéticos independientes aprobados; Ruff pasa; **100 pruebas pasan
en 22.47 s**. Los hashes verifican código/configuración/pruebas/scripts/lock
idénticos a H2. No se hizo nueva auditoría de mercado ni se atribuyen sus
resultados anteriores a esta ejecución. `.python-version` sigue eliminado por
el cambio previo, fuera de esta entrega.

Siguiente paso: revisión académica conjunta del objetivo finito, alcance de la
restricción y regla de despliegue continuo. ADR-002 permanece abierto. No cambiar
el contrato del simulador ni implementar agentes hasta revisar la propuesta;
no entrenar ni acceder al conjunto final. No hubo acceso a datos de mercado en
esta tarea ni modificaciones a la tesis.

## ADR-002 v2 — revisión académica incorporada, 22-09-2026 UTC

[Propuesta v2](proposals/ADR-002-propuesta-v2.md) y
[resumen de respuesta](proposals/ADR-002-v2-resumen-academico.md), sobre v1
`082db3e` y simulador H2 `cc913b6`. Estado **PROPUESTA PARA REVISIÓN, NO ADOPTADA**.
V1 y sus evidencias se conservan. Se reconoce explícitamente que h=1 con cartera
heredada está fuera del soporte conjunto de entrenamiento; se mantiene evaluación
continua móvil como transferencia operacional, sin garantía CVaR a 30 días.
El contraste Sortino mide los procedimientos completos, con posible interacción
entre mecanismo de riesgo y cambio de soporte.

Se define procedimiento único: Q estima eta mediante cuantil empírico, A nuevo
actualiza actor y luego crítico separado; política nueva genera Q nuevo y B
independiente; el dual usa F_B al eta de Q. Eta y lambda quedan fijos en las
épocas PPO. B es diagnóstico y señal dual, no prueba confirmatoria independiente.
La cota d es común y congelada; el presupuesto incluye auxiliares también en C0.
Pseudocódigo, reutilización, sesgos, empates y cortes están en la propuesta.

[Evidencia local v2](evidence/adr002-proposal-v2/COMMANDS.md): seis grupos v1
reproducidos y seis adicionales (tres algebraicos/tres de especificación), Ruff
pasa y **100 pruebas H2 pasan en 21.72 s**. No se modificó src/configs/tests/scripts,
lock ni pyproject; huellas iguales a H2. No se cargó ningún dato de mercado,
no hubo agentes ni entrenamientos y no se accedió al conjunto final. La
reproducción del chat académico es información del usuario, distinta de estos logs.
Se conserva la eliminación local previa de `.python-version` fuera del commit.

El ZIP académico contiene snapshot del commit documental, historial Git bundle,
propuestas/evidencias y descriptor de huellas; no datos de mercado. Próximo paso:
revisión de v2 antes de cualquier cambio al contrato H2. ADR-002 sigue abierto.

## ADR-002 v2.1 — armonización con la tesis, 22-09-2026 UTC

[Propuesta v2.1](proposals/ADR-002-propuesta-v2-1.md) y
[resumen académico](proposals/ADR-002-v2-1-resumen-academico.md).
Estado: **PROPUESTA PARA REVISIÓN, NO ADOPTADA**. V2 (`28cda8b`) permanece intacta.
La revisión académica comunicada por el usuario considera resueltos Q/A/B y
la interpretación de transferencia; se conservaron sus secciones byte a byte.

Armonización limitada: Sortino anualizado primario sqrt(2190)*S_4h, retornos
simples netos, MAR=0, DD sobre todos los períodos, cero DD indefinido. Anualización
solo como convención de reporte, sin independencia temporal asumida. Plan de
tesis registrado: diferencias pareadas por bloques de semillas, bootstrap
unilateral centrado de su media, Holm para C5–C0/C10–C0 y significancia familiar .05.
Réplicas, remuestras, semillas/bloques, precisión y gestión de indefinidos deben
cerrarse antes de evaluar confirmatoriamente. Sortino superior no acredita CVaR.

[Evidencia local](evidence/adr002-proposal-v2-1/COMMANDS.md): tres grupos
sintéticos afectados y uno de preservación aprobados; Ruff pasa y **100 pruebas
H2 pasan en 21.73 s**. Sin cambios operativos, agentes, entrenamientos o acceso
a mercado/conjunto final. `.python-version` sigue eliminado localmente por el
cambio previo, fuera del commit. ZIP con snapshot documental, antecedentes,
evidencias, Git bundle y descriptor verificado. Próximo paso: revisar v2.1 y
cerrar los parámetros pendientes, manteniendo ADR-002 abierto.
