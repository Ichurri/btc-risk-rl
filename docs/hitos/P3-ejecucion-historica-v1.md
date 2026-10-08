# P3 v1.1 — campaña histórica autorizada, pausa válida tras sesión 01

**Estado de este informe:** primera sesión cerrada y verificada; campaña
abierta, **sin resultado de campaña**.
El usuario autorizó el 08/10/2026 una campaña P3 nueva, separada de P2R,
solo para diagnóstico de desarrollo sobre el derivado H1 exclusivo de
entrenamiento 2018–2022. La [aprobación fijada](../protocols/P3-market-approval.json)
quedó en el commit `618a08f`, con raíz local `artifacts/p3-approved-v1`.
No incorpora corridas ni checkpoints P2R. El protocolo P3 v1.1 mantiene
18 corridas ordenadas, semillas 710031/710047/710081, C0/C5/C10,
β=0/1, K10, D64, Q0 y Q/A/B+D y los límites de 3 h globales por día
America/La_Paz y hasta tres días activos.

El preflight posterior al permiso, a las 15:53:36 UTC, verificó
las huellas del protocolo, adopción, diseño, código, configuración,
manifiesto del derivado y ledgers P0/P1/P2/P2R. Confirmó 7.048 inicios,
ninguna trayectoria generada y ninguna actualización de optimizador.
La vigilancia registró los archivos abiertos: productos del derivado
exclusivo de entrenamiento y solo el manifiesto H1 compartido, con cero
aperturas de sus CSV. CA conectada, batería 91 %, memoria disponible
9.192.357.888 B y disco libre 174.248.849.408 B; `Linger=yes`, gestor
`systemd --user` activo y 10.800 s de presupuesto global disponibles
en ese momento. Son mediciones de entrada, no garantía de continuidad.
Ver [preflight](../evidence/p3-market-2026-10-08/preflight.json).

La sesión `p3-market-v1-session-01.service` inició bajo `systemd --user`
con `InvocationID=8b3d6b175bd34b78a655010d46cccf3d`. La primera
corrida es `run-00-C0-b0` (710031, C0, β=0). Q0 cerró a las 15:54:16
UTC en `after_q0`, con 400 trayectorias de aprendizaje y marcador
`market_training_executed=false`. La primera Q/A/B+D cerró a las
15:55:15 UTC en `after_dual_and_D`, con 864 trayectorias de aprendizaje,
64 D, marcador `true` y reportes y checkpoints aceptados por el
supervisor. Su tiempo de pared en ledger fue 59,003 s; el algoritmo
midió 56,016 s, guardado 0,220 s y D 4,420 s. Estos tiempos son solo
diagnóstico de viabilidad de esa unidad. Las huellas están en
[first-units.json](../evidence/p3-market-2026-10-08/first-units.json).
Después, el primer brazo β=0 completó sus once unidades en 702,348 s de
pared; el reporte final suma 45,859 s de D sobre diez registros únicos.
El cursor pasó al segundo brazo β=1. La comprobación predefinida de
identidad inicial encontró Q0/η, inicios A y actor tras la primera
actualización iguales entre brazos; el crítico difirió, como corresponde
a las dos pérdidas. Las etiquetas de realización son distintas. Ver
[first-pair-identity.json](../evidence/p3-market-2026-10-08/first-pair-identity.json).
La primera pareja C0 terminó después: β=0 registró 702,348 s de pared
y 45,859 s de D; β=1 registró 732,087 s y 48,020 s. Cada brazo aceptó
once unidades, 9.040 trayectorias de aprendizaje, 640 D, 80 pasos de
actor y 160 de crítico. El cursor pasó a C5 sin reutilizar corridas.
La [instantánea de la pareja](../evidence/p3-market-2026-10-08/first-pair-completion.json)
contiene las huellas finales. Estos costos no cambian los parámetros ni
permiten aplicar aún la regla conjunta de P3.

## Cierre verificable de la primera sesión — 08/10/2026

