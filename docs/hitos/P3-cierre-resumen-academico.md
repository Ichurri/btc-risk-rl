# P3 v1.1 — resumen académico del diagnóstico de desarrollo

P3 comparó β=0 (MSE) con β=1 (MSE más energía de salida del crítico)
en C0/C5/C10, tres bloques de semillas y diez actualizaciones por
corrida, manteniendo Q/A/B+D y el derivado H1 exclusivo de entrenamiento.
Completó las 18 corridas y 198 unidades en dos días activos dentro del
presupuesto autorizado. La auditoría cotejó todos los reportes,
checkpoints, contadores, huellas y cadenas del supervisor.

El resultado predefinido fue **`review`**, con cero de tres bloques de
semilla que cumplieran conjuntamente las puertas. En las nueve parejas
la señal de objetivos fue elegible, pero β=1 no superó la comparación
exacta de MSE D tardía con el predictor cero ni la mejora pareada D
tardía exigida. Las 2.520 advertencias de estabilidad de los reportes
finales son diagnósticos del error relativo del crítico, no fallos de
integridad. El estudio responde una pregunta de ingeniería sobre el
crítico en trayectorias nuevas del mismo histórico; no mide desempeño
fuera de muestra ni prueba un beneficio financiero o cumplimiento CVaR.

Fuente: [informe de cierre](P3-cierre-historico-v1.md) y
[auditoría reproducible](../evidence/p3-market-2026-10-13/final-audit.py).
