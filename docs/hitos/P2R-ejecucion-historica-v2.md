# P2R v2 — campaña histórica autorizada, diagnóstico de desarrollo

**Estado provisional al 07/10/2026:** campaña en curso. El usuario autorizó
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

La medición de D es diagnóstico de viabilidad, no cambia la admisión,
los umbrales, d ni los hiperparámetros. La campaña sigue las pausas solo en
frontera completa y fallo irreversible para una unidad interrumpida. Si se
agotan tres días activos sin 99 unidades íntegras, debe quedar `incomplete`.
Este resultado de desarrollo sobre el histórico de entrenamiento no demuestra
generalización temporal, rentabilidad ni cumplimiento poblacional de CVaR.