`p3-market-v1-session-01.service` salió normalmente a las 18:07:25 UTC
(14:07:25 America/La_Paz) con `{"status":"ready","units":116}`. El
ledger durable quedó `ready`, `cursor=10`, `pending=null`: diez corridas
K10 completas y `run-10-C0-b1` aceptada hasta la unidad 5, en
`after_dual_and_D`. No hubo fallo, unidad parcial aceptada ni reinicio
selectivo. La cadena de 351 registros del ledger y la de 2.171 eventos
del journal pasaron verificación de hash; se cotejaron los hashes de
los 116 reportes y checkpoints y sus marcadores (`false` en Q0, `true`
tras cada actualización). Ver [auditoría reproducible](../evidence/p3-market-2026-10-08/session01-audit.py),
[resultado](../evidence/p3-market-2026-10-08/session01-closure.json) y
[journal de systemd](../evidence/p3-market-2026-10-08/systemd-session01.txt).
Los archivos voluminosos originales permanecen en `artifacts/p3-approved-v1`.
La línea final de systemd sobre la ruta transitoria ausente se generó
después de la salida de la unidad y es compatible con una consulta a la
unidad ya retirada; el trabajador y el ledger cerraron `ready`.

| Corrida | Unidades | Pared ledger (s) | D acumulada única (s) |
| --- | ---: | ---: | ---: |
| 00 C0 β0 | 11 | 702,348 | 45,859 |
| 01 C0 β1 | 11 | 732,087 | 48,020 |
| 02 C5 β1 | 11 | 763,308 | 50,017 |
| 03 C5 β0 | 11 | 733,365 | 47,797 |
| 04 C10 β0 | 11 | 750,976 | 49,718 |
| 05 C10 β1 | 11 | 769,180 | 50,518 |
| 06 C5 β1 | 11 | 771,081 | 50,214 |
| 07 C5 β0 | 11 | 781,682 | 51,642 |
| 08 C10 β0 | 11 | 783,368 | 51,280 |
| 09 C10 β1 | 11 | 797,456 | 52,228 |
| 10 C0 β1 — parcial válida | 6 | 415,008 | 26,865 |

La suma D de 524,157 s incluye la corrida parcialmente completada; se
tomó **una sola vez** de la telemetría acumulada del último reporte de
cada corrida. El ledger debitó 8.016,088 s globales, incluyendo carga,
supervisión y guardado; la suma de pared de unidades fue 7.999,859 s.
Se aceptaron 95.120 trayectorias de aprendizaje y 6.720 diagnósticas,
840 pasos del actor y 1.680 del crítico. El mayor RSS individual
registrado por el supervisor fue 680.103.936 B; systemd informó un pico
de memoria del cgroup de 2,7 G y 2 h 12 min 33,258 s de CPU para la
sesión. Las listas de advertencias de cada reporte son acumuladas y
quedan preservadas, **no** sumadas entre reportes como eventos nuevos.

La pausa se produjo antes de la unidad 6 de `run-10-C0-b1`: quedaban
83,966 s hasta el límite de trabajo, frente a 117,073 s exigidos por
la admisión conservadora (1,5× el máximo completo observado en C0).
Los 2.783,912 s hasta el límite duro contenían las reservas aprobadas
para preflight y cierre; no se reutilizaron como tiempo de aprendizaje.
Una nueva sesión solo puede considerarse en otro día local, tras un
preflight completo y las mismas guardas. Se mantienen la raíz, el orden,
las semillas y todos los parámetros. El protocolo limita la campaña a
tres días activos y no permite ampliar límites por resultados.

Las huellas SHA-256 **de los prefijos al cierre de esta sesión** son:
ledger `cff406928d2ff5655599c5fb1c99465c3a13bbb8aeb505fa39e1291724c446ce`
(30.414.121 B) y journal
`5b4e2a51bd11ba4d10d7e2a6f39ae1b575177890204d3dedb17d7c5aa611e85b`
(1.698.157 B). Futuras sesiones añadirán registros a esos archivos:
sus hashes completos cambiarán, pero los prefijos fijados aquí deberán
permanecer idénticos. El estado final del ledger tenía hash de cadena
`3dd62d29fe50064b32fdde04f071067ad7c8db6792d136ee8b53e8a6a7cde23a`;
el último evento del journal tenía
`6772d67a19bfed8b83f111502cef48336bed3dc20a3ea79315cac422a4b776c4`.

Este informe **no adjudica** las 18 corridas ni presenta resultados de
las puertas de decisión P3. Los tiempos observados no autorizan cambiar
topes, seleccionar checkpoints o repetir corridas por resultados.
Validación 2023 y prueba final 2024–2025 siguen protegidas. Incluso si
la campaña completa las 18 corridas, sus resultados serán diagnóstico
de desarrollo sobre el histórico de entrenamiento, **no evidencia
confirmatoria** de generalización temporal, rentabilidad ni cumplimiento
poblacional de CVaR.
