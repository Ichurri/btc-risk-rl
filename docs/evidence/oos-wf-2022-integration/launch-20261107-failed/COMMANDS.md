# Comandos del intento WF 2022-01 y diagnóstico

El comando `systemd-run` completo está en
[`docs/hitos/OOS-v1-2-costo-2022-primer-intento-fallido.md`](../../../hitos/OOS-v1-2-costo-2022-primer-intento-fallido.md).
La unidad lanzó, en ese orden, `uv run --frozen python
scripts/run_oos_wf_cost_2022.py --prepare` y, solo si pasaba,
`uv run --frozen python scripts/run_oos_wf_cost_2022.py --run`. El segundo
comando **no se ejecutó**. Dentro de `--prepare` se ejecutó
`python -m pytest -q`; falló antes de invocar Ruff o el preflight formal.

Comprobaciones posteriores, **fuera del intento fallido** y sin unidades:

```bash
systemctl --user show oos-wf-cost-2022-01-session-01.service \
  -p ActiveState -p Result -p ExecMainStatus -p InvocationID -p Restart \
  -p ExecMainStartTimestamp -p ExecMainExitTimestamp
journalctl --user -u oos-wf-cost-2022-01-session-01.service \
  -o short-iso-precise --no-pager
sha256sum artifacts/shared-pilot-budget/wf-2022-only-01-attempts.jsonl \
  artifacts/shared-pilot-budget/wf-2022-only-01-checks.jsonl
/home/ichurri/.local/bin/uv run --frozen python scripts/run_oos_wf_cost_2022.py --run
/home/ichurri/.local/bin/uv run --frozen pytest -q \
  tests/test_p2r_historical_executor.py::test_separate_historical_command_requires_user_service_before_data_access
/home/ichurri/.local/bin/uv run --frozen pytest -q \
  tests/test_oos_wf_2022_executor.py \
  tests/test_p2r_historical_executor.py::test_separate_historical_command_requires_user_service_before_data_access
/home/ichurri/.local/bin/uv run --frozen ruff check .
```

La suite de desarrollo completa posterior a la corrección se ejecutó con
`/home/ichurri/.local/bin/uv run --frozen pytest -q`: **504 passed en
434,88 s**. Se ejecutó de nuevo `ruff check .`: **All checks passed**.
Ambas salidas se conservan en esta carpeta; no son la suite formal de la
unidad. Una ejecución intermedia de desarrollo fue interrumpida con
señales durante una prueba del supervisor y no es evidencia de aceptación.
