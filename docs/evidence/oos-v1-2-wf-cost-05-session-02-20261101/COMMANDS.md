# Comandos y resultados — WF `...05`, sesión 02

Ejecutados el 01/11/2026 (`America/La_Paz`) desde la raíz del repositorio.
Las capturas de este directorio son nuevas; los artefactos de campaña se
auditaron sin editarlos. `.python-version` estaba eliminado solo en el
árbol local y no se incorporó.

1. Estado de Git y Q0 anterior:

   ```bash
   git status --short
   git rev-parse HEAD
   uv run --frozen python docs/evidence/oos-v1-2-wf-cost-05-q0-20261101/audit.py > /tmp/oos-wf05-q0-before-20261101-session02.json
   sha256sum /tmp/oos-wf05-q0-before-20261101-session02.json
   ```

   HEAD `0b06b7e70d88bdf66f6db47e0fc33152857fec6a`; única modificación
   preexistente: eliminación local de `.python-version`. La salida Q0
   coincidió byte por byte con la auditoría publicada; SHA-256
   `32ef4b4fc0df6816d8b1cae9b6668b5b8d5324d1d09e1d685ad34214918c785d`.
   Se conservó como `q0-before.json`.

2. Verificación de código previa al lanzamiento:

   ```bash
   uv run --frozen pytest -q > /tmp/oos-wf05-20261101-retry-pytest.log 2>&1
   uv run --frozen ruff check . > /tmp/oos-wf05-20261101-retry-ruff.log 2>&1
   ```

   Salida 0 en ambos: **463 passed in 349.96s**; `All checks passed!`.
   Las salidas se conservaron como `pytest-before-launch.log` y
   `ruff-before-launch.log`.

3. Preflight vigilado nuevo y puertas de reingreso:

   ```bash
   uv run --frozen python -m scripts.audit_oos_wf_cost_05_preflight > /tmp/oos-wf05-20261101-retry-preflight.json
   sha256sum /tmp/oos-wf05-20261101-retry-preflight.json
   systemctl --user list-units --type=service --state=running
   ```

   `status=ready`, sin bloqueos; SHA-256
   `b9221cac25257afb0eaa313f3e1ebf037e450d81a6f3f9b83cae3543ea337a6c`.
   La captura está en `preflight-launch.json`. Se comprobaron además la
   Q0 aceptada, la raíz propia, las huellas y la admisión del tope de la
   unidad siguiente; no había otra campaña activa. No se abrió CSV H1
   compartido ni conjunto protegido.

4. Único lanzamiento de la sesión 02:

   ```bash
   systemd-run --user --unit=oos-wf-cost-20261101-05-session-02 \
     --property=Type=exec --property=Restart=no \
     --property=WorkingDirectory=/home/ichurri/Desktop/personal_projects/btc-risk-rl \
     --property=RuntimeMaxSec=3600 \
     /home/ichurri/.local/bin/uv run --frozen python scripts/run_oos_wf_cost_05.py --run
   ```

   `InvocationID=16d210a2098e4ab58f83cf8fbb7d0423`. Se observó hasta
   su salida sin enviar señales ni lanzar otra sesión. Se capturaron
   `journalctl --user -u oos-wf-cost-20261101-05-session-02.service` y
   `systemctl --user show oos-wf-cost-20261101-05-session-02.service` en
   `systemd-journal.txt` y `systemd-show.txt`. Resultado `success`, estado
   de ledger `ready`, 11 unidades aceptadas, pausa `budget`.

5. Auditoría final de solo lectura:

   ```bash
   uv run --frozen python docs/evidence/oos-v1-2-wf-cost-05-session-02-20261101/audit.py > docs/evidence/oos-v1-2-wf-cost-05-session-02-20261101/audit.json
   sha256sum docs/evidence/oos-v1-2-wf-cost-05-session-02-20261101/*
   ```

   Salida 0. `audit.json` SHA-256
   `9b5426f58d065feae02ea8e00c05e77dd3665ff6773ef8d908dfcc5d76b9275a`.
   No se ejecutó la siguiente Q0.
