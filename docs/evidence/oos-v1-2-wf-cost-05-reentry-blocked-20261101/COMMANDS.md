# Comandos ejecutados — reingreso WF `...05` bloqueado

Directorio: `/home/ichurri/Desktop/personal_projects/btc-risk-rl`.

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/codex/oos-wf05-profile
TZ=America/La_Paz date '+%F %T %Z'
systemctl --user list-units 'oos-wf*' --state=running --no-pager --plain
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-05-q0-20261101/audit.py \
  > /tmp/oos-wf05-q0-before-session-02.json
uv run --frozen pytest -q > /tmp/oos-wf05-20261101-session02-pytest.log 2>&1
uv run --frozen ruff check . > /tmp/oos-wf05-20261101-session02-ruff.log 2>&1
uv run --frozen python -m scripts.audit_oos_wf_cost_05_preflight \
  > /tmp/oos-wf05-20261101-session02-preflight.json
sha256sum /tmp/oos-wf05-20261101-session02-preflight.json
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-05-q0-20261101/audit.py \
  > /tmp/oos-wf05-q0-after-blocked-preflight.json
cmp /tmp/oos-wf05-q0-before-session-02.json \
  /tmp/oos-wf05-q0-after-blocked-preflight.json
systemctl --user list-units 'oos-wf*' --state=running --no-pager --plain
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-05-reentry-blocked-20261101/checks.py \
  > docs/evidence/oos-v1-2-wf-cost-05-reentry-blocked-20261101/results.json
```

Suite completa: **463 passed en 338,85 s**. Ruff:
`All checks passed!`. Preflight: `blocked` por memoria disponible
4.241.289.216 B, mínimo 4.294.967.296 B; las demás puertas pasaron.
El cotejo Q0 `cmp` fue idéntico antes/después y no había unidad activa.
**No se ejecutó `systemd-run` ni ningún trabajador histórico en este hito.**
