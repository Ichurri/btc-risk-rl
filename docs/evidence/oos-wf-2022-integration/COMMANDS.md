# Comandos realmente ejecutados — integración WF 2022

Estado de esta captura: 06/11/2026 `America/La_Paz`. Las pruebas de
trabajador/supervisor usan una fuente controlada; **no son entrenamiento
histórico**. La raíz `artifacts/oos-v12-wf-cost-only-2022-01/` no se creó
durante estas pruebas.

```bash
git status --short --branch
git log -3 --oneline
uv run --frozen pytest -q tests/test_oos_wf_2022_orchestrator.py::test_night_window_never_starts_a_unit_that_cannot_close_by_eight
uv run --frozen pytest -q tests/test_oos_wf_2022_executor.py tests/test_oos_wf_2022_orchestrator.py tests/test_p2r_journal_signal_atomic.py
uv run --frozen pytest -q tests/test_oos_wf_2022_executor.py::test_2022_profile_has_independent_pinned_approval tests/test_oos_wf_2022_executor.py::test_2022_worker_rejects_closed_gate_before_request tests/test_oos_wf_2022_executor.py::test_2022_forged_registration_rejected_before_worker_request tests/test_oos_wf_2022_orchestrator.py::test_closed_public_entry_creates_no_journal_or_campaign
uv run --frozen pytest -q tests/test_oos_wf_2022_executor.py::test_service_resource_drop_before_root_is_a_metered_block tests/test_oos_wf_2022_executor.py::test_stale_prepare_before_root_is_a_metered_block
uv run --frozen pytest -q tests/test_oos_wf_2022_executor.py::test_2022_supervisor_accepts_q0_then_unit_one_in_new_session
uv run --frozen ruff check .
uv run --frozen pytest -q
uv run --frozen python scripts/audit_oos_wf_cost_2022_preflight.py
```

El reloj sintético detectó primero **1 fallo** de admisión a las 23:15 y
después **1 passed** al exigir la reserva global antes de medianoche. El
grupo focal de trabajador, supervisor, presupuesto y journal dio **31 passed
in 102.82s** antes de fijar el permiso. La prueba focal del permiso fijado
dio **4 passed in 1.23s**; Ruff informó `All checks passed!`.

La primera suite completa del código integrado, durante ediciones de
fuentes, dio **499 passed, 1 failed in 448.34s**. La falla fue una
comparación de huellas de procedencia mientras cambiaba una fuente en la
misma ejecución. No se toma como suite final. La suite sobre código fijado
dio **502 passed in 442.93s** y se conserva en
`/tmp/oos-wf-2022-suite-pinned-20261106.txt`. Dos pruebas nuevas
detectaron un bloqueo entre preparación y servicio que se marcaba como
fallo irreversible: dieron **2 failed** antes de corregir y **2 passed**
después. El reingreso con una pausa intermedia dio **1 passed in 88.64s**.
Tras volver a fijar el permiso, la suite final dio **504 passed in
433.71s**, registrada en `/tmp/oos-wf-2022-suite-final-pinned-20261106.txt`.
Ruff y `git diff --check` pasaron.

El preflight de solo lectura anterior al permiso está en
[`preflight-closed.json`](preflight-closed.json), SHA-256
`6968dff853da06b6ca03ff8f05d05072e977a0683c38893d7416ff975b46624d`.
Abrió exclusivamente el derivado H1 de entrenamiento y metadatos, nunca los
CSV H1 compartidos. Fue `blocked` por permiso inactivo y memoria
`4110069760 B < 4294967296 B`. No sirve para lanzar.

El preflight vigilado **posterior** al permiso está en
[`preflight-after-approval.json`](preflight-after-approval.json), SHA-256
`cbf8dad2d2c4f8fe9fb29b24ecf55fff3e7ba78dcf35253829ef34b5bf720fa8`.
También registró únicamente rutas permitidas y cero trayectorias/pasos.
Quedó `blocked` a las 17:24 La Paz por **CA desconectada** (`ac=false`,
batería 81 %). MemAvailable fue 5854142464 B, disco libre 128975572992 B,
`Linger=yes`, gestor `running` y presupuesto externo 0 s. Debe repetirse
después de reconectar CA; no es una autorización de lanzamiento.

La comprobación de integridad posterior al repin está en
[`integrity-after-repin.json`](integrity-after-repin.json), SHA-256
`1da26b0a6826768cf0e0f30322b78218c729d40597772d98a976de0a25eaf13e`.
Los 2647 archivos WF05 conservaron el mapa SHA-256 del cierre, la raíz
2022 siguió ausente y el código coincidió con el registro de aprobación.

Sonda sintética de persistencia e inhibición, sin mercado:

```bash
systemd-run --user --unit=oos-wf-cost-2022-power-probe-20261106 --property=Restart=no /usr/bin/systemd-inhibit --what=sleep:idle --mode=block --why='WF 2022 synthetic host check' /usr/bin/sleep 20
systemctl --user show oos-wf-cost-2022-power-probe-20261106.service -p ActiveState -p SubState -p Result -p Restart
systemd-inhibit --list --no-pager
```

`InvocationID=f6b1c27478a446688938d7dd40591de4` al crear la unidad;
durante ella se observó `ActiveState=active`, `Restart=no` y un inhibidor
`sleep:idle` en modo `block`; después terminó `Result=success`. No se apagó
físicamente la pantalla en esta sonda.
