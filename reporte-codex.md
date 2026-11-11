# Estado en ejecución — 11/11/2026 11:30 America/La_Paz

- Rama `codex/oos-v12-expanded-budget`, commit `fef5d74`; enmienda `b86ea47`, código `20c3e96`, permiso v3 `8860fb9`.
- Suite manual: 587 passed en 570,02 s; Ruff correcto. Preflight manual vigilado `ready`, CA conectada, batería 98 %, `MemAvailable=6.868.131.840 B`, 4.678 rutas `wf-2022`, sin aperturas protegidas. Evidencia: `docs/evidence/oos-v12-expanded-20261111/preflight.json`.
- Una sesión `oos-v12-training.service` inició el 11/11 a las 11:28:14, `InvocationID=097bd51bfa774984a3913721e364f67e`, `Restart=no`. A las 11:29 estaba en la suite formal interna, sin ledger ni Q0 de `wf-2022`. No duplicar el lanzamiento.
- Presupuesto ampliado: 50.400 s globales por fecha y 2.700 s de reserva; hoy se cargan 10.800 s previos conservadores (6.942,163 s medidos + 3.857,837 s de ajuste). Antes de esta sesión quedaban 36.900 s productivos; la bitácora cobrará su tiempo nuevo.
- `wf-2021`: 99/99 unidades y 9/9 corridas íntegras, raíz histórica conservada; exclusividad del bloqueo original no demostrada. `wf-2022`: 0/99 al iniciar; principal: 0/1188.
- Próxima acción: esperar suite, Ruff y preflight internos; auditar Q0, unidades, ledger y checkpoint al cierre. Si bloquea recursos, no iniciar unidad; si falla dentro de una unidad, no reanudar. Timer diario siguiente 12/11 01:00.
- Validación 2023 y prueba final 2024–2025 siguen cerradas.

---

# Continuación preparada — 11/11/2026, 08:50 America/La_Paz

- Rama `codex/oos-v12-training-root-fix`; código `1dcff09`, nueva
  aprobación `dbffdf6`. `.python-version` sigue eliminada solo localmente.
- Se corrigieron las tres raíces para que coincidan con el protocolo y
  preparación/supervisor compitan por el mismo `global.lock`. Las dos
  pruebas de regresión fallaron antes del cambio y pasaron después;
  suite completa **585 passed en 539,80 s**, dos advertencias de `fork`
  sintético, Ruff sin errores. Permiso v2 SHA-256
  `ef601eb95df48e3f3376b11d61eb64328914b225c43927c7e8baa12142f5c806`;
  huella de código `662edcea4367ea8a6f470cbb0a64ab25f0827585f55f0ccfc1fc7d159aa70177`.
- `wf-2021`: ledger original en `artifacts/artifacts/` **intacto**,
  9/9 corridas, 3/3 ternas, 99/99 unidades; cadena y las 99 huellas de
  checkpoints/reportes/solicitudes verificadas. Último checkpoint:
  `artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10/state.pt`,
  SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
  Las 99 unidades habrían cabido con la reserva en la reconstrucción
  conservadora; margen mínimo 1.128,211 s. **Integridad aceptada, uso como
  prueba de cumplimiento estricto del supervisor pendiente de revisión.**
  No repetir ni migrar el corte.
- `wf-2022`: ninguna unidad iniciada; es independiente de los pesos y
  checkpoints de 2021. El selector lo identifica como próximo perfil.
  Timer habilitado para **12/11/2026 01:00 America/La_Paz**, servicio ahora
  inactivo, `Restart=no`. Suite, Ruff, preflight vigilado y admisión con
  saldo/reserva se repetirán en esa ventana; si falla una puerta, no se
  inicia Q0. El contador automático del 11/11 no incluye la suite manual
  posterior de 539,80 s ni todo el trabajo de desarrollo: no usarlo para
  admitir más unidades hoy.
- Informe, comandos y evidencia:
  `docs/hitos/OOS-v1-2-entrenamiento-ruta-presupuesto-20261111.md` y
  `docs/evidence/oos-v12-training-root-fix-20261111/`.
  **Próxima acción:** auditar el servicio del 12/11, ledger y último
  checkpoint completo; conservar 2023 y la prueba final cerrados.

---

# Reporte automático — 11/11/2026 08:47 America/La_Paz

