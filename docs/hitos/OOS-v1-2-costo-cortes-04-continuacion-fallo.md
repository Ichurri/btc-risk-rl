# WF `...04`: continuación desde Q0 y fallo de recursos en unidad 8

**Estado final: `failed`, 8/22 unidades aceptadas, unidad 8 parcial no aceptada.**
Esta raíz no se reanuda ni se repite. El gate `...04` quedó cerrado
prospectivamente; el registro de aprobación histórico y todos los artefactos
permanecen como evidencia. No se abrió validación 2023 ni prueba final.

## Puertas antes de la segunda sesión

Se partió de `084cb5d` en `codex/oos-wf-cost-only-04-profile`, coincidente
con origin; la eliminación local de `.python-version` quedó fuera del
trabajo. Se cotejaron los **16 archivos** de la raíz con la auditoría Q0
publicada. El ledger tenía 8 estados encadenados, `ready`, 1/22 unidades,
`pending=null`, cursor en la unidad 1 y checkpoint `after_q0` con SHA-256
`0b37a844f6fef063ab07f792c61fc0a508cb43675f809e9c9ce885c45dcd1d28`.
No existían solicitud ni checkpoint de unidad 1.

El 30/10/2026 `America/La_Paz`, CA=1, batería=97 %, `MemAvailable`
superaba 4 GiB, disco superaba 20 GiB, `Linger=yes`, gestor de usuario
`running` y ninguna otra campaña estaba activa. La Q0 cargaba
**28,567081 s propios**, incluidas las porciones de ledger y bitácora sin
doble conteo; el consumo externo era 0 s y el saldo global después de la
reserva de 2700 s era **8071,433 s**. La admisión de la unidad 1 con su
tope de 180 s devolvió `start`.

La suite completa previa dio **447 passed en 302,16 s**; Ruff pasó. El
[preflight vigilado nuevo](../evidence/oos-v1-2-wf-cost-04-session-02-20261030/preflight.json)
de **06:04:36 UTC** dio `ready`, con CA, batería 97 %, memoria disponible
**5.296.250.880 B**, disco libre **144.849.342.464 B**, huella de código
aprobada `e7f86952…`, 57 rutas abiertas, cero aperturas protegidas y cero
trayectorias o pasos. SHA-256 de esa captura:
`c5c2123789fa3f745b8bec0b5c153bfc379cf1bc483486a214c8b5b2f1294402`.
Esta medición fue previa al lanzamiento; no certifica recursos durante toda
la sesión.

## Ejecución y cierre

Se lanzó exactamente una sesión nueva,
`oos-wf-cost-20261030-04-session-02.service`, con `Type=exec`, `Restart=no`
y `RuntimeMaxSec=3600`. `InvocationID=c5b3e44d338d42e1b4081592fe55132c`.
El servicio comenzó a las **06:05:14 UTC** y terminó a las **06:13:15 UTC**
con `Result=exit-code`, `ExecMainStatus=1`, CPU **478,035 s** y memoria pico
del servicio **846.553.088 B**. La bitácora de esta sesión mide
**479,692213 s** de pared y termina `failed`.

El ledger aceptó las unidades 1–7 de `wf-2021`; junto con Q0 quedaron
**8/22**. Cada una terminó en `after_dual_and_D` con reporte y checkpoint
cuyas huellas coinciden con el ledger. La unidad 1, primera Q/A/B+D, midió
**59,357432 s** de pared en el ledger, **56,102108 s** de algoritmo y
**4,304662 s** para D (fase `D`, iteración 0). D registró 64 trayectorias y
11.520 transiciones; la unidad 1 registró 8 pasos de actor y 16 de crítico.
Su checkpoint `after_dual_and_D` tiene SHA-256
`2d1b91c7621259eaf82a0c4dd5b135a4f01a3e7ba8ce894fababae185e75de1e`.
Estos relojes tienen alcances distintos y no se suman.

En el total aceptado: **6448 trayectorias de aprendizaje**, 1.160.640
transiciones, **448 trayectorias D**, 80.640 transiciones D, **56 pasos de
actor** y **112 de crítico**. La unidad 8 estaba activa y dejó una solicitud,
pero **no produjo `unit-8.json` ni `checkpoint-8` aceptados**. Sus cálculos
parciales no se incorporan a los contadores aceptados ni se rescatan.

