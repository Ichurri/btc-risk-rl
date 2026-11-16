# P0 — resumen académico de ejecución

P0 autorizado completó las nueve corridas en el orden y semillas aprobados,
con dos iteraciones Q/A/B por corrida, sin fallos, pausas ni repeticiones.
Ejecutor: commit 0838ac8; aprobación: e0e3495; propuesta original: 7a379b7.
Rama `codex/p0-approved-execution`.

Se utilizó exclusivamente entrenamiento aceptado 2018–2022. La cota común
C5/C10 d=-ln(0.90)=0.10536051565782628 fue fijada antes de resultados y no cambió.
Representa una referencia del 10% de pérdida logarítmica H180; no limita cada
pérdida individual ni drawdown. Se conservaron contrato, normalizador, índices,
contabilidad y calendario Q/A/B, con auxiliares C0 dentro del presupuesto.

- 19152 trayectorias y 3447360 transiciones; 144 actualizaciones por red.
- Tiempo global supervisado: 1385.677 s (23 min 5.677 s), el 24/09/2026
  America/La_Paz, dentro de tres horas; una sesión por corrida, sin concurrencia.
- Pico RSS del trabajador: 358.44 MiB. Mediciones de CPU local, no estimaciones GPU.
- Verificación previa: 186 pruebas sintéticas y Ruff aprobados. Cierre posterior:
  orden, parámetros, recursos, límites, regla dual y hashes coherentes.

**Advertencia principal:** 162 registros de MSE relativo del crítico superior
al predictor cero (18 por corrida; rango 1.653690–25.780955). Las demás alertas
preespecificadas no se dispararon. Esto requiere revisión de estabilidad antes
de una campaña posterior; no se cambió la configuración durante P0.

En ambas auditorías de C5/C10, la función variacional evaluada con eta de Q y
el CVaR empírico de B superaron d. El multiplicador aumentó; C0 mantuvo cero.
Dos iteraciones no demuestran convergencia, superioridad entre condiciones ni
cumplimiento de CVaR poblacional. B participa en aprendizaje: no es una evaluación
independiente fuera de muestra. No se calculó Sortino ni se accedió a validación
ni al conjunto final. La tesis permanece intacta.

**Estado:** ejecución cerrada, revisión de advertencias pendiente. Siguiente paso:
analizar las evidencias del crítico y la señal de riesgo y proponer seguimiento;
P1, nuevas corridas y evaluación confirmatoria requieren autorización propia.
No modificar retrospectivamente d ni seleccionar checkpoints por rendimiento.

[Informe con resultados por corrida y tiempos](P0-ejecucion.md).
[Resultados y versiones](../evidence/p0-execution/campaign-results/results.json).
[Comandos y pruebas](../evidence/p0-execution/COMMANDS.md).
