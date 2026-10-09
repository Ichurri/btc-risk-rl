# Reglas para Codex: tesis BTC

## Autoridad y alcance
- Campaña histórica P3 v1.1 autorizada el 08/10/2026 **solo como
  diagnóstico de desarrollo** sobre el derivado H1 exclusivo de
  entrenamiento 2018–2022. Permiso independiente fijado en
  `docs/protocols/P3-market-approval.json` y commit `618a08f`; raíz nueva
  `artifacts/p3-approved-v1`. La sesión inicial
  `p3-market-v1-session-01.service` cerró en pausa presupuestaria válida:
  ledger `ready`, 10/18 corridas completas, 116 unidades aceptadas y
  ninguna unidad pendiente. La campaña sigue abierta; consultar el último
  ledger y repetir preflight otro día antes de otra sesión `systemd --user`.
  El preflight de las 00:04 America/La_Paz del 09/10 quedó bloqueado:
  `ADP1/online=0`, batería 37 %; no se lanzó la sesión 02 ni se modificó
  el ledger. Exigir CA y batería ≥50 % antes de volver a intentar.
  Ver `docs/hitos/P3-ejecucion-historica-v1.md` y el último ledger antes
  de actuar. Conservar 18 corridas K10, orden y brazos β, Q0/Q/A/B+D,
  tres horas globales por día America/La_Paz, hasta tres días activos,
  admisión y pausas solo en fronteras completas; un fallo dentro de
  unidad es irreversible. **No usar validación 2023 ni prueba final
  2024–2025, no reutilizar P2R y no repetir por resultados.** Esta
  autorización sustituye las prohibiciones cronológicas de campaña
  únicamente para P3 v1.1.
- Hito P3 posterior a `a1d9032`: el usuario autorizó **solo implementar y
  verificar sintéticamente la infraestructura del ejecutor histórico P3**.
  Perfil, supervisor, presupuesto y métricas P3 quedan separados de P2R;
  el preflight puede leer únicamente el derivado H1 exclusivo de
  entrenamiento y metadatos para comprobar huellas. Ver
  `docs/hitos/P3-ejecutor-historico-infraestructura.md`. La bandera P3
  permanece desactivada y no hay registro de aprobación ni raíz histórica
  P3. **No ejecutar entrenamiento de mercado, activar permiso, abrir
  validación 2023 ni prueba final 2024–2025.** P0/P1/P2/P2R y sus
  artefactos permanecen intactos. Esta autorización sustituye las
  prohibiciones cronológicas de implementación solo para este hito.
- Hito P3 posterior a `eed4b74`: el usuario autorizó únicamente implementar
  y verificar **con datos sintéticos** la pérdida del crítico β=0/1 de P3
  v1.1. β=0 conserva MSE; β=1 añade `mean(V²)` en los mismos minibatches A
  y targets Monte Carlo congelados. Ver `docs/hitos/P3-critico-sintetico.md`.
  No hay ejecutor ni permiso histórico P3; P0/P1/P2/P2R y sus artefactos
  permanecen intactos. **No entrenar con mercado ni abrir validación/final.**
  Esta autorización sustituye la prohibición cronológica de implementar
  βV² solo para este hito sintético.
- Hito prospectivo P3 posterior a `699d8da`: el usuario autorizó **solo**
  corregir `market_training_executed` y verificar sintéticamente el rechazo
  supervisor de reportes incoherentes antes de aceptar unidades. Ver
  `docs/hitos/P3-marcador-supervisor-sintetico.md`. El marcador requiere
  fuente `accepted_train_collection_only` y pasos completados de **ambos**
  optimizadores; Q0 es `false`. La prueba de perfil histórico usa sobres
  sintéticos, no datos de mercado. Los 99 reportes P2R y P0/P1/P2 siguen
  intactos. **No activar P3 ni ejecutar entrenamiento histórico;
  validación y final siguen protegidas.** La prohibición de
  implementación del párrafo cronológico siguiente fue sustituida
  únicamente para este hito acotado.
