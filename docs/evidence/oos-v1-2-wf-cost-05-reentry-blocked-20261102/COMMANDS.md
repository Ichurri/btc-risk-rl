# Comandos reales: intento WF05 del 02/11/2026

Ejecutados desde la raíz del repositorio. Ninguno inició una unidad.

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse origin/codex/oos-wf05-profile
date '+%Y-%m-%dT%H:%M:%S%:z %Z'
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-05-session-02-20261101/audit.py > /tmp/oos-wf05-20261102-before-audit.json
cmp /tmp/oos-wf05-20261102-before-audit.json docs/evidence/oos-v1-2-wf-cost-05-session-02-20261101/audit.json
uv run --frozen python -c 'import json; from btc_risk_rl.pilots.wf_cost_replacement_05_exec import inspect_budget,inspect_host; from btc_risk_rl.pilots.protocol import ROOT; s=json.loads((ROOT/"artifacts/oos-v12-wf-cost-only-05/ledger.jsonl").read_text().splitlines()[-1]); print(json.dumps({"status":s["status"],"units":len(s["units"]),"pending":s["pending"],"days":s["days"],"budget":inspect_budget(),"host":inspect_host()},default=str))' > /tmp/oos-wf05-20261102-before-budget.json
systemctl --user list-units 'oos-wf-cost*' --all --no-pager --no-legend
uv run --frozen pytest -q > /tmp/oos-wf05-20261102-pytest.log 2>&1
uv run --frozen ruff check . > /tmp/oos-wf05-20261102-ruff.log 2>&1
uv run --frozen python -m scripts.audit_oos_wf_cost_05_preflight > /tmp/oos-wf05-20261102-preflight.json
sha256sum /tmp/oos-wf05-20261102-preflight.json
sha256sum artifacts/oos-v12-wf-cost-only-05/ledger.jsonl artifacts/oos-v12-wf-cost-only-05/wf-2021/checkpoint-10/state.pt
systemctl --user list-units 'oos-wf-cost*' --all --no-legend --no-pager
```

Resultados: auditoría anterior idéntica; 463 pruebas correctas en
390,45 s; Ruff correcto; preflight `blocked` por memoria. No se ejecutó
`systemd-run` ni `scripts/run_oos_wf_cost_05.py --run`. Las salidas
conservadas son `ledger-before.json`, `budget-before.json`, `pytest.log`,
`ruff.log` y `preflight.json`. SHA-256, respectivamente:

```text
9b5426f58d065feae02ea8e00c05e77dd3665ff6773ef8d908dfcc5d76b9275a
d45e195fc72412a6c1fe93a57cc2b8c8c1f50af9f65cc1b55da5f78f5c244303
c9de2cabcedc8a7f02e34a9fbcaafb40d9b019580bcd9f585a27ae00f6502103
82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18
cd3260e1ba5b76cd2aa959fd79d287dbb481ff75bfde51ade62000b63509ce4f
```
