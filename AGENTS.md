# Reglas para Codex: tesis BTC

## Autoridad y alcance
- P2R v2 desde `af14af2`: consolidación **documental para revisión**, no
  adopción ni permiso de ejecutor/mercado. Conserva v1, anexo, P2 fallido y
  sondas 01–05. El estado actualizado de `Linger`, logout, heartbeat y señal
  está en `docs/proposals/P2R-protocolo-v2.md`; los párrafos cronológicos de
  abajo describen su momento y no revocan esta lectura. No ejecutar unidades
  ni entrenamientos por esta revisión.
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
