# Adjudicación P2R v2: `market_training_executed`

**ADJUDICADO SOLO PARA INTERPRETACIÓN DESCRIPTIVA DE DESARROLLO.** Esta
adjudicación documenta la instrucción del usuario posterior al cierre
P2R y no modifica el protocolo adoptado, sus reportes, ledger, checkpoints
ni la decisión numérica `review`. No concede permiso para otra campaña,
validación, prueba final o evaluación confirmatoria.

## Hecho y desviación

Los 99 reportes originales dicen `market_training_executed=false` porque
el generador del campo solo reconoce los perfiles P0/P1, mientras P2R usa
`authorized_p2r_only`. Los nueve Q0 no contienen actualizaciones de
optimizador; las 90 unidades Q/A/B+D sí contienen 720 pasos acumulados
del actor y 1440 del crítico, con estados de optimizador y cambios de pesos
en checkpoints íntegros. La [auditoría de solo lectura](../hitos/P2R-metadato-entrenamiento-revision.md)
contrasta reportes, perfiles, contadores, procedencia y huellas. El campo
incorrecto es de informe; no se encontró una lectura del mismo que gobierne
Q/A/B+D o la admisión de unidades.

El [protocolo P2R v2, §5](../proposals/P2R-protocolo-v2.md) exigía
**corregir o verificar el metadato antes de congelar el ejecutor histórico**.
Esa verificación faltó. Esta adjudicación **no declara cumplido
retrospectivamente** el requisito, no cambia `false` a `true` y no convalida
silenciosamente la integridad del preflight. La omisión queda como
desviación metodológica explícita, aun cuando los artefactos independientes
demuestran pasos de optimizador y origen de entrenamiento.

## Decisión de alcance

1. El cálculo numérico ya publicado permanece **`review`**. No se vuelve a
   ejecutar, recalcular para favorecer un resultado ni reemplazar por otra
   etiqueta en los artefactos originales.
2. Las nueve corridas P2R se pueden describir **únicamente como diagnóstico
   de desarrollo sobre el histórico de entrenamiento**. Sus comparaciones
   A/D, advertencias y tiempos sirven para formular hipótesis y diseñar
   P3; no son evidencia confirmatoria, no prueban generalización temporal,
   rentabilidad ni cumplimiento poblacional de CVaR.
3. La aceptación de P2R como campaña plenamente conforme al preflight v2
   **no se declara**. La distinción entre `review` numérico y elegibilidad
   metodológica debe acompañar cada traslado a la tesis. Esta decisión
   conserva la regla de §6 y no inventa una ejecución sin desviaciones.
4. P2R no se reabre ni se repite. El defecto se corrige solo
   prospectivamente, bajo protocolo y permiso separados. Los reportes
   históricos, P0/P1/P2 y el derivado H1 permanecen intactos.

El [análisis de MSE tardía](../hitos/P2R-error-valor-tardio.md) utiliza
los nueve checkpoints finales ya existentes. La [propuesta P3](../proposals/P3-protocolo-v1.md)
es un diseño **no autorizado para implementación o ejecución**; no es
parte de la adjudicación de los resultados originales.
