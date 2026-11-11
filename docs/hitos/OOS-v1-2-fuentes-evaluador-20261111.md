# Fuentes y evaluador OOS v1.2 — preparación aislada, 11/11/2026

## Inventario permitido

El [inventario de metadatos](../evidence/oos-v12-evaluation-source-inventory-20261111/metadata.json)
se obtuvo leyendo solo manifiestos JSON y nombres de archivo. No se abrieron
velas de validación ni del conjunto final. El manifiesto de la descarga
original declara Binance spot API, `BTCUSDT`, `4h`, desde 01/12/2017 hasta
01/01/2024 exclusivo; SHA-256
`5608f59ca77d73c2afe564f94a0eddc50d26a477f73b6d3e38a47d930a9fb807`.
H1 aceptó el desarrollo segmentado, cuyo manifiesto SHA-256 es
`d7cd59b7cda003a0f69883a83a0bacf06a65c37f3653a2f466c249ddf41a6998`.
Su metadato de cobertura registra **2.190/2.190 velas de 2023 y cero
exclusiones**; esto no sustituye una auditoría de la exportación 2023.

| Partición | Transiciones exigidas | Velas con 42 de calentamiento y observación inicial | Primera vela requerida UTC | Última vela requerida UTC | Disponibilidad local por metadatos |
| --- | ---: | ---: | --- | --- | --- |
| Comprobación técnica 2023 | 2.190 | 2.233 | 24/12/2022 20:00 | 31/12/2023 20:00 | H1 compartido y descarga de desarrollo; acceso aún cerrado. |
| Prueba final 2024–2025 | 4.386 | 4.429 | 24/12/2023 20:00 | 31/12/2025 20:00 | **No se identificó fuente local final** por nombre ni manifiesto; acceso aún cerrado. |

La forma prevista de obtener el período final, **después de su permiso
separado**, es una descarga inmutable y paginada del mismo mercado Binance
spot `BTCUSDT` a 4 h y UTC para 2024–2025, junto con el prefijo de 43
velas de 2023 auditado contra H1. Deben persistirse solicitudes, respuestas,
huellas y manifiesto nuevo; exigir exactamente la malla temporal, OHLCV
finitos y velas completas, sin interpolar ni seleccionar otras fechas. Una
falta, diferencia de fuente o interrupción impide aceptar la exportación.
El lector interno `source_final` ya verifica un manifiesto y páginas
inmutables, pero **aún falta el descargador autorizado** que crearía esos
archivos y una auditoría independiente de origen. No se descargó ni se abrió
ese período en este hito. Si el origen público
no entrega la cobertura exigida, habrá que documentar el bloqueo y solicitar
una fuente equivalente auditada; no se dará por válida otra automáticamente.

## Integración sintética añadida

### Puertas separadas y continuidad de procedencia

El módulo `evaluation.access` deja **cerradas en código** las puertas
`technical_2023` y `final_2024_2025`. Una aprobación JSON futura debe tener
huella fijada en código, y se comprueban los bytes reales de las congelaciones
metodológica y de entrenamiento antes de abrir entradas protegidas. El lector
de aprobación permite examinar solo el permiso ya fijado; la verificación
completa exige además ledger, exportación, fuente, normalizador y código con
huellas concordantes. La puerta final requiere un cierre técnico 2023
separado, íntegro y de 108 políticas. No hay permiso ni comando histórico
activo en esta entrega.

`evaluation.code_identity` calcula una huella de los archivos Python del
paquete, dependencias/configuración y futuras entradas de evaluación. Solo
normaliza las dos declaraciones de activación y registro del permiso; un
cambio de algoritmo altera la huella. Esta función debe emplearse en el
futuro ejecutor antes de comparar la aprobación. La puerta de acceso ya la
calcula directamente, sin aceptar una cadena de huella suministrada por el
llamador. Habrá que fijar su
valor **tras** integrar el código definitivo. No se interpreta la huella
de una prueba aislada como permiso de acceso.

