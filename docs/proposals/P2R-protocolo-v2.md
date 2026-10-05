# P2R v2 — repetición íntegra y supervisada del diagnóstico P2

**PROPUESTA PARA REVISIÓN ACADÉMICA, NO ADOPTADA. NO AUTORIZA IMPLEMENTAR
EL EJECUTOR HISTÓRICO NI EJECUTAR P2R SOBRE MERCADO.** Revisión documental
desde `af14af2`. Consolida [v1](P2R-protocolo-v1.md), su
[anexo de infraestructura](P2R-infraestructura-addendum-v1.md) y las sondas
sintéticas 01–05. V1 y el anexo se conservan como antecedentes. La adopción
de ADR-002 y la autorización consumida de P2 no constituyen permiso P2R.

## 1. Pregunta, unidad de análisis y separación de P2

P2R repetiría **íntegramente nueve corridas nuevas**, desde Q0, con semillas
610031, 610047 y 610081 y las condiciones C0/C5/C10. P2 quedó `failed` tras
un apagado coincidente con una unidad incompleta; el iniciador del apagado
sigue desconocido. Sus cinco corridas completas y su sexta parcial se
preservan para trazabilidad, tiempos y contraste descriptivo de
reproducibilidad, pero **nunca** completan la matriz P2R, sus denominadores ni
sus criterios. P2R requiere raíz, unidad, ledger, permiso y manifiestos
propios. No se reanuda P2 ni se mezcla una trayectoria suya. Si P2R falla,
queda fallida o incompleta según la regla predefinida; no nace un permiso
automático para otra repetición.

Elegir semillas nuevas respondería otra pregunta y dejaría sin reconstruir
el diseño interrumpido; incorporar solo las cuatro corridas faltantes
seleccionaría supervivientes. Ambas alternativas se descartan para P2R.

La pregunta técnica se mantiene: si, con el contrato aprobado de P2 y cuatro
épocas **provisionales** del crítico, el error de valor evoluciona en A y en
D nuevo dentro del histórico de entrenamiento. D comparte período de mercado
y puede solaparse con A/Q/B; por tanto no es validación temporal. Esta
propuesta no evalúa Sortino fuera de muestra, rentabilidad, cumplimiento
poblacional de CVaR ni eficacia confirmatoria.

## 2. Matriz y contrato científico propuesto

| Bloque de semilla | Orden secuencial, sin concurrencia | Unidades por corrida |
| --- | --- | --- |
| 610031 | C0 → C5 → C10 | Q0; k=0,…,9: Q/A/B+D |
| 610047 | C5 → C10 → C0 | Q0; k=0,…,9: Q/A/B+D |
| 610081 | C10 → C0 → C5 | Q0; k=0,…,9: Q/A/B+D |

Cada Q0 contiene 400 trayectorias Q. Cada iteración contiene 64 A, 400 Q,
400 B y 64 D. Son 81360 trayectorias de aprendizaje y 5760 diagnósticas
para nueve corridas completas, equivalentes a 14644800 y 1036800
transiciones de 180 pasos. Hay 720 pasos de actor y 1440 de crítico previstos;
los D no actualizan parámetros. C0 consume Q/B auxiliares y mantiene
multiplicador exactamente cero para igualar presupuesto y preservar RNG de A.

Se hereda sin cambio algorítmico el
[ADR-002 v2.1 adoptado](../decisions/ADR-002-risk-horizon.md) y la
[configuración P2](../protocols/P2-infrastructure-v1.json), SHA-256
`d5fa2f2726cd6458df3c290e7b58c591f11310c7a9b645c47a5fb6bd419e5238`:
H=180, gamma=1, retornos Monte Carlo completos, logística-normal sin clipping
silencioso, actor y crítico separados, recompensa logarítmica neta, costos y
contabilidad H3, actor dos épocas, crítico cuatro provisionales, red 32/tanh,
minibatch 16, tasas y Adam del JSON. La pérdida de riesgo es el negativo de
la suma de recompensas netas; `d=−ln(0.90)=0.10536051565782628` es referencia
económica común C5/C10, fijada antes de P2, no tope de pérdida individual ni
drawdown. No se cambian semillas, K, tamaños, hiperparámetros o d a partir de
resultados.

