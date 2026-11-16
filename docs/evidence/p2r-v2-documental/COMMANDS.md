# P2R v2 — comprobaciones documentales ejecutadas

Base: `af14af2`, rama `codex/p2r-protocol-v2`, 05/10/2026. Este hito leyó
documentos, configuración y huellas pequeñas; **no** lanzó unidades,
workers, reanudaciones, entrenamiento ni lecturas de datos de mercado.

```bash
git status --short --branch
git log -5 --oneline
sha256sum docs/proposals/P2R-protocolo-v1.md docs/proposals/P2R-infraestructura-addendum-v1.md docs/protocols/P2-infrastructure-v1.json docs/decisions/ADR-002-risk-horizon.md
.venv/bin/python docs/evidence/p2r-v2-documental/checks.py > docs/evidence/p2r-v2-documental/results.json
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen ruff check .
git diff --check
```

El [comprobador de solo lectura](checks.py) dio los
[resultados versionados](results.json): 9 corridas, 81360 trayectorias de
aprendizaje/14644800 transiciones, 5760 D/1036800 transiciones,
720 pasos actor y 1440 crítico; revisó 10 huellas de fuentes, P2 y sonda
01, más 32 archivos de sonda 02, 18 de 03 y 28 de 04/05; comprobó ocho
enlaces locales de los nuevos documentos. La primera versión del comprobador
falló por exigir el rótulo «PROPUESTA PARA REVISIÓN» también en el archivo de
diferencias; se limitó correctamente esa aserción a la propuesta y el
resumen. La ejecución final pasó.

Ruff respondió `All checks passed!`; `git diff --check` no produjo salida y
devolvió cero. No se ejecutó `pytest`: no se modificaron algoritmos ni
pruebas del producto. Los resultados de sondas y pruebas de hitos anteriores
se **citan** desde sus informes; no se atribuyen a este hito. La eliminación
local previa de `.python-version` quedó fuera del commit.
