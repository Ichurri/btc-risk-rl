# Comandos ejecutados — señal Q0 sintética 04/05

Desde la raíz del repositorio. Los comandos de lanzamiento usan un perfil
explícitamente sintético. Las salidas crudas, timestamps de petición de señal,
journals y estados están en las dos raíces `artifacts/*-record`, fuera de Git.

## Verificación y preparación

```bash
git status --short --branch
git rev-parse HEAD
.venv/bin/python -c 'from pathlib import Path; from btc_risk_rl.pilots.p2r import check_resources; print(check_resources(stage="preflight", disk_path=Path("artifacts")))'
systemctl --user is-system-running
systemctl --user show p2r-signal-q0-review-04.service -p LoadState -p ActiveState
systemctl --user show p2r-signal-q0-review-05.service -p LoadState -p ActiveState
systemctl --user list-units 'p2r-*.service' --state=running --no-legend
```

Ambas comprobaciones de recursos dieron `ready`, el gestor `running` y las
unidades nuevas `not-found`/`inactive`. Antes de lanzar se comprobó que cada
raíz aún no existía. El ledger P2R informó `external_seconds=0` para este día.

## Sonda 04, código base `c105816`

```bash
systemd-run --user --unit=p2r-signal-q0-review-04.service --service-type=exec --description='P2R synthetic Q0 in-unit SIGTERM probe' --working-directory=/home/ichurri/Desktop/personal_projects/btc-risk-rl --setenv=PYTHONUNBUFFERED=1 /home/ichurri/Desktop/personal_projects/btc-risk-rl/.venv/bin/python /home/ichurri/Desktop/personal_projects/btc-risk-rl/scripts/run_p2r.py --profile synthetic --mode algorithm --hold-seconds 120 --max-units 1 --output /home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/p2r-synthetic-signal-q0-review-04
systemctl --user show p2r-signal-q0-review-04.service -p InvocationID -p MainPID -p ActiveState -p SubState -p Result
systemctl --user kill --kill-whom=main --signal=SIGTERM p2r-signal-q0-review-04.service
journalctl --user -b -u p2r-signal-q0-review-04.service --output=short-iso-precise --no-pager
```

Se comprobó ledger `running`, `pending.unit=0` y heartbeat antes de enviar
SIGTERM. Resultado: ledger `failed`, cero checkpoints; systemd `success`
por el defecto de salida de la CLI. No se volvió a ejecutar en esta raíz.

## Corrección y regresión

```bash
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen pytest -q 'tests/test_p2r_units.py::test_signal_inside_unit_fails_permanently[0]'
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen pytest -q tests/test_p2r_units.py::test_cli_exits_nonzero_when_synthetic_unit_failed
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen pytest -q
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen ruff check .
git diff --check
```

La prueba nueva de CLI falló antes del cambio porque no salía con código
no cero; después pasó. El test de señal existente pasó. El conjunto completo
dio `267 passed in 180.85s`. Ruff inicialmente detectó solo orden de imports
en la prueba nueva; se corrigió y dio `All checks passed!`. Luego pasó de
nuevo la prueba específica de CLI. El commit de corrección fue `08c0fda`.

## Repetición necesaria 05, código `08c0fda`

```bash
systemd-run --user --unit=p2r-signal-q0-review-05.service --service-type=exec --description='P2R synthetic Q0 in-unit SIGTERM repeat' --working-directory=/home/ichurri/Desktop/personal_projects/btc-risk-rl --setenv=PYTHONUNBUFFERED=1 /home/ichurri/Desktop/personal_projects/btc-risk-rl/.venv/bin/python /home/ichurri/Desktop/personal_projects/btc-risk-rl/scripts/run_p2r.py --profile synthetic --mode algorithm --hold-seconds 120 --max-units 1 --output /home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/p2r-synthetic-signal-q0-review-05
systemctl --user show p2r-signal-q0-review-05.service -p InvocationID -p MainPID -p ActiveState -p SubState -p Result
systemctl --user kill --kill-whom=main --signal=SIGTERM p2r-signal-q0-review-05.service
systemctl --user show p2r-signal-q0-review-05.service -p InvocationID -p MainPID -p ActiveState -p SubState -p Result -p ExecMainStatus -p ExecMainCode
journalctl --user -b -u p2r-signal-q0-review-05.service --output=short-iso-precise --no-pager
```

Antes de la señal: Q0 `running`, pendiente 0, sin unidad aceptada y seis
heartbeats. Después: `Result=exit-code`, `ExecMainStatus=1`, ledger `failed`,
cero checkpoints. No se hizo ninguna repetición adicional.

## Auditoría de solo lectura

```bash
.venv/bin/python docs/evidence/p2r-signal-q0/checks.py > docs/evidence/p2r-signal-q0/results.json
sha256sum -c docs/evidence/p2r-signal-q0/SHA256SUMS.txt
sha256sum -c docs/evidence/p2r-heartbeat-cadence-03/SHA256SUMS.txt
sha256sum -c docs/evidence/p2r-logout-q0-02/SHA256SUMS.txt
sha256sum artifacts/p2r-synthetic-logout-q0-review-01/ledger.jsonl artifacts/p2r-synthetic-logout-q0-review-01/supervisor.jsonl artifacts/p2r-synthetic-logout-q0-review-01/run-00-C5/checkpoint-0/state.pt artifacts/p2r-logout-q0-review-01-record/logind-journal.txt
```

La auditoría pasó: 28/28 hashes nuevos, 18/18 de 03, 32/32 de 02 y cuatro
huellas principales de 01 coincidentes. El script de checks es read-only:
no invoca trabajador, optimizador, reanudación ni carga de mercado.
