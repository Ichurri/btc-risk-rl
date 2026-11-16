# WF `...05`: segunda sesión y pausa presupuestaria

**Estado: `ready`, 11/22 unidades aceptadas, `pending=null`.** La campaña no
terminó ni falló. Esta auditoría corresponde a la raíz exclusiva
`artifacts/oos-v12-wf-cost-only-05/`; las raíces `...01`–`...04` conservan
sus huellas. La evaluación fuera de muestra v1.2 permanece inactiva.

## Admisión y ejecución

El 01/11/2026 en `America/La_Paz`, antes de lanzar, se comprobó que el
ledger seguía `ready` con solo Q0 aceptada, `pending=null` y checkpoint
`after_q0` de SHA-256
`8310507d87c7ea2020ed872bb74adcfb20615debe4de271a827a4011ba93f185`.
La auditoría Q0 repetida fue idéntica, byte por byte, a la publicada. No
había otra unidad de campaña activa. La suite completa dio **463 passed**
en 349,96 s; Ruff pasó. El preflight vigilado nuevo, tomado a las
`2026-11-01T22:43:42.683121Z`, dio `ready` sin bloqueos: CA conectada,
batería 100 %, `MemAvailable=7.354.462.208 B`, disco libre
`134.322.737.152 B`, `Linger=yes`, gestor `systemd --user=running`,
huellas conformes y ninguna apertura de CSV H1 compartidos ni de datos
protegidos. Su SHA-256 es
`b9221cac25257afb0eaa313f3e1ebf037e450d81a6f3f9b83cae3543ea337a6c`.

Se lanzó **una** sesión `systemd --user`, con `Restart=no`:

- Unidad: `oos-wf-cost-20261101-05-session-02.service`.
- `InvocationID`: `16d210a2098e4ab58f83cf8fbb7d0423`.
- Inicio: `2026-11-01T22:44:00.364578Z`; cierre:
  `2026-11-01T22:55:58.848938Z`.
- Tiempo de pared de la sesión: **718,484360 s**. El journal de systemd
  informó **11 min 54,832 s de CPU** y un pico de memoria redondeado a
  **1 GiB**; `Result=success`, `ExecMainStatus=0`.

La sesión admitió las unidades `wf-2021/1` a `wf-2021/10`, sin repetir Q0.
Así quedó completo el primer corte: Q0 y diez actualizaciones. El ledger
registra 11/22 unidades aceptadas, cero pendientes y próximo trabajo
`wf-2022/Q0`. Los reportes aceptados suman 80 pasos de actor, 160 pasos
de crítico, 9.040 trayectorias y 1.627.200 transiciones de aprendizaje y
auxiliares, además de 640 trayectorias y 115.200 transiciones diagnósticas
D. El tiempo D registrado en las diez unidades fue **47,817987 s**; el de
unidad 1, **4,711580 s**. Es tiempo de fase informado por la instrumentación,
no una medición independiente del proceso. La unidad 1 tuvo 64,847268 s
de pared en ledger. El detalle por unidad, incluidas huellas de reportes y
checkpoints, está en [`audit.json`](../evidence/oos-v1-2-wf-cost-05-session-02-20261101/audit.json).

## Frontera, presupuesto e integridad

El supervisor registró `paused` con motivo `budget` **antes** de
`wf-2022/Q0`, seguido de `supervisor_exit` en estado `ready`. No hubo evento
`resource_guard_failed` ni una unidad parcial. El último checkpoint completo
es `wf-2021/checkpoint-10`, frontera `after_dual_and_D`, con SHA-256 del
estado `80626e96b6294492ca2ce116327f8ae32611f6419bede0219622cdb442f386cf`.
El checkpoint Q0 conserva su huella original. El ledger tiene SHA-256
`218ae4d4efad8f3440bb898a1f30f6ca33a09a26045c2b0bff0fe15c0303c1ba`.
La huella de mapeo de todos los archivos de la raíz es
`0d034efccb2138c4fb975c86e504763ff69ce331f2a5fdbb9919f4e1d06931eb`.
El script de auditoría verifica cadena de ledger, reportes, checkpoints,
fronteras, contadores, bitácora, journal, aprobación y huellas anteriores.

El cargo conservador propio del 01/11 fue **3.484,510403 s**: el ledger
abarca **3.482,644557 s** desde Q0 e incluye el intervalo sin trabajo
entre sesiones; la bitácora añadió **1,865846 s** no solapados. No equivale
a tiempo de entrenamiento: los tiempos de pared medidos de las dos
sesiones suman **749,205481 s**. No hubo cargo externo en la medición.
Quedaron **115,489597 s** del tope propio de 3.600 s, insuficientes para
admitir el tope de **120 s** de la próxima Q0. El saldo global antes de la
reserva de 2.700 s era 4.615,489597 s; la restricción que causó esta
pausa fue el tope propio. Ningún límite se amplió ni se redujo D.

La continuación requiere un día local admisible, otro preflight y las
guardas del protocolo; el 01/11 ya cuenta como un día activo del máximo
de dos. Este informe **no** inicia una tercera sesión. Un
ledger `failed` no sería reanudable. Estos tiempos miden costo del estudio
de entrenamiento en dos cortes de desarrollo; no son resultados de
rentabilidad, superioridad, generalización ni cumplimiento CVaR. No se
abrieron validación 2023 ni prueba final.

## Evidencia y reproducción

Ver [`COMMANDS.md`](../evidence/oos-v1-2-wf-cost-05-session-02-20261101/COMMANDS.md)
para comandos realmente ejecutados y
[`audit.py`](../evidence/oos-v1-2-wf-cost-05-session-02-20261101/audit.py)
para la auditoría de solo lectura. La instantánea
[`audit.json`](../evidence/oos-v1-2-wf-cost-05-session-02-20261101/audit.json)
tiene SHA-256
`9b5426f58d065feae02ea8e00c05e77dd3665ff6773ef8d908dfcc5d76b9275a`.
