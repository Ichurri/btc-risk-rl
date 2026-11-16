# Comandos ejecutados — continuación WF `...04`

Directorio: `/home/ichurri/Desktop/personal_projects/btc-risk-rl`.
Antes de lanzar: `084cb5d551c3dbfe45605ab7c7f909d016fea1ab`, igual a
origin; ` D .python-version` era un cambio local ajeno y no se incorporó.

```bash
git status --short --branch
git log -1 --oneline
TZ=America/La_Paz date '+%Y-%m-%d %H:%M:%S %Z'
systemctl --user list-units 'oos-wf*' 'p*-market*' --state=running --no-pager
systemctl --user is-system-running
loginctl show-user "$(whoami)" -p Linger
cat /sys/class/power_supply/ADP1/online
cat /sys/class/power_supply/BAT1/capacity
grep MemAvailable /proc/meminfo
df -B1 --output=avail .
```

Se comparó en Python cada archivo de la raíz con el mapa SHA-256 de
`docs/evidence/oos-v1-2-wf-cost-04-q0-20261030/audit-q0.json`, se validó
la cadena `state_hash`/`previous_hash` del ledger, frontera `ready`,
`pending=null`, la Q0 y el cargo propio de 28,567081 s. La función
`admit(BudgetState(...), day, 1)` devolvió `start` con el cargo propio y el
externo sumados. No se escribió en la raíz.

```bash
uv run --frozen pytest -q > /tmp/oos-wf-04-20261030-reentry-pytest.log 2>&1
uv run --frozen ruff check . > /tmp/oos-wf-04-20261030-reentry-ruff.log 2>&1
uv run --frozen python -m scripts.audit_oos_wf_cost_04_preflight \
  > /tmp/oos-wf-04-20261030-reentry-preflight.json
sha256sum /tmp/oos-wf-04-20261030-reentry-preflight.json
```

Resultado: 447 passed en 302,16 s, Ruff `All checks passed!`, preflight
`ready`; SHA-256 de preflight
`c5c2123789fa3f745b8bec0b5c153bfc379cf1bc483486a214c8b5b2f1294402`.

```bash
systemd-run --user --unit=oos-wf-cost-20261030-04-session-02 \
  --property=Type=exec --property=Restart=no \
  --property=WorkingDirectory=/home/ichurri/Desktop/personal_projects/btc-risk-rl \
  --property=RuntimeMaxSec=3600 \
  /home/ichurri/.local/bin/uv run --frozen python scripts/run_oos_wf_cost_04.py --run
systemctl --user show oos-wf-cost-20261030-04-session-02.service \
  -p Result -p ExecMainPID -p ExecMainStatus -p MemoryPeak -p CPUUsageNSec \
  -p ActiveState -p SubState -p InvocationID \
  -p ExecMainStartTimestamp -p ExecMainExitTimestamp
journalctl --user -u oos-wf-cost-20261030-04-session-02.service \
  --no-pager -o short-iso-precise
```

Se observó el ledger y la unidad cada 30–50 s, sin enviar señales al
supervisor. La sesión terminó por su propia guarda con `Result=exit-code`.
El `InvocationID` fue `c5b3e44d338d42e1b4081592fe55132c`.

Después del fallo se cambió prospectivamente solo
`MARKET_EXECUTION_ENABLED=False` para el perfil `...04`, se conservaron
el JSON de aprobación y los artefactos históricos y se ejecutó:

```bash
uv run --frozen python scripts/run_oos_wf_cost_04.py --run
uv run --frozen python -m btc_risk_rl.pilots.wf_cost_replacement_04_worker \
  artifacts/oos-v12-wf-cost-only-04/wf-2021/request-8.json
uv run --frozen pytest -q tests/test_oos_wf_cost_04_profile.py \
  > /tmp/oos-wf-04-closure-focal.log 2>&1
python3 docs/evidence/oos-v1-2-wf-cost-04-session-02-20261030/audit.py \
  > docs/evidence/oos-v1-2-wf-cost-04-session-02-20261030/audit.json
uv run --frozen ruff check .
uv run --frozen pytest -q > /tmp/oos-wf-04-closure-pytest.log 2>&1
```

Ambos comandos de ejecución salieron con código 1 y rechazo
`NOT AUTHORIZED`. La prueba focal dio 5 passed en 14,27 s; la suite de
cierre dio **447 passed en 307,06 s** y Ruff pasó. La auditoría lee
reportes y checkpoints aceptados y verifica las huellas sin pasos de
optimizador ni trayectorias nuevas. Para `budget-close.json` se llamó
`inspect_budget(campaign=ROOT/'artifacts/never-used-audit-only')`, a fin de
incluir el cargo de `...04` en el cálculo compartido.

**No ejecutado:** otra sesión tras el fallo, repetición de la unidad 8,
evaluación v1.2, validación 2023 o prueba final.