Solo se usarían los 7048 inicios aceptados H1 de entrenamiento
`[2018-01-01, 2023-01-01) UTC`, con reemplazo uniforme y sin cruzar
exclusiones ni particiones. El normalizador H1 se reutiliza sin refit.
El ejecutor histórico futuro debe fallar antes de cargar trayectorias si la
identidad de datos, normalizador, código, configuración o protocolo difiere
de las huellas congeladas. No debe exponer validación 2023 ni final
2024–2025. Esa entrada histórica P2R **todavía no existe**.

En cada k, `Q_k` estima eta con su lote y la política vigente; `A_k` actualiza
actor y luego crítico con targets/coeficientes congelados conforme al ADR;
la política nueva genera `Q_{k+1}` y `B_{k+1}` independientes para auditoría
y única actualización dual. `D_k` se recoge después, con copia congelada de
`π_k`, la política que produjo `A_k`, y RNG propio. Ambos críticos
`φ_k` anterior y `φ_{k+1}` posterior se evalúan sobre **los mismos** retornos
Monte Carlo completos de D. D no actualiza actor, crítico, eta,
multiplicador, optimizadores, gradientes ni generadores de Q/A/B. La
comparación pre/post debe reconocer que `φ_k` puede estar desfasado respecto
de `π_k`; el contraste post-D frente a post-A tampoco es un holdout temporal.
Se registran inicios duplicados, solapamiento de inicios y transiciones y
denominadores; no se filtra D por solapamiento.

## 3. Decisiones, fundamento, evidencia y brecha

«Adoptado» en ADR-002 y «aceptado para P2» describen antecedentes, **no**
adopción de este protocolo P2R. «Verificado» aquí se limita al alcance
indicado por la evidencia.

| Decisión científica o regla de integridad propuesta | Fundamento | Implementación y verificación disponibles | Brecha antes de P2R histórico |
| --- | --- | --- | --- |
| Nueve corridas nuevas, tres semillas y orden rotado; separar absolutamente P2 | Evita completar selectivamente una campaña fallida y conserva el bloque semilla/condición | Diseño P2 aceptado; P2 fallido y parcial documentados y preservados | Permiso, raíz y ejecutor P2R propios; comprobar huellas P0/P1/P2 al ingreso |
| C0/C5/C10 con mismo entorno, recompensa, H=180, gamma=1 y Q/A/B | Comparabilidad exigida por ADR-002; retorno completo de objetivo finito | ADR-002 adoptado; algoritmo P2 reutilizado por unidades sintéticas con equivalencia de estado | Verificar conexión histórica sin alterar Q/A/B |
| Cuatro épocas provisionales del crítico y parámetros P2 sin cambios | P1 motivó estudiar evolución, no congeló parámetro confirmatorio | JSON P2 y pruebas sintéticas; P2 parcial aporta solo desarrollo | Ninguna selección retrospectiva de épocas ni ajuste de parámetros en P2R |
| d=−ln(0.90) común C5/C10; C0 con auxiliares y riesgo apagado | Referencia económica preseleccionada; presupuesto comparable y RNG de A estable | ADR/P2 y pruebas de equivalencia sintética previas | Verificar identidad de configuración y streams en ejecutor histórico |
| A y D completos H180; D64 con `π_k` congelada, RNG separado y mismos targets para `φ_k`/`φ_{k+1}` | Separa ajuste del crítico de diagnóstico nuevo sin confundir política generadora | Infraestructura P2 y pruebas sintéticas de equivalencia/reanudación; trabajador P2 reutilizado | Medir y auditar la integración train-only, solapamiento y costo D real |
| Dos unidades: Q0 y Q/A/B+D; fronteras `after_q0`, `after_dual_and_D` | Q/A/B+D es indivisible; D parcial no completa muestra de riesgo ni unidad | Supervisor sintético conectado al trabajador P2; manifiestos y contadores verificados; reanudación sintética desde ambas fronteras | Repetir verificación de identidad, contadores y reanudación con ejecutor histórico antes de permiso |
| 10800 s globales/día La Paz, hasta tres días activos y reserva de cierre | Límite del equipo y comparabilidad; ninguna corrida reinicia el reloj | Lock y débito compartido probados con fixtures; sondas usan ventana sintética | Preflight real con saldo externo, medición de Q0/D y admisión antes de cada unidad |
| Solo entrenamiento H1, normalizador fijo; validación/final inaccesibles | Evita fuga temporal y uso del conjunto reservado | CLI sintética rechaza `market`/`validation`/`final` antes de crear salida | Falta ejecutor histórico train-only con permiso específico y huellas congeladas |
| Diagnóstico D no confirmatorio y criterio conjunto por semilla/condición | D comparte histórico; evita tratar trayectorias/condiciones como réplicas independientes | Métricas y reglas P2 aceptadas; no hay P2R histórico | Publicar nueve recorridos, solapamiento y denominadores completos; no inferir generalización ni CVaR |