- Adjudicación P2R posterior a `75b450c`: el usuario ordenó conservar
  `review`, reconocer que faltó corregir/verificar
  `market_training_executed` antes de congelar el ejecutor y clasificar
  las nueve corridas **solo como diagnóstico descriptivo de desarrollo**.
  Ver `docs/protocols/P2R-adjudicacion-metadato-v1.md`. No se convalida
  retrospectivamente el preflight ni se editan los 99 reportes. El
  análisis de MSE tardía motivó P3 v1.1, **adoptado solo como protocolo
  metodológico exploratorio de desarrollo** en
  `docs/protocols/P3-adopcion-metodologica-v1-1.md` tras la aclaración
  `e30708a` (v1 preservada). **Esta adopción no autoriza implementar ni
  ejecutar P3**. La v1.1 corrige la comparación con predictor cero y
  define razones pareadas exactas; sus comprobaciones son algebraicas
  sintéticas.
  Corrección prospectiva del marcador pendiente, P2R cerrado,
  P2 fallido intacto, sin validación ni prueba final.
- P2R v2 histórico **ejecutado y cerrado operativamente el 07/10/2026 solo
  como diagnóstico de desarrollo** sobre el derivado H1 exclusivo de
  entrenamiento 2018–2022.
  Registro fijado en `docs/protocols/P2R-market-approval.json` y commit
  `38fc54b`; raíz `artifacts/p2r-approved-v2`, con tres sesiones de
  `systemd --user` registradas en el informe. Nueve corridas nuevas y 99
  unidades cerradas, sin incorporar P2,
  sin cambiar protocolo ni seleccionar checkpoints. Ver
  `docs/hitos/P2R-ejecucion-historica-v2.md`. El supervisor aplica
  3 h globales/día America/La_Paz, hasta tres días activos, admisión por
  unidad, pausas solo en frontera completa y fallo irreversible dentro de
  unidad. El ledger está `completed`; no volver a lanzarlo. La regla
  numérica da `review`, pero la aceptación formal queda pendiente por el
  marcador heredado `market_training_executed=false` en los 99 reportes.
  Ver HANDOFF. **No iniciar otra campaña, no reanudar una fallida ni acceder a
  validación 2023 o prueba final 2024–2025.** Los párrafos históricos de abajo
  describen autorizaciones anteriores y no revocan esta autorización
  específica.
- Exportación H1→P2R autorizada el 06/10/2026: derivado exclusivo de
  entrenamiento creado y auditado fila por fila; huella del manifiesto
  fijada en un commit independiente. La lectura puntual de CSV H1
  compartidos, incluidos bytes 2023, fue solo para hash e igualdad del
  prefijo. El preflight posterior vigilado no abre esos CSV. Ver
  `docs/hitos/P2R-training-shard-export.md`. **Sigue sin permiso de campaña**:
  `MARKET_EXECUTION_ENABLED=False`, sin registro aprobado; no lanzar
  unidades, entrenamiento histórico, validación ni prueba final.
- Revisión P2R posterior a `93515ef`: autorizado **solo** aislar físicamente
  el preflight/cargador de los CSV H1 con filas 2023 y ejecutar una sonda
  de señal **sintética** durante cálculo de gradientes en Q/A/B+D.
  P2R ahora exige un derivado exclusivo de entrenamiento aún **no creado
  ni registrado**; preflight histórico falla cerrado. Sondas nuevas 07/08:
  conservar raíces y evidencias, sin reinterpretar 07 como éxito de su
  controlador. Ver `docs/hitos/P2R-preflight-optimizer-signal.md` y
  `docs/protocols/P2R-training-shard-contract-v1.md`. No exportar el
  derivado histórico, activar permiso, entrenar mercado, acceder a
  validación/final ni reanudar campañas fallidas por este hito.
