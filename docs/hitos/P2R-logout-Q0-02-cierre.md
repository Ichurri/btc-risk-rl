# Cierre de la prueba de logout P2R Q0 sintética 02 — 05/10/2026

**Resultado de esta prueba: aprobado para continuidad Q0 tras logout completo
y ausencia de suspensión hasta el reingreso.** La unidad
`p2r-logout-q0-review-02.service` llegó a `ready`, `Result=success` y
checkpoint íntegro `after_q0` durante un intervalo sin sesión interactiva.
El journal de logind obtenido con `sudo` no contiene anuncios ni finales de
suspensión entre la retirada de la sesión 40 y la creación de la 54. El
`InvocationID` de todos los eventos del journal P2R es
`bd87136bed89438db7f419ba98308285`. Este resultado cierra **solo** la
sonda sintética 02; no autoriza una campaña histórica P2R.

## Cronología verificada (UTC)

| Hora | Hecho y fuente |
| --- | --- |
| 15:53:10 | Prelaunch: commit `918c1d0b23ceb440d0a715d49a63a00df56447ee`, unidad y raíz ausentes, `Linger=yes`, gestor `running`, AC, batería 98 %, `MemAvailable=6843150336` bytes y disco libre `184660746240` bytes. |
| 15:54:31 | Servicio iniciado bajo el gestor del usuario, PID principal 40734 y cgroup propio. |
| 15:54:32.743779 | `unit_started` de Q0 sintética en el journal P2R. |
| 15:57:37.582970 | logind retiró la última sesión interactiva registrada antes de la prueba, la 40. La sesión 3 `Class=manager` permaneció por `Linger=yes`. |
| 15:57:37.697135 | logind creó una sesión de greeter `Debian-gdm`. |
| 15:57:38.000084–16:09:31.407840 | 139 heartbeats del mismo `InvocationID` sin sesión interactiva. |
| 16:09:34.879911 | `unit_completed` en `after_q0`: 2 trayectorias, 360 transiciones, cero actualizaciones de actor/crítico y cero trayectorias D. |
| 16:09:34.889259 | `supervisor_exit` en frontera entre unidades; ledger final `ready`, sin unidad pendiente. El servicio acabó con `Result=success`. |
| 16:51:58.504184 | logind creó la primera sesión interactiva nueva, la 54. |

El intervalo completo sin sesión interactiva fue **3260.921214 s**
(54 min 20.921 s), más largo que el antiguo umbral de 900 s. Los
heartbeats cubren la parte en que Q0 estaba activa; **no** hay heartbeats
entre la salida normal del supervisor y el nuevo ingreso, porque la unidad
ya había terminado. La ausencia de suspensión en ese tramo se establece por
el journal de logind, no por extrapolación de heartbeats. Las comprobaciones
de la sección C dieron `suspension_events_during_logout=0` y
`heartbeats_without_interactive_session=139`. El journal de la unidad y
`after-unit.txt` respaldan `Result=success`.

La configuración visible del greeter en el preflight tenía
`sleep-inactive-ac-timeout=0` y `sleep-inactive-battery-timeout=0`, SHA-256
`61ab39f3c987ffad3d4389cbb467b8e54d5d41aaa37a6d02e21fe214fa6845a0`.
La prueba muestra ausencia de suspensión durante este logout; no identifica
retrospectivamente el llamador de la suspensión de la prueba 01 ni prueba
que el ajuste sea eficaz ante cualquier otra fuente de suspensión.

## Integridad y conservación

Se releyeron el ledger, manifiesto y journal P2R originales **sin
modificarlos**. La cadena del journal pasó `P2RJournal`, los eventos
corresponden a un único `InvocationID`, el ledger terminó `ready` con una
sola Q0 aceptada y sin `pending`, y el hash de `state.pt` coincide tanto con
el manifiesto como con el ledger. El checkpoint declara perfil
`p2_synthetic_tests_only`, condición C5 y frontera `after_q0`. El perfil
no accedió al histórico, validación ni prueba final.

