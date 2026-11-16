# H5 — comandos y resultados de esta ejecución

2026-09-23; repositorio local Debian, base H4 19fa2e6, rama
codex/h5-infrastructure. Implementación verificada: 3cbd342.
Python, versiones, hilos, config, SHA de código y productos: provenance en los
JSON adjuntos. CPU-only PyTorch 2.8.0+cpu, sin instalar dependencias nuevas H5.
La eliminación previa de .python-version se conservó sin versionarla.

Todos los comandos uv usaron el prefijo
`UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache` por permisos del entorno. No se usó
ningún comando de descarga, entrenamiento de mercado o evaluación.

## Desarrollo dirigido por pruebas

| Comando `uv run --frozen …` | Log | Resultado de esa etapa |
|---|---|---|
| `pytest tests/test_h5_market.py -q` | market-red.log | 4 fallos, API aún inexistente |
| mismo | market-green.log | 4 aprobadas |
| `pytest tests/test_h5_resume.py -q` | resume-red.log | 6 fallos antes de implementación |
| mismo | resume-green.log | 6 aprobadas |
| mismo, con casos adicionales | resume-extra-red.log | fallo de reset presupuestario reproducido |
| `pytest tests/test_h5_resume.py::test_stale_checkpoint_writer_cannot_roll_back_completed_continuation -q` | stale-red.log | rollback obsoleto reproducido |
| `pytest tests/test_h5_resume.py -q` | resume-final.log | 9 aprobadas tras corrección |
| mismo, ampliado | resume-final-extra.log | 11 aprobadas |
| `pytest` | pytest-first-full.log | 162 aprobadas antes de dos pruebas adicionales |
| `pytest` | pytest-final.log | **164 aprobadas, 54.74 s** |
| `ruff check .` | ruff-final.log | **All checks passed** |

Los fallos RED son antecedentes conservados. No representan el estado final.
Se aplicaron Ruff format/check durante el desarrollo; la comprobación final
pasó. pytest usa fixtures sintéticos, incluido el H1 fabricado de los tests del
adaptador. El código de contabilidad y las suites H2/H3 se mantienen.

## Verificadores separados en commit 3cbd342

```bash
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python scripts/verify_infrastructure.py --profile synthetic --output artifacts/h5-synthetic-20260923
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python scripts/verify_infrastructure.py --profile market-integration --output artifacts/h5-market-20260923
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python scripts/run_pilot.py --protocol docs/proposals/H5-P0-instrumentado.md
```

Primeros dos: exit 0, `synthetic.log` / `market-integration.log`. Resultados
copiados sin cambios desde sus carpetas a synthetic-results.json y
market-results.json. Checkpoint/journal binarios fuera de Git en artifacts;
SHA del checkpoint en resultado. Para repetir, elegir output nuevo.
El tercero: **exit 2 esperado**, `pilot-blocked.log`, sin abrir protocolo ni datos.
Un test verifica también que `authorized=true` no levanta el bloqueo.

Sintético: comparación continua frente a pausada/reanudada, 2 iteraciones C5 por
corrida, 12 trayectorias/2160 transiciones cada una. Igualdad exacta de actor,
crítico, optimizadores, estado de riesgo, eventos, auditorías y muestras siguientes.
Mercado: semilla 20260923, 3 episodios prefijados, 540 transiciones, cero pasos
Adam. Solo entrenamiento; política inicial congelada ancho 8 es configuración
de prueba. Todos los productos H1 conservan su hash. No se seleccionó por retorno.

Se lanzaron pytest y ambos verificadores como procesos independientes en
paralelo. Sus tiempos son mediciones reales de estas comprobaciones, **no
benchmarks aislados ni estimaciones de una iteración de entrenamiento de mercado**.
El consumo de cada corrida es independiente; JSON sintético contiene referencias
continua/reanudada, no sumar su historia común como si ambas fueran una corrida.
No atribuir al equipo resultados remotos/históricos: estas evidencias son nuevas.

Revisión independiente y defecto corregido: REVIEW.md. Historial H4 conservado.
