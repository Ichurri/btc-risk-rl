# Cierre del entrenamiento principal OOS v1.2 — 14/11/2026

## Alcance y resultado

El perfil `main-2018-2022` usó exclusivamente el derivado H1 de entrenamiento.
La sesión `oos-v12-training.service`, `InvocationID`
`8a7a764ba6b04acab12ca78a3d3ddbe3`, reingresó desde la Q0 aceptada de
`run-103-C10-b0`. Su suite formal pasó en 881,605 s, Ruff en 0,093 s y el
preflight vigilado dio `ready` en 43,288 s: 7.048 inicios, sin apertura de
CSV H1 compartidos ni protegidos. El proceso principal informó
`nightly_result=completed` el 14/11 a las 11:14:56 `America/La_Paz`.

El ledger original, que no se modificó para este informe, terminó
`completed`, cursor 108, `pending=null`, **108/108 corridas**, **36/36 ternas**
y **1.188/1.188 unidades**. Cada condición C0, C5 y C10 tiene 36 corridas.
La auditoría de solo lectura recorrió sus 3.622 filas, verificó cada enlace
`previous_hash` y `state_hash`, y calculó de nuevo la huella de cada uno de
los 1.188 checkpoints aceptados (26.091.150.220 bytes). No encontró
desacuerdos. El ledger SHA-256 es
`c3e1d793997e6379739d01223876962260d988c892ed44c7b161878adfc81e6b`;
el último checkpoint es `run-107-C5-b0/checkpoint-10/state.pt`, SHA-256
`e2c2b35e695251824574e32a4203545dca86f12bb36a681f652c3f2298009cce`.
Los resultados reproducibles están en
[`closure.json`](../evidence/oos-v12-main-closure-20261114/closure.json).

## Cierre del servicio y presupuesto

`systemd` terminó con **`Result=timeout`**, aunque el proceso principal
salió con código 0. El journal identifica el fallo en `ExecStopPost`: el
generador de `reporte-codex.md` permaneció 90 s y fue terminado con estado
143 a las 11:16:27. No fue una unidad de aprendizaje fallida. Se dejó ese
estado y el journal intactos y se completó `reporte-codex.md` mediante una
auditoría independiente. No se inició otra sesión ni se repitió ninguna
unidad. El timer sigue deshabilitado.

La lectura del presupuesto compartido a las 11:28:24 local carga el 14/11
**33.621,063 s**: 32.729,203 s del ledger principal y 891,860 s de la
bitácora previa fuera de ese intervalo. Con máximo global de 50.400 s y
reserva de 2.700 s, quedaban 14.078,937 s antes de reserva. No había otra
campaña activa. El cargo propio acumulado del ledger principal en los cuatro
días fue 156.791,374 s. Ver
[`budget.json`](../evidence/oos-v12-main-closure-20261114/budget.json).

La contabilidad conservadora del **12/11** conserva un cargo de
51.223,830 s, **823,830 s sobre el máximo nominal de 50.400 s**. El ledger
registra 38.973,205 s activos ese día; su última unidad aceptada terminó
a las 13:09:39 local, antes de agotarse la ventana de admisión y su reserva.
La cifra mayor incluye tiempo cargado hasta las 16:34:51 tras la última
unidad. Por tanto, el dato demuestra exceso del cargo conservador de cierre,
pero no una unidad iniciada después del límite. No se corrige ni oculta esa
desviación retrospectivamente; cualquier afirmación de cumplimiento
presupuestario estricto de toda la campaña requiere adjudicarla por separado.

## Interpretación y siguiente etapa

Este cierre acredita ejecución y trazabilidad del **entrenamiento**. Las
corridas `wf-2021` originales permanecen íntegras, pero su exclusividad de
bloqueo original no quedó demostrada y siguen siendo diagnóstico descriptivo.
WF05 y las campañas P0–P3 conservan sus cierres. No se evaluaron políticas
en 2023 ni en 2024–2025. Tampoco se ha demostrado superioridad financiera,
rentabilidad, generalización temporal o cumplimiento poblacional de CVaR.

Antes de la evaluación se requiere el protocolo y permiso separados, la
verificación del evaluador histórico, el tratamiento académico de la
desviación de 2021 y de la contabilidad del 12/11, y las demás puertas de la
propuesta OOS v1.2. No seleccionar checkpoints según resultados futuros.

## Evidencias y comandos

- [`closure.json`](../evidence/oos-v12-main-closure-20261114/closure.json):
  cadena, roster y huellas de todos los checkpoints.
- [`budget.json`](../evidence/oos-v12-main-closure-20261114/budget.json):
  cargo global y fuentes no solapadas.
- [`service-close-journal.txt`](../evidence/oos-v12-main-closure-20261114/service-close-journal.txt)
  y [`service-state.txt`](../evidence/oos-v12-main-closure-20261114/service-state.txt):
  distinción entre final del proceso principal y fallo de `ExecStopPost`.
- [`COMMANDS.md`](../evidence/oos-v12-main-closure-20261114/COMMANDS.md):
  comandos realmente ejecutados y procedimiento de auditoría.
