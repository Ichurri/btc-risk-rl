# P2R — aislamiento físico de entrenamiento y señal durante optimizador

**Estado:** infraestructura y sonda sintética para revisión; campaña P2R
bloqueada. Base `93515ef`, código `50ce691`, rama
`codex/p2r-historical-executor`. No se
ejecutaron unidades ni actualizaciones con histórico, y no se consultaron
observaciones de validación ni la prueba final en este hito.

## Integridad sin abrir CSV compartidos

El preflight y el trabajador P2R usan ahora el contrato de
[derivado exclusivo de entrenamiento](../protocols/P2R-training-shard-contract-v1.md).
La prueba de vigilancia de aperturas intercepta `open` y falla si se toca
uno de los cinco CSV H1 compartidos. En el repositorio real, con la
huella del derivado aún sin registrar, `inspect_preflight()` rechazó antes
de abrir **cualquier** archivo de `data/processed/segmented-B-h1`. Con un
H1 **sintético** y un derivado sintético registrado durante el test, abrió
el manifiesto padre y los siete archivos y manifiesto del derivado;
ningún CSV compartido. El [rastro original](../evidence/p2r-training-shard/access-trace.txt)
enumera cada archivo. Las pruebas rechazan alteración de hash y enlaces
simbólicos o duros a un CSV compartido antes de abrirlo.

El producto histórico actual **impide** un preflight positivo bajo la
regla de cero lectura física de archivos con filas 2023. El derivado y su
auditoría de exportación quedan pendientes; no se debilitaron los hashes
H1 ni se sustituyó la relación H1→derivado por una afirmación no
verificada. P2R mantiene `TRAIN_SHARD_MANIFEST_SHA256=None`,
`MARKET_EXECUTION_ENABLED=False` y `REGISTRATION_SHA256=None`.

## Sonda sintética de cálculo del optimizador

Se conservaron las raíces nuevas 07 y 08 fuera de Git y se versionaron
resúmenes y artefactos pequeños. La 07 alcanzó el cálculo, pero el
envoltorio de la sonda devolvió 0 pese al ledger `failed`; el controlador
la señaló como fallo de su expectativa. El [diagnóstico 07](../evidence/p2r-optimizer-signal-07/diagnostic.json)
conserva el resultado y sus hashes. Se corrigió **solo** la salida del
envoltorio y se ejecutó la 08 con raíz nueva.

| Evento de sonda 08 | UTC 06/10/2026 |
| --- | --- |
| Q0 aceptada en `after_q0` | 16:45:29.606915 |
| Unidad 1 Q/A/B+D iniciada | 16:45:30.868378 |
| Marcador leído: 301 iteraciones de norma del gradiente | 16:45:32.565459 |
| SIGTERM al PID principal del supervisor | 16:45:32.567042 |
| Ledger `failed`, unidad 1 rechazada | 16:45:32.621626 |

El worker sintético ya había ejecutado `loss.backward()` y repetía una
operación tensorial de norma de gradientes dentro de `_optimizer_step`,
**antes** de `Adam.step()`. La repetición amplía deliberadamente la ventana
de señal sin usar `sleep`. El controlador observó el marcador mientras
seguía activo el worker y envió SIGTERM al supervisor principal. El
journal registró `signal` en unidad 1 y después `unit_failed`;
`worker-1` terminó por SIGTERM. El ledger quedó `failed` por
`interrupted_supervisor_or_unit`, con solo Q0 aceptada, tres trayectorias
sintéticas y 540 transiciones observadas en el contador parcial. No
existen `checkpoint-1` ni `unit-1.json`. El proceso supervisor de la
sonda devolvió 1.

Las huellas SHA-256 de `checkpoint-0/state.pt` y su manifiesto fueron
idénticas antes y después: respectivamente
`1dff3594469d14c1f4f8b731db1ab5323d10d6062ec4eb5601e4a97e4207b39f`
y `40d3a901a031932bb412b7285d797688bd1ada81401aefe51b1f4a8a97d50554`.
El [resultado completo](../evidence/p2r-optimizer-signal-08/results.json),
las copias byte a byte del ledger y journal, y el
[manifiesto de huellas](../evidence/p2r-optimizer-signal-08/SHA256SUMS.txt)
permiten revisar la sonda. Conservación de Q0 **no autoriza reanudar**
ninguna corrida fallida.

**Límites:** la operación repetida es una carga sintética de cálculo de
gradientes en la actualización, no el kernel real de Adam ni una iteración
histórica. La sonda 08 se lanzó desde un proceso local, no como unidad
`systemd --user`; el `InvocationID` heredado por el entorno no prueba una
invocación de servicio. No prueba apagado físico, señal durante B/D ni
rentabilidad o cumplimiento CVaR. La sonda 06 anterior y P0/P1/P2 no se
modificaron.

Comandos y comprobaciones efectivamente ejecutados:
[COMMANDS.md](../evidence/p2r-training-shard/COMMANDS.md).
