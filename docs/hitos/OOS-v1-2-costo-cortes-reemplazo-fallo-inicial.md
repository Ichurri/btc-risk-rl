# WF de reemplazo `...02`: fallo en el primer arranque, antes de Q0

**Resultado operativo: detenido; ninguna unidad aceptada.** La autorización
para la campaña íntegra de 22 unidades quedó en el commit `743e51b`, con
registro independiente
[`OOS-v1-2-wf-cost-replacement-approval.json`](../protocols/OOS-v1-2-wf-cost-replacement-approval.json)
(SHA-256 `c0d6973d98951dabe1cbc0cfef2f79304c2662cba01e09ff58276547c453f242`).
El perfil de `...01` siguió cerrado; sus artefactos no cambiaron.

## Puertas y lanzamiento

La suite completa anterior al lanzamiento terminó **415 passed, 1 skipped**
(omisión condicionada por la medianoche real de La Paz), y Ruff pasó. La
[captura vigilada de las 03:46:54 UTC](../evidence/oos-v1-2-wf-cost-replacement-campaign/preflight-launch.json)
tuvo `status=ready`, sin bloqueos: CA conectada, batería 100 %, memoria
disponible 4.778.885.120 B (mínimo 4 GiB), disco libre 151.965.974.528 B
(mínimo 20 GiB), `Linger=yes`, gestor de usuario `running`, gasto global del
día 0 s, raíz aún ausente y huellas de código, protocolo, diseño y derivado
H1 correctas. Los cortes conservaron 3.639/4.678 episodios y 5.764/7.703
filas de ajuste. El vigilante registró 31 aperturas relevantes, ninguna de
CSV H1 compartidos, validación o prueba final. SHA-256 de la captura:
`fdda73ba046a2fb247f6c26ffa5427b51e4bb9b77026acb8eed64c39186a9c9c`.
Son mediciones del momento, no una garantía posterior.

Se lanzó **una sola** unidad de servicio, con el comando íntegro en
[COMMANDS.md](../evidence/oos-v1-2-wf-cost-replacement-campaign/COMMANDS.md):
`oos-wf-cost-20261027-replacement-session-01.service`,
`InvocationID=3bb524765d3c4b669fcad7f2ee4b18f4`. No hubo segundo
lanzamiento.

## Fallo y causa demostrada

El [journal](../evidence/oos-v1-2-wf-cost-replacement-campaign/session-01-journal.txt)
sitúa el inicio a las **03:47:04 UTC** y la excepción a las **03:47:05 UTC**.
`run_units()` creó la raíz para abrir `sessions.jsonl` **antes** de llamar a
`_launch_readiness()`. Esta última comprobó que toda raíz existente debía
tener `ledger.jsonl`; como el ledger aún no se había creado, rechazó la
primera sesión con `ValueError: WF cost root exists without a valid ledger`.
Es un defecto de orden de operaciones demostrado por código y traceback.
La prueba sintética previa cubrió reingreso y fallo preledger, pero no esta
combinación del primer arranque del supervisor real.

La [bitácora original](../../artifacts/oos-v12-wf-cost-only-02/sessions.jsonl)
se conserva en la raíz de artefactos, con una
[copia pequeña](../evidence/oos-v1-2-wf-cost-replacement-campaign/session-01-events.jsonl).
Su cadena verificó `start` a las 03:47:05.541014 UTC y `end failed` a las
03:47:05.865252 UTC: **0,324237 s de pared de bitácora**. SHA-256:
`72e790c0daf96a8da188e47b3791d759de625d170813fdc98c60d6ae888cb276`.
[`systemd`](../evidence/oos-v1-2-wf-cost-replacement-campaign/session-01-systemd.txt)
registró `Result=exit-code`, estado 1, **3,251232 s de CPU** y
**377.544.704 B de pico de memoria** para el servicio. Estas medidas no
equivalen al tiempo de bitácora ni a costo de Q0: Q0 no empezó.
Después del fallo, `systemctl --user is-system-running` devolvió `degraded`;
no se ejecutó `reset-failed`, para conservar el estado del servicio.

La [auditoría de solo lectura](../evidence/oos-v1-2-wf-cost-replacement-campaign/audit-failure.json)
confirma **ningún ledger, solicitud, unidad, trayectoria, paso de optimizador
ni checkpoint aceptado**. La raíz `...02` contiene solo `sessions.jsonl` y
`sessions.lock`. La sesión `failed` impide reingreso; el presupuesto
compartido debe imputarle conservadoramente el día local al considerarla
como fuente externa. La campaña no tiene un resultado de costo WF medido.

El permiso operativo de `...02` quedó **cerrado prospectivamente** en
`279e6ab` (`MARKET_EXECUTION_ENABLED=False`), conservando el registro y su
huella. Tras ese cierre, 15 pruebas focales y la suite completa
(415 aprobadas, una omitida por la ventana de medianoche) pasaron; Ruff
también pasó. El ledger `...01` mantiene SHA-256
`b6bc9a30d25387813d664708edfa07347c21174d2df216fc6f6be2d844ec6af6`
y su Q0 SHA-256
`22f9f60484db6ae5a04b7b35f4ebe2149debb16ac357437536c24f571bf8bca7`.
No se reintenta esta raíz por estar fallida. Una eventual corrección debe
probar sintéticamente el primer arranque completo y requerirá otra raíz y
autorización; este informe no las habilita.

No se activó la evaluación v1.2, ni se abrió validación 2023 o prueba final.