- Ejecutor histórico P2R v2: el usuario autorizó **solo implementarlo y
  verificarlo** tras `ccb010a`. Rama `codex/p2r-historical-executor`.
  `scripts/run_p2r_market.py` y el trabajador exigen un permiso de campaña
  independiente, inactivo en código (`MARKET_EXECUTION_ENABLED=False` y sin
  huella de registro). El preflight puede leer metadatos de entrenamiento
  aceptado sin generar trayectorias; las pruebas de aprendizaje son solo
  sintéticas. **No activar permiso, ejecutar unidades históricas, reanudar
  P2 ni usar validación/final** por esta autorización. Ver HANDOFF e informe
  del ejecutor.
- Sonda 06 P2R **solo sintética** desde `d840d6a`: Q0 cerró `after_q0` y
  SIGTERM al proceso principal durante la primera unidad Q/A/B+D produjo
  ledger `failed`, `Result=exit-code`, ninguna aceptación de unidad 1 y
  huella inalterada del checkpoint Q0. La señal llegó durante la espera
  sintética supervisada, antes de cálculos Q/A/B+D; no prueba un corte de
  optimizador ni apagado físico. Preservar raíces 01–06. El checkpoint
  conservado es evidencia, **no permiso de reanudación**. Ver
  `docs/hitos/P2R-signal-QABD-06.md`. Sigue bloqueado P2R histórico,
  validación y final.
- P2R v2 **ADOPTADO solo como protocolo metodológico de diagnóstico de
  desarrollo** tras precisar `Z>10⁻¹²` por separado en D temprana, D tardía y
  A tardía. Ver `docs/protocols/P2R-adopcion-metodologica-v2.md`. La adopción
  **no autoriza** implementar el ejecutor histórico, activar permiso de
  campaña, ejecutar P2R de mercado, usar validación/final ni reanudar P2.
  Mantener separados P2 y P2R; conservar v1, anexo y sondas 01–05.
- P2R v2 desde `af14af2`: consolidación documental inicialmente **para
  revisión**, antes de la adopción metodológica indicada arriba. Conserva
  v1, anexo, P2 fallido y sondas 01–05. El estado actualizado de `Linger`,
  logout, heartbeat y señal
  está en `docs/proposals/P2R-protocolo-v2.md`; los párrafos cronológicos de
  abajo describen su momento y no revocan la lectura adoptada. No ejecutar
  unidades ni entrenamientos por esta adopción.
- Sonda de señal P2R Q0 **solo sintética** 04/05: SIGTERM al proceso
  principal durante Q0 produjo ledger `failed`, cero unidades/checkpoints
  aceptados y fallo irreversible. La sonda 04 reveló que la CLI devolvía 0;
  `08c0fda` lo corrigió y la repetición 05 dio `Result=exit-code`, estado 1.
  Preservar las cuatro raíces originales 04/05 y las sondas 01–03. Ver
  `docs/hitos/P2R-signal-Q0-sintetica.md`. No hay autorización de P2R
  histórico, validación ni final; la sonda no prueba una interrupción del host
  ni conservación de un checkpoint previo en una unidad posterior.
- Cadencia P2R sintética 03 desde `76757ed`: se corrigió el reloj de
  `run_synthetic_units` para solicitar heartbeats con margen de 4 s y
  rechazar intervalos registrados >5 s. Una sola Q0 sintética breve bajo
  `systemd --user` completó `after_q0` con 6/6 intervalos ≤5 s (máximo
  4.143739 s UTC). Es verificación de infraestructura sintética, **no
  permiso de P2R histórico**. Ver `docs/hitos/P2R-cadencia-heartbeat-03.md`.
  Conservar artefactos 01/02/03; no repetir la sonda ni hacer la prueba de
  señal dentro de unidad con esta autorización.
- Logout Q0 sintético 02 del 05/10/2026: `ready`, checkpoint `after_q0`
  íntegro, `Result=success`, 139 heartbeats sin sesión interactiva y ningún
  evento de suspensión durante 3260.921214 s hasta el reingreso. **Cierra
  solo la sonda sintética de logout**, no habilita P2R histórico. Los 174
  intervalos entre heartbeats superaron 5 s; la corrección posterior consta
  en el hito 03 y no reescribe esta evidencia.
  Conservar intactas raíces/journals 01 y 02. Ver
  `docs/hitos/P2R-logout-Q0-02-cierre.md`.
