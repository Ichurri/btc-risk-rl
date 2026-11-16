# P2R v2 — revisión final de preparación, sin lanzamiento

**Estado al 06/10/2026:** preparación técnica revisada sobre `dc6285c`.
**Campaña NO AUTORIZADA ni iniciada.** `MARKET_EXECUTION_ENABLED=False`,
`REGISTRATION_SHA256=None`, sin `docs/protocols/P2R-market-approval.json`
ni raíz `artifacts/p2r-approved-v2`. Este informe no crea el permiso ni
convierte el diagnóstico de desarrollo en evaluación confirmatoria.

## Verificación ejecutada

La suite completa sobre el código final dio **288 passed in 212.65s**;
`ruff check .` dio **All checks passed!**. La única modificación local
preexistente fue la eliminación sin versionar de `.python-version`, que se
conservó. Local y `origin/codex/p2r-historical-executor` coincidían en
`dc6285c` antes de este informe.

El manifiesto derivado local y su copia de evidencia dieron ambos SHA-256
`62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9`,
igual al ancla del commit `cd6b686`. El manifiesto H1 original conservó
`d7cd59b7cda003a0f69883a83a0bacf06a65c37f3653a2f466c249ddf41a6998`;
los **12 productos H1** coincidieron con las huellas declaradas. Esta
segunda comprobación de productos H1 fue un hash de integridad separado:
leyó bytes de los CSV compartidos, incluidos los de 2023, sin materializar
filas para entrenamiento, diagnóstico o selección. No forma parte del
preflight P2R. Los ledgers P0, P1 y P2 conservaron respectivamente
`1d1ee72c…339b8c`, `926eab40…5755` y `e6dedc6b…7b8` (SHA completos en
[anchors.sha256](../evidence/p2r-final-readiness/anchors.sha256)); P2 sigue
`failed` y no se reanuda.

El [preflight vigilado](../evidence/p2r-final-readiness/preflight-opens.json)
del 06/10/2026 18:47:05 UTC registró 7.048 inicios, **cero aperturas de los
cinco CSV H1 compartidos**, cero trayectorias, cero actualizaciones y
`read_only_ready_campaign_disabled`. Solo abrió el manifiesto H1 y los
siete archivos y manifiesto del derivado. La vigilancia aborta si aparece
una apertura compartida. El resultado no reserva recursos ni tiempo.

| Lectura puntual | Resultado observado | Umbral o alcance |
|---|---:|---|
| Host, 18:47 UTC | `Linger=yes`; gestor de usuario `running`; sin unidades `p2r-*`/`p2-*` cargadas ni lock observado | Repetir en ingreso real |
| Alimentación | CA conectada; batería del sistema 98 % | ≥50 % preflight; ≥40 % antes de cada unidad |
| `MemAvailable` | 7.055.130.624 B (6,57 GiB) | ≥4 GiB |
| Disco libre en raíz de artefactos | 182.391.967.744 B (169,87 GiB) | ≥10 GiB |
| Presupuesto compartido, día `2026-10-06` La Paz | Débito externo 0 s; saldo teórico 10.800 s; lock **no adquirido** | 3 h globales/día; excluir 30/09/2026 |
| Ventana civil, 14:47 La Paz | Medianoche siguiente: 07/10 04:00 UTC, unas 9 h 13 min después | El límite diario de 3 h es más restrictivo en esta instantánea |

La primera consulta de `loginctl`/`systemctl` desde el sandbox no pudo
conectarse al bus (`Operation not permitted`). La lectura de solo lectura
con acceso local autorizado devolvió los estados indicados; no se modificó
`systemd`. No se detectó otra campaña en los ledgers inspeccionados; el
saldo y la ausencia de unidad/lock son instantáneos, no una garantía de
exclusividad futura.

## Procedimiento exacto propuesto para la autorización posterior

**Los comandos de este apartado NO SE EJECUTARON.** Primero tendría que
existir un permiso específico humano, registrado en un commit separado:
`MARKET_EXECUTION_ENABLED=True`, `REGISTRATION_SHA256` fijado al JSON de
`docs/protocols/P2R-market-approval.json`, con `active=true`, alcance
`accepted_training_2018_2022_only`, huellas de protocolo/adopción y nombre
canónico `p2r-approved-v2`. Editar solo el JSON o invocar la CLI no basta.
La raíz canónica debe seguir ausente y ser distinta de P2 y de las sondas.
Revisar el diff, huellas y estado de Git antes de ese commit; esta revisión
no resuelve la eliminación local de `.python-version`.

Tras esa autorización, repetir **en el mismo host y día**: huellas de
código, configuración, protocolo, H1/derivado, scaler y ledgers P0/P1/P2;
`scripts/audit_p2r_preflight_opens.py`; alimentación, memoria, disco,
`Linger=yes`, gestor `running`, ausencia de campaña concurrente y saldo
global. Rechazar cualquier discrepancia antes de crear una raíz o unidad.
La matriz inalterable es:

| Bloque | Corridas secuenciales, sin concurrencia |
|---|---|
| Semilla 610031 | `run-00-C0` → `run-01-C5` → `run-02-C10` |
| Semilla 610047 | `run-03-C5` → `run-04-C10` → `run-05-C0` |
| Semilla 610081 | `run-06-C10` → `run-07-C0` → `run-08-C5` |

