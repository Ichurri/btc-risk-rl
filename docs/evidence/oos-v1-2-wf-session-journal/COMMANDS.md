# Ejecución y evidencia — bitácora WF

Base comprobada antes de editar: `c59855b34da9ed1e514e26ee14be1867766d4dcd`,
igual a `origin/codex/oos-wf-cost-resume-prospective`. Se creó
`codex/oos-wf-cost-session-journal`; la eliminación local ajena de
`.python-version` permaneció sin incorporar.

```bash
git status --short --branch
git log -4 --oneline
git switch -c codex/oos-wf-cost-session-journal
uv run --frozen pytest -q tests/test_oos_wf_session_journal.py
uv run --frozen pytest -q tests/test_oos_wf_session_journal.py tests/test_oos_wf_cost_executor.py
uv run --frozen ruff check --fix src/btc_risk_rl/pilots/wf_cost_units.py tests/test_oos_wf_session_journal.py
uv run --frozen ruff check .
uv run --frozen pytest -q
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-reentry/check_frozen_artifacts.py
git diff --check
```

Las pruebas rojas iniciales observaron sucesivamente la ausencia del módulo
de sesiones, la falta de cargo compartido para un fallo sin ledger, la
admisión incorrecta de un tercer día y la falta de registro antes de cargar
la fuente. La prueba del esquema alterado también pasó de fallo a rechazo.
Esas salidas de desarrollo no son resultados de campañas. Las ejecuciones
finales están en [`pytest-focused.txt`](pytest-focused.txt),
[`pytest-full.txt`](pytest-full.txt) y [`ruff.txt`](ruff.txt).

La primera suite completa se lanzó mientras aún se editaban archivos de
código y terminó con 395 aprobadas y 1 fallo de huella de procedencia en
`test_signal_inside_unit_fails_permanently[1]`:
[`pytest-full-during-edit.txt.gz`](pytest-full-during-edit.txt.gz),
comprimido sin alterar su salida (`gzip -cd` para leerlo). La prueba
aislada se repitió y pasó (`1 passed in 2.91s`). Tras dejar estable el
código, una suite completa pasó con 400 pruebas; su registro previo al
último caso límite se conserva en
[`pytest-full-pre-edge-fix.txt`](pytest-full-pre-edge-fix.txt). La
verificación final pasó con **41 pruebas focales en 5,57 s**, **401 pruebas
completas en 255,29 s** y Ruff sin errores. No se editaron fuentes durante
esa última suite.

[`frozen-artifacts.json`](frozen-artifacts.json) contiene la auditoría
read-only de las cinco huellas históricas y del gate. Ningún comando llamó
al trabajador de mercado ni creó o reanudó una unidad histórica. Las
raíces usadas por las pruebas nuevas pertenecen a `tmp_path` de pytest.
