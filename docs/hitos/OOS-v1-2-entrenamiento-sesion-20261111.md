# Sesión OOS v1.2 del 11/11/2026: cierre y auditoría

## Estado observado

La única sesión `oos-v12-training.service` arrancó a las 01:00:00 y terminó
a las 02:55:46 `America/La_Paz`, con `Result=success`, `Restart=no` e
`InvocationID=67732d86aae44562a2e68a34d14b2124`. El journal de systemd
registró 1 h 56 min 9,137 s de CPU y un pico de memoria de 4,6 G. No se
lanzó otra sesión. La prueba formal terminó `ready` en 537,146 s, Ruff en
0,071 s y el preflight vigilado `ready` en 1,293 s. Este último observó CA
conectada, `MemAvailable=9.254.907.904 B`, 3.639 rutas del corte 2021 y
ninguna apertura de CSV H1 compartidos ni de conjuntos protegidos.

El ledger de `wf-2021` terminó `completed`, `cursor=9`, `pending=null`: las
nueve corridas y 99 unidades previstas (tres bloques completos C0/C5/C10).
Se verificaron los 302 estados de la cadena hash y las huellas de los 99
checkpoints, 99 reportes y 99 solicitudes contra cada unidad aceptada. El
último checkpoint es
`artifacts/artifacts/oos-v12-training-wf-2021-01/run-08-C5-b0/checkpoint-10/state.pt`,
SHA-256 `864ad767592ca4bf99a53e8c5cd696d3eab1968a226ace5fa74aae222a301774`.
El ledger tiene SHA-256
`811f7456a08ed74a53c2be2d39efa56de0dbb49f3e42f033dd30a630502798b4`.
No existe ledger de `wf-2022` ni del entrenamiento principal. A las 02:55:44,
el lanzador rechazó comenzar las comprobaciones de `wf-2022` porque no cabían
suite, Q0 y reserva de cierre; no fue un fallo de unidad.

## Tiempo y presupuesto

La primera bitácora de preparación cubre 6.941,899 s (01:00:01–02:55:43);
el intento de admisión del siguiente perfil, 0,264 s. Su unión carga
**6.942,163 s** globales el 11/11. El ledger propio midió 6.401,296 s,
contenido dentro de la bitácora: no se suma otra vez. Quedaban
**1.157,837 s antes de la reserva de cierre de 2.700 s**, insuficientes
para la admisión de 900 s de preparación más 1.800 s para Q0. La bitácora
de preparación tiene SHA-256
`f372dc56f36e41e8e3948ecccc4d45ebf8f251d32c4ff1f13d39034fed3a915d`;
la de comprobaciones,
`1b765cc04abaa3f3f55af93552ea42dfc319121504e56ffa4a3d3e65bda1ab74`.

## Desviación detectada y medida conservadora

El protocolo congeló la raíz `artifacts/oos-v12-training-wf-2021-01`, pero
`CAMPAIGNS` antepone otro `artifacts` a esa ruta ya relativa. La ejecución
real escribió en `artifacts/artifacts/oos-v12-training-wf-2021-01`. Por ello
el supervisor tomó su bloqueo y contabilidad de unidades en el directorio
anidado, separado del bloqueo global de `artifacts/shared-pilot-budget`.
La bitácora principal sí midió el intervalo completo y no había otra
campaña activa; el cargo global observado quedó debajo de 10.800 s y
conservó la reserva. Sin embargo, **la admisión por unidad no satisfizo
literalmente la ruta de presupuesto compartido congelada**. Los nueve
resultados son unidades técnicamente aceptadas por su ledger, pero esta
desviación requiere adjudicación antes de incorporarlos sin salvedad al
análisis previsto. No se movió, reescribió ni reanudó ningún artefacto.

Se deshabilitó `oos-v12-training.timer` durante la sesión, sin afectar el
servicio activo, para impedir una ejecución desatendida posterior con la
misma desviación. Tras el cierre: servicio `inactive`, timer `disabled`.
El timer separado de restauración de la preferencia de suspensión continúa
programado para el 16/11 a las 09:05. Antes de otra sesión se necesita una
corrección prospectiva de rutas y de la contabilidad compartida, pruebas,
huella de código/permiso coherente y un preflight nuevo. El corte 2021 no
debe repetirse ni migrarse alterando el ledger. Validación 2023 y prueba
final 2024–2025 siguen cerradas. Esto es entrenamiento, no evaluación fuera
de muestra ni demostración de rentabilidad o de cumplimiento de CVaR.

## Comprobaciones de solo lectura ejecutadas

```bash
systemctl --user show oos-v12-training.service -p ActiveState -p Result
journalctl --user -u oos-v12-training.service --since '2026-11-11 01:00:00' -o cat --no-pager
uv run --frozen python -  # auditoría de bitácoras y presupuesto
PYTHONPATH=src python3 -  # cadena del ledger y SHA-256 de 99 checkpoints/reportes/solicitudes
systemctl --user is-enabled oos-v12-training.timer
```

Los dos fragmentos Python se ejecutaron como heredocs de lectura; sus
resultados resumidos figuran arriba. La suite y Ruff los ejecutó el mismo
servicio, antes de entrenar, y sus estados/duraciones proceden de
`artifacts/shared-pilot-budget/oos-v12-training-checks.jsonl`. El journal,
las bitácoras, el ledger y los checkpoints originales permanecen en
`artifacts/` y no se incorporan a Git.