El lector de páginas finales exige ahora que sus **43 velas de contexto de
2023 coincidan exactamente** en tiempo y OHLCV con el prefijo aceptado de H1
que le entregue el futuro ejecutor autorizado. Rechaza tiempos no enteros
aun cuando la página y el manifiesto se vuelvan a firmar. Los tests
construyeron ambas entradas; no abrieron datos de 2023 ni 2024–2025.
El adaptador H1 comprueba también la huella y los recuentos de
`coverage.json` antes de parsear `bars.csv`: 2.190 velas de validación,
un segmento continuo y cero exclusiones. Una fixture con exclusión falsa
y manifiesto rehuellado fue rechazada antes de abrir el CSV.

En la rama aislada, `evaluation.export_builder` escribe un export nuevo a
partir de velas suministradas por un futuro adaptador autorizado; valida
antes de escribir filas, fechas, OHLCV y huellas declaradas. No carga
particiones por sí mismo. `source_h1` comprueba el manifiesto H1 fijado y
extrae, tras una futura autorización, las 2.233 barras de 2023/contexto;
`source_final` comprueba un manifiesto final y cada página Binance fijada
antes de reconstruir las 4.429 barras requeridas. Ambos se probaron solo
con fuentes inventadas. `evaluation.historical_unit` verifica primero la
identidad del manifiesto de origen, luego checkpoint K10 y export, evalúa una
cartera continua con `sigmoid(μ)`, persiste la traza y vuelve a auditarla;
rechaza una raíz previa. Una segunda lectura recalcula la contabilidad y
rechaza reportes o trazas manipulados. `reporting.oos_contrast` prepara la tabla de 36
bloques y aplica la inferencia pareada congelada solo con 108 reportes
finales completos. Son **componentes internos, sin comando público ni
permiso histórico activo**. La prueba de extremo a extremo utilizó velas y
pesos inventados de ambas longitudes. No constituyen evaluación de políticas
sobre 2023 o 2024–2025.

Falta verificar los adaptadores contra fuentes reales después de sus
permisos, la carga de los 108 checkpoints tras el cierre del roster,
un descargador final, un supervisor por evaluación,
presupuesto/bitácora y permisos
distintos para 2023 y final. Estas puertas deben verificarse antes de abrir
cualquier CSV protegido. La [armonización metodológica de la tesis](../proposals/OOS-v1-2-armonizacion-tesis-20261111.md)
también está preparada como texto propuesto; todavía no está aplicada al
documento académico.

La guarda `evaluation.complete_roster` exige el ledger `completed`, las
**108 corridas y 1.188 unidades**, 36 ternas con semilla pareada, cadena y
huellas de todos los checkpoints, reportes y solicitudes. En la captura
real aún activa devolvió `ValueError: OOS main training is not completed`;
no se abrió ninguna partición de evaluación. Dos pruebas con un ledger
completo inventado ejercitaron aceptación y rechazo por cambio de huella,
estado y protocolo.

## Estimación separada de 108 recorridos

La sonda **sintética** bajo `systemd --user` del 26/10 midió pared externa
de **6,631, 6,833 y 7,916 s** en tres procesos de 2.190 pasos, y
**7,080 s** en un proceso de 4.386 pasos. Estas son [mediciones del proceso
sintético anterior](OOS-v1-2-evaluador-sintetico.md), con hardware/caché de
ese momento; la nueva ruta de exportación y la adquisición histórica no
están incluidas. Multiplicarlas aritméticamente da:

| Partida | Base medida | Extrapolación para 108 políticas | Límite |
| --- | --- | ---: | --- |
| Comprobación técnica 2023 | 2.190 pasos; media 7,1267 s | **769,680 s** (12,83 min); sensibilidad 716,148–854,928 s según el mínimo/máximo observados | No mide exportación real, 108 cargas, auditoría global ni contención de recursos. |
| Evaluación final 2024–2025 | 4.386 pasos; una medición 7,080 s | **764,640 s** (12,74 min) | Un solo proceso no da dispersión ni cota. |

