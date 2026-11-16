# Hito P2R — unidades reales bajo supervisor, solo sintético

Base `e1e98dd`; rama `codex/p2r-unit-integration`. Alcance autorizado:
conectar el supervisor P2R con las unidades Q0 y Q/A/B+D **del perfil
sintético** y verificar su ciclo de vida. P2R histórico sigue sin permiso ni
entrada de campaña. El diseño científico de la propuesta P2R v1 no se ha
adoptado para ejecución.

## Contrato implementado

`p2r_units.run_synthetic_units` crea exclusivamente `SyntheticMarket` y exige
`P2SyntheticSettings` exacto. La CLI `scripts/run_p2r.py --mode algorithm`
rechaza `market`, `validation` y `final` antes de crear salida. La unidad usa
el **worker P2 existente** por subprocess: `complete_unit` ejecuta Q0 o una
iteración completa de Q/A/B seguida de D. No hay otra implementación del
algoritmo, selección de checkpoints ni acceso al histórico.

El supervisor admite por presupuesto global compartido, topes Q0/iteración,
reserva de cierre, memoria del worker y recursos de host. Conserva un lock
global y escribe journal durable con inicio, heartbeat, señales, fin y
salida. Los heartbeats leen el marcador del worker: los contadores no se
inventan ni se heredan de la unidad anterior. Al cerrar, valida los **deltas
reales** de trayectorias, transiciones, D y pasos actor/crítico contra el
contrato del perfil sintético. Verifica además hash de `state.pt`, manifiesto,
configuración, código, datos sintéticos, condición, generación y frontera.
Q0 solo se acepta en `after_q0`; cada iteración completa con D, en
`after_dual_and_D`. Únicamente esas fronteras admiten reanudación.

`SIGTERM`/`SIGINT` durante una unidad detienen al worker, marcan ledger
`failed`, conservan logs, marcadores y cualquier archivo parcial, y prohíben
reintento. Si el proceso supervisor desaparece sin manejar la señal, el
ledger `running` se convierte en fallo permanente al abrirlo de nuevo.
Pérdida de disponibilidad durante una unidad se registra; el watchdog deja
terminar solo dentro de los topes y se pausa antes de la siguiente. Un
checkpoint corrupto o incompatible no puede cerrar la unidad. La pausa
planificada por límite sintético o presupuesto ocurre antes de abrir otra.

## Qué demuestra y qué falta

La equivalencia sintética compara estado de actor, crítico, optimizadores,
η, multiplicador, eventos, auditorías y contadores con el worker P2 directo.
La reanudación se ensaya desde `after_q0` y desde
`after_dual_and_D`, conservando archivos D ya creados. Las interrupciones se
ensayan tanto en Q0 como en Q/A/B+D. Son comprobaciones del software, **no**
entrenamiento histórico ni evidencia de mejora del crítico, rentabilidad,
generalización o cumplimiento CVaR.

Una futura P2R histórica requeriría permiso nuevo registrado, ejecutor
train-only de nueve corridas, huellas congeladas del histórico/normalizador,
preflight real, verificación de `Linger=yes`, logout completo y recursos aptos.
Este trabajo no implementa ni activa esa entrada. El
[procedimiento de revisión del host](../protocols/P2R-host-preflight-review.md)
es independiente de estas pruebas; no modifica `systemd` ni umbrales.

Las rutas y huellas P0/P1/P2 se comprueban en
[COMMANDS.md](../evidence/p2r-unit-integration/COMMANDS.md). El ledger P2
fallido y su unidad parcial siguen fuera de los contadores P2R y no se
reanudaron. La eliminación local anterior de `.python-version` no forma parte
de los commits.
