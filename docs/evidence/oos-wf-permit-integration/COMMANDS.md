# Comandos realmente ejecutados

Directorio de trabajo: `/home/ichurri/Desktop/personal_projects/btc-risk-rl`. No se ejecutó ninguna unidad `systemd --user` ni entrenamiento histórico.

```bash
git status --short --branch
git log -5 --oneline
git switch -c codex/oos-wf-permit-integration
grep -RInE 'type\(permit\)|WFCostPermit|Diagnostic\.bind|def bind\(' src/btc_risk_rl/pilots tests
uv run --frozen pytest -q tests/test_wf_permit_integration.py -x
uv run --frozen pytest -q tests/test_wf_permit_integration.py tests/test_oos_wf_cost_03_profile.py tests/test_oos_wf_cost_replacement_executor.py tests/test_oos_wf_cost_executor.py
uv run --frozen ruff check .
uv run --frozen pytest
git diff --check
```

El primer `pytest -x` del fixture falló por un parche en el módulo equivocado. Corregido ese error de prueba, `pytest -x` reprodujo exactamente el rechazo `WF cost market unit requires registered lease` en `p2_runner.py:79`, antes de aplicar la corrección. El primer Ruff señaló cuatro importaciones desordenadas; `ruff check --fix` sobre los dos archivos nuevos las ordenó y el siguiente Ruff pasó. Resultado final: focal **52 passed**; suite completa **435 passed, 287,40 s**; Ruff **All checks passed!**; `git diff --check` sin salida. Los logs finales están junto a este documento.

La auditoría final se ejecutó con `uv run --frozen python` en modo lectura: comparó mapas SHA-256 de `artifacts/oos-v12-wf-cost-only-01/` y `...02/` contra `docs/evidence/oos-v1-2-wf-first-start-fix/hashes-before.json`, y de `...03/` contra `docs/evidence/oos-v1-2-wf-cost-03-campaign/audit-failure.json`. Comprobó los tres gates y la lista exacta de permisos. Lanzó los tres módulos trabajadores con una solicitud inexistente para comprobar rechazo previo a lectura. Guardó resultados en `verification.json`; su SHA-256 inicial fue `a16514a644eb5be6464f040b444a975b42e27bf020a7a6c7edf4a183cb23ac15`.

La eliminación local previa de `.python-version` no se incorporó. El commit `803abc1` contiene solo código y pruebas; este directorio y las actualizaciones documentales se publican aparte.
