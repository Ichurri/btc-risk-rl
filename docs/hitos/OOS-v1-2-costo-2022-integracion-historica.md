# Integración aislada del costo WF 2022 — 06/11/2026

## Estado y alcance

Se implementó el perfil `oos-v12-wf-cost-only-2022-01` para medir **una**
corrida C10 nueva sobre el corte de entrenamiento 2022, semilla 498614892,
Q0 y diez actualizaciones Q/A/B+D. El gate técnico y el registro de
aprobación son independientes de WF01–WF05. La raíz histórica 2022 no
existía al cerrar esta integración. No se ha abierto 2023 ni 2024–2025.

La autorización del 06/11 está en
[`OOS-2022-y-evaluacion-autorizacion-20261106.md`](../protocols/OOS-2022-y-evaluacion-autorizacion-20261106.md).
El registro técnico fijó las huellas de código, configuración, propuesta y
derivado H1 en un commit separado (`61602a9`, repin `b142d20` por la
corrección de una pausa previa a unidad). El estudio exige suite, Ruff, preflight
vigilado y admisión de presupuesto **de nuevo, dentro de la bitácora de la
campaña**, inmediatamente antes de iniciar una sesión de mercado.

## Contrato implementado

- `WF2022Permit` es un tipo autorizado exacto. El trabajador verifica el
  registro, lease del supervisor, raíz, Q0 o unidad en orden, semilla,
  condición, solicitud, checkpoint previo y fuente exclusiva de entrenamiento.
- El supervisor y el trabajador usan el algoritmo Q/A/B+D existente. El
  supervisor exige el reporte, los pasos de ambos optimizadores, el marcador
  `market_training_executed` y un checkpoint `after_q0` o
  `after_dual_and_D` antes de aceptar una unidad.
- `BudgetAttempt` inicia la bitácora durable antes del preflight y de la
  carga del corte. Reconcilia intentos, sesiones y ledger por unión de
  intervalos; cuenta fechas de `America/La_Paz`, incluye reservas y rechaza
  estados fallidos o incompletos. En 23:00–08:00 la unidad debe caber antes
  de medianoche o de las 08:00; antes de medianoche queda también la reserva
  global de 2700 s.
- Si un recurso o el presupuesto compartido dejan de cumplir entre la
  preparación y una unidad, el supervisor registra un bloqueo o pausa en
  frontera completa. Si el fallo ocurre **dentro** de la unidad, el ledger
  queda `failed` y no se reanuda.
- El preflight vigilado permite abrir solo el derivado H1 de entrenamiento
  bajo `data/` y registra las rutas observadas. Rechaza CSV H1 compartidos,
  validación y prueba final antes de abrirlos.

## Verificación de integración

Una prueba controlada recorrió el trabajador real y `complete_unit` hasta
Q0 y la unidad 1, con reporte, contadores y hashes de dos checkpoints. Otra
recorrió el supervisor en dos sesiones, reabrió el ledger y verificó el
reingreso desde `after_q0` hacia `after_dual_and_D`. Estas pruebas usan una
fuente sintética encapsulada con el perfil del entrenamiento; **no generan
trayectorias históricas ni miden el costo del corte 2022**. Hay pruebas de
lease alterado, aprobación falsificada, raíz simbólica o huérfana, presupuesto,
cruce de medianoche, fallos y pausas.

La captura de preflight anterior al permiso, en
[`preflight-closed.json`](../evidence/oos-wf-2022-integration/preflight-closed.json),
registró 4678 inicios y 7703 filas para ajuste del normalizador. Quedó
`blocked` tanto por permiso inactivo como por `MemAvailable=4110069760 B`,
inferior a 4 GiB en ese instante. La alimentación, disco, gestor, Linger y
archivos abiertos fueron conformes en esa captura. Es un estado del momento,
no una admisión posterior.

El primer barrido de suite después de integrar registró **499 passed, 1
failed**: una prueba de reingreso leyó una huella de código mientras se
editaba la fuente durante la suite. La misma prueba pasó al ejecutarse con
fuente estable. La suite sobre código fijado dio **502 passed**. Dos pruebas
adicionales detectaron y corrigieron el tratamiento de recursos o presupuesto
perdidos antes de unidad; tras el repin, la suite final dio **504 passed in
433,71 s** y Ruff pasó. Comandos y resultados constan en
[COMMANDS.md](../evidence/oos-wf-2022-integration/COMMANDS.md).

El preflight vigilado tras activar el permiso siguió sin abrir archivos
protegidos, pero dio `blocked` a las **17:24 hora de La Paz** por CA
desconectada: batería 81 %, `MemAvailable=5854142464 B`, disco libre
`128975572992 B`, `Linger=yes`, gestor `running`, presupuesto externo 0 s.
La alimentación debe reconectarse y medirse de nuevo; ninguna unidad
histórica se inició con esta captura.

## Límites y siguiente puerta

La prueba sintética de `systemd --user` confirmó `Restart=no`,
`InvocationID` y un inhibidor `sleep:idle` activo durante la unidad de
sonda. No demuestra físicamente la pantalla apagada ni un corte eléctrico.
El lanzamiento histórico requiere recursos y presupuesto **vigentes**, un
preflight `ready`, una unidad con reserva, y una sesión nueva bajo
`systemd --user`. No se reutiliza WF05 ni se acepta un ledger `failed`.

La evaluación fuera de muestra v1.2 conserva estado **propuesta**. Los
17 días activos mínimos de su escenario no caben entre el 06 y el 16/11
bajo 3 h globales y reserva de 2700 s por día. La medición 2022 puede
refinar costos, pero no resuelve por sí sola el cambio de alcance o
presupuesto académico. La prueba final continúa cerrada.
