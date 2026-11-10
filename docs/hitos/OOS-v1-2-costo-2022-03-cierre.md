# Cierre de la medición WF 2022-03 — 10/11/2026

**Estado:** `completed`, 11/11 unidades aceptadas (Q0 y diez Q/A/B+D), `pending=null`. Es una medición de costo sobre entrenamiento de desarrollo, no una evaluación financiera. La evaluación v1.2 y los conjuntos 2023 y 2024–2025 continúan cerrados.

## Cronología y causa del reingreso

El timer transitorio previsto para las 01:00 desapareció tras un reinicio de Debian a las 01:39:29, hora de La Paz. No dejó servicio, bitácora, ledger ni Q0. La memoria estuvo primero por debajo de la guarda inicial de 6.026.846.208 B. Tras liberar aplicaciones, la captura de las 01:43 registró 8.927.412.224 B de `MemAvailable`; el preflight formal posterior registró 9.362.132.992 B, CA conectada, batería 100 %, gestor `running` y `Linger=yes`.

Se lanzó **una** sesión nueva `oos-wf-cost-2022-03-session-02.service`, `Restart=no`, `InvocationID=367e1c7feaad4a268a3f31069f35bfe7`, a las 01:43:56. La suite formal pasó con **549 pruebas** en 527,07 s; Ruff y preflight vigilado pasaron. El preflight abrió once archivos del protocolo, configuración y derivado H1 exclusivo de entrenamiento; no abrió CSV H1 compartidos ni conjuntos protegidos. Q0 comenzó después de las verificaciones. El ledger cerró `completed` a las 02:04:45 y systemd registró `Result=success` a las 02:04:46. No queda unidad WF 2022-03 activa.

## Integridad y costos

El ledger registra 11 checkpoints completos y 11 reportes. Se calcularon de nuevo los SHA-256 del estado y del reporte de cada unidad: **22/22 coincidieron** con el ledger; los 11 estados coincidieron también con sus manifiestos. El último estado `after_dual_and_D` es `artifacts/oos-v12-wf-cost-only-2022-03/wf-2022/checkpoint-10/state.pt`, SHA-256 `5740732f226667d79ede579f4be96afc71705882cb68e53c1e6eb75c5fc2ea2e`. Ledger SHA-256 `707a643073d21588cd7dab631bb3b7331946adf97714a576b5c8f0177dff7b1e`.

| Tramo | Tiempo medido |
| --- | ---: |
| Preparación, incluida suite, Ruff y preflight | 531,643 s |
| Segunda fase, incluida supervisión y 11 unidades | 716,202 s |
| Unión de ambos tramos, sin duplicar ledger ni sesión | **1.247,845 s** |
| Q0 (ledger) | 29,120 s |
| Diez actualizaciones, suma de tiempos de unidad del ledger | 681,571 s |

El cargo global del 10/11 es 1.247,845 s; bajo el límite de 10.800 s y reserva de 2.700 s, el saldo previo a reserva tras el cierre es 6.852,155 s. Esto es una conciliación de los tramos de bitácora de esta campaña; no suma otra vez los 715,096 s cargados por el ledger, porque están dentro del segundo tramo. El servicio midió 20 min 50,189 s de pared, 22 min 5,539 s de CPU y un pico de memoria de 2,1 GiB; el mayor RSS individual de trabajador registrado fue 672.198.656 B. Son métricas distintas y no deben sumarse. El preflight midió memoria y disco antes de la ejecución, no un mínimo continuo de `MemAvailable` durante toda la sesión.

Los artefactos originales de WF05, 2022-01 y 2022-02 se conservaron. El cierre de esta medición no adopta el protocolo confirmatorio v1.2 ni demuestra viabilidad total de sus 36 bloques.

## Reproducción de la auditoría

Desde la raíz del repositorio:

```bash
journalctl --user -u oos-wf-cost-2022-03-session-02.service --no-pager -o short-iso
sha256sum artifacts/oos-v12-wf-cost-only-2022-03/{ledger.jsonl,sessions.jsonl,supervisor.jsonl}
sha256sum artifacts/oos-v12-wf-cost-only-2022-03/wf-2022/checkpoint-10/state.pt
python3 -m json.tool docs/evidence/oos-wf-2022-03-relaunch-20261110/closure-summary.json >/dev/null
```

La captura reproducible con rutas, tiempos, once unidades, huellas y archivos abiertos está en `docs/evidence/oos-wf-2022-03-relaunch-20261110/closure-summary.json`; el journal y las comprobaciones previas están en el mismo directorio. La evidencia registra la pérdida del timer y el lanzamiento manual del servicio. La clave `boot_utc` de la captura inicial proviene de `uptime -s`, que imprime hora **local**; la cronología usa esa interpretación y el journal con zona `-04:00`.
