# Comandos realmente ejecutados — WF `...05` Q0

Directorio: `/home/ichurri/Desktop/personal_projects/btc-risk-rl`.
Eliminación local previa ` D .python-version` excluida de Git.

```bash
git fetch origin
git status --short --branch
systemctl --user list-units 'oos-wf*' --state=running --no-pager --plain
uv run --frozen pytest -q tests/test_oos_wf_cost_05_profile.py tests/test_wf_permit_integration.py::test_only_named_wf_permit_types_are_listed
uv run --frozen ruff check .
git commit -m "Authorize exclusive WF 05 cost campaign"
uv run --frozen pytest -q > /tmp/oos-wf05-20261101-pytest.log 2>&1
uv run --frozen ruff check . > /tmp/oos-wf05-20261101-ruff.log 2>&1
uv run --frozen python -m scripts.audit_oos_wf_cost_05_preflight > /tmp/oos-wf05-20261101-launch-preflight.json
sha256sum /tmp/oos-wf05-20261101-launch-preflight.json
git push origin codex/oos-wf05-profile
```

Pruebas focales: 10 passed; suite completa: 463 passed en 339,63 s; Ruff:
`All checks passed!`. Una aserción de solo lectura exigió el preflight
`ready`, cero archivos protegidos, identidad y huellas aprobadas, raíz
ausente, recursos y saldo antes del lanzamiento; imprimió
`WF05_LAUNCH_GATES_READY`. No se usó el preflight antiguo de preparación.

```bash
systemd-run --user --unit=oos-wf-cost-20261101-05-session-01 \
  --property=Type=exec --property=Restart=no \
  --property=WorkingDirectory=/home/ichurri/Desktop/personal_projects/btc-risk-rl \
  --property=RuntimeMaxSec=3600 \
  /home/ichurri/.local/bin/uv run --frozen python scripts/run_oos_wf_cost_05.py --run
systemctl --user show oos-wf-cost-20261101-05-session-01.service \
  -p Result -p ExecMainPID -p ExecMainStatus -p MemoryPeak \
  -p CPUUsageNSec -p ActiveState -p SubState -p InvocationID
journalctl --user -u oos-wf-cost-20261101-05-session-01.service \
  --no-pager -o short-iso-precise
uv run --frozen python docs/evidence/oos-v1-2-wf-cost-05-q0-20261101/audit.py \
  > docs/evidence/oos-v1-2-wf-cost-05-q0-20261101/audit-q0.json
sha256sum docs/evidence/oos-v1-2-wf-cost-05-q0-20261101/audit-q0.json
```

`systemd-run` devolvió
`InvocationID=d69d5d0157544abc96f3235ab9d339c3`. La sesión terminó
`Result=success`, con ledger `ready` y una sola Q0 aceptada. La auditoría
fue de solo lectura sobre la raíz histórica; escribió únicamente el
resumen en `docs/evidence/`. No se inició unidad 1.
