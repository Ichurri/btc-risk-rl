# Preparación de la prueba de logout completo P2R (solo sintético)

**PREPARADA, NO INICIADA.** Esta prueba usa una única Q0 sintética y deja un
checkpoint `after_q0`. No usa histórico, validación ni conjunto final; no
concede permiso de campaña P2R. La unidad propuesta es
`p2r-logout-q0-review-01.service` y su raíz nueva sería
`artifacts/p2r-synthetic-logout-q0-review-01`. La espera de 900 segundos
ocurre **dentro del child supervisado**, antes de ejecutar el worker sintético
en el mismo PID. El supervisor y sus heartbeats permanecen activos durante
esa espera; el tope Q0 de 1800 segundos y la reserva diaria no cambian.

El usuario informó `Linger=yes` y `systemctl --user is-system-running=running`
en su terminal. Debe registrarlos de nuevo inmediatamente antes de empezar.
`InvocationID` lo asigna systemd **al lanzar** la unidad: antes se registra
como `NO_ASIGNADO`, y se captura su valor real antes de cerrar sesión. No es
posible registrar un `InvocationID` real de una unidad que aún no existe.

## Condiciones de entrada

- Ejecutar manualmente desde una sesión del usuario en el mismo host y rama.
  No iniciar si hay otra campaña activa, si el nombre de unidad o la raíz ya
  existen, ni si la rama/código cambiaron desde la preparación.
- `Linger=yes`, gestor `running`, AC conectada, batería del sistema ≥50 %,
  `MemAvailable` ≥4 GiB y ≥10 GiB libres en `artifacts/`. El supervisor
  comprobará de nuevo batería ≥40 % y los demás recursos antes de Q0.
- Iniciar al menos **65 minutos antes** de la medianoche America/La_Paz, con
  saldo global diario apto. La admisión exige 1800 s para Q0 más 1800 s de
  reserva; el margen adicional cubre preparación y captura inicial. El
  ledger aplicará los débitos de otras campañas y puede rechazar la unidad.
- Tener una forma de volver a entrar y de observar después el journal de
  `systemd-logind`. El logout debe cerrar **todas** las sesiones interactivas
  de este usuario; cerrar solo Codex o el terminal no prueba el requisito.
  No apagar ni suspender el equipo.

Lectura local de solo recursos el 05/10/2026 a las 14:13:17 UTC: AC=1,
batería=98 %, disco libre=184778977280 bytes, pero
`MemAvailable=3981492224` bytes, **inferior a 4294967296**. La guarda real
`check_resources(stage="preflight")` rechazó la entrada. Es una medición
puntual; hay que repetirla al ejecutar y no reducir el umbral.

## A. Preparación y registro **antes** de lanzar

Ejecutar el bloque completo en el terminal cuando se cumplan las condiciones.
Si falla cualquier comando, **no** ejecutar B. Este bloque no inicia ninguna
unidad.

```bash
set -euo pipefail
repo=/home/ichurri/Desktop/personal_projects/btc-risk-rl
unit=p2r-logout-q0-review-01.service
probe_root="$repo/artifacts/p2r-synthetic-logout-q0-review-01"
record="$repo/artifacts/p2r-logout-q0-review-01-record"
cd "$repo"
test ! -e "$probe_root"
test ! -e "$record"
test "$(loginctl show-user "$UID" -p Linger --value)" = yes
test "$(systemctl --user is-system-running)" = running
test "$(systemctl --user show "$unit" -p LoadState --value)" = not-found
"$repo/.venv/bin/python" -c 'from pathlib import Path; from btc_risk_rl.pilots.p2r import check_resources; print(check_resources(stage="preflight", disk_path=Path("artifacts")))'
"$repo/.venv/bin/python" - <<'PY'
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
now = datetime.now(ZoneInfo("America/La_Paz"))
midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), now.tzinfo)
remaining = (midnight - now).total_seconds()
print(f"seconds_to_La_Paz_midnight={remaining:.0f}")
if remaining < 3900:
    raise SystemExit("Less than the 65-minute preparation window")
PY
mkdir -m 700 "$record"
{
  date -u --iso-8601=seconds
  printf 'unit=%s\nprobe_root=%s\ninvocation_id=NO_ASIGNADO\n' "$unit" "$probe_root"
  printf 'initial_state=not_started\n'
  git rev-parse HEAD
  loginctl show-user "$UID" -p Linger -p State
  systemctl --user is-system-running
  systemctl --user show "$unit" -p LoadState -p ActiveState -p InvocationID
  "$repo/.venv/bin/python" - <<'PY'
from pathlib import Path
from shutil import disk_usage
from btc_risk_rl.pilots.p2r import read_power
ac, battery = read_power()
memory = next(int(line.split()[1]) * 1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))
print(f"ac={ac} battery_percent={battery} mem_available_bytes={memory} disk_free_bytes={disk_usage('artifacts').free}")
PY
} | tee "$record/prelaunch.txt"
```

