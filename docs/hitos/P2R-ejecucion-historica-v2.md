# P2R v2 — campaña histórica autorizada, diagnóstico de desarrollo

**Cierre operativo al 07/10/2026:** `completed`, nueve corridas nuevas,
99 unidades íntegras y un día activo. **Interpretación metodológica pendiente
de revisión:** el marcador heredado `market_training_executed` contradice la
ejecución observada y no cumplió la corrección/verificación previa exigida en
P2R v2. El usuario autorizó
las nueve corridas nuevas de P2R v2 solo sobre el derivado H1 de entrenamiento
2018–2022. El permiso quedó fijado en el commit `38fc54b`, separado de la
evidencia de ejecución. P2 conserva su estado `failed` y ninguna unidad o
checkpoint suyos cuenta para P2R. No se usó validación 2023 ni la prueba
final 2024–2025.

La verificación previa repitió la suite completa (289 pruebas), Ruff y el
preflight de solo lectura con vigilancia de aperturas. El derivado contiene
7.048 inicios, conserva normalizador e índices aceptados y no abrió ningún
CSV H1 compartido. Huellas de protocolo, adopción, configuración, manifiestos,
derivado y ledgers P0/P1/P2 coincidieron. CA, batería, memoria, disco, Linger,
gestor de usuario y saldo diario cumplieron en la medición de las 05:34:52 UTC;
los recursos se vuelven a comprobar antes y durante cada unidad.

`p2r-market-v2-session-01.service` inició con
`InvocationID=98473fe6e319417e8fe84abceb1bcd53`. La raíz nueva es
`artifacts/p2r-approved-v2` (fuera de Git). El ledger, journal, requests,
logs y checkpoints quedan allí sin sobrescribir P0/P1/P2 ni las sondas.
La primera Q0 cerró `after_q0`. La primera Q/A/B+D, `run-00-C0/unit=1`,
cerró `after_dual_and_D`, con 66,285994 s de pared y 4,724537 s de D.
El [registro de comandos](../evidence/p2r-market-2026-10-07/COMMANDS.md) y
la [medición de unidad](../evidence/p2r-market-2026-10-07/first-unit.json)
permiten cotejar estos números con el ledger y `unit-1.json` locales.

La medición de D fue diagnóstico de viabilidad y no cambió la admisión,
los umbrales, d ni los hiperparámetros. Las pausas fueron solo en fronteras
completas; no se aceptó ninguna unidad interrumpida.
Este resultado de desarrollo sobre el histórico de entrenamiento no demuestra
generalización temporal, rentabilidad ni cumplimiento poblacional de CVaR.

## Pausa de recursos tras la décima unidad aceptada

La primera sesión aceptó Q0 y k=0…7, hasta `unit=8`. Durante esa unidad el
journal anotó `availability_lost` a las 05:43:51.855808 UTC; el supervisor
aceptó el checkpoint completo y salió en `ready` a las 05:45:00 UTC,
`Result=success`. Un nuevo preflight leyó CA conectada, batería 97 %,
4.570.796.032 B de memoria disponible y 182.038.847.488 B de disco libre;
permitió la segunda sesión
`p2r-market-v2-session-02.service`,
`InvocationID=7887fd6ad3164da08959f337e05bc3c2`. Ésta aceptó
`unit=9` y pausó de igual modo a las 05:48:15 UTC.

El ledger quedó `ready`, cursor 0, 10 unidades aceptadas, `pending=null`;
su débito diario de pared era 791,119772 s y el checkpoint `unit=9` tenía
SHA-256 `aed5b00c68c6741746ccb82ba0c658aaed20c4bf2fb26d6adfddd212dde0d634`.
El aviso de la guarda combina memoria y disco: no registró el valor exacto
en el instante de cruce. El disco midió más de 181 GB después de ambas
pausas, por lo que la presión de memoria es la explicación más probable,
no una medición directa del valor transitorio. No se borró ni repitió unidad.
La [instantánea de pausa](../evidence/p2r-market-2026-10-07/pause-01.json)
conserva huellas del ledger y journal de ese momento. La memoria disponible
subió después a 6.353.022.976 B y un nuevo preflight permitió la tercera
sesión, `p2r-market-v2-session-03.service`,
`InvocationID=24fd4f1c433e4c27adb2a47de154b789`. Completó `unit=10`
de `run-00-C0` y las ocho corridas restantes sin nueva pausa.

## Cierre y presupuesto medido

