# P2R infraestructura: comandos y resultados reales (30/09–01/10/2026 La Paz)

Base comprobada: `d7f253b27ca84a9ec6b116f9965cb77bcf4c930b`; rama
`codex/p2r-infrastructure`. `.python-version` ya estaba eliminada localmente
y no se incluye en este hito. Se usó `UV_CACHE_DIR=/tmp/uv-p2r-cache` porque
el cache de uv en el home no permitía crear su lock dentro del sandbox.

## Pruebas automáticas

```text
UV_CACHE_DIR=/tmp/uv-p2r-cache uv run --frozen pytest -q tests/test_p2r_infrastructure.py
17 passed in 1.95s

UV_CACHE_DIR=/tmp/uv-p2r-cache uv run --frozen ruff check .
All checks passed!
```

La primera suite completa, antes de proteger un caso de prueba dependiente de
la hora real, dio `243 passed, 1 failed in 135.64s`: la prueba sintética
heredada `test_public_synthetic_supervisor_pauses_resumes_shared_budget`
intentó admitir Q0 a menos de una hora de la medianoche La Paz y el presupuesto
correctamente la rechazó. Se añadió un `skip` explícito solo a esa prueba
cuando no existe ventana aprobada de 3700 s; no se cambiaron topes operativos.
La siguiente suite completa dio `243 passed, 1 skipped in 129.45s`, con motivo
`real La Paz midnight leaves no approved Q0 admission window`. Tras medianoche,
la prueba heredada volvió a ejecutarse: una suite intermedia dio
`248 passed in 123.26s`. La suite final después de los últimos casos se
ejecutó con el estado final:

```text
UV_CACHE_DIR=/tmp/uv-p2r-cache uv run --frozen pytest -q
251 passed in 140.41s (0:02:20)
```

## Gestor de usuario y sondas sintéticas reales

```text
loginctl show-user "$UID" -p Linger -p State
State=active; Linger=no
systemctl --user is-system-running
running
```

Se ejecutó `systemd-run --user --collect` con `WorkingDirectory` en el
repositorio y `scripts/run_p2r.py --profile synthetic` en raíces nuevas bajo
`/tmp/p2r-systemd-probe`. Las tres sondas del 30/09 usaron `--fixture-window`
para probar señales cerca de medianoche; la última del 01/10 usó el
presupuesto diario real. `systemd-run` devolvió de
inmediato el nombre e invocation ID; el journal de usuario registró después:

| Unidad transitoria | Trabajo sintético | Resultado comprobado |
|---|---:|---|
| `p2r-final-1790826599892.service` | `sleep(3)` | inició 23:50:03, terminó 23:50:07 La Paz; `completed`, 1 unidad; eventos `supervisor_started`, `unit_started`, `heartbeat`, `unit_completed`, `supervisor_exit`; hash final del journal `f5222282309371fd62462a89780399cda2958302b66cccd0b8f2c4c8f27706ba` |
| `p2r-final-sig-1790826907126.service` | `sleep(30)` | `systemctl --user kill --kill-whom=main --signal=SIGTERM ...` durante unidad; señal 15, ledger `failed`, razón `interrupted_supervisor_or_unit`, 0 unidades aceptadas; eventos incluyen `signal`, `unit_failed`, `supervisor_exit`; hash final `9be71efe183fd88b9aeaa845e05d2168dd2d2768500cc2c1f50a8ce46af8935f` |
| `p2r-heartbeat-1790826185776.service` | `sleep(9)` | 3 heartbeats, gaps monotónicos medidos `4.008` y `4.008` s, `unit_completed` |
| `p2r-real-window-1790828796181.service` | `sleep(3)` | el 01/10, sin `--fixture-window`: ledger `completed`, 1 unidad, día La Paz `2026-10-01`, débito externo `0.0` s; hash final `f299e56af2d45f1b7ae96376f17a66f850746d10148c3df2793c7be9c0932427` |

La prueba de SIGTERM es sobre la versión final del supervisor. Hubo además
una sonda inicial `sleep(10)` que terminó antes de entregar la señal; se
descartó **solo como prueba de señal**, sin ocultarla ni contarla como fallo.
Las pruebas automatizadas separadas envían SIGTERM dentro de unidad, SIGINT
entre unidades y SIGKILL al supervisor; validan señal, ausencia de checkpoint
aceptado, muerte del worker huérfano y rechazo permanente de reentrada.

La salida del proceso lanzador no cerró la unidad transitoria. **No se cerró
la sesión completa del usuario**: `Linger=no` impide afirmar supervivencia
tras logout. No se modificó esa configuración del sistema.
El [resumen JSON](service-summary.json) conserva estados, secuencias de
eventos, gaps y SHA256 de los archivos sintéticos completos guardados fuera
de Git; omite rutas locales y datos del usuario.

## Guardas vivas e integridad heredada

Lectura local de solo disponibilidad (sin datos de mercado): AC conectada,
batería 90 %, `MemAvailable=3295506432` bytes y disco libre en la raíz del
repositorio `182004838400` bytes. `check_resources(stage='preflight')` devolvió
`Insufficient P2R memory or disk`; el umbral de RAM es 4 GiB. Los fixtures
comprobaron también 50 %/40 % de batería, sensor ausente, memoria y disco.

`sha256sum` antes y después de las sondas sobre P2 original:

```text
e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8  artifacts/p2-approved-v1/ledger.jsonl
bb2af51c8192303d062b095646a772948072e4eeb36c039f1aa8f9e0037af2b3  artifacts/p2-approved-v1/run-05-C0/progress.json
45ef6ad0421e062a7a1b150f5711cfbf07bfec8d47e5e3a72dabf2a149f6002b  artifacts/p2-approved-v1/run-05-C0/journal/events.jsonl
```

No se llamó `run_p2.py`, no se cargó `TrainingMarket` ni se generaron
trayectorias históricas. No hubo entrenamiento ni acceso a validación/final.