El hash del commit y las lecturas quedan en `prelaunch.txt`. Si no aparece
`initial_state=not_started`, si el sistema no informa `LoadState=not-found` o
si la guarda de recursos falla, el ensayo no está listo. Se necesita una raíz
nueva; no borrar ni reutilizar una raíz de una prueba fallida.

## B. Lanzamiento manual y registro inicial, **solo cuando el usuario decida**

Este bloque **sí inicia** la unidad. No se ejecutó al preparar este documento.
Debe conservarse el terminal abierto hasta capturar `InvocationID`, estado
`active`, ledger `running` con Q0 pendiente y al menos un heartbeat. Después
se anota UTC y se cierran todas las sesiones.

```bash
systemd-run --user --unit="$unit" --service-type=exec \
  --description='P2R synthetic full-logout Q0 probe' \
  --working-directory="$repo" --setenv=PYTHONUNBUFFERED=1 \
  "$repo/.venv/bin/python" "$repo/scripts/run_p2r.py" \
  --profile synthetic --mode algorithm --hold-seconds 900 \
  --max-units 1 --output "$probe_root" | tee "$record/launch.txt"
invocation_id=$(systemctl --user show "$unit" -p InvocationID --value)
test -n "$invocation_id"
printf 'invocation_id=%s\n' "$invocation_id" | tee "$record/invocation.txt"
systemctl --user show "$unit" -p LoadState -p ActiveState -p MainPID \
  -p ControlGroup -p InvocationID | tee "$record/started-unit.txt"
sleep 7
"$repo/.venv/bin/python" - "$probe_root" <<'PY' | tee "$record/initial-ledger.txt"
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
ledger = json.loads((root / 'ledger.jsonl').read_text().splitlines()[-1])
events = [json.loads(line) for line in (root / 'supervisor.jsonl').read_text().splitlines()]
assert ledger['status'] == 'running' and ledger['pending']['unit'] == 0
assert any(event['event'] == 'heartbeat' and event['unit'] == 0 for event in events)
print('ledger=running, unit=Q0, heartbeat=present, accepted_units=0')
PY
date -u --iso-8601=seconds | tee "$record/about-to-logout-utc.txt"
```

Si Q0 no figura `running`, no se recibe heartbeat o falta `InvocationID`,
**no cerrar sesión**: registrar el fallo y revisarlo; no relanzar la misma
raíz. El contador esperado durante la espera es cero; Q0 empieza tras los
900 s. Salir de todas las sesiones después de B, sin detener la unidad.

## C. Lectura después de volver a entrar; sin reanudación ni entrenamiento

El bloque siguiente es de solo lectura. Reestablece variables porque el
terminal inicial ya no existirá. Si Q0 sigue en espera, consultar de nuevo
pasados los 900 s y el tiempo de cálculo/guardado, sin reiniciar ni repetir.

