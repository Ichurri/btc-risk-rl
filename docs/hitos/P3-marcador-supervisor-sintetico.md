# Hito prospectivo P3 — marcador y aceptación supervisada

**Alcance autorizado:** implementación del marcador y pruebas sintéticas.
No se implementó la pérdida βV², no se habilitó P3, no se entrenó con
mercado y no se consultó validación ni prueba final. La adopción
metodológica de P3 v1.1 en `699d8da` sigue separada de cualquier permiso
de campaña.

## Resultado técnico

El reporte calcula `market_training_executed` a partir de la identidad
de la **fuente** y de los contadores acumulados de pasos completados:

    fuente == accepted_train_collection_only
    AND actor_updates > 0
    AND critic_updates > 0

La función rechaza contadores negativos, no enteros o booleanos. Q0,
incluso con colección histórica Q, es `false`; una Q/A/B+D completada
sobre entrenamiento aceptado es `true`. Una actualización sintética con
ambos optimizadores sigue siendo `false`. La regla deja de depender de
una lista de nombres de campaña que omitía P2R.

Antes de `ledger.finish`, el supervisor coteja el perfil de procedencia
con el perfil de ajustes, el reporte de la unidad, los deltas de
recursos, el manifiesto/huella del checkpoint y el estado `state.pt`.
Compara pasos acumulados de actor y crítico con calendario, reporte y
estados Adam, más contadores de aprendizaje y D con la frontera Q0 o
Q/A/B+D. Exige que el marcador sea un booleano idéntico al valor
calculado desde procedencia y pasos verificados. Un reporte ausente,
incoherente o manipulado produce fallo cerrado antes de aceptar la
unidad. La frontera completa anterior permanece como evidencia, sin
habilitar reanudación de la campaña fallida.

## Verificación y alcance

| Comprobación | Evidencia | Límite |
| --- | --- | --- |
| Matriz Q0/iteración × fuente sintética/entrenamiento | Cuatro sobres de checkpoint fabricados, con marcador correcto y opuesto | La fila de entrenamiento usa solo metadatos y contadores sintéticos; no ejecuta un trabajador histórico |
| Reporte de optimización sintética | Q0 `false`; tras pasos reales sintéticos del actor y crítico, `false` | Verifica la fuente real `SyntheticMarket`, no una campaña P3 |
| Manipulación de reporte/estado | Se rechazan marcador falso con pasos positivos de perfil aceptado, marcador verdadero sintético, propósito erróneo, pasos del reporte/estado/Adam incompatibles y campo ausente | No simula corrupción física del host |
| Ledger y checkpoint previo | Q0 aceptado; la unidad siguiente con marcador falso deja ledger `failed`, unidad 1 no aceptada y misma huella `checkpoint-0`; reanudación rechazada | El checkpoint candidato de la unidad fallida se conserva como evidencia física, sin aceptarse |
| Artefactos anteriores | [Anclas leídas](../evidence/p3-marker-supervisor/results.json): P2R 99 reportes, hashes de ledger/journal iguales a los publicados; P0/P1 completados, P2 fallido | No se modifica ni reinterpreta la aceptación histórica P2R |

La primera ejecución de la suite completa encontró un test heredado que
solo esperaba ausencia de `ledger.jsonl` en una solicitud P2R falsificada.
Ahora que la campaña P2R cerrada sí tiene ledger, el trabajador la rechaza
por no corresponder a una unidad pendiente. Se amplió **solo la
aserción** para reconocer cualquiera de los dos rechazos seguros; no se
cambió el ejecutor histórico. Los comandos y salidas reales constan en
[COMMANDS.md](../evidence/p3-marker-supervisor/COMMANDS.md). Tras esa
corrección, la suite completa cerró **312/312 pruebas** en 225,10 s y
Ruff pasó. De ellas, 23 pruebas nuevas cubren el marcador y la guarda;
las demás prueban contratos previos, no convierten esta verificación en
una campaña P3.

## Límites y siguiente revisión

El cambio es prospectivo: los 99 reportes originales P2R conservan
`false` y el resultado adjudicado continúa `review` solo descriptivo.
Aplicar la nueva guarda a esos reportes no convalida el preflight omitido
ni altera una campaña ya cerrada. La guarda reside en el supervisor de
unidades Q0/Q/A/B+D actualmente compartido con P2R; los supervisores
históricos P0/P1/P2 no se reescribieron. Integrar un futuro perfil P3 y
verificar la equivalencia de reporte/estado en su trabajador histórico,
así como conceder permiso de campaña, quedan para hitos y autorizaciones
separados. Las pruebas de esta entrega no
demuestran rentabilidad, generalización temporal ni cumplimiento CVaR.
