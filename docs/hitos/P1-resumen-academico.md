# P1 — resumen académico

**Criterio primario cumplido en 3/3 semillas.** Comparación aprobada de 2 frente
a 4 épocas del crítico, 18 corridas nuevas K=2, solo entrenamiento 2018–2022.
Aprobación 7eb9738; ejecutor publicado antes de mercado 7617d84. d=-ln(.90),
actor, arquitectura, tasas, Q/A/B, índices y normalizador permanecieron fijos.

| Semilla | MSE post-A con 2 épocas | Con 4 épocas | Reducción |
|---|---:|---:|---:|
| 510031 | 0.0191134948 | 0.0094144755 | 50.74% |
| 510047 | 0.0274345902 | 0.0113297886 | 58.70% |
| 510081 | 0.1399264058 | 0.0777488528 | 44.44% |

Se exigía ≥20% en al menos dos de tres semillas tras primera actualización.
Mismo A inicial y actor posterior idéntico verificados en todos los pares.
C0/C5/C10 repiten esta comparación por construcción: son tres bloques de semillas,
no nueve réplicas. La segunda iteración se conserva como diagnóstico secundario.

18 corridas completadas, 54 unidades/checkpoints, sin fallos, pausas, reintentos ni
selección por rendimiento. Consumo: 38304 trayectorias, 6894720 transiciones,
288 pasos actor y 432 crítico. Cada brazo consumió las mismas trayectorias;
crítico: 144 pasos en brazo2 frente a 288 en brazo4. Ejecución P1: 44 min 10.523 s.
Débito diario compartido con P0 y preparación P1: **1 h 30 min 24.038 s**, dentro
de 3h, día 24/09/2026 America/La_Paz; timestamps UTC. Pico RSS trabajador: 358.973 MiB.

**Advertencias:** 465 del MSE relativo del crítico (162 brazo2, 303 brazo4).
El segundo brazo registra más minibatches: conteos brutos no comparan estabilidad.
Todas las mediciones post-A completas permanecieron peor que predictor cero,
aunque mejoraron relativamente. No hubo otras alertas preespecificadas. En la
segunda iteración el término de riesgo fue activo en todas las corridas C5/C10;
F_B final siguió por encima de d. Ningún resultado certifica cumplimiento CVaR.

198 pruebas sintéticas y Ruff pasaron antes de ejecutar; cierre posterior verifica
hashes de código/checkpoints, modelos pareados, recursos, presupuesto y P0 intacto.
No se accedió a validación/final, no se modificó la tesis.

El resultado demuestra **mejor ajuste sobre A utilizado por el crítico** en este
piloto. No demuestra generalización, rentabilidad, superioridad de políticas ni
convergencia. Cuatro épocas no se congelan automáticamente para el experimento
confirmatorio. Siguiente paso: revisión académica y decisión explícita sobre el
próximo protocolo; no ejecutar campañas adicionales por inferencia.

[Informe por corrida, tiempos y límites](P1-epocas-critico.md) ·
[Evidencia pequeña](../evidence/p1-execution/campaign-results/results.json) ·
[Comandos](../evidence/p1-execution/COMMANDS.md).
