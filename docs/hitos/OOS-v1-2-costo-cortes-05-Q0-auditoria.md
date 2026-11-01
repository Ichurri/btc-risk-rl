# WF `...05`: autorización y primera Q0 histórica

**Estado al 01/11/2026 `America/La_Paz`: pausa válida para auditoría.**
Santiago autorizó exclusivamente la raíz nueva
`artifacts/oos-v12-wf-cost-only-05/` conforme al perfil publicado en
`08e7e6a`. El [registro independiente](../protocols/OOS-v1-2-wf-cost-05-approval.json)
y el gate exclusivo `...05` quedaron fijados en `cacf6a9`; su SHA-256 es
`c2b287ec646a6d6a85c849474f1411f5be28fabb1f1c5701b65005e3374a3c59`.
El código fijado tiene SHA-256 agregado
`9a4a9117c51ecf074a40f20d867dc2a0996588f5435d314f781bf6e3883684aa`;
el perfil, protocolo, diseño y manifiesto H1 coinciden con las huellas del
registro. Las raíces `...01`–`...04` no aportaron unidades ni checkpoints.

## Puertas previas y lanzamiento

La suite completa dio **463 passed en 339,63 s** y Ruff
`All checks passed!`. El [preflight vigilado nuevo](../evidence/oos-v1-2-wf-cost-05-q0-20261101/preflight-launch.json)
del **2026-11-01 21:57:35 UTC** (`SHA-256
0c6a88499ad34518708a00498f1d0824f3eff774c4f391eb4cebd949c85a97cf`)
devolvió `ready`, sin bloqueos: CA conectada, batería 100 %, `MemAvailable`
5.361.602.560 B (mínimo 4 GiB), disco libre 134.326.116.352 B (mínimo
20 GiB), `Linger=yes`, gestor `running`, ninguna campaña activa y 8.100 s
antes de la reserva de cierre. Verificó 3.639 y 4.678 inicios en los
cortes 2021/2022, abrió 1.920 rutas vigiladas y **ningún CSV H1 compartido
ni archivo de validación/final**. No generó trayectorias ni pasos de
optimizador. Estos recursos y saldo corresponden al instante del preflight.

Tras comprobar explícitamente `ready`, huellas, raíz ausente y presupuesto,
se lanzó una sola unidad `systemd --user`,
`oos-wf-cost-20261101-05-session-01.service`, con `Restart=no`.
`InvocationID=d69d5d0157544abc96f3235ab9d339c3` coincide entre la
salida de lanzamiento, la bitácora y el journal del supervisor. El
[journal de systemd](../evidence/oos-v1-2-wf-cost-05-q0-20261101/systemd-journal.txt)
registra inicio a las **21:57:52,935 UTC**, cierre del trabajador con
`{"status":"ready","units":1}` a las **21:58:25,065 UTC** y
`Result=success` / código 0; también informa **33,323 s de CPU** y pico
de memoria del servicio **461,5 MiB**. El `systemctl show` posterior ya no
conserva `MemoryPeak`, por lo que ese pico se atribuye al journal, no a
una lectura actual del proceso.

## Cierre verificado

La [auditoría reproducible](../evidence/oos-v1-2-wf-cost-05-q0-20261101/audit.py)
verificó las cadenas SHA-256 del ledger (8 registros), bitácora y journal,
el reporte y el checkpoint, además de la frontera `after_q0`. El ledger
está **`ready`, 1/22 unidades aceptadas, `pending=null`**; no existen
`unit-1.json` ni `checkpoint-1`. El checkpoint Q0 tiene SHA-256
`8310507d87c7ea2020ed872bb74adcfb20615debe4de271a827a4011ba93f185`
y su manifiesto
`e67714f35c63d79ef4f41596934bc7dd6908c3279c33350a3d8ccf957529c279`.
Se cargó con `weights_only=True`: `next_iteration=0`, cero pasos del actor
y crítico. El reporte Q0 señala `market_training_executed=false`, como
exige el contrato; Q0 recolectó **400 trayectorias/72.000 transiciones**
exclusivamente del entrenamiento y no actualizó parámetros. No se
confunde esa recolección con una actualización de aprendizaje.

La unidad aceptada midió **28,650246 s**. La bitácora cerrada va de
**21:57:54,339 a 21:58:25,060 UTC** y mide **30,721120 s** de pared.
El ledger carga **28,855961 s** desde su apertura y el tramo de bitácora
no solapado añade **1,865159 s**: cargo global total **30,721120 s**,
saldo **8.069,278880 s** antes de la reserva de 2.700 s, sin cargo de
otra campaña ese día. La [salida auditada](../evidence/oos-v1-2-wf-cost-05-q0-20261101/audit-q0.json)
(`SHA-256 32ef4b4fc0df6816d8b1cae9b6668b5b8d5324d1d09e1d685ad34214918c785d`)
incluye los hashes y contadores. La comparación archivo por archivo
reprodujo las huellas fijadas de las raíces `...01`–`...04`.

## Alcance y siguiente frontera

Se aceptó **solo Q0**. No se inició la unidad 1 ni otra sesión, no se
usaron validación 2023 o prueba final 2024–2025 y no se activó la
evaluación v1.2. El estado `ready` y el checkpoint completo permiten una
eventual continuación bajo el protocolo, pero este hito **se detiene para
revisión**. Antes de una sesión posterior se deberán volver a comprobar
integridad, recursos, presupuesto compartido y preflight nuevo; la captura
de este día no autoriza un lanzamiento futuro por sí sola.
