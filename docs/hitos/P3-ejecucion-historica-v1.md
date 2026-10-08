# P3 v1.1 — campaña histórica autorizada, en curso

**Estado de este informe:** inicio verificado, **sin resultado de campaña**.
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

La sesión continúa; este informe **no adjudica** las 18 corridas, no
presenta resultados de métricas P3 ni extrapola tiempos. El supervisor
debe pausar antes de una unidad que no quepa con reserva, aceptar solo
`after_q0` o `after_dual_and_D`, y dejar `failed` irreversible ante
interrupción dentro de unidad. No seleccionar checkpoints ni repetir
corridas por resultados. Validación 2023 y prueba final 2024–2025
permanecen protegidas. Cualquier resultado completo seguirá siendo
diagnóstico de desarrollo sobre el histórico de entrenamiento, nunca
evidencia confirmatoria de generalización, rentabilidad o cumplimiento
poblacional de CVaR.