El [journal](../evidence/oos-v1-2-wf-cost-04-session-02-20261030/systemd-journal.txt)
registra `ValueError: WF cost resources lost during unit` en la sonda de
recursos del supervisor. Esa sonda exige simultáneamente CA, batería ≥50 %,
`MemAvailable ≥4 GiB` y disco ≥20 GiB. **Está demostrado que una guarda
devolvió falso; no quedó registrado cuál valor lo hizo ni por cuánto tiempo.**
La [lectura posterior](../evidence/oos-v1-2-wf-cost-04-session-02-20261030/host-after.json)
de las 06:24:36 UTC (CA=1, batería=97 %, memoria disponible
7.734.751.232 B y disco libre 144.144.793.600 B) no prueba los valores en
el instante del fallo. No hubo aceptación de
la unidad parcial ni proceso WF restante.

El ledger conserva `failed` y `pending.unit=8`; SHA-256 del ledger
`5e61ed0ee1b0503ba289fa8ab54c53f1c5bcc7a351e56c5ca02eed29bbbe8024`,
de la bitácora
`c0265234ae9f5bd6c7cb5371dee0f817ecff52bb29dfda2c9b40bc3617ca8573`
y del supervisor
`dd58be9833affaf6691950c9c234af202a349dcb2ad028e31a43d8deab88bfc7`.
Su cargo acumulado de día es
**1425,975488 s** según el intervalo conservador desde la primera Q0.
La bitácora de la segunda sesión mide 479,692213 s; son relojes y políticas
de cargo diferentes. La [captura de presupuesto](../evidence/oos-v1-2-wf-cost-04-session-02-20261030/budget-close.json)
confirma que la contabilidad compartida trata un ledger fallido con
unidad pendiente como **10.800 s** consumidos para el 30/10, con saldo 0.
Esto es un cargo de seguridad, no 10.800 s de cómputo medido. El fallo es
irreversible en esta raíz aunque queden checkpoints completos anteriores.

## Integridad y alcance

El [script de auditoría de solo lectura](../evidence/oos-v1-2-wf-cost-04-session-02-20261030/audit.py)
verifica las cadenas de ledger, bitácora y supervisor, las ocho unidades
aceptadas y sus manifiestos, reportes y checkpoints. El checkpoint Q0
conserva exactamente su SHA-256 anterior. Los 1860 archivos locales de la
raíz tienen huella de mapa `3c22543a9238b07f84ae790e92fcd8b627d53483898e15204d9a8a5fb6a859da`.
Las raíces `...01`, `...02` y `...03` conservan sus huellas de mapa
`b93caafa…`, `e11a6cfa…` y `34270a3a…`, respectivamente. Los datos
voluminosos siguen fuera de Git; el
[resultado pequeño](../evidence/oos-v1-2-wf-cost-04-session-02-20261030/audit.json)
y los [comandos](../evidence/oos-v1-2-wf-cost-04-session-02-20261030/COMMANDS.md)
quedan versionados.
SHA-256 de `audit.json`:
`db39db891bb86744d01e0b7588bf295629536bb9090a0393c806a82558c06304`.

El cierre prospectivo cambió únicamente el gate de `...04` a `False`.
La aprobación histórica permanece con SHA-256
`f9230d841757a3cf99ce79c81e50ad2c9794bf4615781fae3e0a4f2c1c74275d`;
su huella de código corresponde a la ejecución anterior, no al gate cerrado.
El comando público y el trabajador reales devolvieron código 1 y
`NOT AUTHORIZED` sin añadir archivos a la raíz. La prueba focal dio
**5 passed en 14,27 s**; la suite completa tras el cierre dio **447 passed
en 307,06 s** y Ruff pasó. Los logs están en la carpeta de evidencia.

Este estudio mide costos en cortes de **entrenamiento**. Su interrupción no
produce una comparación completa de cortes, no valida rentabilidad ni
habilita evaluación fuera de muestra. Una nueva campaña, si se propusiera,
requeriría raíz, autorización y revisión metodológica propias; no debe
rescatar ni reetiquetar estas ocho unidades.
