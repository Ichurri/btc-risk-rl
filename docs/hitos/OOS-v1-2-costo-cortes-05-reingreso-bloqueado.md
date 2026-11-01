# WF `...05`: reingreso bloqueado antes de la unidad 1

**Dictamen:** no se inició la sesión 02. La campaña conserva el ledger
`ready` y su única Q0 aceptada. El preflight vigilado nuevo del
**01/11/2026 18:13:38 `America/La_Paz`** (22:13:38 UTC) rechazó la
admisión por memoria disponible inferior al mínimo. No se modificó la
decisión de la guarda ni se intentó lanzar el supervisor.

## Comprobaciones previas

Se partió de `bd58774` en `codex/oos-wf05-profile`, coincidente con
`origin`; la única alteración local era la eliminación previa de
`.python-version`, no incorporada a Git. No había unidades WF activas.
La [auditoría Q0 reproducida antes del preflight](../evidence/oos-v1-2-wf-cost-05-reentry-blocked-20261101/q0-audit-before.json)
coincidió exactamente con la publicada: SHA-256
`32ef4b4fc0df6816d8b1cae9b6668b5b8d5324d1d09e1d685ad34214918c785d`.
Verifica cadena del ledger, bitácora, checkpoint y huellas de las cuatro
raíces previas. El checkpoint Q0 conserva SHA-256
`8310507d87c7ea2020ed872bb74adcfb20615debe4de271a827a4011ba93f185`.

La suite completa dio **463 passed en 338,85 s**; Ruff,
`All checks passed!`. Los logs están en
[evidencias](../evidence/oos-v1-2-wf-cost-05-reentry-blocked-20261101/).
Después se ejecutó un preflight vigilado nuevo, sin reutilizar el de la
sesión 01. Su [JSON](../evidence/oos-v1-2-wf-cost-05-reentry-blocked-20261101/preflight.json)
tiene SHA-256
`53b66659d34db0a152b81c430a667d43295fd4342a3ac39204bd958c5f4c9d3d`.
Registró 1.920 rutas abiertas, ninguna protegida; cero trayectorias y
pasos de optimizador.

| Puerta | Medición del preflight | Estado |
| --- | ---: | --- |
| CA y batería | conectada; 100 % | conforme |
| `MemAvailable` | **4.241.289.216 B** | **bloqueada**: faltan 53.678.080 B para 4 GiB |
| Disco libre | 134.296.645.632 B | conforme, mínimo 20 GiB |
| `Linger` / gestor | `yes` / `running` | conforme |
| Código, aprobación, datos y normalizadores | huellas conformes | conforme |
| Presupuesto externo del día | 0 s; sin campaña activa | conforme |
| Raíz `...05` | existente con ledger Q0 válido | conforme |

El preflight informa 8.100 s antes de reserva **excluyendo la propia
campaña**. El cargo Q0 ya auditado es 30,721120 s; al sumarlo una vez,
quedan **8.069,278880 s** antes de la reserva de 2.700 s. La unidad 1
tenía cota de 180 s y cabía en ese saldo. Esto no corrige la puerta de
memoria. Las cifras de recursos corresponden solo al instante medido;
no demuestran cuál será la memoria disponible en otro momento.

## Estado tras el bloqueo

No se invocó `systemd-run`, no se creó sesión 02 y no se abrió la unidad 1.
La [auditoría posterior](../evidence/oos-v1-2-wf-cost-05-reentry-blocked-20261101/q0-audit-after.json)
es idéntica a la anterior y a la Q0 publicada. Ledger `ready`, **1/22
unidades aceptadas**, `pending=null`, sin reporte ni checkpoint de unidad
1. La lista de unidades WF en ejecución quedó vacía. Las raíces
`...01`–`...04` conservaron sus huellas. El [resumen reproducible](../evidence/oos-v1-2-wf-cost-05-reentry-blocked-20261101/results.json)
(`SHA-256 bb87b6de501204f6ca56848580bb54492f7a20e0dd74207e8df8e45cd954d1bf`)
fija estos resultados y la diferencia de memoria.

La campaña sigue en una frontera completa válida, pero **esta captura
`blocked` no autoriza reingreso**. Cualquier nuevo intento exige verificar
el estado de nuevo, ejecutar las comprobaciones de código exigidas y
obtener un preflight vigilado nuevo `ready`. Ante un eventual ledger
`failed`, el protocolo prohíbe reanudar. No se consultó validación 2023,
prueba final 2024–2025 ni se activó la evaluación v1.2.
