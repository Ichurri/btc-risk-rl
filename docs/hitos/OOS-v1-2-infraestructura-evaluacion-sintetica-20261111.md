# Evaluación OOS v1.2: infraestructura aislada, 11/11/2026

## Alcance y estado

Esta rama prepara cálculos y comprobaciones **sin abrir validación 2023 ni
prueba final 2024–2025**. El servicio de entrenamiento histórico usa otra
rama y una huella de código fijada; estos cambios no están incorporados allí.
No se ha ejecutado una política sobre datos fuera de muestra ni se ha hecho
inferencia confirmatoria.

El método previo a los datos está fijado en
`docs/protocols/OOS-v1-2-evaluation-method-freeze-20261111.json`:
36 bloques pareados de semillas, checkpoint K=10, acción determinista
`sigmoid(mu)`, una cartera continua, Sortino anualizado, bootstrap unilateral
centrado con 19.999 remuestras comunes y ajuste de Holm. Una observación
indefinida o una terna incompleta impide el contraste primario.

## Componentes verificados con entradas sintéticas

| Componente | Entrada y comprobación | Límite |
| --- | --- | --- |
| `evaluation.inference` | Acepta exactamente 36 ternas C0/C5/C10 completas, calcula diferencias pareadas, intervalo descriptivo, tamaño `d_z`, p unilateral centrada y Holm. Rechaza registros de otro piloto, partición o frontera. | Recibe métricas ya auditadas; aún falta verificar huellas de reportes, trazas y checkpoints en la ruta histórica. |
| `evaluation.historical_path` | Exige 2.190 o 4.386 transiciones continuas, precios y características finitos, fechas completas y una sola cartera. Ejecuta la contabilidad existente y vuelve a auditar precios, costos y retornos. | Solo recibe arrays en memoria inventados por las pruebas; no tiene lector ni permiso de datos protegidos. |
| `evaluation.features` | Reutiliza las fórmulas H1 sobre barras sintéticas con 42 velas de calentamiento y aplica el normalizador congelado, sin reajuste. La ruta pública de desarrollo conserva su bloqueo de fechas finales. | Es una transformación pura de arrays suministrados; no acredita procedencia ni autoriza abrir 2023/final. |
| `evaluation.export_reader` | En fixtures inventados de ambas longitudes, exige manifiesto fijado por SHA-256, partición y período exactos, 42 barras de contexto, velas completas, OHLCV válido, hash de CSV y hash de normalizador aportado por el llamador. Rechaza partición ajena antes de abrir el CSV, cambio de bytes, hueco, vela abreviada y enlace simbólico. Una prueba une exportación inventada de 4.386 pasos con cartera continua, métricas y auditoría. | El manifiesto y el hash del origen todavía requieren auditoría independiente. No existe exportación real ni permiso histórico; esta función no tiene comando público y no debe llamarse con 2023/final hasta abrir esas puertas. |
| `evaluation.checkpoint_read` | En fixtures verifica checkpoint K10, frontera `after_dual_and_D`, condición, semilla, configuración, origen, contadores de actor/crítico y SHA del estado antes de cargar el actor. Una prueba integra actor congelado, `sigmoid(μ)`, exportación inventada de 2.190 pasos y contabilidad continua. La lectura de solo lectura del checkpoint real `wf-2022/run-00-C0-b0` coincidió con el ledger: estado `ce1d9760b42e8b863d7deef83b9557097f724747a9111fffa4e18a3782f84091`, manifiesto `0ea39f1652888e44a47d46b77cad0cc9cec0eb8140d53a32a8052a5b21459be1`, actor `2c6942c49d3bdc3eda7323ac5bbffffe5961f50a6addff6245ab918354e05d58`. | El checkpoint de corte es auxiliar y no produce evaluación 2023/final. El estado del entrenamiento está activo; no se seleccionó por rendimiento. |
| `reporting.oos_progress` | Comprueba la cadena del ledger y cuenta solo unidades/corridas completas; produce SVG local sin red. | Es una instantánea del ledger, no una auditoría de las huellas de todos los checkpoints ni una evaluación financiera. |
| `reporting.oos_tables` y `scripts/render_oos_v12_training_progress.py` | Verifican huella del protocolo, cadena del ledger, roster y hash de **cada** checkpoint aceptado; concilian contadores de recursos por corrida y generan tabla de tiempos, trayectorias, pasos y memoria junto con SVG local. Rechazan unidades parciales como corridas completas. | Son fotografías de entrenamiento, no resultados de rentabilidad ni pruebas fuera de muestra. La salida se guarda fuera de los artefactos originales y cambia de nombre con el hash del ledger. |

## Comandos realmente ejecutados en este worktree