- Rama `codex/oos-v12-training-root-fix`, commit `dbffdf6`.
- `wf-2021`: raíz histórica íntegra `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01`; conservada sin migración ni repetición.
- `wf-2021`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
- `wf-2021`: cargo propio medido en ledger 6401.296 s; última unidad 71.336 s.
- Último checkpoint `wf-2021`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
- `wf-2022`: sin ledger; no se inició una unidad.
- `main-2018-2022`: sin ledger; no se inició una unidad.
- Bitácora de comprobaciones: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl`; SHA-256 `f372dc56f36e41e8e3948ecccc4d45ebf8f251d32c4ff1f13d39034fed3a915d`.
- Presupuesto global del día: 6942.163 s cargados; 1157.837 s antes de la reserva de cierre de 2.700 s. Puerta: ready.
- Validación 2023 y prueba final 2024–2025 permanecen cerradas.
- Siguiente acción: consultar el ledger y el journal de `systemd --user`; reanudar solo un estado `ready` en la siguiente ventana con suite, Ruff, preflight vigilado y admisión nuevos. Un estado `failed`/`incomplete` no se reanuda.

---

# Cierre auditado — 11/11/2026, 02:56 America/La_Paz

- Rama `codex/oos-v12-training-prep`, base publicada `a5eef29`, código
  `1ce1382` y permiso `cbd11de`. La eliminación local de `.python-version`
  permanece fuera de los commits.
- `oos-v12-training.service` terminó `Result=success` a las 02:55:46,
  `InvocationID=67732d86aae44562a2e68a34d14b2124`. No queda servicio
  de entrenamiento activo. Suite formal, Ruff y preflight vigilado pasaron;
  este último confirmó CA, 9.254.907.904 B de memoria disponible, 3.639
  rutas 2021 y ninguna apertura protegida.
- `wf-2021`: **9/9 corridas, 3/3 ternas C0/C5/C10 y 99/99 unidades**;
  ledger `completed`, `pending=null`. La cadena de 302 estados y las 99
  huellas de checkpoints, reportes y solicitudes coincidieron. Último
  checkpoint válido:
  `artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10/state.pt`,
  SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
  Ledger SHA-256 `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
  `wf-2022` y el perfil principal siguen sin iniciar.
- Cargo global del 11/11: **6.942,163 s**, incluidos preparación y unidades
  sin duplicar los 6.401,296 s del ledger. Saldo antes de la reserva de
  2.700 s: **1.157,837 s**. A las 02:55 se bloqueó el comienzo de `wf-2022`
  porque no cabían suite, Q0 y cierre; no fue un fallo de unidad.
- **Desviación de ruta:** el protocolo fija `artifacts/oos-v12-training-*`,
  pero el código escribió el corte 2021 en `artifacts/artifacts/oos-v12-training-*`.
  Por ello el supervisor de unidades usó otro bloqueo/presupuesto compartido.
  La bitácora principal sí midió la sesión completa y el cargo quedó dentro
  del límite global, pero la admisión por unidad no fue la ruta congelada.
  Se deshabilitó el timer nocturno, sin interrumpir esta sesión. Los artefactos
  originales se conservan; **no repetir ni migrar el corte 2021**.
- **Siguiente acción:** adjudicar la desviación, corregir prospectivamente
  ruta/contabilidad con pruebas y nueva huella de permiso, y solo entonces
  reactivar el timer para una ventana futura con preflight nuevo. Validación
  2023 y prueba final 2024–2025 siguen cerradas. Detalle y comandos:
  `docs/hitos/OOS-v1-2-entrenamiento-sesion-20261111.md`.

---

# Reporte automático — 11/11/2026 02:55 America/La_Paz

- Rama `codex/oos-v12-training-prep`, commit `a5eef29`.
- `wf-2021`: ledger `completed`, 99 unidades aceptadas, cursor 9, pending=False; SHA-256 ledger `811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
- `wf-2021`: cargo propio medido en ledger 6401.296 s; última unidad 71.336 s.
- Último checkpoint `wf-2021`: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10`; estado SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
- `wf-2022`: sin ledger; no se inició una unidad.
- `main-2018-2022`: sin ledger; no se inició una unidad.
- Bitácora de comprobaciones: `/home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/shared-pilot-budget/oos-v12-training-preflight.jsonl`; SHA-256 `f372dc56f36e41e8e3948ecccc4d45ebf8f251d32c4ff1f13d39034fed3a915d`.
- Presupuesto global del día: 6942.163 s cargados; 1157.837 s antes de la reserva de cierre de 2.700 s. Puerta: ready.
- Validación 2023 y prueba final 2024–2025 permanecen cerradas.
- Siguiente acción: consultar el ledger y el journal de `systemd --user`; reanudar solo un estado `ready` en la siguiente ventana con suite, Ruff, preflight vigilado y admisión nuevos. Un estado `failed`/`incomplete` no se reanuda.

---

