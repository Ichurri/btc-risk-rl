# Comandos de la corrección prospectiva WF

Rama: `codex/oos-wf-cost-resume-prospective`. Base local y remota antes de editar:
`7106fef99e776b259e46e9d392270f7621485d97`. Solo había una eliminación
local ajena de `.python-version`, conservada sin incorporar.

```bash
git status --short --branch
git log -5 --oneline
git switch -c codex/oos-wf-cost-resume-prospective
uv run --frozen pytest -q tests/test_oos_wf_cost_executor.py
uv run --frozen ruff check --fix tests/test_oos_wf_cost_executor.py
uv run --frozen ruff check .
uv run --frozen pytest -q
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-reentry/check_frozen_artifacts.py
```

La primera ejecución focal tras añadir las pruebas, antes de corregir el
constructor, reprodujo `Campaign identity mismatch` al reingresar. Luego
pasaron las 23 pruebas focales; véase [`pytest-focused.txt`](pytest-focused.txt).
Ruff detectó primero el orden de importación de la prueba nueva, corregido
por el comando `--fix`; el resultado final está en [`ruff.txt`](ruff.txt).
La suite completa queda en [`pytest-full.txt`](pytest-full.txt).

La auditoría [`frozen-artifacts.json`](frozen-artifacts.json) se obtuvo con
el verificador de solo lectura [`check_frozen_artifacts.py`](check_frozen_artifacts.py).
Sus SHA-256 corresponden al ledger, Q0, reporte, journal y aprobación
histórica. Ninguno de estos comandos inició el trabajador de mercado ni
modificó la raíz histórica.

El tiempo de la sesión histórica que falló antes de abrir el ledger se
revisó mediante el informe parcial, el flujo del supervisor y los registros
existentes. No se recalculó como cargo del ledger ni se cambió el presupuesto.
