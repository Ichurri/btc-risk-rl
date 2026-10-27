# Bitácora prospectiva de sesiones WF

**Alcance:** infraestructura y pruebas sintéticas desde `c59855b`. El estudio
histórico de costos sigue detenido después de Q0. Su ledger, checkpoint,
reporte, journal y registro de aprobación no se reescribieron; el permiso de
mercado continúa desactivado. Esta bitácora no adjudica retroactivamente el
tiempo de la sesión histórica que falló antes de la unidad 1.

## Contrato implementado

Tras comprobar el permiso de código y adquirir el bloqueo de presupuesto
compartido, el supervisor escribe y sincroniza un evento `start` en
`sessions.jsonl` **antes** del preflight completo y de `build_fold_source`.
Cada evento enlaza su SHA-256 con el anterior y contiene campaña, token,
`InvocationID`, época y timestamp UTC, reloj monotónico y día local de
`America/La_Paz`. El cierre guarda estado `ready` o `failed`, motivo y
duración `max(tiempo de pared, tiempo monotónico)`. También se sincroniza el
directorio cuando se crea la bitácora. Un fallo previo a `WFCostLedger`,
incluida una identidad distinta al reabrirlo, termina en un `end` fallido.

La sesión en curso carga su tiempo transcurrido hasta cada admisión. Para
cualquier día local, el cargo adicional es la longitud de los intervalos de
sesión **fuera de la unión** de intervalos que ya cubre el ledger; por ello
una sesión cerrada y el `charged_wall_seconds` de su día no suman dos veces
el tramo común. La diferencia conservadora entre tiempo monotónico y tiempo
de pared se asigna al día de cierre. Los intervalos se parten a medianoche
en `America/La_Paz`. Los días activos son la unión de días del ledger y de
la bitácora, incluidos los días consumidos antes de abrir un ledger; una
tercera fecha impide admitir más unidades. Siguen vigentes los límites de
3 h globales/día, 3600 s propios/día, 5400 s propios acumulados y la reserva
de 2700 s.

Una sesión antigua sin `end` bloquea cualquier reingreso y se debita por
**10800 s en cada día local que alcance** hasta el momento de inspección.
Una sesión cerrada en `failed` también impide el reingreso; frente a otras
campañas, su día afectado se carga conservadoramente hasta 10800 s. El
preflight de solo lectura y `P2RSharedBudget` incluyen bitácoras WF sin
ledger y descuentan únicamente el tramo adicional cuando sí hay ledger.
Si el ledger ya imputa 10800 s por falta de una medición válida, la bitácora
no añade segundos por encima de ese débito diario conservador.
El permiso continúa siendo una guarda anterior a la creación de raíz y
bitácora.

## Evidencia sintética

Las pruebas con raíces temporales cubren duración y solapamiento exactos,
admisión después de una carga previa larga, cierre y apertura en procesos
lógicos sucesivos, dos días por cruce de medianoche y rechazo de una tercera
fecha. También cubren una sesión sin cierre, bitácora con esquema alterado,
fallo del preflight, fallo al construir una fuente sintética y el caso
observado de `Campaign identity mismatch` con un ledger sintético previo.
En los fallos previos al ledger queda un `end` fallido y no aparece una
unidad aceptada. Ninguna prueba reconstruyó cortes históricos ni ejecutó
optimizadores.

El cierre de pruebas registró **41 pruebas focales aprobadas**, **401 pruebas
de suite aprobadas** y Ruff sin errores. Una ejecución anterior de la suite
tuvo 1 fallo de huella de procedencia P2R mientras todavía se editaba el
código; la prueba aislada pasó después y la suite completa se repitió con
el código estable. Ambas salidas se conservaron como evidencia.

Los comandos y resultados están en
[`COMMANDS.md`](../evidence/oos-v1-2-wf-session-journal/COMMANDS.md),
[`pytest-focused.txt`](../evidence/oos-v1-2-wf-session-journal/pytest-focused.txt),
[`pytest-full.txt`](../evidence/oos-v1-2-wf-session-journal/pytest-full.txt)
y [`ruff.txt`](../evidence/oos-v1-2-wf-session-journal/ruff.txt).
[`frozen-artifacts.json`](../evidence/oos-v1-2-wf-session-journal/frozen-artifacts.json)
repite la auditoría de huellas de la raíz histórica y constata
`MARKET_EXECUTION_ENABLED=False`.

## Límites

La bitácora comienza después del permiso y de adquirir el bloqueo global;
un rechazo previo a esos pasos no crea una sesión WF. Las pruebas son
sintéticas y no miden el costo real de los cortes ni prueban una suspensión
física o una señal durante optimización. El estudio histórico parcial no
puede reanudarse mediante esta corrección y la propuesta de evaluación
fuera de muestra v1.2 sigue sin autorización.
