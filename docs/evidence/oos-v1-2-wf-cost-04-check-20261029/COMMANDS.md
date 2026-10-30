# Comprobación WF `...04` del 29/10/2026 local

Estado inicial: rama `codex/oos-wf-cost-only-04-profile`, commit
`b3863348f4905364a8fbda9c3fbb32d49b51f5c9`, igual a origin; única
modificación previa: eliminación local no incorporada de `.python-version`.

| Comando ejecutado | Resultado |
|---|---|
| `TZ=America/La_Paz date '+%Y-%m-%d %H:%M:%S %Z'` | `2026-10-29 20:12:13 -04` al comenzar. |
| `git status --short --branch` y `git rev-parse HEAD` / `git rev-parse origin/codex/oos-wf-cost-only-04-profile` | Rama y origin coincidentes; solo ` D .python-version`. |
| `test ! -e artifacts/oos-v12-wf-cost-only-04` | Raíz ausente. |
| `uv run --frozen pytest -q > /tmp/oos-wf-04-check-20261029-pytest.log 2>&1` | 447 passed en 322,70 s. [Log](pytest.log). |
| `uv run --frozen ruff check .` | `All checks passed!`; se repitió para guardar [log](ruff.log). |
| `uv run --frozen python -m scripts.audit_oos_wf_cost_04_preflight > /tmp/oos-wf-04-check-20261029-preflight.json` | Captura vigilada nueva: `status=blocked`. [JSON íntegro](preflight.json). |
| `sha256sum /tmp/oos-wf-04-check-20261029-preflight.json` | `e55a0c854a7a942a98eff96f4d884f3a1e6e51d5d7667b330c573d673a1fad36`. |

La auditoría de huellas calculó SHA-256 archivo por archivo en las raíces
`...01`–`...03` mediante `uv run --frozen python`; comparó `...01`/`...02`
con `docs/evidence/oos-v1-2-wf-first-start-fix/hashes-before.json` y
`...03` con
`docs/evidence/oos-v1-2-wf-cost-03-campaign/audit-failure.json`.
[Resultado](frozen-roots.json): 15/15, 2/2 y 10/10 coincidencias. No se
escribió en esas raíces.

**No ejecutado:** `scripts/run_oos_wf_cost_04.py --run`, `systemd-run`,
trabajador histórico, Q0 ni unidad 1. No se abrió validación ni prueba final.
