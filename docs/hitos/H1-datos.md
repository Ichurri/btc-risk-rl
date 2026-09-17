# H1 técnico: módulo de datos y características

Commit de implementación: f92574e
(feat(data): add causal development pipeline and fail-closed historical audit).

Estado: código implementado y verificado; dataset histórico NO aceptado.
Este hito técnico contribuye al hito académico 2 / OE2. No declara terminado OE2.

## Componentes implementados
- Cliente Binance con límites UTC, paginación, reintentos acotados y páginas originales.
- Manifiesto con consultas, fecha efectiva y SHA-256 por página.
- Calidad OHLCV, rejilla temporal, cierres, duplicados, faltantes e incompletos.
- Diez características causales y normalización ajustada solo en entrenamiento.
- Preparación train/validation con una barra contextual anterior no puntuada.
- CLI de desarrollo, protección del período final y reconsulta de anomalías.
- Configuración estricta, sin flag de desbloqueo o entrenamiento.

## Pruebas realmente ejecutadas
En el entorno remoto de construcción, Python 3.12.14; no en el Debian del usuario:

```
uv run --frozen pytest -q --junitxml=docs/evidence/tests-data.xml
28 passed in 1.23s
uv run --frozen ruff check .
All checks passed!
uv run --frozen ruff format --check .
22 files already formatted
uv run --frozen btc-risk config-check
valid=true; training_enabled=false; final_test_locked=true
```

Las pruebas automatizadas usan datos sintéticos: casos inválidos, independencia
de características respecto al futuro, ajuste exclusivo de normalización,
integridad de hashes, paginación, fronteras y bloqueo de emisión ante huecos.
Las pruebas de preparación de extremo a extremo verifican 10.956 transiciones
train y 2.190 validation sobre una serie sintética continua. Esos números NO
describen una aceptación de los datos reales.

## Evidencia real de mercado
- fetch-development: 14 páginas, 13.316 registros, [2017-12-01, 2024-01-01).
- Esperadas 13.332 barras; faltan 16. Hay 20 cierres abreviados.
- Cero OHLCV/aperturas inválidas en los registros recibidos.
- prepare-development: salida 1 por fallo de calidad; comportamiento esperado.
- recheck-anomalies: 36 consultas exactas; 16 still_missing y 20 unchanged.
- No se rellenaron velas ni se cambiaron las respuestas originales.
- No se descargó, inspeccionó o utilizó el conjunto final 2024–2025.
- No se ejecutó entrenamiento ni se calculó rendimiento de estrategias.

Archivos: docs/evidence/{download-manifest,quality-real,recheck,runtime}.json
y tests-data.xml. Respuestas originales en data/raw/ dentro del paquete,
excluidas de Git. La verificación secundaria sigue pendiente.

## Bloqueo y siguiente tarea
El simulador no se implementó: depende de aceptar los datos/características.
Resolver ADR-003 conservando causabilidad, ventanas contiguas y exclusiones
documentadas. No cambiar fechas ni descartar períodos por desempeño.
ADR-002 mantiene bloqueado el agente hasta resolver horizonte/descuento/riesgo.

## Cambios para coordinar con el chat académico
1. Incorporar recursos y parámetros de trabajo, marcando los que son provisionales.
2. Registrar el diagnóstico de discontinuidades como resultado de ingeniería.
3. Concretar la regla de interrupciones y calentamiento antes de afirmar datos aptos.
4. No afirmar que ya existen simulador, PPO/CVaR-PPO, pilotos ni evaluación final.
5. Mantener la segunda fuente y configuración CPCV pendientes, no omitidas.