# Reporte Codex — 10/11/2026, 10:57 America/La_Paz

- Rama `codex/oos-v12-training-prep`; código `1ce1382`, permiso de
  entrenamiento exclusivo `cbd11de`. `.python-version` sigue borrada solo
  localmente y fuera de los commits.
- La suite final pasó **576 pruebas en 573,22 s** (dos advertencias del
  `fork` sintético); Ruff pasó. Comprobación de fuentes de solo lectura:
  3.639/4.678/7.048 inicios, solo derivado H1 de entrenamiento y
  manifiesto H1 compartido. No se generaron trayectorias ni se entrenó.
- Timer `oos-v12-training.timer` habilitado, próximo disparo
  **11/11/2026 01:00 America/La_Paz**; servicio `oos-v12-training.service`
  inactivo y tres raíces de campaña ausentes. No hay unidad OOS aceptada.
  El servicio tiene `Restart=no` e inhibición de sueño; con CA se cambió la
  preferencia GNOME de suspensión automática de `suspend` a `nothing`.
  El timer `oos-v12-restore-power.timer` restaurará `suspend` el
  **16/11 a las 09:05** (`Persistent=true`); verificar el cierre.
- Captura 10:57: CA=1, batería 98 %, `MemAvailable=5.536.272.384 B`
  frente al mínimo inicial 6.026.846.208 B, disco 125,79 GB,
  `systemd --user=running`, `Linger=yes`. La memoria debe volver a superar
  el umbral en el preflight nocturno; con la captura actual se bloquearía.
- Presupuesto medido 10/11: WF 2022-03 cargó **1.247,845 s**; saldo antes
  de reserva 6.852,155 s. Para 11–16/11 hay como máximo 48.600 s
  productivos suponiendo saldo íntegro. Extrapolación: 16 ternas como
  techo sin gasto adicional, 14/13 con 500/900 s diarios supuestos. No
  implica que estén entrenadas; el roster conserva las 36 previstas.
- Evidencia: `docs/hitos/OOS-v1-2-entrenamiento-preparacion.md`,
  `docs/evidence/oos-v12-training-prep-20261110/`,
  `docs/protocols/OOS-v1-2-training-freeze-20261110.json` y aprobación
  `docs/protocols/OOS-v1-2-training-approval-20261110.json`.
- Siguiente acción: a la 01:00, el servicio repite suite, Ruff y preflight
  vigilado; solo con `ready`, CA, memoria, presupuesto y admisión inicia
  Q0. Tras la sesión, auditar ledger, journal y checkpoint. Un estado
  `failed`/`incomplete` no se reanuda. Validación 2023 y prueba final
  2024–2025 permanecen cerradas.

---

# Reporte anterior — 10/11/2026, 02:10 America/La_Paz

- Rama `codex/oos-wf-2022-03`, base publicada `69aaf80` al iniciar. `.python-version` sigue eliminada solo localmente.
- El timer de 01:00 desapareció tras reinicio a 01:39:29; no produjo intento ni Q0. Tras liberar memoria se repitieron guardas (8.927.092.736 B en captura inicial; 9.362.132.992 B en preflight formal; mínimo 6.026.846.208 B).
- Una sola sesión `oos-wf-cost-2022-03-session-02.service`, `InvocationID=367e1c7feaad4a268a3f31069f35bfe7`, se inició 01:43:56 y terminó 02:04:46 con `Result=success`, `Restart=no`. No hay proceso WF activo.
- Suite formal **549 passed en 527,07 s**, Ruff y preflight vigilado `ready`. Ledger `completed`, **11/11** unidades, `pending=null`: Q0 y diez Q/A/B+D. Los 11 checkpoints y 11 reportes coinciden con las huellas del ledger. Último checkpoint `artifacts/oos-v12-wf-cost-only-2022-03/wf-2022/checkpoint-10`, estado SHA-256 `5740732f226667d79ede579f4be96afc71705882cb68e53c1e6eb75c5fc2ea2e`.
- Preparación 531,643 s, segunda fase 716,202 s; cargo total reconciliado **1.247,845 s**, saldo global **6.852,155 s antes de la reserva de 2.700 s**. Servicio: pared 20 min 50,189 s, pico de memoria 2,1 GiB. No sumar la duración del servicio ni el ledger otra vez al cargo de la bitácora.
- Evidencia: `docs/hitos/OOS-v1-2-costo-2022-03-cierre.md`, `docs/evidence/oos-wf-2022-03-relaunch-20261110/` y artefactos originales en `artifacts/oos-v12-wf-cost-only-2022-03/`. No se abrió validación ni prueba final.
- Siguiente acción: recalcular el calendario de evaluación v1.2 con el costo medido y resolver la prórroga y los cambios académicos antes de congelar el protocolo. La evaluación confirmatoria sigue cerrada; WF05, `2022-01` y `2022-02` no se reanudan.

