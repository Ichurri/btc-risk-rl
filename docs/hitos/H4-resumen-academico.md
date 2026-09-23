# Resumen académico — H4

**Implementación y verificación sintética; sin pilotos ni entrenamiento de mercado.**
Base H3: 8f027c5. Alcance/dependencias: 31b4c87. Código H4: a6c391a.
[Rama](https://github.com/Ichurri/btc-risk-rl/tree/codex/h4-agents-collector).

Se implementó el contrato ADR-002 v2.1: actor y crítico separados, observación
H3 de 13 componentes, MC completo de 180 pasos, gamma=lambda_GAE=1 y ningún
bootstrap posterior al horizonte. No cambiaron contabilidad, costos, recompensa,
datos, índices, normalizador ni reglas de evaluación continua.

Acción logística-normal: transformar una normal por sigmoid y contabilizar
el jacobiano en log-probabilidades. No clipping ni remuestreo ante saturación:
un problema numérico invalida el lote. El soporte es (0,1); los extremos 0/1
no tienen masa. Por ello la referencia siempre efectivo no está exactamente
representada en esta familia, aunque el entorno sí permite esa acción.
La factibilidad de aprendizaje requiere estudio; no se infiere del simulador.

El recolector distingue realización, ruta y versión de política, congela la
política por lote y ensambla fragmentos contiguos sin perder reloj/cartera.
Registra terminalidad y procedencia del corte. Un fallo aborta y diagnostica
sin reemplazo selectivo. Hay serialización de trayectorias versionada y sin
pickle; no hay reanudación de optimizadores ni replay.

Calendario implementado: Q0; A con actor/crítico antiguos congelados; actor PPO
con coeficientes fijos; crítico separado contra MC; Q nuevo del actor actualizado;
B independiente con eta fijo; una actualización dual para la próxima iteración.
Se respeta cuantil inferior, empates exactos y masa fraccionaria. F_B(eta_Q),
CVaR empírico y restricción poblacional siguen distinguiéndose.

C0/C5/C10 comparten implementación y presupuesto, incluidos Q/B auxiliares.
Pruebas verifican equivalencia exacta de pesos y Adam entre C0 y riesgo apagado,
y que cambiar el consumo Q/B de C0 no altera aprendizaje ni parada.

Verificación local: Ruff pasa, **149 pruebas aprobadas**, 32 nuevas H4.
Oráculos analíticos y diferencias finitas independientes se separan de
actualizaciones pequeñas sobre rutas fabricadas y de pruebas sintéticas H1/H3.
La ejecución adicional realizó cinco corridas sintéticas, 95 trayectorias y
17100 transiciones; confirmó equivalencia de riesgo apagado. Sus versiones/huellas están en
[evidencias](../evidence/agents-h4/COMMANDS.md). No se cargó mercado.

Se entrega [propuesta de pilotos con máximo 3h diarias](../proposals/H4-pilotos-3h.md),
NO autorizada ni ejecutada. Propone medir costo antes de fijar K, presupuesto
común con auxiliares y congelación económica de d. Parámetros y criterios
cuantitativos siguen pendientes; los valores sintéticos no se trasladan al piloto.

Antes de pilotos faltan adaptador autorizado de mercado, checkpoint integral,
instrumentación y aprobación del protocolo. Antes de confirmar, también réplicas,
remuestras, bloques/semillas, precisión e indefinidos. Sortino anualizado y plan
inferencial adoptados no cambian; Sortino superior no acredita CVaR.
No se modificó la tesis ni se generó ZIP.