```bash
uv run --frozen pytest -q tests/test_oos_v12_inference.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_progress.py
uv run --frozen ruff check src/btc_risk_rl/evaluation/historical_path.py src/btc_risk_rl/evaluation/inference.py src/btc_risk_rl/reporting/oos_progress.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_inference.py tests/test_oos_v12_progress.py
uv run --frozen pytest -q tests/test_oos_v12_evaluation_features.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_inference.py tests/test_oos_v12_progress.py
uv run --frozen pytest -q tests/test_features.py tests/test_oos_v12_evaluation_features.py
uv run --frozen ruff check src/btc_risk_rl/evaluation src/btc_risk_rl/features/market.py src/btc_risk_rl/reporting/oos_progress.py tests/test_oos_v12_evaluation_features.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_inference.py tests/test_oos_v12_progress.py
uv run --frozen pytest -q tests/test_oos_v12_evaluation_export.py tests/test_oos_v12_evaluation_features.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_inference.py tests/test_oos_v12_progress.py tests/test_features.py
uv run --frozen ruff check src/btc_risk_rl/evaluation src/btc_risk_rl/features/market.py src/btc_risk_rl/reporting/oos_progress.py tests/test_oos_v12_evaluation_export.py tests/test_oos_v12_evaluation_features.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_inference.py tests/test_oos_v12_progress.py tests/test_features.py
uv run --frozen pytest -q tests/test_oos_v12_evaluation_export.py
uv run --frozen pytest -q tests/test_oos_v12_tables.py tests/test_oos_v12_progress.py
uv run --frozen ruff check src/btc_risk_rl/reporting/oos_tables.py src/btc_risk_rl/reporting/oos_progress.py scripts/render_oos_v12_training_progress.py tests/test_oos_v12_tables.py tests/test_oos_v12_progress.py
uv run --frozen pytest -q tests/test_oos_v12_checkpoint_read.py tests/test_oos_v12_evaluation_export.py
uv run --frozen ruff check src/btc_risk_rl/evaluation/checkpoint_read.py tests/test_oos_v12_checkpoint_read.py tests/test_oos_v12_evaluation_export.py
uv run --frozen python scripts/render_oos_v12_training_progress.py --source-root /home/ichurri/Desktop/personal_projects/btc-risk-rl --profile wf-2022
uv run --frozen pytest -q tests/test_oos_v12_checkpoint_read.py tests/test_oos_v12_evaluation_export.py tests/test_oos_v12_evaluation_features.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_inference.py tests/test_oos_v12_progress.py tests/test_oos_v12_tables.py tests/test_features.py
uv run --frozen ruff check src/btc_risk_rl/evaluation src/btc_risk_rl/features/market.py src/btc_risk_rl/reporting/oos_progress.py src/btc_risk_rl/reporting/oos_tables.py scripts/render_oos_v12_training_progress.py tests/test_oos_v12_checkpoint_read.py tests/test_oos_v12_evaluation_export.py tests/test_oos_v12_evaluation_features.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_inference.py tests/test_oos_v12_progress.py tests/test_oos_v12_tables.py tests/test_features.py
```

Resultados: **16 passed**, luego **20 passed**, **10 passed** y finalmente
**31 passed**, **6 passed**, **32 passed**, **9 passed**, **10 passed** y **40 passed** en los grupos indicados; Ruff pasó en las invocaciones finales. El comando de tabla leyó un snapshot real del ledger activo: en la captura SHA-256 `9d1ed1d88ccc05cbeb78ed3d46c66122f035fdb8de8a9fa3a4961ddf6aed10d3` había 5 corridas completas y 57 unidades aceptadas. Es una instantánea, no un cierre. Una primera ejecución de las pruebas nuevas produjo
4 fallos esperados por módulo ausente; la siguiente produjo 1 fallo por una
expectativa textual incorrecta de la prueba. Se corrigió esta expectativa
sin rebajar la guarda de contigüidad. `uv` instaló el entorno
reproducible del worktree antes de las pruebas. No se ejecutó la suite
completa aquí mientras el entrenamiento histórico sigue activo.

## Puertas que faltan

1. Cerrar y auditar las 36 ternas principales y sus checkpoints finales.
   `wf-2021` conserva una desviación de exclusividad del bloqueo original;
   se presenta como diagnóstico descriptivo, no como cumplimiento estricto.
2. Implementar un lector histórico con manifiesto y huellas propios, sin
   relajar la segmentación ni el normalizador. Probarlo con fixtures antes
   de permitir acceso a 2023.
3. Aplicar la comprobación técnica predefinida de 2023 y armonizar las
   secciones de la tesis indicadas en el método. Un fallo detiene el acceso
   al final; 2023 no se usa para elegir hiperparámetros o checkpoints.
4. Registrar permisos separados y la identidad exacta de código, datos,
   reportes y checkpoints antes de la prueba final. Solo un conjunto de
   108 recorridos íntegros habilita el contraste primario.

El archivo SVG local generado durante la sesión activa es una instantánea
transitoria; se debe regenerar tras el cierre y etiquetar con el SHA del
ledger correspondiente antes de incorporarlo a una tabla o figura de tesis.
