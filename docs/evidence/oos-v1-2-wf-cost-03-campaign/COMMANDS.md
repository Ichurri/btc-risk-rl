# Comandos ejecutados — WF `...03`, 29/10/2026

Directorio de trabajo: `/home/ichurri/Desktop/personal_projects/btc-risk-rl`. Los logs y capturas pequeñas de esta carpeta son copias de la ejecución; los originales de la campaña están en `artifacts/oos-v12-wf-cost-only-03/` y no se editan.

## Antes del lanzamiento

Se leyó el estado Git y se cotejó `origin`; la única modificación local previa fue ` D .python-version`. Se comprobó repetidamente `/sys/class/power_supply/ADP1/online` y `/sys/class/power_supply/BAT1/capacity`; la suite comenzó tras alcanzar CA=1 y batería=50 %.

```bash
uv run --frozen pytest
uv run --frozen ruff check .
uv run --frozen python -m scripts.audit_oos_wf_cost_03_preflight > /tmp/wf03-campaign-preflight-launch.json
sha256sum /tmp/wf03-campaign-preflight-launch.json
```

Resultados: 428 passed en 289,88 s; Ruff `All checks passed!`; preflight `ready`, sin aperturas protegidas, SHA-256 `370b2904d79f26191082e28fc8c8158baa11ade3d01ccada0111488221de94db`.

## Único lanzamiento

```bash
systemd-run --user --unit=oos-wf-cost-20261029-03-session-01 \
  --property=Type=exec --property=Restart=no \
  --property=WorkingDirectory=/home/ichurri/Desktop/personal_projects/btc-risk-rl \
  --property=RuntimeMaxSec=3600 \
  /home/ichurri/.local/bin/uv run --frozen python scripts/run_oos_wf_cost_03.py --run
systemctl --user show oos-wf-cost-20261029-03-session-01.service \
  -p Result -p ExecMainPID -p ExecMainStatus -p MemoryPeak \
  -p CPUUsageNSec -p ActiveState -p SubState -p InvocationID
journalctl --user -u oos-wf-cost-20261029-03-session-01.service --no-pager
```

`InvocationID=d763be02a01a49b7b4ef2c88069009ca`; `Result=exit-code`, `ExecMainStatus=1`. Una sola Q0 quedó pendiente, ninguna unidad fue aceptada. No hubo segundo lanzamiento.

## Auditoría y cierre

```bash
sha256sum artifacts/oos-v12-wf-cost-only-03/ledger.jsonl \
  artifacts/oos-v12-wf-cost-only-03/sessions.jsonl \
  artifacts/oos-v12-wf-cost-only-03/supervisor.jsonl \
  artifacts/oos-v12-wf-cost-only-03/wf-2021/worker-0.log
uv run --frozen pytest -q tests/test_oos_wf_cost_03_profile.py
uv run --frozen ruff check .
uv run --frozen python scripts/run_oos_wf_cost_03.py --run
uv run --frozen python -m btc_risk_rl.pilots.wf_cost_replacement_03_worker /tmp/nonexistent-wf03-request.json
```

Las pruebas focales finales dieron 9 passed en 12,48 s; Ruff pasó. Los dos comandos públicos finales devolvieron código 1 y `NOT AUTHORIZED` antes de cargar datos o escribir en la raíz. El script de auditoría leyó el último estado del ledger, verificó las cadenas y calculó SHA-256 de 10 archivos de `...03`; comparó los 15 archivos de `...01` y los 2 de `...02` con el manifiesto previo, sin diferencias. El presupuesto fallido aplica cargo conservador de 10.800 s el 29/10; la sesión medida duró 3,310445 s.

La suite completa se ejecutó **antes** de lanzar, con gate activo y código autorizado. Tras el fallo solo cambiaron el gate y pruebas de guarda; se ejecutaron pruebas focales y Ruff sobre ese estado. No se repitió la suite completa tras el cierre.
