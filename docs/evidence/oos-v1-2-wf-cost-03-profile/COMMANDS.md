# Comandos ejecutados para el perfil WF `...03`

Base `9efe521`; rama `codex/oos-wf-cost-only-03-profile`; código `0446164`.
No se ejecutó `--run`, `systemd-run` ni trabajador histórico.

| Comando | Resultado |
| --- | --- |
| `git status --short --branch`; `git log -4 --oneline` | base sincronizada; solo eliminación local previa de `.python-version` |
| `uv run --frozen pytest -q tests/test_oos_wf_cost_03_profile.py` antes del código | 7 fallos por módulos/rutas inexistentes; prueba roja de alcance |
| `uv run --frozen pytest -q tests/test_oos_wf_cost_03_profile.py -k fold_paths` antes de fijar el wrapper | 1 fallo: helper heredaba raíz `...01` |
| `uv run --frozen pytest -q tests/test_oos_wf_cost_03_profile.py tests/test_oos_wf_cost_replacement_executor.py tests/test_oos_wf_session_journal.py` | [40 passed](pytest-focused.log) |
| `uv run --frozen pytest` | [428 passed, 323,19 s](pytest-full.log) |
| `uv run --frozen ruff check .` | [All checks passed](ruff.log) |
| `uv run --frozen python -m scripts.audit_oos_wf_cost_03_preflight > preflight.json` | [blocked](preflight.json): batería <50 %, aprobación ausente; 43 aperturas pertinentes, ninguna protegida |
| `uv run --frozen python -` con `inspect_budget(now=27/10/2026 23:50 La Paz)` | [10.800 s de `...02` cargados](budget-failed-02-day.json) |
| `uv run --frozen python -` con mapa SHA-256 por archivo de `...01`/`...02` | [15+2 archivos idénticos](frozen-roots-check.json); raíz y aprobación `...03` ausentes |
| `git diff --cached --check` | sin errores |

La primera suite completa se interrumpió deliberadamente a los 98 casos
aprobados para aplicar el orden de imports indicado por Ruff. El log final
corresponde a una ejecución completa posterior, sobre el código definitivo.
La salida de preflight fue generada tras el commit de código, por eso contiene
`git_commit=0446164`. Su SHA-256 es
`630cbf531a224eb1ea90badf2466d2f175baa0054397e1de44596654a4315911`.
El registro `...03` no se creó y su gate permanece apagado.
