# Infraestructura de adquisición y evaluación final OOS v1.2

**15/11/2026, America/La_Paz. Estado: implementada y verificada con datos
sintéticos; fuente y evaluación final aún cerradas en esta entrega.** La
puerta técnica 2023 cerró `passed` con 108 políticas K10 y su SHA-256
`a2e33b16dc8f6e56e25ca0975afc080ca16348b9c2ee9b1dcfef42afdbd3d5e3`.
La tesis de Google Drive fue cotejada en lectura: sus secciones 2.7.2,
2.7.3, tabla 4, 3.8.4 y 3.8.5 ya describen los dos cortes cronológicos,
2023 como puerta técnica sin selección y 2024–2025 como contraste separado.
No se editó la tesis.

`historical_final_supervisor.py` añade un permiso de **fuente** separado del
permiso de **evaluación**. Antes de abrir bytes finales comprueba cierre
técnico, ledger y exportación 2023 por huellas; el origen Spot de Binance
queda fijado en el código y exige 4.429 velas contiguas de cuatro horas,
incluidas 43 de contexto, sin relleno. Las 43 velas de contexto deben ser
idénticas a la exportación aceptada de 2023. La exportación final queda
inmutable en una raíz nueva. La evaluación usa los 108 K10, una cartera por
política, `sigmoid(μ)`, normalizador congelado y cero actualizaciones. El
contraste usa los 36 bloques pareados y el bootstrap/Holm ya fijados; una
métrica primaria indefinida invalida el contraste completo. Un fallo de
fuente o de unidad conserva la raíz y no permite repetición selectiva.

La nueva ruta comparte `global.lock` y la bitácora
`oos-v12-evaluation-sessions.jsonl` con 2023. La prueba sintética detectó y
corrigió antes de acceder al final un nombre de campaña discordante en esa
bitácora. El preflight reserva 900 s completos para la adquisición, y cada
política se admite con el máximo de 900 s, cierre de 2.700 s y las guardas
de CA, batería, 4 GiB de `MemAvailable` y 20 GiB de disco. El presupuesto
prospectivo está en
[`OOS-v1-2-final-evaluation-budget-20261115.json`](../protocols/OOS-v1-2-final-evaluation-budget-20261115.json).

Pruebas del estado final: `uv run --frozen pytest -q` → **694 passed**, dos
`DeprecationWarning` de `fork` sintético, 939,21 s de Pytest y 940,190397 s
de proceso completo. `uv run --frozen ruff check .` → `All checks passed!`.
El log y los tiempos medidos están en
[`docs/evidence/oos-v12-evaluation-20261115/`](../evidence/oos-v12-evaluation-20261115/).
Pruebas focales de permisos, procedencia, raíces nuevas, presupuesto y
reingreso: **14 passed**. La primera ejecución de suite tras añadir el
supervisor, antes de las últimas dos guardas, fue 692 passed; se repitió
para fijar el estado final. Otra ejecución iniciada antes de una corrección
se interrumpió tras 367 passed y no se presenta como suite completa.

La verificación sintética no demuestra acceso a Binance, cobertura real
2024–2025, tiempos finales, ni resultado de hipótesis. La documentación
oficial de [Binance Spot REST](https://developers.binance.com/en/docs/products/spot/rest-api)
indica que `startTime` con `endTime` devuelve velas cronológicas hasta el
límite; el lector local exige además continuidad y huellas exactas.

Comandos realmente ejecutados:

```bash
uv run --frozen pytest -q tests/test_oos_v12_final_supervisor.py tests/test_oos_v12_evaluation_access.py
# 14 passed
uv run --frozen pytest -q
# 694 passed, 2 warnings in 939.21 s
uv run --frozen ruff check .
# All checks passed!
```

Siguiente puerta: permiso de fuente final fijado al código
`b0cfbfcb6cb5c95b8c5455a2221be0c7d736a64b83e6fe1b438c65f043c793b3`,
preflight vigilado y adquisición en servicio único. Solo después de auditar
su manifiesto podrá fijarse el permiso de evaluación final.