Las asignaciones v1.2 de **10.800 s por partición** siguen siendo topes
propuestos, no tiempos medidos de evaluación histórica. La extrapolación
no reduce topes, reservas ni requisitos de admisión. El coste de descargar,
exportar y auditar la fuente final es desconocido hasta verificarla. No
se usa esta tabla para declarar viable automáticamente la fecha 16/11.

## Comprobaciones realmente ejecutadas

```bash
uv run --frozen python docs/evidence/oos-v12-evaluation-source-inventory-20261111/checks.py
uv run --frozen ruff check docs/evidence/oos-v12-evaluation-source-inventory-20261111/checks.py
uv run --frozen pytest -q tests/test_oos_v12_historical_unit.py
uv run --frozen pytest -q tests/test_oos_v12_complete_roster.py
uv run --frozen pytest -q tests/test_oos_v12_h1_source.py
uv run --frozen pytest -q tests/test_oos_v12_final_source.py
uv run --frozen pytest -q tests/test_oos_v12_export_builder.py
uv run --frozen pytest -q tests/test_oos_v12_contrast_table.py
uv run --frozen pytest -q tests/test_oos_v12_contrast_table.py tests/test_oos_v12_export_builder.py tests/test_oos_v12_historical_unit.py
uv run --frozen ruff check src/btc_risk_rl/evaluation/export_builder.py src/btc_risk_rl/evaluation/historical_unit.py src/btc_risk_rl/reporting/oos_contrast.py tests/test_oos_v12_contrast_table.py tests/test_oos_v12_export_builder.py tests/test_oos_v12_historical_unit.py
uv run --frozen pytest -q tests/test_oos_v12_checkpoint_read.py tests/test_oos_v12_evaluation_export.py tests/test_oos_v12_evaluation_features.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_inference.py tests/test_oos_v12_progress.py tests/test_oos_v12_tables.py tests/test_oos_v12_contrast_table.py tests/test_oos_v12_export_builder.py tests/test_oos_v12_historical_unit.py
uv run --frozen ruff check src/btc_risk_rl/evaluation src/btc_risk_rl/reporting/oos_contrast.py src/btc_risk_rl/reporting/oos_progress.py src/btc_risk_rl/reporting/oos_tables.py scripts/render_oos_v12_training_progress.py tests/test_oos_v12_checkpoint_read.py tests/test_oos_v12_evaluation_export.py tests/test_oos_v12_evaluation_features.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_inference.py tests/test_oos_v12_progress.py tests/test_oos_v12_tables.py tests/test_oos_v12_contrast_table.py tests/test_oos_v12_export_builder.py tests/test_oos_v12_historical_unit.py
uv run --frozen pytest -q tests/test_oos_v12_complete_roster.py tests/test_oos_v12_checkpoint_read.py tests/test_oos_v12_evaluation_export.py tests/test_oos_v12_evaluation_features.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_inference.py tests/test_oos_v12_progress.py tests/test_oos_v12_tables.py tests/test_oos_v12_contrast_table.py tests/test_oos_v12_export_builder.py tests/test_oos_v12_historical_unit.py
```

