# P2R: exportación auditada del derivado H1 exclusivo de entrenamiento

**Alcance:** exportación y auditoría autorizadas el 06/10/2026. **No es
permiso de campaña.** El producto local está en
`data/processed/p2r-training-h1/`; los datos voluminosos quedan fuera de Git.
El código de exportación se fijó en `a7cd7e7`, la evidencia inicial en
`fa70ddd` y el ancla del manifiesto en el commit independiente `cd6b686`.

## Procedimiento y comprobaciones

Se verificó el SHA-256 del manifiesto H1 aceptado
`d7cd59b7cda003a0f69883a83a0bacf06a65c37f3653a2f466c249ddf41a6998`
y de sus doce productos declarados. Esta operación leyó puntualmente los
cinco CSV compartidos, incluidos bytes de 2023, **solo** para comprobar
integridad y comparar el prefijo. La exportación copió las líneas originales
sin redondear ni recalcular precios o características, y releyó fila por fila
para exigir igualdad exacta. Ninguna observación de 2023 se copió al
derivado ni se usó en aprendizaje, diagnóstico o selección. Una falla deja
un directorio `.partial-*` con `failure.json` y sin producto aceptado.

| Archivo | Filas derivadas | Primera fila incluida UTC | Última fila incluida UTC | SHA-256 derivado |
|---|---:|---|---|---|
| bars.csv | 11.086 | 2017-12-01 00:00 | 2022-12-31 20:00 | `c12d098b5d0d5b27a29da1cd8a955c7a26783e6677034a102a9939b4baa8e690` |
| observations.csv | 10.217 | 2017-12-08 00:00 | 2022-12-31 20:00 | `d5014b99cf0367ea77169c933f51761c0d2e7b8874789ec3a4991cb878c1b0a7` |
| features.csv | 10.217 | 2017-12-08 00:00 | 2022-12-31 20:00 | `7ec2c031eb712303cd300fdd74ebe62eba9bb0b8dd6e8936ebbf313874314194` |
| episodes.csv | 7.048 | 2018-03-18 12:00 | 2022-12-31 20:00 | `b57f19452711f0b97882bb21420d22f4c23d3132fc44adf58ee7e71ae991254d` |
| transitions.csv | 10.054 | 2018-01-01 00:00 | 2022-12-31 20:00 | `f7827e0a742e9126f747e340640cb23e570a98c616caa8df330d21a2c4530fb9` |

`scaler.json` y `audit.json` son copias byte a byte de H1: SHA-256
`a598a99c368f1d50bba9f78fca2f803e46d77702d05547ccc12d076771e57479`
y `5a9a1fa5bbff3d52d321ade46877a568fe6f32c69390ddd67941c3e391071af8`.
No hubo reajuste del normalizador (`fit_count=10073`). Se conservó el
calentamiento de 2017. El cotejo independiente del producto ya publicado
repitió los cinco recuentos e igualdad fila por fila.

La auditoría de índices reconstruyó las **7.048 rutas** completas de 180
transiciones; verificó pertenencia a entrenamiento, contigüidad de 4 h,
frontera anterior a 2023 y ausencia de cruces de segmento. H1 contiene
21 segmentos de entrenamiento, 15 utilizables; se conservaron 10.054
transiciones y las exclusiones: 16 ausentes, 20 velas abreviadas, 20 de
reapertura. La huella del manifiesto derivado, fijada en código, es
`62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9`.
El [manifiesto](../evidence/p2r-training-shard-export/manifest.json),
[informe de exportación](../evidence/p2r-training-shard-export/export-audit.json)
y [segunda auditoría](../evidence/p2r-training-shard-export/re-audit.json)
son evidencia pequeña versionada.

El [preflight vigilado](../evidence/p2r-training-shard-export/preflight-opens.json)
abrió el manifiesto H1 y los siete archivos del derivado, **ninguno** de los
cinco CSV H1 compartidos. El gancho de auditoría aborta ante tal apertura.
Devolvió `read_only_ready_campaign_disabled`, 7.048 inicios, cero
trayectorias y cero actualizaciones. Verificó las huellas registradas de
P0/P1/P2; sus ledgers y las sondas previas no se modificaron. El presupuesto
y los recursos registrados son una lectura instantánea, no reserva ni
autorización futura.

## Comandos realmente ejecutados

```bash
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen pytest -q tests/test_p2r_training_shard_export.py tests/test_p2r_training_shard.py
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check src/btc_risk_rl/data/training_shard_export.py scripts/export_p2r_training_shard.py tests/test_p2r_training_shard_export.py
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python scripts/export_p2r_training_shard.py export
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python scripts/export_p2r_training_shard.py audit
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python scripts/audit_p2r_preflight_opens.py
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check .
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen pytest -q
```

La exportación y segunda auditoría pasaron. La suite focalizada inicial
pasó 8/8; la suite completa pasó **287/287** en 209,88 s. Después se añadió
una prueba sintética de intento explícito de apertura compartida: el
gancho la rechazó antes de leer bytes. La suite focalizada final pasó
**9/9** en 22,74 s; Ruff pasó antes y después. Esta prueba de rechazo usa
un H1 fabricado, no abre de nuevo los CSV históricos.

## Límites y siguiente decisión

La comparación prueba identidad exacta respecto del H1 aceptado en este
momento. El preflight posterior confía en el informe versionado y la huella
registrada del derivado: ya no rehace el hash completo de los CSV H1
compartidos porque eso volvería a leer bytes de 2023. El derivado local
ignorado por Git debe mantenerse junto a los commits; si falta o cambia,
el preflight falla cerrado. No se generaron trayectorias históricas ni se
ejecutaron unidades. `MARKET_EXECUTION_ENABLED=False` y
`REGISTRATION_SHA256=None` permanecen. La eventual campaña requiere una
autorización y registro separados, además de repetir el preflight en ese
momento. Validación y prueba final siguen fuera de alcance.