Cada corrida tiene Q0 (`unit=0`, 400 Q), luego diez unidades indivisibles
`unit=1…10` para k=0…9 (64 A, 400 Q, 400 B y 64 D por iteración). H=180,
γ=1, actor 2 épocas, crítico 4 provisionales, `d=−ln(0.90)` común C5/C10,
datos H1 de entrenamiento y normalizador fijo. La primera unidad sería
`run-00-C0/unit=0`; su único checkpoint aceptado es `after_q0`. Cada
unidad posterior acepta solo `after_dual_and_D`.

Para la **primera sesión futura**, una vez satisfechas todas las puertas:

```bash
repo=/home/ichurri/Desktop/personal_projects/btc-risk-rl
unit=p2r-market-v2-session-01.service
test ! -e "$repo/artifacts/p2r-approved-v2"
systemd-run --user --unit="$unit" --service-type=exec \
  --description='P2R v2 historical training, approved protocol' \
  --working-directory="$repo" --setenv=PYTHONUNBUFFERED=1 \
  "$repo/.venv/bin/python" "$repo/scripts/run_p2r_market.py"
systemctl --user show "$unit" -p InvocationID -p MainPID \
  -p ActiveState -p SubState -p Result
journalctl --user -u "$unit" -o short-iso-precise --no-pager
```

Registrar inmediatamente `InvocationID`, UTC, PID, cgroup y nombre de
unidad; conservar `artifacts/p2r-approved-v2/supervisor.jsonl` (cadena
SHA-256 con `fsync`), `ledger.jsonl` encadenado, `run-XX-<condición>/request-N.json`,
`phase-N.json`, `progress.json`, `worker-N.log`, `unit-N.json` y
`checkpoint-N/{manifest.json,state.pt}`. El supervisor verifica deltas,
identidad y fronteras completas antes de aceptar un checkpoint. La primera
Q/A/B+D mide el costo real de D; D tiene subtope de 900 s.

El supervisor se detiene solo en una frontera completa si la unidad
siguiente no cabe con reserva o falla una guarda **entre** unidades. El
ledger queda sin `pending` y el journal registra `paused`; una nueva sesión
con nombre de unidad distinto (`p2r-market-v2-session-02.service`, etc.)
solo puede continuar la **misma raíz** y autorización tras nuevo preflight,
saldo y huellas íntegros. Máximo tres sesiones por corrida, 27 de campaña y
tres días activos. No borrar ni reescribir ledgers, requests, logs o
checkpoints. No usar una señal manual como método normal de pausa: puede
llegar dentro de Q0/Q/A/B+D. Si debe detenerse por emergencia:

```bash
systemctl --user stop "$unit"
systemctl --user show "$unit" -p InvocationID -p Result -p ExecMainStatus
journalctl --user -u "$unit" -o short-iso-precise --no-pager
```

Una señal, pérdida de worker/supervisor, heartbeat registrado >5 s,
discontinuidad de reloj >2 s, no finitos, huella/cadena corrupta,
RSS worker >10 GiB, tope Q0 1800 s, tope Q/A/B+D 2700 s, D >900 s o
invasión de reserva **dentro** de unidad exige `failed`, conserva toda la
evidencia y prohíbe reanudar esa campaña aunque exista un checkpoint
anterior. No se repite selectivamente una corrida. Si se agotan días o
sesiones sin nueve K10 completos, estado `incomplete`; no se amplían topes.
Una salida exitosa de servicio por presupuesto no equivale a nueve corridas
completas: verificar el cursor, las 99 unidades aceptadas, nueve
checkpoints finales, contadores y cadenas antes de clasificar cierre.

## Riesgo de factibilidad

El estado actual impide **iniciar**: falta autorización/registro específico
y el gate permanece cerrado. El preflight de recursos de hoy no garantiza
aptitud al lanzamiento; suspensión/apagado físico, sensor ilegible o
campaña concurrente también lo impedirían. Hasta tres días con 8100 s de
trabajo cada uno dejan como máximo **24.300 s de trabajo para 99 unidades**
antes de contar la carga y sobrecostos de supervisión; el promedio necesario
es <245,5 s por unidad y la admisión por día/unidad puede ser más estricta.
Es una condición aritmética, **no una predicción**. P2 midió 57 unidades
completas en su campaña fallida, pero no valida el costo de P2R supervisado
ni permite extrapolar D. Si la primera medición o el máximo medido por
condición exigen una reserva que no cabe, se pausa en frontera; si se agotan
los tres días, se informa `incomplete` sin alterar el protocolo.
Los 6,57 GiB disponibles hoy superan el mínimo de 4 GiB, pero son menores
que el tope de RSS del worker de 10 GiB; pasar el umbral no garantiza que el
host soporte cualquier pico real. Una caída de memoria antes de la unidad
bloquea o pausa; dentro de ella puede invalidar la campaña.

La campaña, si alguna vez se autoriza, sería diagnóstico de desarrollo
sobre entrenamiento 2018–2022. Ni este preflight ni nueve corridas futuras
demostrarían generalización temporal, superioridad financiera o
cumplimiento poblacional de CVaR.
