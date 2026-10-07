# P3 v1.1 — comprobaciones algebraicas

Ejecutar desde la raíz del repositorio:

```bash
python3 docs/evidence/p3-v1-1-algebra/checks.py
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check docs/evidence/p3-v1-1-algebra/checks.py
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check .
git diff --check
```

El script usa únicamente `decimal` y fixtures sintéticos internos.
No importa el ejecutor ni lee datos de mercado, checkpoints o reportes
P2R. Es una prueba de **álgebra y de la especificación propuesta**, no
una prueba de agente, del simulador ni de preflight histórico. El
resultado queda en [results.json](results.json).

Ejecución local de esta revisión: `python3` → `passed`; Ruff dirigido
y completo → `All checks passed!`; `git diff --check` → sin salida,
código 0.
Antes se intentaron `python` y `uv run` sin `UV_CACHE_DIR`: fallaron
respectivamente porque `python` no existe en `PATH` y por caché uv de
solo lectura. Se repitieron con los comandos anteriores, sin cambiar
dependencias. No se corrió pytest ni se usaron datos históricos.