- Logout Q0 sintético del 05/10/2026: la unidad 01 llegó a `ready`,
  `after_q0` y `Result=success` sin sesión interactiva, pero el host se
  suspendió entre Q0 y el reingreso; por tanto **falló la condición sin
  suspensión**. Conservar intactas las dos raíces de evidencia 01. La causa
  principal inferida es el temporizador de 900 s del greeter GDM, aún sin
  identidad de llamador privilegiada. Corrección del host y repetición 02
  documentadas, **no aplicadas ni iniciadas**. No habilita P2R histórico.
  Ver `docs/hitos/P2R-logout-Q0-diagnostico.md`.
- En `codex/p2r-unit-integration` se preparó una prueba de logout completo
  **solo sintética**: unidad `p2r-logout-q0-review-01.service`, espera de
  900 s dentro del child supervisado y Q0 con checkpoint `after_q0`. Este
  párrafo describe la preparación previa; el resultado posterior consta
  arriba. Ver `docs/protocols/P2R-logout-Q0-synthetic-review.md`.
- P2R desde `e1e98dd`: autorizado conectar y verificar **solo con datos
  sintéticos** Q0 y Q/A/B+D, contadores reales, checkpoints completos y
  fallo irreversible dentro de unidad. Rama `codex/p2r-unit-integration`.
  `scripts/run_p2r.py --mode algorithm` acepta únicamente perfil sintético;
  P2R histórico no tiene permiso ni entrada de campaña. No entrenar con mercado,
  acceder a validación/final, alterar P0/P1/P2 o cambiar configuración del
  sistema. Ver el nuevo informe P2R y el procedimiento de revisión del host.
- P2R: el usuario autorizó desde `d7f253b` **solo infraestructura y pruebas
  sintéticas** de supervisor, journal, guardas, presupuesto e interrupciones.
  Rama `codex/p2r-infrastructure`. La propuesta P2R v1 sigue sin autorización
  para campaña histórica: no hay permiso ni ejecutor de mercado P2R. El perfil
  sintético `scripts/run_p2r.py` es una sonda de ciclo de vida; su ventana de
  reloj ficticia no es admisión de campaña. `Linger=no` del gestor de usuario
  impide verificar continuidad tras logout completo; no cambiar configuración
  del sistema implícitamente. Ver HANDOFF e informe P2R antes de continuar.
- Investigación posterior a `a2014e4`: los registros de sesión y wtmp sitúan
  un apagado del equipo a las 02:20:12 America/La_Paz, coincidente con la
  pérdida del supervisor P2; el iniciador del apagado sigue desconocido.
  `docs/proposals/P2R-protocolo-v1.md` es **propuesta, NO autorización** de
  implementación ni ejecución. Preservar ledger/unidad parcial P2 intactos.
- P2 histórico quedó **detenido por interrupción del supervisor** el 30/09/2026:
  cinco corridas K10 completas, una sexta con una iteración completa y la
  siguiente parcial. El ledger registra `interrupted_supervisor_or_unit` y
  prohíbe reanudar o repetir selectivamente esta campaña. Consultar
  `docs/hitos/P2-ejecucion-interrumpida.md` y el HANDOFF antes de cualquier
  otra acción. La autorización anterior no habilita una campaña de reemplazo.
- P2 histórico autorizado el 30/09/2026 sobre entrenamiento aceptado 2018–2022,
  desde integración `2f01d6c`. Registrar permiso en commit separado y ejecutar
  solo después de preflight, pruebas sintéticas e integridad P0/P1. Son nueve
  corridas K10, tres semillas, C0/C5/C10, crítico4 provisional, D64 y diseño
  de `P2-infrastructure-v1.json` sin cambios. Máximo global 3h/día La Paz,
  tres días activos; pausa solo en frontera completa, fallos sin reintento
  selectivo. Ver `docs/protocols/P2-market-approval-2026-09-30.md`.
  Validación 2023, final 2024–2025 y campañas posteriores siguen bloqueadas.