Las primeras invocaciones de cada prueba fallaron por módulo ausente, según
el ciclo test-first; después pasaron. El grupo conjunto terminó **7 passed**
antes de añadir el segundo período y la lectura auditada; la prueba focal
actualizada terminó **4 passed**. La batería focal de evaluación terminó
**43 passed en 6,98 s** y Ruff pasó. No se ejecutó suite completa
en este worktree mientras el servicio histórico entrenaba en otro árbol.
Después de añadir la guarda de roster, la batería focal quedó en
**45 passed en 7,32 s** y Ruff volvió a pasar. La suite general del
repositorio todavía no se ejecutó en este worktree.
Después de los adaptadores inventados, la batería focal quedó en
**51 passed en 6,80 s** y Ruff pasó. Ninguna prueba abrió 2023 real o
2024–2025 real.
Tras las puertas y el cotejo de contexto, la batería focal quedó en
**58 passed en 6,84 s** y Ruff pasó; es verificación sintética, no
evaluación histórica. Las llamadas focales de las puertas fueron
`uv run --frozen pytest -q tests/test_oos_v12_evaluation_access.py`
(3 passed) y de la fuente final
`uv run --frozen pytest -q tests/test_oos_v12_final_source.py`
(7 passed). El test de contexto falló primero por argumento ausente y
pasó tras exigirlo. La suite completa del repositorio continúa pendiente
en este worktree mientras el servicio de entrenamiento sigue activo.
El test de identidad de código falló inicialmente por módulo ausente;
después terminó `2 passed` y Ruff pasó. Verificó que cambiar un módulo
altera la huella, que las dos declaraciones de permiso se normalizan y
que un archivo ejecutable obligatorio ausente se rechaza.
Tras enlazar ese cálculo con la puerta, la batería focal completa de
evaluación terminó **62 passed en 6,54 s** y Ruff volvió a pasar. El test
nuevo falló primero porque la función exigía una huella aportada por el
llamador y pasó cuando la calculó internamente.

La bitácora interna `evaluation.ledger` añade estados encadenados y
durables por política: `ready → running → ready/completed`, con reingreso
solo tras una unidad aceptada. Un proceso nuevo continuó desde la primera
unidad sintética; una interrupción con unidad pendiente dejó `failed` y
rechazó reintento. Se rechazaron roster, token y cadena alterados. La
bitácora **no ejecuta** una política ni comprueba por sí sola los archivos
de reporte; el futuro supervisor debe verificar esas huellas antes de
`accept`, conservar fallos y aplicar presupuesto. Los tests usaron dos
identidades inventadas y ninguna observación de mercado.
Con esta bitácora, la batería focal terminó **65 passed en 7,84 s** y Ruff
pasó. El primer intento de sus tres pruebas falló por módulo ausente; el
reingreso de la segunda política se repitió luego en un proceso Python
distinto.

El trabajador interno `evaluation.runner` ejecuta una unidad sintética
real con checkpoint K10 y exportación inventados. Antes de aceptar calcula
otra vez la contabilidad desde la traza persistida, compara el reporte y
guarda sus huellas en la bitácora. Revisa los reportes aceptados antes de
continuar. Un checkpoint corrupto dejó `failed` sin aceptación, y una
unidad huérfana se convirtió en fallo irreversible antes de reingresar.
Esta ruta **aún no tiene supervisor histórico, admisión temporal, permisos
activos ni fuente final**; no es una evaluación de las 108 políticas.
La batería focal tras esta integración terminó **69 passed en 8,51 s**;
Ruff pasó. Las cuatro pruebas del trabajador utilizaron únicamente velas,
checkpoint y normalizador inventados. Sus intentos iniciales fallaron por
módulo y función ausentes, y luego pasaron con la ruta implementada.

Se preparó un descargador **interno, aún no habilitado** para la fuente
final: cinco páginas como máximo para 4.429 velas requeridas, consultas
UTC fijadas, archivos nuevos y huellas por página. Una falta temporal
conserva el manifiesto `failed` y las páginas ya recibidas; la raíz no
se reutiliza. Dos pruebas con transporte inventado comprobaron cobertura
exacta y fallo por un hueco. No hubo llamada HTTP ni acceso a 2024–2025.
Su ejecución futura depende de la puerta final separada y del cierre
técnico 2023; la descarga por sí sola no acepta el conjunto final.
La batería focal acumulada quedó en **71 passed en 8,64 s** y Ruff pasó.
El test de páginas falló primero por módulo ausente y luego pasó con el
descargador. La suite completa del repositorio aún no se corre en paralelo
con el entrenamiento activo.
El verificador del inventario devolvió `matched_metadata_only`; el
`metadata.json` capturado tiene SHA-256
`beadbaf093c7e1013ad4876601287456b7d01042628d43111721c60cd9a44895`.
