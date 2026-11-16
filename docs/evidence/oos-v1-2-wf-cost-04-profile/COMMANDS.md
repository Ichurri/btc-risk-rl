# Comandos y resultados — perfil WF `...04`

Base: `2d3b6a4`. Rama: `codex/oos-wf-cost-only-04-profile`.
Código verificado: `5d232c8`.

| Comando | Resultado observado |
|---|---|
| `uv run --frozen pytest -q tests/test_oos_wf_cost_04_profile.py -x` | 4 passed, 12.00 s, tras implementar fixture entre procesos. Antes, la ejecución roja falló por `ImportError` del módulo `...04` aún ausente. |
| `uv run --frozen pytest -q tests/test_oos_wf_cost_04_profile.py tests/test_wf_permit_integration.py` | 18 passed, 22.60 s; [salida](pytest-focal.log). |
| `uv run --frozen pytest -q` | 446 passed, 318.33 s, repetida sobre el código ya fijado en `5d232c8`; [salida](pytest-full.log). Una ejecución previa también dio 446 passed en 315.16 s. |
| `uv run --frozen ruff check .` | `All checks passed!`; [salida](ruff.log). Una ejecución previa señaló un único orden de imports, corregido antes del commit. |
| `uv run --frozen python -m scripts.audit_oos_wf_cost_04_preflight > /tmp/oos-wf-cost-04-preflight.json` | `blocked` por presupuesto global agotado ese día y permiso ausente; [captura](preflight.json). |
| `sha256sum /tmp/oos-wf-cost-04-preflight.json` | `bf89c4cb7f76c69ff3c74d6a0314d1720958696dc2d786b2e10bd90f04efcd15`. |
| `git diff --cached --check` | Sin errores antes del commit de código. |

La auditoría de raíces se calculó con `uv run --frozen python` leyendo los
archivos de cada raíz `...01`–`...03`, comparando cada SHA-256 con
`docs/evidence/oos-v1-2-wf-first-start-fix/hashes-before.json` para
`...01`/`...02` y con
`docs/evidence/oos-v1-2-wf-cost-03-campaign/audit-failure.json` para
`...03`. El primer intento de la consulta ad hoc usó la clave `roots` que
no existe y devolvió `KeyError`; se corrigió la ruta de la clave y el
resultado verificable está en [frozen-roots-check.json](frozen-roots-check.json).
La captura vigilada enumera todas las rutas abiertas y sus SHA-256, además
de `market_trajectories_generated=0` y `optimizer_steps=0`.

**No ejecutado:** comando `--run`, unidad `systemd` histórica ni
actualizaciones de aprendizaje sobre mercado.