## 4. Supervisor, cortes y evidencia 01–05

El supervisor P2R propuesto debe operar como unidad `systemd --user`
independiente del chat y del terminal, con cgroup/`InvocationID`, journal de
systemd y JSONL propio con cadena SHA-256 y `fsync`. Cada heartbeat registra
UTC, monotónico, día La Paz, campaña/corrida/unidad, fase, PID/cgroup,
contadores publicados por worker, RSS y alimentación. La cadencia **medida**
entre heartbeats no puede superar 5 s; se programa aproximadamente a 4 s
para dejar margen, pero una desplanificación todavía puede producir fallo.
El intervalo posterior al último heartbeat hasta el cierre se informa aparte.

| Sonda sintética | Resultado comprobado | Lo que no demuestra |
| --- | --- | --- |
| 01, logout Q0 | Q0 llegó a `after_q0` sin sesión interactiva; después el host se suspendió antes del reingreso: **falló «sin suspensión»** | Ausencia de futuras suspensiones o causa privilegiada del evento 01 |
| 02, logout Q0 | Con `Linger=yes` y gestor `running`, última sesión interactiva retirada; 139 heartbeats de la misma invocación sin sesión, Q0 `ready` y cero eventos de suspensión hasta el regreso | Continuidad ante apagado físico; heartbeat ≤5 s (174/174 intervalos lo excedieron) |
| 03, cadencia Q0 | Tras corrección, 6/6 intervalos registrados ≤5 s; máximo 4.143739 s, checkpoint `after_q0` íntegro | Garantía bajo cualquier carga o en histórico |
| 04/05, señal Q0 | SIGTERM durante Q0 dejó ledger `failed`, ninguna unidad/checkpoint aceptado; 04 reveló salida CLI 0, corregida; 05 terminó systemd `exit-code`/1 | Conservación de checkpoint **anterior**; señal real durante Q/A/B+D; apagado físico |

Así, el estado antiguo `Linger=no` del anexo es **histórico**, no el resultado
del preflight 02. `Linger=yes` se observó para esa sonda, pero debe volver a
verificarse en la fecha y usuario de una campaña. El logout completo 02 fue
positivo para continuidad de Q0 y ausencia de suspensión en ese intervalo;
no borra el fallo de 01. La corrección de heartbeat 03 tampoco reescribe
los 174 intervalos fallidos de 02. La señal 05 confirma la salida no cero
tras corregir 04, pero **no** convierte una sonda Q0 en prueba de Q/A/B+D.
Existen pruebas automatizadas sintéticas de SIGTERM en unidad 1 después de Q0
y de reanudación desde fronteras completas; son evidencia de software,
no una sonda de señal bajo systemd con Q/A/B+D activo. En particular, aún
falta comprobar con huellas antes/después que un checkpoint anterior permanezca
intacto y sea el único aceptado si falla una unidad posterior, aunque la
campaña ya no pueda reanudarse. Ningún servicio de usuario garantiza
continuidad ante apagado físico; la evidencia P2 solo sitúa la pérdida del
supervisor junto a un apagado, sin identificar quién lo inició.

