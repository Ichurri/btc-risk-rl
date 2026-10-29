# Comandos y evidencia: primer arranque WF

Repositorio: `/home/ichurri/Desktop/personal_projects/btc-risk-rl`.
Rama: `codex/oos-wf-cost-first-start-fix`.
Pruebas en `cefa2ab`; código en `2294420`.

```bash
git status --short --branch
git log -5 --oneline --decorate
uv run --frozen pytest -q tests/test_oos_wf_cost_replacement_executor.py -k 'supervisor_first_start or supervisor_rejects_existing_root or supervisor_reentry'
uv run --frozen pytest -q tests/test_oos_wf_cost_replacement_executor.py
uv run --frozen pytest
uv run --frozen ruff check .
git diff --check
sha256sum docs/protocols/OOS-v1-2-wf-cost-replacement-approval.json artifacts/oos-v12-wf-cost-only-01/ledger.jsonl artifacts/oos-v12-wf-cost-only-01/wf-2021/checkpoint-0/state.pt artifacts/oos-v12-wf-cost-only-02/sessions.jsonl
```

La primera prueba con las tres variantes nuevas, **antes de la corrección**, dio
`2 failed, 1 passed`: el primer arranque rechazó la raíz creada por su propia
bitácora y la raíz huérfana recibió archivos nuevos. Tras la corrección, la
prueba focal completa dio `13 passed`; la suite `419 passed` en 283,16 s;
Ruff pasó. [Log focal](pytest-focal.log), [log completo](pytest-full.log) y
[Ruff](ruff.log). No hubo unidad `systemd`, trayectoria ni paso de optimizador.

Las [huellas previas](hashes-before.json) y [posteriores](hashes-after.json)
se calcularon con SHA-256 por archivo regular en cada raíz, ordenando las
rutas relativas y aplicando SHA-256 al JSON del mapa con `sort_keys=True`.
La comparación de los mapas fue exacta. El comando usado fue `uv run --frozen
python -` con ese cálculo y una aserción `files == before[name]['files']`.
Los JSON conservan rutas y hashes para repetir la comparación. No se
modificaron los artefactos originales.
