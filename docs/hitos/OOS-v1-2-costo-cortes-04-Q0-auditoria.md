# WF `...04`: primera Q0 aceptada y pausa para auditoría

**Estado: `ready`, una unidad aceptada, ninguna unidad pendiente.** La
campaña `...04` permanece en frontera `after_q0`; no se inició la unidad 1.
El 30/10/2026 `America/La_Paz` se partió del commit `9a9ce9f`, coincidente
con origin, con la raíz `...04` ausente. La eliminación local previa de
`.python-version` quedó fuera de Git.

## Verificación previa

CA conectada, batería **97 %**, `MemAvailable=5.493.870.592 B` al inicio.
La suite completa dio **447 passed en 311,98 s** y Ruff pasó. El
[preflight vigilado nuevo](../evidence/oos-v1-2-wf-cost-04-q0-20261030/preflight.json),
de **05:48:54 UTC**, dio `ready`: batería 97 %, memoria disponible
**7.902.384.128 B**, disco libre **144.858.316.800 B**, `Linger=yes`,
`systemd --user=running`, presupuesto externo del día 0 s y 8.100 s antes
de reserva, raíz `...04` ausente, entradas y código con huellas aprobadas.
Registró **57 rutas abiertas** y ninguna protegida; cero trayectorias y
pasos de optimizador. SHA-256 de la captura:
`b4af51dda7acb2dcc364623fa0bcb40165afe3542e6817eed7e816e405ebd789`.

## Único lanzamiento y Q0

Se lanzó solo `oos-wf-cost-20261030-04-session-01.service` mediante
`systemd --user`, `Type=exec`, `Restart=no`, `RuntimeMaxSec=3600`.
`InvocationID=9ea19b05c8584dcb8dc8cfccbcc2e032`. El journal sitúa el
inicio del servicio a **05:49:26.605 UTC** y su salida a **05:49:56.758 UTC**;
`Result=success`, código 0, servicio inactivo. El journal informa **31,350 s
de CPU** y **458,4M de memoria pico** del servicio.

La bitácora durable inició a **05:49:27.895 UTC** y cerró `ready` a
**05:49:56.463 UTC**, **28,567081 s** de pared. El ledger aceptó
`wf-2021/Q0` en **27,151188 s**. El supervisor midió **26,965554 s** de
pared del trabajador y un pico RSS de **360.226.816 B**. El reporte de
Q0 registró **24,550751 s** de algoritmo y **0,060615 s** de guardado;
estos relojes tienen alcances distintos y no se suman.

Q0 recolectó **400 trayectorias y 72.000 transiciones** del corte de
entrenamiento 2021. No hubo lote D ni actualizaciones del actor o crítico;
por ello `market_training_executed=false` es coherente para Q0. Esta unidad
no mide todavía el costo de Q/A/B+D.

## Integridad y presupuesto

La [auditoría reproducible](../evidence/oos-v1-2-wf-cost-04-q0-20261030/audit-q0.json)
(SHA-256 `5c9d4c33fa62fe4b40dffcc4d75cb25d507e169f695f4bd24a1e72d92d5fbca7`)
verificó las cadenas del ledger (8 estados), sesiones y supervisor.
El ledger final está `ready`, con **1/22 unidades**, `pending=null` y
cursor en la primera corrida. `checkpoint-0` conserva la frontera
`after_q0`, iteración 0 y cero pasos; SHA-256 de `state.pt`:
`0b37a844f6fef063ab07f792c61fc0a508cb43675f809e9c9ce885c45dcd1d28`.
La misma huella aparece en manifiesto, reporte y ledger. SHA-256 del
ledger: `b91d0febb3f5f713860031251c3ceeab90e3c381fa6661cc1e6052ded1aa2d4c`;
de la bitácora: `5f8e6fc3a33a877a1bedba8afff11e4de2e3c9079ba874b58bd78e10d5d14c84`.
No existen `request-1.json`, `unit-1.json` ni `checkpoint-1`.

El cargo del día se compone de **27,347103 s** del intervalo del ledger y
**1,219978 s** de bitácora fuera de él: **28,567081 s** globales sin doble
conteo. El saldo global antes de reserva tras Q0 es **8.071,433 s**.
`inspect_budget()` informa 0 s porque excluye deliberadamente la propia
campaña al medir consumos externos; la auditoría añade el intervalo propio
y su porción de bitácora exactamente una vez. Este cargo no autoriza
iniciar la unidad 1 antes de revisar esta entrega.

Las raíces anteriores coinciden archivo por archivo: `...01` **15/15**,
`...02` **2/2** y `...03` **10/10**, con los mapas SHA-256 registrados en
la auditoría. Sus artefactos no se modificaron. Los
[comandos y registros pequeños](../evidence/oos-v1-2-wf-cost-04-q0-20261030/COMMANDS.md)
quedaron versionados; el checkpoint voluminoso permanece solo en la raíz
local. No hubo acceso a validación 2023 ni prueba final, ni se activó v1.2.

**Pausa de revisión:** esta Q0 es una medición de costo y una verificación
de infraestructura, no un resultado de rendimiento financiero ni la
campaña de 22 unidades completa. No iniciar unidad 1 hasta compartir y
revisar esta auditoría.