```bash
set -euo pipefail
repo=/home/ichurri/Desktop/personal_projects/btc-risk-rl
unit=p2r-logout-q0-review-01.service
probe_root="$repo/artifacts/p2r-synthetic-logout-q0-review-01"
record="$repo/artifacts/p2r-logout-q0-review-01-record"
cd "$repo"
date -u --iso-8601=seconds | tee "$record/returned-utc.txt"
systemctl --user show "$unit" -p ActiveState -p Result -p MainPID \
  -p ControlGroup -p InvocationID | tee "$record/after-unit.txt"
invocation_id=$(sed -n 's/^invocation_id=//p' "$record/invocation.txt")
test -n "$invocation_id"
journalctl --user -u "$unit" --output=short-iso-precise --no-pager \
  | tee "$record/systemd-journal.txt"
journalctl --user _SYSTEMD_INVOCATION_ID="$invocation_id" \
  --output=short-iso-precise --no-pager \
  | tee "$record/invocation-journal.txt"
test -s "$record/invocation-journal.txt"
journalctl -b -u systemd-logind --output=short-iso-precise --no-pager \
  > "$record/logind-journal.txt" || \
  printf 'systemd-logind journal inaccessible; logout not verified\n' \
  | tee -a "$record/logind-journal.txt"
sha256sum "$probe_root/supervisor.jsonl" "$probe_root/ledger.jsonl" \
  "$probe_root/run-00-C5/checkpoint-0/state.pt" \
  | tee "$record/hashes.txt"
"$repo/.venv/bin/python" - "$probe_root" "$invocation_id" <<'PY' | tee "$record/checks.txt"
import hashlib, json, sys
from pathlib import Path
import torch
from btc_risk_rl.pilots.p2r import P2RJournal
root = Path(sys.argv[1])
invocation_id = sys.argv[2]
rows = [json.loads(line) for line in (root / 'ledger.jsonl').read_text().splitlines()]
ledger = rows[-1]
assert ledger['status'] == 'ready' and ledger['pending'] is None
assert len(ledger['units']) == 1 and ledger['units'][0]['unit'] == 0
assert ledger['runs']['run-00-C5']['next_unit'] == 1
expected = dict(trajectories=2, transitions=360, diagnostic_trajectories=0,
                diagnostic_transitions=0, actor_updates=0, critic_updates=0)
assert ledger['units'][0]['resources'] == expected
checkpoint = root / 'run-00-C5' / 'checkpoint-0'
manifest = json.loads((checkpoint / 'manifest.json').read_text())
state_path = checkpoint / 'state.pt'
digest = hashlib.sha256(state_path.read_bytes()).hexdigest()
assert manifest['boundary'] == 'after_q0'
assert manifest['profile'] == 'p2_synthetic_tests_only'
assert manifest['state_sha256'] == digest
assert ledger['units'][0]['checkpoint_sha256'] == digest
state = torch.load(state_path, map_location='cpu', weights_only=True)
assert state['attrs']['boundary'] == 'after_q0'
assert state['collector']['trajectories'] == 2
journal = P2RJournal(root / 'supervisor.jsonl', campaign=root.name)
events = [json.loads(line) for line in journal.path.read_text().splitlines()]
assert {e['invocation_id'] for e in events} == {invocation_id}
assert any(e['event'] == 'unit_completed' and e['phase'] == 'after_q0' for e in events)
assert any(e['event'] == 'supervisor_exit' for e in events)
print('synthetic Q0 complete; ledger, journal chain, counters and checkpoint verified')
PY
```

La condición decisiva de logout no es simplemente que exista el checkpoint:
en `logind-journal.txt` debe poder identificarse la retirada de la **última**
sesión de este usuario y su siguiente inicio, y en `supervisor.jsonl` deben
existir heartbeats con UTC entre esos dos hechos, asociados al mismo
`InvocationID`/unidad y al ledger de esta raíz. `about-to-logout-utc.txt` y
`returned-utc.txt` acotan la revisión, pero no sustituyen al registro de
logind. Si el journal de logind no es accesible, persisten otras sesiones o
faltan heartbeats durante el intervalo sin sesión, declarar el resultado
**no verificado**, aunque Q0 termine. Si ledger queda `failed`, conservar
todo y no reiniciar la misma raíz. No ejecutar en esta prueba la segunda
sonda de `SIGTERM` sugerida por el protocolo; requiere preparación aparte.
