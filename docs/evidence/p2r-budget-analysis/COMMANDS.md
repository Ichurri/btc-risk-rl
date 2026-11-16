# Comandos de análisis P2R sin entrenamiento — 07/10/2026

Base `4bc3066`, rama `codex/p2r-historical-executor`. Se leyeron exclusivamente `artifacts/p0-approved-v1`, `artifacts/p1-approved-v1` y `artifacts/p2-approved-v1`: ledgers y JSON de unidades aceptadas. El script verifica los SHA-256 anclados de los tres ledgers y rechaza cambios de estado/recuento, unidades no aceptadas o telemetría acumulada incoherente. No lee CSV, checkpoints de pesos ni productos de validación/final.

```bash
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python scripts/analyze_p2r_budget.py > docs/evidence/p2r-budget-analysis/results.json
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check scripts/analyze_p2r_budget.py
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check .
git diff --check
```

Resultado del cálculo: exit 0; P0 `completed` con 27 unidades, P1
`completed` con 54, P2 `failed` con 57 aceptadas. Reconciliación P2:
3.695,943 s de unidades y 248,335 s de fase D, según el cierre previo.
Ruff global: `All checks passed!`; `git diff --check` sin errores. Una
comprobación algebraica auxiliar de 99 unidades, 24.300 s, 51 D y fórmulas
de escenarios pasó al ejecutarse **después** de generar el JSON. Su primer
intento, lanzado simultáneamente con la redirección del archivo, encontró
el JSON temporalmente vacío y devolvió `JSONDecodeError`: fue un error de
orden de comandos, no un fallo de cálculo o de datos. Los escenarios en
`results.json` aplican aritmética a medianas/máximos P2 y a sobrecostos
hipotéticos, marcados como tales. Ningún comando inició unidades, modificó
el algoritmo, registró aprobación o cambió `MARKET_EXECUTION_ENABLED`.
No se repitió la suite de agentes/simulador: este hito añadió un lector de
artefactos y documentación, sin alterar el ejecutor operativo.
