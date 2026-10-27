# Comandos de preparación WF de reemplazo

Base verificada: `a5b692986d8f31bd036bb1385d5b777f73a70cb4`, igual a
`origin/codex/oos-wf-cost-session-journal`. La rama de esta propuesta es
`codex/oos-wf-cost-replacement-proposal`. La eliminación local previa de
`.python-version` sigue fuera del índice.

```bash
git status --short --branch
git log -4 --oneline
git switch -c codex/oos-wf-cost-replacement-proposal
uv run --frozen pytest -q tests/test_oos_wf_cost_replacement_proposal.py
uv run --frozen ruff check --fix tests/test_oos_wf_cost_replacement_proposal.py
uv run --frozen ruff check .
uv run --frozen pytest -q
uv run --frozen python -c 'import json; from btc_risk_rl.pilots.wf_cost_replacement import inspect_candidate; print(json.dumps(inspect_candidate(), indent=2, sort_keys=True))'
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-reentry/check_frozen_artifacts.py
sha256sum docs/proposals/OOS-v1-2-costo-entrenamiento-cortes-v1.md docs/protocols/OOS-v1-2-wf-cost-executor-v1.json docs/protocols/OOS-v1-2-wf-cost-replacement-proposal-v1.json
git diff --check
```

Las pruebas nuevas usan `tmp_path` y procesos Python separados. No invocan
`run_historical_units`, no construyen cortes de mercado ni crean la raíz
real `...02`. El preflight es de solo lectura y terminó `blocked` por falta
de autorización y de perfil ejecutor de reemplazo. Los archivos que abrió
y las huellas están en [`preflight.json`](preflight.json). Las huellas de la
campaña parcial constan además en
[`frozen-artifacts.json`](frozen-artifacts.json); las de los documentos de
diseño, en [`sha256.txt`](sha256.txt).

La primera ejecución roja falló al importar el validador inexistente; otra
prueba roja detectó que aún no se auditaban las huellas históricas en el
preflight. Ambas pasaron tras implementar esas funciones. Ruff encontró un
orden de importación en la prueba nueva, corregido con `--fix`.

Resultados finales: **5 pruebas focales aprobadas en 6,16 s**
([`pytest-focused.txt`](pytest-focused.txt)), **406 pruebas completas
aprobadas en 258,33 s** ([`pytest-full.txt`](pytest-full.txt)) y Ruff
sin errores ([`ruff.txt`](ruff.txt)). Se repitieron tras la suite el
preflight y la comprobación de huellas; ambos archivos coincidieron byte
por byte con las capturas versionadas. La raíz `...02` y el registro de
aprobación nuevo seguían ausentes.
