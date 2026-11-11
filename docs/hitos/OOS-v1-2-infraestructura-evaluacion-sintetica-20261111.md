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
| `evaluation.export_reader` | En fixtures inventados de ambas longitudes, exige manifiesto fijado por SHA-256, partición y período exactos, 42 barras de contexto, velas completas, OHLCV válido, hash de CSV y hash de normalizador aportado por el llamador. Rechaza partición ajena antes de abrir el CSV, cambio de bytes, hueco, vela abreviada y enlace simbólico. | El manifiesto y el hash del origen todavía requieren auditoría independiente. No existe exportación real ni permiso histórico; esta función no tiene comando público y no debe llamarse con 2023/final hasta abrir esas puertas. |
| `reporting.oos_progress` | Comprueba la cadena del ledger y cuenta solo unidades/corridas completas; produce SVG local sin red. | Es una instantánea del ledger, no una auditoría de las huellas de todos los checkpoints ni una evaluación financiera. |

## Comandos realmente ejecutados en este worktree

```bash
uv run --frozen pytest -q tests/test_oos_v12_inference.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_progress.py
uv run --frozen ruff check src/btc_risk_rl/evaluation/historical_path.py src/btc_risk_rl/evaluation/inference.py src/btc_risk_rl/reporting/oos_progress.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_inference.py tests/test_oos_v12_progress.py
uv run --frozen pytest -q tests/test_oos_v12_evaluation_features.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_inference.py tests/test_oos_v12_progress.py
uv run --frozen pytest -q tests/test_features.py tests/test_oos_v12_evaluation_features.py
uv run --frozen ruff check src/btc_risk_rl/evaluation src/btc_risk_rl/features/market.py src/btc_risk_rl/reporting/oos_progress.py tests/test_oos_v12_evaluation_features.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_inference.py tests/test_oos_v12_progress.py
uv run --frozen pytest -q tests/test_oos_v12_evaluation_export.py tests/test_oos_v12_evaluation_features.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_inference.py tests/test_oos_v12_progress.py tests/test_features.py
uv run --frozen ruff check src/btc_risk_rl/evaluation src/btc_risk_rl/features/market.py src/btc_risk_rl/reporting/oos_progress.py tests/test_oos_v12_evaluation_export.py tests/test_oos_v12_evaluation_features.py tests/test_oos_v12_historical_path.py tests/test_oos_v12_inference.py tests/test_oos_v12_progress.py tests/test_features.py
```

Resultados: **16 passed**, luego **20 passed**, **10 passed** y finalmente
**31 passed**; Ruff pasó en las invocaciones finales. Una primera ejecución de las pruebas nuevas produjo
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
