# P2: comprobaciones de la pérdida del supervisor

Consultas **solo de lectura** efectuadas después del cierre `a2014e4`.
No se invocó `run_p2.py`, no se abrió `TrainingMarket` ni se cargaron datos de
validación o prueba final. Se preservaron el ledger y `run-05-C0`.

```bash
git status --short --branch
git log -5 --oneline --decorate
sha256sum artifacts/p2-approved-v1/ledger.jsonl \
  artifacts/p2-approved-v1/run-05-C0/progress.json \
  artifacts/p2-approved-v1/run-05-C0/journal/events.jsonl \
  artifacts/p2-approved-v1/run-05-C0/request-2.json \
  artifacts/p2-approved-v1/run-05-C0/worker-2.log
TZ=UTC stat -c '%n %s %y' \
  artifacts/p2-approved-v1/run-05-C0/progress.json \
  artifacts/p2-approved-v1/run-05-C0/worker-2.log
last -x -F reboot shutdown
journalctl --list-boots --no-pager
journalctl -b -1 --since '2026-09-30 02:20:09' \
  --until '2026-09-30 02:20:13' --no-pager -o json
```

El journal JSON se filtró localmente por tiempo, `MESSAGE` y `_COMM`; no se
versionan entradas de otras aplicaciones. Señales relevantes, convertidas a
UTC: GNOME `endSessionDialog` 06:20:11.000; `Shutting down GNOME Shell`
06:20:12.527; `systemd` detuvo servicios de sesión desde 06:20:12.617 y
alcanzó `shutdown.target`/`exit.target` a las 06:20:16. `last -x -F`
registró `shutdown system down` a las 02:20:12 La Paz y siguiente `reboot`
a las 12:06:59 La Paz. El progreso P2 tiene mtime
06:20:12.741924 UTC. El archivo de log worker-2 existe desde
06:19:30.489141 UTC y mide 0 bytes.

Huellas SHA256 al investigar:

| Artefacto local | SHA256 |
|---|---|
| `artifacts/p2-approved-v1/ledger.jsonl` | `e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8` |
| `run-05-C0/progress.json` | `bb2af51c8192303d062b095646a772948072e4eeb36c039f1aa8f9e0037af2b3` |
| `run-05-C0/journal/events.jsonl` | `45ef6ad0421e062a7a1b150f5711cfbf07bfec8d47e5e3a72dabf2a149f6002b` |
| `run-05-C0/request-2.json` | `0f274167a35f242ed17d07ff6cfa25ffcb880872f1f823b089c681079beca668` |
| `run-05-C0/worker-2.log` vacío | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

El ledger conserva `status=failed`, `cursor=5`, 57 unidades cerradas y
`pending={run_id:run-05-C0,unit:2,kind:iteration}`. La última unidad
cerró a las 06:19:30.457 UTC; la marca `failed` se añadió al inspeccionar
el 30/09/2026 a las 16:32:06.528 UTC. Esta última hora **no** mide la
duración de la unidad inconclusa.

La primera búsqueda con `journalctl --utc --since '...06:18'` no mostró
entradas porque el filtro de tiempo interpretó la cadena en la zona local.
La consulta correcta usó `02:20` La Paz. El journal accesible contiene la
sesión del usuario; la consulta al journal del sistema/kernel no mostró sus
mensajes con los permisos disponibles. `sudo -n journalctl ...` informó
`a password is required`; no se intentó modificar privilegios. Por ello no
se atribuye el apagado a un iniciador concreto.

El contrato del supervisor fue inspeccionado en
`src/btc_risk_rl/pilots/supervisor.py`, `p2_runner.py` y `budget.py`:
`PR_SET_PDEATHSIG=SIGKILL`, escritura de resultado tras retorno del worker,
fallo persistido al reabrir ledger `running`, y fronteras P2
`after_q0`/`after_dual_and_D`. Es lectura del código existente, no prueba de
que una señal particular se entregó durante el apagado.

Una comprobación algebraica/de lectura con `python3` confirmó nuevamente
SHA256 del ledger, 57 unidades cerradas, 3264 D, fase B, ausencia de los
cuatro artefactos de cierre de la unidad 2 y las tres entradas GNOME citadas.
No abrió checkpoints de aprendizaje ni ejecutó pruebas que entrenen agentes.

Al redactar, `UV_CACHE_DIR=/tmp/uv-cache uv run --frozen ruff check .` y
`git diff --check` pasaron. Un verificador estático comprobó 85 enlaces
relativos de README/HANDOFF/los tres documentos nuevos y ausencia de
marcadores `TBD`/`TODO` como palabras completas. El primer intento de buscar
subcadenas confundió `todo` dentro de «método»; se corrigió el verificador,
sin cambiar la propuesta por ese falso positivo. No se ejecutó `pytest`
porque incluye pequeñas actualizaciones sintéticas ajenas a esta investigación.