La sesión 03 cerró a las **07:29:57.107013 UTC**. El ledger terminó
`completed`, cursor 9, 99 unidades aceptadas, `pending=null`. `systemd --user`
registró `Result=success` en las tres sesiones; las dos primeras terminaron
`ready` en frontera completa y la tercera `completed`. La cadena del ledger
y del journal, los 99 checkpoints y los 5.760 archivos diagnósticos D fueron
releídos y verificados por hash con el
[auditor de cierre](../evidence/p2r-market-2026-10-07/checks.py). El
[resultado íntegro](../evidence/p2r-market-2026-10-07/results.json) y el
[journal systemd](../evidence/p2r-market-2026-10-07/systemd-journal.txt)
están versionados; ledger y artefactos grandes siguen en la raíz local.

| Corrida | Semilla | Condición | Pared de 11 unidades, s | D de 10 iteraciones, s |
|---|---:|---|---:|---:|
| run-00-C0 | 610031 | C0 | 739,329 | 49,976 |
| run-01-C5 | 610031 | C5 | 726,030 | 49,480 |
| run-02-C10 | 610031 | C10 | 731,310 | 49,759 |
| run-03-C5 | 610047 | C5 | 729,074 | 49,397 |
| run-04-C10 | 610047 | C10 | 737,377 | 49,420 |
| run-05-C0 | 610047 | C0 | 732,386 | 49,263 |
| run-06-C10 | 610081 | C10 | 725,302 | 49,451 |
| run-07-C0 | 610081 | C0 | 722,666 | 49,591 |
| run-08-C5 | 610081 | C5 | 732,820 | 49,657 |

El día `2026-10-07` America/La_Paz cargó **6.893,096 s** de los 10.800 s
globales; 6.587,363 s fueron actividad de las sesiones. Quedaron
3.906,904 s sin usar al cierre, no transferibles como permiso de otra
campaña. Las nueve Q0 sumaron 268,193 s de pared; las 90 Q/A/B+D,
6.308,101 s; D sola sumó 445,994 s. El ledger contabilizó **81.360
trayectorias y 14.644.800 transiciones de aprendizaje** por separado de
**5.760 trayectorias y 1.036.800 transiciones D**; 720 actualizaciones del
actor y 1.440 del crítico. No hubo unidades fallidas: dos eventos de
disponibilidad produjeron dos pausas válidas. Los 1.547 intervalos de
heartbeat auditados por sesión/unidad tuvieron máximo 4,228481 s, bajo 5 s.
El pico RSS de worker en los registros fue 669.433.856 B; `systemd` informó
2,5 GB de pico de memoria de la sesión 03, magnitudes con alcances distintos.

## Regla técnica y limitación de trazabilidad

El cálculo numérico **predefinido** de la regla conjunta da `review`: solo
la semilla 610081 cumple todas las puertas y umbrales en C0, C5 y C10
(1/3 por condición, frente a 2/3 exigidos). En 610031 y 610047, la razón
MSE D tardía frente al predictor cero queda por encima de 1 en las tres
condiciones; las demás puertas de escala, mejora, sesgo y brecha pasan.
Hubo 69 advertencias D/post de MSE relativa >1 entre 90 oportunidades.
Las trayectorias D fueron nuevas realizaciones, pero compartieron el mismo
histórico de entrenamiento: 2.823/5.760 inicios coincidieron con algún
inicio de aprendizaje y 1.036.590/1.036.800 ocurrencias de transición
coincidieron. No constituyen generalización temporal.

**No se declara aceptación metodológica formal** del diagnóstico: los 99
informes de unidad dicen `market_training_executed=false` porque el código
heredado de `src/btc_risk_rl/agents/trainer.py` solo marca `true` para P0/P1.
P2R v2 pidió corregir o verificar ese metadato **antes** de congelar el
ejecutor histórico, condición que esta ejecución no satisfizo. Los contadores,
checkpoints, manifiestos del derivado exclusivo de entrenamiento y el
supervisor muestran que sí hubo aprendizaje histórico P2R; no se cambia el
campo a posteriori ni se repite la campaña para ocultar la discrepancia.
Por tanto, `review` es el resultado **numérico condicional**; la decisión
formal debe quedar pendiente de revisión de esta brecha de integridad.

Los checkpoints registran tres hashes de commit (`38fc54b`, `0d20766`,
`b185088`) porque se publicaron documentos durante la ejecución; el auditor
verificó que **todas** las huellas de archivos de código en los 99
checkpoints son idénticas. Las huellas P0/P1/P2 permanecieron iguales. No
hubo acceso a la prueba final según los 99 informes; la ruta de datos fue
el derivado de entrenamiento, con preflight sin aperturas de CSV compartidos.
Esto no convierte la campaña en evaluación confirmatoria ni demuestra
rentabilidad, generalización o cumplimiento poblacional de CVaR.
