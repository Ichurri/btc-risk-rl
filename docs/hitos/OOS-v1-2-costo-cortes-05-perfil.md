# Perfil WF `...05` para revisión

**Estado: infraestructura verificada sintéticamente; campaña no autorizada.**
La rama `codex/oos-wf05-profile` parte de la entrega de observabilidad
`dda554e`. La raíz histórica `artifacts/oos-v12-wf-cost-only-05/` y el
registro `docs/protocols/OOS-v1-2-wf-cost-05-approval.json` **no existen**.
El gate del comando público y del trabajador permanece cerrado
(`MARKET_EXECUTION_ENABLED=False`, `REGISTRATION_SHA256=None`). No se
crearon trayectorias históricas ni se ejecutaron unidades de entrenamiento.

## Configuración exacta conservada

El [perfil v1](../protocols/OOS-v1-2-wf-cost-05-profile-v1.json) tiene
SHA-256 `7dbec963f27064ac02669091400a19dc031394daffb51afbee95ae614776581a`
y fija por huella el diseño original
`66109d4400e04440c9450d1f1c0c7cc4332b66b9079703e3a1e62596032b5ad0`.
Solo cambian la raíz, el registro independiente, la identificación de la
campaña y la observabilidad prospectiva. No se reutiliza un checkpoint de
`...01`–`...04`.

| Orden | Condición | Semilla | Corte | Unidades |
| --- | --- | ---: | ---: | --- |
| 1 | C10 | 276696733 | 2021 | Q0 + 10 Q/A/B+D |
| 2 | C10 | 498614892 | 2022 | Q0 + 10 Q/A/B+D |

Se mantienen K=10, β=0, cuatro épocas del crítico, D=64, cota común
`d=−ln(0,90)`, Q/A/B, objetivos Monte Carlo, datos exclusivamente del
derivado H1 de entrenamiento y normalizador propio por corte. Las fronteras
admitidas son `after_q0` y `after_dual_and_D`; la primera Q0 exige pausa de
auditoría. Los límites siguen en **dos días activos** `America/La_Paz`,
10.800 s globales/día, 2.700 s de reserva, 3.600 s propios/día,
5.400 s propios acumulados, 120 s por Q0 y 180 s por Q/A/B+D. La suma
de cotas de unidad es 3.840 s. La bitácora de sesiones cobra los tramos
previos al ledger sin duplicar intervalos; los fallos previos y las sesiones
sin cierre conservan su tratamiento conservador. El presupuesto global
incluye sesiones fallidas anteriores en el día que les corresponde.

## Integridad y comprobación sintética

El [auditor de procedencia](../evidence/oos-v1-2-wf-cost-05-profile/checks.py)
recalcula los mapas SHA-256 de **cada archivo** de las cuatro raíces
previas. Coincidieron 15/15 (`...01`), 2/2 (`...02`), 10/10 (`...03`) y
1.860/1.860 (`...04`); las huellas agregadas están en
[results.json](../evidence/oos-v1-2-wf-cost-05-profile/results.json).
`...04` sigue `failed`, con ocho unidades aceptadas y la 8 pendiente.
Los gates de `...01`–`...04` están cerrados. El perfil comprueba diseño,
protocolo, manifiesto H1 y aprobaciones previas fijadas, sin utilizar sus
checkpoints o lotes.

Una prueba sintética atravesó el primer arranque del supervisor con raíz
temporal ausente, bitácora, ledger y Q0 fabricada; rechazó una raíz
huérfana antes de crear bitácora. Otra prueba ejecutó el trabajador de Q0
y el de unidad 1 en **procesos distintos**, reabrió el ledger, verificó
ambos checkpoints y la cadena de hashes. Las cuatro condiciones de la
guarda (CA, batería, memoria y disco) registraron su valor exacto en un
journal sintético. El supervisor de reingreso de esa prueba no fue un
servicio `systemd --user`; no mide duración histórica ni valida una
interrupción física. La capacidad de registrar una falla real de recursos
en `...05` queda prospectiva.

## Preflight de solo lectura

El preflight vigilado del **2026-11-01 21:31:18 UTC**,
commit `98954ee`, dio `blocked` **solo por falta de aprobación activa**.
En ese instante había CA, batería 100 %, `MemAvailable` 4.355.284.992 B
(mínimo 4 GiB), disco libre 139.387.125.760 B (mínimo 20 GiB),
`Linger=yes`, gestor `running`, ninguna campaña activa y 8.100 s
globales antes de reserva para iniciar Q0. Son valores del instante, no
disponibilidad futura. Los cortes auditados contienen 3.639 y 4.678
inicios elegibles, con 5.764 y 7.703 filas de ajuste. Se abrieron 1.919
rutas registradas por el vigilante; la [lista](../evidence/oos-v1-2-wf-cost-05-profile/opened-files.txt)
es reproducible. Ninguna apertura correspondió a CSV H1 compartidos con
2023, validación ni prueba final. Cero trayectorias y cero pasos de
optimizador. El JSON completo quedó en
`/tmp/oos-wf05-preflight-20261101.json` con SHA-256
`cee65fea9b0cf0c0df061b6606cf29eab7454d5788e8eac87d7728975cb5fd01`;
el [resumen versionado](../evidence/oos-v1-2-wf-cost-05-profile/results.json)
fija su huella, rutas, recursos y presupuesto.

Pruebas focales: **10 passed**. Suite completa: **463 passed en 386,07 s**.
Ruff: `All checks passed!`. Los comandos realmente ejecutados constan en
[COMMANDS.md](../evidence/oos-v1-2-wf-cost-05-profile/COMMANDS.md).
La eliminación local de `.python-version` quedó fuera de ambos commits.

## Límite de la entrega

Este perfil no autoriza ni programa `...05`. Cualquier campaña futura
necesita autorización específica, registro independiente fijado en un
commit separado, gate activado exclusivamente para esa raíz, suite y Ruff
vigentes, preflight vigilado inmediato `ready`, y admisión por presupuesto
antes de cada unidad. Las raíces fallidas no se reanudan. El estudio de
costos tampoco adopta la evaluación v1.2 ni abre 2023 o 2024–2025.
