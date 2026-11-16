# P0 — ejecución técnica autorizada

Base propuesta 7a379b7; aprobación e0e3495; ejecutor verificado 0838ac8.
Rama `codex/p0-approved-execution`. La aprobación y la propuesta originales
permanecen versionadas. [Protocolo aprobado](../protocols/P0-approved-v1.md).

## Alcance y método

Entrenamiento aceptado 2018–2022, sin validación ni conjunto final. Misma
contabilidad, características, normalizador H1, índices, acción y calendario
Q/A/B. Cota común d=-ln(.90)=0.10536051565782628, fijada antes de resultados.
Es referencia económica del 10% en pérdida logarítmica del objetivo H=180,
no máximo de pérdida individual ni drawdown. No se ajustó por cumplimiento.

N_A=64, N_Q=N_B=400, K=2 por corrida, semillas 410031/410047/410081 y órdenes
C0-C5-C10 / C5-C10-C0 / C10-C0-C5. Auxiliares C0 incluidos. CPU float64/un hilo,
sin CUDA. Parámetros exclusivos de P0, no definitivos del contraste confirmatorio.

Campaña canónica `artifacts/p0-approved-v1`, lock exclusivo y registro append-only.
Día America/La_Paz; timestamps UTC. Una sola ventana GLOBAL de tres horas,
incluidos carga, comprobaciones, trabajo, guardado y cierre. Un cambio de corrida
o proceso no renueva la ventana. Contadores de recursos por corrida y campaña;
las sesiones de cada corrida cuentan fechas distintas, máximo tres.

Primera medición sin estimación: topes aprobados Q0=30 min, iteración=45 min.
Después 1.5×máximo de trabajo completo de igual condición/config/runtime. No
usar tiempos sintéticos. Guardado usa reserva separada de cierre; el supervisor
valida la marca de fin de trabajo antes de permitirla. Se conservan todos los
checkpoints de fronteras completas, no el de mejor resultado. No hay repetición
selectiva; fallos o interrupciones invalidan campaña. SIGKILL al trabajador si
muere el supervisor; vigilancia de reloj monotónico y RSS de trabajador.

La identidad fija hashes de código, lock, configuración y manifiesto H1, runtime
y autorización. Checkpoint schema p0_complete_boundary_v2: parámetros, dos Adam,
eta/lambda, generación, siguiente iteración, RNG y contadores. Ledger enlaza cada
checkpoint con fecha/unidad y registra recursos acumulados. Los pesos y los logs
completos quedan fuera de Git; se versionan hashes y resúmenes pequeños.

## Verificación previa

186 pruebas aprobadas (63.77 s) y Ruff sin errores. Ver
[comandos](../evidence/p0-execution/COMMANDS.md) y
[revisión](../evidence/p0-execution/REVIEW.md). Nuevas pruebas sintéticas:
reanudación exacta C0/C5 y optimizadores, dos corridas en un día, deadlines
persistentes/reinicios, medianoche LaPaz, límite sesiones, corrupción, tiempo,
RSS, muerte del supervisor, guardado en reserva y rechazo de permisos no registrados.
No se extrapolan esos tiempos a mercado.

La revisión previa corrigió rechazo de C0 al cargar risk_enabled=False,
invalidación al consultar fuera del horario y mezcla del guardado en la estimación
de trabajo. Logs RED/intermedios conservados; los defectos estaban corregidos
antes de ejecutar mercado. La revisión automática de permisos agotó una vez su
plazo al preparar el commit; el reintento separado funcionó y no ejecutó mercado.

## Interpretación y límites

P0 mide integridad, costo y señales técnicas de estabilidad. Dos iteraciones no
representan convergencia ni demuestran cumplimiento de CVaR poblacional.
F_B(eta_Q), rho_B empírico y restricción poblacional se distinguen; B participa
en el aprendizaje. Las advertencias no cambian orden, parámetros ni parada por
rendimiento. No se calculó Sortino fuera de muestra ni se seleccionaron agentes.
La tesis y las decisiones metodológicas adoptadas permanecen intactas.

## Resultados observados — 24 de septiembre de 2026

Estado **completed**: nueve corridas, 27 unidades y 18 iteraciones completas, sin fallos, pausas ni reintentos. Cada corrida consumió una sesión del mismo día America/La_Paz. Inicio UTC 05:08:14.845408; cierre UTC 05:31:20.522467.

Presupuesto registrado por el supervisor: **1385.677 s (23 min 5.677 s)** de pared global, frente al máximo diario de 10800 s; tiempo activo 1385.347 s. Incluye la ejecución supervisada, carga, comprobaciones, guardado y cierre. La exportación y redacción posteriores son tareas documentales separadas; no son tiempo de entrenamiento ni nuevas sesiones.

Recursos: **19152 trayectorias, 3447360 transiciones, 144 actualizaciones Adam del actor y 144 del crítico**, incluidos auxiliares C0. Por corrida: 2128 trayectorias, 383040 transiciones y 16 actualizaciones por red. Pico RSS del trabajador: **375853056 bytes (358.44 MiB)**; no es la memoria total del sistema.

