# P3 — preflight de sesión 02 bloqueado, sin lanzamiento

El 09/10/2026 a las 00:03–00:04 America/La_Paz se ejecutaron estas
comprobaciones de solo lectura en `codex/p3-market-campaign`:

```bash
git status --short
git rev-parse HEAD
git rev-parse origin/codex/p3-market-campaign
systemctl --user list-units --all --type=service 'p3-*' --no-legend --no-pager
systemctl --user is-system-running
loginctl show-user ichurri -p Linger -p State -p Sessions
cat /sys/class/power_supply/ADP1/online
cat /sys/class/power_supply/BAT1/capacity
df -B1 /home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts
grep MemAvailable /proc/meminfo
uv run --frozen python docs/evidence/p3-market-2026-10-09/preflight-stdin.py
sha256sum docs/evidence/p3-market-2026-10-09/preflight-blocked.json
uv run --frozen ruff check docs/evidence/p3-market-2026-10-09/preflight-stdin.py
git diff --check
```

El preflight registró `read_only_resources_blocked`, razón
`AC not connected`; CA=0 y batería=37 % en la medición del preflight.
MemAvailable=8.278.441.984 B, disco libre=170.801.852.416 B,
`Linger=yes`, gestor `running`, presupuesto disponible=10.800 s y
ningún servicio P3 activo. Local y origin coincidían en `9b0d9f3`.
La vigilancia abrió solo el manifiesto H1 compartido, ningún CSV H1
compartido, y produjo cero trayectorias y actualizaciones. El SHA-256 de
[preflight-blocked.json](preflight-blocked.json) es
`a8ce02af8fed4a312a8bc69bbc19d6eb2dde634a651ad84cd94e938424fdc712`.
No se llamó a `systemd-run`, no se creó sesión 02 y no se tocó el ledger.
La eliminación local previa de `.python-version` permanece fuera del
commit.