| Archivo original | SHA-256 |
| --- | --- |
| `artifacts/p2r-synthetic-logout-q0-review-02/ledger.jsonl` | `0c64a16f540ecc612ad513d5dc1bf14f50b4cf3123562b8147ae09a3a650a079` |
| `artifacts/p2r-synthetic-logout-q0-review-02/supervisor.jsonl` | `1f3ba6e6965ce4a8d4076a23196e111c0ed477c98f65351ce539e7338abbb84e` |
| `artifacts/p2r-synthetic-logout-q0-review-02/run-00-C5/checkpoint-0/manifest.json` | `a1e66073bc485659a3e75e27cf9169ee69070829e05730bea252bc09194170b4` |
| `artifacts/p2r-synthetic-logout-q0-review-02/run-00-C5/checkpoint-0/state.pt` | `1a34914c8d6a923dfd4cc646e6992cb088d1d4ec8446c236238276395d6d0b74` |
| `artifacts/p2r-logout-q0-review-02-record/logind-journal.txt` | `a23f076bb27363e232ef4646dfa300ec31e870569c3a72f20ab06dd7a535ee12` |
| `artifacts/p2r-logout-q0-review-02-record/systemd-journal.txt` | `5fcc33130a4d428c4dac92f724fe9923b429c9a5b870f62dc88883aceefe4d30` |

El [manifiesto completo de 32 archivos](../evidence/p2r-logout-q0-02/SHA256SUMS.txt)
incluye también prelaunch, registros de sesiones, comprobaciones y logs del
worker. Las dos raíces locales 02 y las raíces 01 quedan intactas fuera de
Git; solo sus hashes y el informe se versionan. No se reutilizará la unidad
ni la raíz 02.

## Límite técnico observado y requisitos pendientes

La prueba **no valida el límite de heartbeat ≤5 s** del protocolo P2R: los
174 intervalos entre los 175 heartbeats de esta Q0 midieron más de 5 s
(mínimo 5.033190 s, mediana 5.179871 s, máximo 5.212391 s). El código
actual de `p2r_units.py` espera el umbral de 5 s y además sondea cada 0.2 s;
esa combinación explica un sobrepaso pequeño y sistemático, que debe
corregirse y comprobarse sintéticamente antes de un permiso histórico. No
se cambió el algoritmo en este cierre. El logro de logout/no suspensión se
mantiene, pero el preflight histórico **no está completo**.

Antes de ejecutar una campaña histórica P2R siguen pendientes:

1. Revisar y adoptar explícitamente el protocolo científico P2R v1 y su
   addendum; registrar una autorización de mercado propia en commit separado.
   La autorización sintética y el permiso P2 fallido no la sustituyen.
2. Implementar y verificar el ejecutor histórico **train-only** de las nueve
   corridas completas, con perfil/permiso separados, AcceptedMarket e índices
   H1, huellas congeladas de código, configuración, datos y normalizador,
   corrección del metadato heredado `market_training_executed=false`, y
   equivalencia Q/A/B+D y reanudación desde ambas fronteras completas.
3. Corregir y verificar la cadencia de heartbeat ≤5 s; completar la sonda
   sintética separada de señal durante unidad prevista en el procedimiento
   del host. Ninguna sonda de logout garantiza continuidad ante apagado físico.
4. En la fecha de ejecución, comprobar integridad de P0/P1 y del ledger P2
   fallido, ausencia de otra campaña, `Linger=yes`, configuración del greeter,
   alimentación y batería, RAM/disco mínimos, saldo global de 3 h/día en
   America/La_Paz, reserva y topes de unidad. Usar raíz y unidad históricas
   nuevas; no reanudar ni mezclar los artefactos P2.

Esta sonda no midió ajuste del crítico, rentabilidad, generalización,
validación 2023, prueba final ni cumplimiento poblacional de CVaR. Tampoco
probó las unidades Q/A/B+D históricas. No se lanzó otra prueba ni se realizó
ninguna actualización de aprendizaje en este cierre documental.
