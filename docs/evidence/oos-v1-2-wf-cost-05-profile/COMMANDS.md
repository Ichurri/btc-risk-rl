# Comandos ejecutados — WF `...05` prospectivo

Desde `/home/ichurri/Desktop/personal_projects/btc-risk-rl`, rama
`codex/oos-wf05-profile`:

```bash
git fetch origin
git switch -c codex/oos-wf05-profile
uv run --frozen pytest -q tests/test_oos_wf_cost_05_profile.py
uv run --frozen pytest -q tests/test_oos_wf_cost_05_profile.py tests/test_wf_permit_integration.py::test_only_named_wf_permit_types_are_listed
uv run --frozen pytest -q tests/test_oos_wf_cost_05_profile.py::test_05_q0_and_unit_one_in_distinct_workers_with_ledger_reentry
uv run --frozen pytest -q tests/test_oos_wf_cost_05_profile.py tests/test_wf_permit_integration.py::test_only_named_wf_permit_types_are_listed
uv run --frozen pytest -q
uv run --frozen ruff check .
git diff --check
git commit -m "Prepare closed WF 05 cost profile"
uv run --frozen python -m scripts.audit_oos_wf_cost_05_preflight > /tmp/oos-wf05-preflight-20261101.json
sha256sum /tmp/oos-wf05-preflight-20261101.json
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-05-profile/checks.py /tmp/oos-wf05-preflight-20261101.json > docs/evidence/oos-v1-2-wf-cost-05-profile/results.json
```

El primer comando pytest se ejecutó antes de crear el perfil y falló
**4/4** por módulos ausentes. La prueba de reingreso falló por fixture
ausente y pasó tras añadirlo. La prueba focal final dio **10 passed en
14,53 s**. La suite completa dio **463 passed en 386,07 s** y Ruff
`All checks passed!`. `git diff --check` no reportó errores. El
preflight vigilado salió con código 0 y reportó `status=blocked` por
ausencia deliberada de permiso; no lanzó unidades. Las huellas y la lista
de rutas abiertas están en `results.json` y `opened-files.txt`.