- P2: diseño de 7357aa1 aceptado (9 corridas, K=10, semillas 610031/610047/610081,
  crítico provisional de 4 épocas, D=64, umbrales §7, hasta 3 días activos).
  La restricción previa de verificación exclusivamente sintética se sustituyó
  **solo para P2 histórico** por la autorización anterior. No repetir P0/P1.
  Conservar d, ADR-002 y Q/A/B. No modificar la tesis. Ver
  docs/protocols/P2-infrastructure-v1.md.

- P1 terminó: 18 corridas, criterio técnico cumplido en 3/3 semillas. La autorización
  se consumió con esta campaña; no repetirla ni inferir autorización de P2.
  Revisar docs/hitos/P1-epocas-critico.md antes de proponer otro piloto.
- Leer README.md, docs/HANDOFF.md y configs/initial.toml antes de modificar código.
- Este repositorio implementa la tesis de Santiago Andrés Iturri Vargas.
- Preservar C0 (PPO), C5 y C10 (CVaR-PPO). Mismo entorno y recompensa.
- P1 aprobado desde 42152c3 autoriza implementar, verificar sintéticamente y ejecutar
  18 corridas K=2: crítico 2/4 épocas, semillas 510031/510047/510081, orden aprobado.
  Descontar consumo de otras campañas del día; P0 cerrado no se repite.
  Rutas nuevas; mismo d, actor y Q/A/B. Validación/final siguen bloqueados.
- P0-approved-v1 autoriza el piloto acotado sobre entrenamiento aceptado 2018–2022,
  después de verificar sintéticamente ejecutor, supervisor y persistencia.
- Presupuesto GLOBAL de campaña: 3h/día America/La_Paz, timestamps UTC; varias
  corridas consecutivas sin concurrencia ni reinicio de contadores al cambiar proceso.
- Configuración, semillas, orden y K=2 aprobados solo para P0; d=-ln(0.90) común.
  Validación/final no accesibles al ejecutor. No repetir selectivamente fallos.
- Se permite PyTorch CPU fijado en el lock. No instalar CUDA ni modificar drivers.
- Fuera de P0/P1 ya cerrados y P2 aquí autorizado, siguen prohibidos otros
  entrenamientos de mercado, pilotos y evaluación confirmatoria.
- No modificar la tesis: entregar evidencia para el chat académico.
- ADR-002 v2.1 está adoptado; H4 autoriza su implementación, sin cambiar su metodología.

## Datos y evaluación
- Prueba final reservada: [2024-01-01, 2026-01-01) UTC. No descargarla,
  cargarla, graficarla o usarla para selección durante desarrollo.
- Los comandos de desarrollo solo admiten datos anteriores a 2024-01-01.
- No retirar las guardas para completar una tarea. Una futura campaña final
  requiere protocolo congelado, revisión explícita y un comando separado.
- Transformadores: ajuste solo en entrenamiento, persistencia y reutilización sin refit.
- No interpolar huecos, eliminar extremos ni fabricar barras.
- No unir segmentos separados como si fueran contiguos.
- Identificar los datos sintéticos de pruebas; no presentarlos como mercado real.
- No reportar pruebas, tiempos o resultados que no se hayan ejecutado.

## Desarrollo y coordinación
- Una tarea de implementación activa por desarrollador; commits pequeños por hito.
- Local y remoto coordinan mediante Git y docs/HANDOFF.md, no mediante memoria de chats.
- Antes de editar: git status, leer último handoff; no sobrescribir trabajo ajeno.
- Usar ramas por tarea cuando exista trabajo concurrente. No force push.
- Al cerrar hito: pruebas, versión/commit, evidencia y cambios metodológicos pendientes.
- Datos voluminosos fuera de Git; manifiestos y huellas en evidencia versionada.
- No credenciales, claves de exchange ni datos personales en archivos versionados.

## Verificación
uv run --frozen ruff check .
uv run --frozen pytest

El entorno debe ser causal y mantener contabilidad float64. No simplificar
el cobro de costos ni ocultar errores con clipping indiscriminado.
