# Diagnóstico P0 — comandos ejecutados

Base local y origin: e0a2dfca508902c00d94848fa4ebbcb071fb5c25, comprobada tras
`git fetch origin`; rama nueva `codex/p0-diagnosis`. Se conservó la eliminación
previa de .python-version. No se invocó run_pilot ni load_checkpoint ni run/update
del experimento. Solo se cargaron estados existentes tras verificar hashes.

## Reconstrucción congelada

```bash
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check docs/evidence/p0-diagnosis/reconstruct.py --fix
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff format docs/evidence/p0-diagnosis/reconstruct.py
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python docs/evidence/p0-diagnosis/reconstruct.py > docs/evidence/p0-diagnosis/reconstruction.log 2>&1
```

Primer check de estilo mostró 10 E701/E702 por sentencias en una línea; format
los resolvió antes de la ejecución. Check posterior del script: All checks passed.
Reconstrucción: **exit 0**, 18 digests exactos, 162 métricas, hashes de originales
intactos. Adam.step/SGD.step bloqueados; no se construyó optimizador. Autograd
calcula gradientes sin aplicarlos. Los 18 A originales son 1152 trayectorias
reconstruidas (207360 transiciones), no nuevos lotes para aprendizaje. El script
rechaza sobrescribir results.json. Runtime registrado en runtime.log con Python
platform e importlib.metadata, usando el entorno uv --frozen.

## Comprobaciones sin actualizaciones

```bash
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff format docs/evidence/p0-diagnosis/test_diagnostic_math.py
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen pytest tests/test_agent_math.py docs/evidence/p0-diagnosis/test_diagnostic_math.py -q > docs/evidence/p0-diagnosis/pytest.log 2>&1
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff format docs/evidence/p0-diagnosis/check_evidence.py
python3 docs/evidence/p0-diagnosis/check_evidence.py > docs/evidence/p0-diagnosis/checks.log
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check . > docs/evidence/p0-diagnosis/ruff.log
git diff --check
```

16 pruebas pasan en 1.23 s, sin pasos de optimizador; checks de evidencia pasan;
Ruff All checks passed y diff --check exit 0. No se ejecuta la suite completa,
pues contiene actualizaciones de aprendizaje excluidas por esta solicitud.
Los 186 tests de cierre P0 son evidencia histórica, no resultados de este turno.

metrics.csv deriva únicamente de results.json: un registro de targets y ocho
registros critic por corrida/iteración; conserva MSE original y denominadores
reconstruidos. El informe/tabla se generaron de ese mismo JSON. No se reestimó eta
ni se calcularon auditorías nuevas Q/B. No se accedió a validación/final. No hubo
selección de checkpoint: se examinaron todas las 27 fronteras disponibles.

## Límites de reproducibilidad

Pesos/mercado quedan locales, no se publican; sus huellas y las de todos los
archivos originales de campaña están en results.json. Requiere esos artefactos
para reconstruir. La correspondencia exacta no convierte en originales las
predicciones post-A ni gradientes adicionales calculados ahora. No hay pesos
intermedios de minibatch: normas originales disponibles, vectores completos no.
