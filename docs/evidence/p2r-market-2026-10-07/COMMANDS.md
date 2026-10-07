# Comandos ejecutados antes y al comienzo de P2R v2

Fecha local: 07/10/2026, America/La_Paz. Los registros íntegros de la campaña
están fuera de Git en `artifacts/p2r-approved-v2`; este directorio conserva
evidencia pequeña y rutas para auditarlos.

```bash
git status --short --branch
git rev-parse HEAD
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python scripts/audit_p2r_preflight_opens.py
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check .
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen pytest -q
loginctl show-user ichurri -p Linger -p State -p Sessions
systemctl --user is-system-running
systemctl --user list-units --all 'p2r-*' 'p2-*' --no-pager
sha256sum data/processed/p2r-training-h1/manifest.json docs/evidence/p2r-training-shard-export/manifest.json
sha256sum artifacts/p0-approved-v1/ledger.jsonl artifacts/p1-approved-v1/ledger.jsonl artifacts/p2-approved-v1/ledger.jsonl
```

El preflight vigilado se repitió con el permiso aún inactivo: 7.048 inicios,
0 aperturas de los cinco CSV H1 compartidos, 0 trayectorias y 0 pasos de
optimizador. Tras fijar el permiso en `38fc54b`, se repitió con un audit hook
equivalente que rechaza cualquier apertura de esos CSV; devolvió
`read_only_ready_campaign_enabled`, 0 aperturas, 7.048 inicios y saldo externo
10.800 s. Ruff: `All checks passed!`; suite final: `289 passed in 218.40s`.
La prueba dirigida intermedia: `22 passed in 38.14s`.

Lectura puntual anterior al lanzamiento, 05:34:52 UTC: CA conectada,
batería 97 %, `MemAvailable=4896944128` B, disco libre `182225588224` B,
`Linger=yes`, gestor `running`, ninguna unidad P2/P2R activa. La memoria
superaba el mínimo de 4 GiB sin margen amplio. H1, derivado y normalizador
coincidieron con las huellas fijadas; P0/P1/P2 conservaron sus ledgers.

```bash
systemd-run --user --unit=p2r-market-v2-session-01.service --service-type=exec \
  --description='P2R v2 historical training, approved development diagnostic' \
  --working-directory=/home/ichurri/Desktop/personal_projects/btc-risk-rl \
  --setenv=PYTHONUNBUFFERED=1 \
  /home/ichurri/Desktop/personal_projects/btc-risk-rl/.venv/bin/python \
  /home/ichurri/Desktop/personal_projects/btc-risk-rl/scripts/run_p2r_market.py
systemctl --user show p2r-market-v2-session-01.service \
  -p InvocationID -p MainPID -p ActiveState -p SubState -p Result -p ExecMainStatus -p ControlGroup
journalctl --user -u p2r-market-v2-session-01.service -o short-iso-precise --no-pager
```

El lanzamiento devolvió `InvocationID=98473fe6e319417e8fe84abceb1bcd53`.
La unidad Q0 fue aceptada y la primera Q/A/B+D está registrada en
[`first-unit.json`](first-unit.json). Su tiempo de pared completo y el de D
son mediciones nuevas de P2R, no extrapolaciones de P2.

Tras `availability_lost_after_unit` en la primera sesión se comprobó un
ledger `ready`, `pending=null`, checkpoint completo y nuevo preflight.
Se ejecutó la continuación válida:

```bash
systemd-run --user --unit=p2r-market-v2-session-02.service --service-type=exec \
  --description='P2R v2 approved development diagnostic, valid-boundary continuation' \
  --working-directory=/home/ichurri/Desktop/personal_projects/btc-risk-rl \
  --setenv=PYTHONUNBUFFERED=1 \
  /home/ichurri/Desktop/personal_projects/btc-risk-rl/.venv/bin/python \
  /home/ichurri/Desktop/personal_projects/btc-risk-rl/scripts/run_p2r_market.py
```

`InvocationID=7887fd6ad3164da08959f337e05bc3c2`. La segunda sesión
aceptó `unit=9` y volvió a pausar por disponibilidad entre unidades.
La [instantánea](pause-01.json) se comprobó contra SHA-256 del ledger,
journal y checkpoint; el estado sigue recuperable solo desde frontera
completa. No hubo repetición de unidad ni de corrida.