---

# Reporte anterior — 09/11/2026, 13:06 America/La_Paz

- Rama `codex/oos-wf-2022-03`. Base `85a08b9`; diagnóstico `6548215`, perfil `9ba423f`, primer permiso sin uso `d0f024c`, corrección `87c544c`, permiso final `3aa8aeb`. La eliminación local de `.python-version` sigue fuera de los commits.
- `2022-02` permanece `failed`: Q0 e iteraciones 1–7 aceptadas (8/11), unidad 8 parcial por `MemAvailable=4.278.210.560 B` (<4 GiB). Último checkpoint completo `artifacts/oos-v12-wf-cost-only-2022-02/wf-2022/checkpoint-7`, estado SHA-256 `618f9b45c42cf7e0976c1b8d6caadde39fddcfe1586a1173f3a5506295c9b0e1`. Ledger, sesión y supervisor conservaron sus huellas; no se reanuda ni repite. WF05 y `2022-01` siguen cerrados.
- Sondas sintéticas de memoria de duración representativa: 04 cruzó 4 GiB durante suite; 05 duró 1127,131 s y sostuvo mínimo 4.870.426.624 B, solo 38.588.416 B sobre 4 GiB + 512 MiB. La causa externa exacta de la caída histórica sigue desconocida. Informe: `docs/hitos/OOS-v1-2-costo-2022-02-memoria-diagnostico.md`.
- Perfil nuevo `2022-03`: una C10, semilla 498614892, Q0 + diez Q/A/B+D, raíz exclusiva `artifacts/oos-v12-wf-cost-only-2022-03/` aún **ausente**. Puerta inicial de memoria 6.026.846.208 B; guarda de 4 GiB durante unidades sin cambio. La aprobación final SHA-256 es `c72292883224c50f86f0ae6a27b2ee6e4aaeed3ee548751cd81f3ac7f7ce73d4`, código `89f9aae6490778170a50aa65596b836ab9dd507447bc526ca34be4adab61bf33`.
- Pruebas realmente ejecutadas: suite completa bajo `systemd --user`/bloqueo global/inhibición de sueño **549 passed en 534,82 s**, focal con permiso final **44 passed en 97,88 s**, `uv run --frozen ruff check .` correcto. Dos suites sintéticas intermedias se detuvieron al detectar guardas incompletas; sus journals se conservan. No hubo entrenamiento `2022-03` ni acceso a validación o prueba final.
- Presupuesto: 09/11 tiene 10.800/10.800 s globales cargados conservadoramente por el fallo `2022-02`, saldo 0. Para 10/11, la instantánea de solo lectura muestra 0 s externos y 8.100 s antes de reserva, sujeto a comprobación nueva. Límites `2022-03`: 3.600 s propios/día, 4.800 s acumulados, dos días activos, reservas propias/globales 600/2.700 s; ventana 01:00–09:00 La Paz.
- Estado de sesión: timer `oos-wf-cost-2022-03-session-01.timer` **active/waiting** para 10/11/2026 01:00 La Paz; servicio `Restart=no`, aún sin `InvocationID` ni unidades. La captura `docs/evidence/oos-wf-2022-03-memory/timer-scheduled-20261109.txt` tiene SHA-256 `2ca6c3e4c789d3f9150ff044b9057ad6cb16b7d063e4b1cd50136b06c0e328b1`. El equipo debe permanecer encendido y sin suspensión hasta el disparo; el servicio inhibe suspensión después.
- Captura de recursos de 09/11 13:04: CA=1, batería=94 %, gestor `running`, `Linger=yes`, `MemAvailable=5.054.701.568 B` (inferior a la nueva guarda inicial), disco disponible 126.937.419.776 B. No anticipa los valores de la noche. Si la memoria sigue baja o alguna puerta falla, no se inicia una unidad de mercado.
- Siguiente acción: al disparar el timer, `--prepare` abre bitácora y ejecuta suite, Ruff, preflight vigilado y admisión con reservas; solo después `--run` puede comenzar Q0. Auditar `systemctl --user show oos-wf-cost-2022-03-session-01.service`, su journal, `artifacts/shared-pilot-budget/wf-2022-only-03-{attempts,checks}.jsonl` y, si existe, el ledger/checkpoint. Un estado `failed` no se reanuda. La evaluación v1.2 sigue sin adoptar; validación 2023 y prueba final permanecen cerradas.