| Corte o incidente | Ledger y artefactos | Reanudación |
| --- | --- | --- |
| Antes de abrir unidad, por presupuesto o guarda no apta | Pausa con causa, sin nueva unidad; conservar débitos y último checkpoint completo | Solo en `after_q0` o `after_dual_and_D`, con identidad íntegra y saldo válido |
| `SIGTERM`/`SIGINT` entre unidades | Pausa registrada; no lanzar worker siguiente | Igual que frontera completa |
| Señal, watchdog, no finito, identidad corrupta, heartbeat >5 s o worker perdido **dentro** de Q0/Q/A/B+D | `failed`; conservar ledger, journal, logs, parcial y checkpoints previos; no aceptar checkpoint de unidad interrumpida | Prohibida en esta campaña; no reemplazar Q/A/B/D ni seleccionar otra corrida |
| Pérdida de AC/batería/recursos durante unidad | Registrar; permitir cierre únicamente dentro de watchdog/reserva, después pausar. Si no se completa íntegra, `failed` | Solo si el cierre alcanzó frontera válida |
| Muerte sin manejador o apagado del host | En inspección posterior, conciliar `running`, journal y bloqueo; marcar `failed` sin iniciar worker | Prohibida; tiempo faltante se trata conservadoramente |
| Tres días/sesiones agotados sin completar matriz | `incomplete`, evidencia intacta | No ampliar límites automáticamente |

Los checkpoints anteriores son evidencia íntegra pero **no** permiso de
recuperar selectivamente una campaña `failed`. La primera Q0 interrumpida
tiene necesariamente cero checkpoints aceptados; no se debe describir como
conservación de uno previo.

## 5. Presupuesto, admisión y preflight futuro

Máximo global **10800 s por día America/La_Paz** entre todas las campañas,
incluida carga, preflight, Q/A/B, D, instrumentación, guardado y cierre;
timestamps UTC. Se permiten corridas secuenciales en un día si caben. Hasta
tres días activos, tres sesiones por corrida y 27 de campaña; ninguna
concurrencia. Preflight ≤900 s, trabajo ≤8100 s y reserva de cierre 1800 s.
La admisión usa el saldo real tras débitos externos, nunca reinicia por
proceso/corrida ni gana tiempo para una unidad en curso al pasar medianoche.
El 30/09/2026 La Paz está excluido por débito P2 incierto; otro día con cargo
externo incompleto se considera agotado (10800 s).

Primera Q0 de cada corrida: admisión 1800 s. Primera Q/A/B+D: 2700 s,
con D ≤900 s dentro de la unidad. Luego exigir 1.5 veces el máximo de
unidades completas medidas para misma condición y runtime; nunca reducir
estimación por un caso rápido ni aumentar topes. La primera unidad programada
mide D real, sin corrida de calibración extra. Los tiempos sintéticos y P2
solo orientan factibilidad; no miden el costo del supervisor P2R histórico.
Si la unidad siguiente no cabe junto con reserva, pausar **antes** de abrirla.
Exceder tope, RSS de worker 10 GiB, discontinuidad de reloj >2 s o invadir
reserva es fallo de integridad.

En el host real, comprobar y registrar en cada entrada: `Linger=yes`, gestor
operativo, ausencia de otra campaña, raíces nuevas, huellas P0/P1/P2 intactas,
código/configuración/protocolo/datos/scaler congelados y permiso P2R específico
en commit separado. Recursos: AC conectada, batería del sistema legible
≥50 % al preflight y ≥40 % antes de cada unidad, `MemAvailable` ≥4 GiB y
disco libre ≥10 GiB en la **raíz real**. Sensor ausente/incoherente bloquea;
no se ajustan umbrales por conveniencia. La prueba 02 y sus lecturas no
constituyen aptitud futura. El metadato heredado
`market_training_executed=false` requiere corrección/verificación antes de
congelar código histórico, sin alterar Q/A/B+D.

