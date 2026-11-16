# P2R — corrección de cadencia y sonda sintética breve 03

**Resultado acotado:** la sonda `p2r-heartbeat-q0-short-03.service` completó
una Q0 sintética con ledger `ready`, checkpoint `after_q0` íntegro y
`Result=success`. Sus **seis intervalos registrados** entre siete heartbeats
fueron ≤5 s: 4.127028, 4.131622, 4.131786, 4.136031, 4.140046 y
4.143739 s por UTC (máximo monotónico 4.143721709 s). El resultado valida
esta corrida breve en este host; no demuestra una garantía temporal para
trabajo histórico o bajo cualquier carga. No hubo logout ni prueba de señal.

## Causa y cambio

La sonda 02 había registrado 174/174 intervalos >5 s, con máximo
5.212391 s. `run_synthetic_units` esperaba **5 s completos** desde el
heartbeat anterior antes de intentar otro. `supervise` sondea cada 0.2 s;
leer estado/recursos y escribir con `fsync` añade tiempo. El parámetro
`heartbeat_seconds=5` era una **espera programada**, no un límite del
intervalo efectivamente registrado. La prueba de regresión reprodujo el
defecto antes de cambiar código: 5.012508 y 5.015442 s.

`run_fixture_unit` ya programaba `min(heartbeat_seconds, 4.0)`, por lo que
dejaba margen. Se alineó únicamente `run_synthetic_units` con esa decisión:
el valor máximo aceptado por la API sigue siendo **5 s**, pero la siguiente
emisión se solicita a los 4 s como máximo. Además, tras escribir cada
heartbeat, el código compara las marcas monotónicas **registradas** por
`P2RJournal`: si el intervalo supera 5 s o retrocede, invalida la unidad y
conserva ledger, journal y parciales. Una pausa de sondeo inyectada en prueba
produjo ese fallo permanente; no se aceptó checkpoint. No se cambiaron Q/A/B,
datos, recompensa, presupuestos ni umbrales del protocolo.

La vigilancia no convierte el tiempo real en determinista: una desplanificación
del proceso o latencia de disco aún podría crear un intervalo >5 s. En ese
caso el resultado debe ser **fallo**, no una redefinición del límite. La
comprobación mide marcas del journal; la durabilidad de cada escritura puede
añadir tiempo después de la marca, que se refleja al llegar al siguiente
heartbeat. El último tramo hasta el cierre se informa por separado.

## Sonda ejecutada (UTC)

Se ejecutó **una sola** unidad nueva, raíz
`artifacts/p2r-synthetic-heartbeat-q0-short-03`, perfil `synthetic`, modo
`algorithm`, `--hold-seconds 25`, `--max-units 1`, commit de código
`40bbd93113b3b32dc11d09f7d9f75c6f578df462`. El `InvocationID` fue
`0f328e5678ee4ab49ea8ded6f8c1c16b`. Preflight de recursos: `ready`;
gestor `running`, unidad previamente `not-found`, sin otra unidad P2R activa.
El bloqueo/presupuesto compartido informó cero segundos externos para el día.

| Marca | Hora UTC / resultado |
| --- | --- |
| Prelaunch | 19:03:26; raíz y unidad nuevas. |
| Inicio Q0 | 19:03:38.731345. |
| Primer heartbeat | 19:03:38.741432, 0.010087 s tras inicio. |
| Último heartbeat | 19:04:03.551684. |
| Último heartbeat → fin Q0 | 2.434755 s. |
| Cierre | Q0 `after_q0`, ledger `ready`, `Result=success`; systemd informó 4.566 s de CPU y pico de memoria de 388.3 MB. |

Los seis pares completos de marcas UTC, diferencias UTC y monotónicas están
en [intervals.json](../evidence/p2r-heartbeat-cadence-03/intervals.json).
La cadena `P2RJournal` pasó, todos los eventos usaron el mismo
`InvocationID`, el ledger aceptó una sola Q0 con 2 trayectorias y 360
transiciones, cero actualizaciones actor/crítico y cero trayectorias D. El
hash de `state.pt` coincidió con el manifiesto y el ledger. Se comprobó el
estado final inactivo de la unidad y `Result=success`.

## Verificación y conservación

- Prueba de regresión antes del cambio: falló como se esperaba con intervalos
  >5 s. Prueba con pausa de sondeo de 5.2 s: el caso de fallo permanente pasó
  tras la corrección. La prueba de `run_fixture_unit` comprobó sus intervalos
  reales con el margen previo de 4 s.
- `uv run --frozen pytest -q tests/test_p2r_units.py tests/test_p2r_infrastructure.py`:
  **28 passed**. `uv run --frozen pytest -q`: **266 passed**.
  `uv run --frozen ruff check .`: **All checks passed**. Se usó
  `UV_CACHE_DIR=/tmp/uv-cache-btc-p2r` porque la caché habitual de uv era
  de solo lectura en el entorno de herramientas.
- [SHA256SUMS.txt](../evidence/p2r-heartbeat-cadence-03/SHA256SUMS.txt) cubre
  18 archivos de la raíz y registro nuevos; `sha256sum -c` dio 18/18.
  Se revalidaron 32/32 hashes de la sonda 02 y las cuatro huellas principales
  de la sonda 01, sin editar sus archivos. La eliminación local previa de
  `.python-version` quedó fuera del commit.

El [registro de comandos](../evidence/p2r-heartbeat-cadence-03/COMMANDS.md)
separa pruebas, preflight, lanzamiento y auditoría. La Q0 usa rutas
`SyntheticMarket` y perfil `p2_synthetic_tests_only`: no se cargaron datos
históricos, validación ni prueba final, ni se ejecutó P2R histórico.

## Implicación para la tesis y pendientes

Se puede describir que **esta sonda sintética breve** mantuvo los intervalos
registrados bajo 5 s y que la guarda rechaza un intervalo tardío inducido.
No se debe presentar como rendimiento de entrenamiento, generalización,
cumplimiento CVaR ni garantía ante apagado/suspensión del host. Sigue
pendiente revisar y adoptar el protocolo P2R, completar la sonda separada
de señal durante unidad (no autorizada en este hito), integrar y verificar
un ejecutor histórico train-only con huellas y preflight propios, y obtener
autorización explícita para una campaña histórica nueva. P2 fallido no se
reanuda; P0/P1 y las sondas 01/02 se conservan.
