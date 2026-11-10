# Preparación del entrenamiento OOS v1.2 — 10/11/2026

## Alcance y estado

Santiago autorizó preparar y ejecutar el entrenamiento que quepa antes de
la presentación del 16/11/2026, sin reducir las 36 ternas principales.
La [adopción operativa](../protocols/OOS-v1-2-entrenamiento-adopcion-20261110.md)
fija **solo entrenamiento**; validación 2023 y prueba final 2024–2025
continúan sin permiso. La lista de 126 corridas, condiciones, semillas,
configuración y orden se congeló en
[`OOS-v1-2-training-freeze-20261110.json`](../protocols/OOS-v1-2-training-freeze-20261110.json),
SHA-256 `0651f396f3157eaa5abd6bb7faf7ec1c6463210d255fa2fbd8a932e2999870a0`.
La ejecución se divide en 9 corridas de corte 2021, 9 de corte 2022 y
108 principales sobre 2018–2022. Cada corrida tiene Q0 y diez unidades
Q/A/B+D, con checkpoint completo en cada frontera.

El ejecutor usa el algoritmo Q/A/B existente, el derivado H1 exclusivo de
entrenamiento y refit por corte. Acepta un trabajador solo con permiso de tipo
exacto, lease y solicitud idénticos al ledger. La verificación de aceptación
coteja reporte, contadores, pasos de ambos optimizadores, marcador de
entrenamiento, checkpoint y huellas. El primer arranque y el reingreso
rechazan raíces sin ledger, pendientes y estados `failed`/`incomplete`.

La bitácora durable empieza antes de suite, Ruff y preflight, permanece
abierta durante la carga y la supervisión, y se concilia con el ledger por
unión de intervalos. La admisión previa cuenta también el ledger propio;
el supervisor lo excluye solo al calcular gasto *externo*. Los días activos
incluyen desde el instante inicial de un ledger o bitácora aunque su cargo
todavía sea cero. El tope global es 10.800 s/día con 2.700 s reservados
para cierre; Q0/iteración conservan topes de 1.800/2.700 s y ventana
01:00–09:00 La Paz. El máximo de 20 días activos se aplica al conjunto
de los tres perfiles.

## Comprobaciones de esta preparación

- `uv run --frozen pytest -q tests/test_oos_v12_training.py`: **27 passed**
  tras la corrección de contabilidad entre preparación y supervisor. Cubrió
  Q0→checkpoint→unidad 1 con fuente controlada en procesos distintos,
  permisos falsos, orden, reingreso, límites, bitácora y archivos protegidos.
- `uv run --frozen ruff check .`: pasó tras los cambios anteriores.
- `uv run --frozen pytest -q -x` sobre el código final: **576 passed**,
  dos `DeprecationWarning` del `fork` en la prueba sintética, 573,22 s.
- `uv run --frozen python docs/evidence/oos-v12-training-prep-20261110/source_check.py > docs/evidence/oos-v12-training-prep-20261110/source_check.json`:
  3.639/4.678/7.048 inicios; abrió solo archivos del derivado H1 de
  entrenamiento y el manifiesto H1 compartido, sin CSV compartidos ni
  archivos de validación/final. SHA-256 de la salida
  `92a3bd7df4af76116ebd3a86080ddf54a82e90271fdd2168a8ac8f5c9542320a`.
  No recolectó trayectorias ni actualizó parámetros.
- `systemd-analyze verify ops/systemd/oos-v12-training.service ops/systemd/oos-v12-training.timer`:
  pasó. Las seis fechas 11–16/11 a las 01:00 se expresan explícitamente,
  con `Persistent=false`, `Restart=no` e inhibición de sueño durante el
  servicio. Tras aprobar el gate, se instalaron copias idénticas en
  `~/.config/systemd/user/` y se habilitó el timer. El `systemctl --user
  status` mostró `active (waiting)`, siguiente disparo **11/11 01:00 La Paz**;
  el servicio seguía `inactive` y las tres raíces ausentes. Véase
  [`schedule.json`](../evidence/oos-v12-training-prep-20261110/schedule.json),
  SHA-256 `ff3ea49ad431608f651745f509527c29ac9072cba3d45a7197e427e45e415d07`.
- `uv run --frozen python scripts/launch_oos_v12_nightly.py` con gate cerrado:
  rechazó `OOS market campaign NOT AUTHORIZED` antes de crear una raíz.

La primera suite completa sobre una versión intermedia del código dio
**568 passed** en 556,13 s. Una suite intermedia posterior se detuvo
deliberadamente al identificar una omisión de presupuesto; no se usa como
resultado de aceptación. Las dos advertencias finales corresponden al uso
de `fork` en una prueba sintética y no a una unidad histórica.

## Viabilidad y alcance

[Cálculo y datos](../evidence/oos-v12-training-prep-20261110/results.json):
WF05 midió 743,408 s por 11 unidades del corte 2021; WF 2022-03 midió
710,691 s por 11 unidades del corte 2022; P3 β=0 midió 726,936 s promedio
por corrida completa. Extrapolar las 126 nuevas corridas da 91.596 s de
unidades, sin preparación diaria ni evaluación. Entre el cierre de
WF 2022-03 y el 16/11 solo caben como máximo 55.452 s productivos bajo
los límites; el techo aritmético es 19 ternas principales, o 16–17 si
se suponen 900–500 s de gasto diario adicional. Estas cifras son escenarios,
no duración ni resultado de la nueva campaña.

La primera ventana real tras esta preparación es **11/11 a la 01:00**: solo
quedan seis fechas, 48.600 s productivos como máximo y un techo de 16
ternas, o 14/13 con gastos diarios supuestos de 500/900 s. No se inició
entrenamiento adicional el 10/11 después de las 09:00.

## Permiso y estado de la máquina al programar

El código de esta preparación quedó en `1ce1382`; el permiso específico de
entrenamiento quedó en el commit separado `cbd11de`, JSON SHA-256
`2a54cf3084b366d11750790e907ae36b826778de47313de060b5a4ee6324dba2`.
El gate acepta únicamente fuentes aceptadas de entrenamiento, roster y
huellas congelados. A las 10:57 del 10/11 `require_campaign()` verificó
la huella de código y el lanzador fuera de horario devolvió `outside_window`
sin crear raíz. CA=1, batería 98 %, memoria disponible 5.536.272.384 B
**bajo el umbral de lanzamiento** de 6.026.846.208 B, disco libre
125.793.193.984 B, gestor `running` y `Linger=yes`. Son medidas de ese
instante; la sesión del 11/11 repetirá todo el preflight y bloqueará Q0
si la memoria no se recupera.

GNOME tenía `sleep-inactive-ac-type='suspend'`, con 900 s de inactividad
en CA. Se cambió a `'nothing'` para permitir pantalla apagada sin suspensión
antes del disparo; la pantalla mantiene `idle-delay=300 s`. El servicio
además usa `systemd-inhibit` durante su ejecución. **Restaurar `'suspend'`
al cierre de esta campaña**. El cambio de preferencia es del usuario local,
sin modificar drivers ni datos. No se realizó una prueba nocturna todavía.

La presentación puede informar corridas y checkpoints completos, tasas y
diagnósticos de desarrollo. Sin 36 ternas y sin evaluación final autorizada
no corresponde el contraste primario de Sortino ni una conclusión financiera.