## 6. Criterios de evaluación y cierre

Para X=A o D y cada versión del crítico, con 64 trayectorias de 180 pasos:

    MSE_X = Σ(V−G)²/(64·180),  Z_X = ΣG²/(64·180)
    R_X = MSE_X/(Z_X+10⁻¹²),  sesgo_X = Σ(V−G)/(64·180)
    sesgo_normalizado_X = sesgo_X/√(Z_X+10⁻¹²)

`Z` es segundo momento, no varianza. Agregar primero SSE, G² y conteos de
las ventanas temprana k={0,1,2} y tardía k={7,8,9}; **no** promediar razones.
Cada `Z` pertenece a un lote y una ventana: `Z_D,temprana`, `Z_D,tardía` y
`Z_A,tardía` son tres denominadores distintos de la regla conjunta. Si alguno
es `≤10⁻¹²`, registrar sus números pero clasificar la razón correspondiente
como no informativa; el estabilizador `10⁻¹²` no convierte esa ventana en
elegible.
Publicar pre/post en A y D, tercios del horizonte, solapamiento y métricas
de eta, multiplicador, shortfalls A, gradiente de riesgo y auditorías B.
Una violación B no implica activación del gradiente de riesgo en A. Publicar
advertencias como tasas con denominador explícito por oportunidad
(10 A/D, 80 minibatches actor, 160 crítico y 10 auditorías B por corrida
completa), no conteos brutos. Una advertencia desfavorable no cambia
hiperparámetros ni detiene selectivamente una corrida.

Solo con **nueve corridas K10 íntegras y sin fallos**, en al menos dos de
tres semillas de **cada** condición deben cumplirse juntas las tres puertas
`Z_D,temprana>10⁻¹²`, `Z_D,tardía>10⁻¹²` y
`Z_A,tardía>10⁻¹²`, más `R_D,post,tardía≤1`,
`R_D,post,tardía≤0.8·R_D,post,temprana`,
`|sesgo_normalizado_D,post,tardía|≤0.25` y
`R_D,post,tardía−R_A,post,tardía≤0.5`. Las tres puertas se evalúan por
separado para cada semilla/condición; no se sustituye una con otra ni se
promedia `Z` entre A y D. La semilla/condición es la unidad
de resumen; tres condiciones de una misma semilla no son réplicas
independientes. Si las nueve cierran pero no se cumple la regla conjunta,
resultado `review`; si falta una o la integridad falla, `not_evaluable`.
Ningún checkpoint se selecciona por rendimiento. Estas tolerancias son
criterios de ingeniería de desarrollo, no un contraste confirmatorio ni una
garantía financiera o poblacional de CVaR.

## 7. Brechas y decisión académica solicitada

Antes de considerar **por separado** una implementación histórica: revisar
esta v2 y resolver si el conjunto de reglas conserva la pregunta técnica de
P2. Si se adopta después, congelar versión/huellas y construir el ejecutor
train-only con permiso específico inaccesible por simple edición de JSON o
por el comando público. Verificar sintéticamente identidad, presupuesto,
equivalencia Q/A/B+D, D sin mutación, ambas fronteras, rechazo de datos
prohibidos, checkpoint previo ante fallo posterior, señal durante Q/A/B+D y
reconciliación tras muerte abrupta. Repetir preflight vivo en la fecha de la
campaña. Una prueba controlada de apagado físico no es requisito para afirmar
que un servicio resiste apagados; **tal afirmación está prohibida**. Si la
política académica exigiera ensayarlo, necesitaría protocolo separado y
aceptaría de antemano la pérdida de esa campaña sintética.

Después, y solo con autorización humana nueva, registrar permiso en commit
separado y decidir si puede iniciarse la primera unidad histórica. Esta v2
no adopta valores automáticamente, no cambia código, no ejecuta campañas y
no concede acceso a validación ni al conjunto final. La tesis permanece
intacta.
