# Evidencia local de la propuesta ADR-002

Fecha del registro: 2026-09-22 UTC. Base H2:
`cc913b629694641543e2b54375dbda5d55130544`.
Los comandos se ejecutaron en el repositorio local abierto. Estado inicial:
solo ` D .python-version`, cambio previo conservado fuera de esta entrega.

## Comandos ejecutados

```bash
git status --short
git log -1 --oneline
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python docs/evidence/adr002-proposal/checks.py > docs/evidence/adr002-proposal/results.json
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check . > docs/evidence/adr002-proposal/ruff.log
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen pytest > docs/evidence/adr002-proposal/pytest.log
```

El primer intento de lectura usó `docs/adr/ADR-002*`, ruta inexistente (salida 1);
se localizó y leyó `docs/decisions/ADR-002-risk-horizon.md`. No hubo cambios de
archivos como consecuencia. Las fuentes primarias se consultaron por navegador
web; sus enlaces y secciones están en el documento de propuesta.

`results.json` registra Python, plataforma, fecha UTC, base y HEAD al ejecutar,
seis grupos de cálculos y hashes de todos los archivos versionados bajo src,
configs, tests, scripts, más lock y pyproject. Comprueba igualdad byte a byte
con H2. No lee datos de mercado. La prueba de cortes comprueba la especificación
propuesta, **no un adaptador de entorno ya implementado**. El gradiente se
contrasta mediante enumeración exacta y diferencias finitas, sin optimización.

La suite pytest ejercita el contrato H2 existente con fixtures sintéticos; no
constituye una nueva auditoría de datos reales, ni valida un agente futuro.
Los resultados de mercado de H1/H2 se citan como evidencia histórica separada.
No se ejecutó entrenamiento, instalación ni comando de mercado. No se accedió
al conjunto final. ADR-002 permanece abierto y la propuesta no está adoptada.

## Resultados comprobados

- Cálculos independientes: salida 0, seis grupos aprobados, 15 comparaciones
  de CVaR empírico/variacional y nueve combinaciones de cortes.
- Ruff: salida 0, `All checks passed!`.
- Pytest: salida 0, **100 passed in 22.47s**, ejecución local nueva.
- `git diff --check`: salida 0.

La propuesta y sus verificaciones son documentación adicional. La eliminación
previa de `.python-version` no forma parte del commit documental.