La tabla muestra la segunda auditoría B; F_B evalúa la función variacional con eta de Q, mientras rho_B es CVaR empírico optimizado en B. Ninguna es una garantía poblacional. Tiempo = suma de unidades supervisadas, con carga y guardado; el pequeño resto del total global corresponde a orquestación. Todas completaron K=2.

| Orden / condición | Semilla | Tiempo (s) | rho_B | F_B(eta_Q) | Multiplicador final | Advertencias |
|---|---:|---:|---:|---:|---:|---:|
| run-00-C0 | 410031 | 161.102 | 0.307437076 | 0.310204470 | 0.000000000 | 18 |
| run-01-C5 | 410031 | 158.109 | 0.307437076 | 0.310204470 | 0.038464498 | 18 |
| run-02-C10 | 410031 | 157.104 | 0.264564211 | 0.266408938 | 0.030699296 | 18 |
| run-03-C5 | 410047 | 152.106 | 0.278199172 | 0.281700026 | 0.033031858 | 18 |
| run-04-C10 | 410047 | 155.112 | 0.245206096 | 0.249070190 | 0.025883105 | 18 |
| run-05-C0 | 410047 | 153.109 | 0.278208208 | 0.281710704 | 0.000000000 | 18 |
| run-06-C10 | 410081 | 154.103 | 0.231199252 | 0.233600395 | 0.027136534 | 18 |
| run-07-C0 | 410081 | 149.105 | 0.258273211 | 0.258378119 | 0.000000000 | 18 |
| run-08-C5 | 410081 | 145.108 | 0.258270861 | 0.258375982 | 0.033555510 | 18 |

### Mediciones para planificar, sin extrapolación de convergencia

| Condición / unidad | n | Mínimo (s) | Mediana (s) | Máximo (s) | 1.5 × máximo (s) |
|---|---:|---:|---:|---:|---:|
| C0/iteration | 6 | 58.227 | 60.151 | 65.732 | 98.598 |
| C0/q0 | 3 | 28.283 | 29.258 | 30.079 | 45.118 |
| C10/iteration | 6 | 58.835 | 60.888 | 63.129 | 94.693 |
| C10/q0 | 3 | 30.109 | 30.244 | 30.581 | 45.871 |
| C5/iteration | 6 | 56.675 | 60.085 | 63.759 | 95.638 |
| C5/q0 | 3 | 28.350 | 28.509 | 31.447 | 47.171 |

Trabajo medido hasta la marca previa al guardado: incluye inicio/carga, algoritmo y diagnósticos. Guardado acumulado: 0.554914 s. El factor 1.5 fue prescrito antes de observar tiempos; no es intervalo de confianza ni garantía para otra máquina/configuración. La telemetría completa por fase, CPU, memoria y versiones está en el JSON de resultados.

### Advertencias y estado de revisión

Hubo **162 advertencias critic_relative_mse**, 18 por corrida. La razón MSE / (segundo momento del target + 1e-12) estuvo entre **1.653690 y 25.780955**, por encima del umbral 1: en esos targets/minibatches el crítico fue peor que el predictor cero bajo esta medida. Son diagnósticos de entrenamiento, no error fuera de muestra. No se dispararon las demás advertencias preespecificadas. No se modificaron hiperparámetros ni se repitieron corridas.

Las auditorías de C5/C10 mostraron F_B y rho_B superiores a d en ambas iteraciones; el multiplicador aumentó según la regla adoptada. C0 mantuvo multiplicador cero. El actor final C0/C5 de semilla 410031 tiene el mismo hash; los otros pares C0/C5 difieren. Esta observación no identifica por sí sola la causa ni demuestra eficacia del mecanismo de riesgo.

**Cierre operativo completo; revisión de estabilidad pendiente.** La campaña no falló por integridad, pero las advertencias requieren análisis antes de proponer una campaña posterior. Próxima tarea: revisar el diagnóstico del crítico y la señal de riesgo con las evidencias existentes, y redactar una propuesta de seguimiento. No está autorizado P1, una repetición de P0, validación ni evaluación confirmatoria. Mantener d y preservar todos los checkpoints.

### Evidencia de cierre

[Resultados completos pequeños](../evidence/p0-execution/campaign-results/results.json), [log de campaña](../evidence/p0-execution/campaign.log), [comprobación de cierre](../evidence/p0-execution/closure-checks.json) y [comandos](../evidence/p0-execution/COMMANDS.md). La comprobación posterior pasó: orden, configuración, contadores, límites diarios/unidades/memoria, actualización dual, código y hashes de 36 artefactos. Solo leyó logs y bytes para hashes; no evaluó mercado ni cargó pesos para seleccionar modelos. Los 27 manifiestos de checkpoint identifican el ejecutor 0838ac863e4f31944323f683ae31385291d3767e.
