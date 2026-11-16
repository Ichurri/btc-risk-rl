# P1 — comparación aprobada de épocas del crítico

Propuesta revisada 42152c3, aprobación registrada en 7eb9738, ejecutor 7617d84.
Rama `codex/p1-critic-epochs`. [Protocolo congelado](../protocols/P1-approved-v1.md)
y [configuración](../protocols/P1-approved-v1.json). P0 y su diagnóstico intactos.

## Diseño y criterio anterior a resultados

18 corridas nuevas K=2, semillas 510031/510047/510081 y condiciones C0/C5/C10.
Orden de condiciones C0-C5-C10 / C5-C10-C0 / C10-C0-C5; dentro de cada condición,
brazos 2→4 / 4→2 / 2→4 según semilla. Solo cambian épocas del crítico (2/4).
Actor, arquitectura, tasas, N_A=64/N_Q=N_B=400, muestreo y calendario Q/A/B intactos;
d=-ln(.90) común, sin cambios retrospectivos. CPU float64, un hilo, sin CUDA.

Criterio primario: tras la primera actualización, MSE post-A del brazo4 <=0.8×
MSE post-A del brazo2 en al menos dos de tres semillas, con integridad/finitud.
Control negativo: mismo A inicial y actor tras esa actualización idéntico.
Las tres condiciones repiten la comparación inicial: **tres bloques de semillas,
no nueve réplicas**. Segunda iteración solo diagnóstico secundario. Si ambos MSE
son cero, la desigualdad literal se satisface pero el porcentaje es indefinido.

Se instrumenta A entero y targets fijos antes del actor, después del actor/antes
del crítico y después del crítico. Se registran MSE, media(G²)+1e-12, estadísticas
de V/G, hashes de A y modelos, eta/lambda, shortfalls y coeficientes. En el inicio
se mide el cambio de gradiente con/sin riesgo mediante autograd sin aplicarlo.
Las pérdidas de minibatch quedan rotuladas como prepaso, aunque se escriben después.
Los diagnósticos no cambian parámetros, gradientes existentes, RNG ni Adam.

## Integridad, recursos y verificación previa

Un runner común exige protocolo y permiso de supervisor ligados a semilla,
condición, brazo y corrida. Pausas únicamente en Q0/dual completos; todos los
checkpoints se conservan. Falta de correspondencia inicial A/actor detiene campaña,
sin sustituir una corrida ni seleccionar por MSE. Se registran recursos ya
consumidos antes de validar esa correspondencia.

Bloqueo global único para entradas públicas P0/P1, consumo previo leído de ledgers
sin alterarlos. 3h GLOBAL/día La Paz, timestamps UTC; carga, comprobaciones y
cierre dentro de la ventana. Para esta entrega se carga conservadoramente además
el intervalo entero desde creación de rama hasta lanzamiento: incluye desarrollo,
pruebas sintéticas y publicación. Recibo de preparación separado, no aprendizaje.
Sin estimaciones P0 para admitir una configuración nueva: primer Q0/iteración
usa topes 1800/2700 s; después 1.5×máximo medido de condición/brazo. Reserva 1800 s,
RSS máximo 10GiB, máximo tres sesiones por corrida y 27 acumuladas de campaña.

198 pruebas sintéticas pasan en 68.45 s; Ruff final pasa. Incluyen reanudación
exacta con cuatro épocas, igual actor/A inicial, contador adicional de crítico,
permisos por brazo, bloqueo/débito diario persistente y diagnósticos sin efecto
sobre parámetros/Adam/RNG/gradientes. Dos pruebas de reporte adicionales cubren
conteo de semillas y desigualdad exacta; están incluidas en las 198.
[Comandos](../evidence/p1-execution/COMMANDS.md) y
[revisión previa](../evidence/p1-execution/REVIEW.md). No atribuir tiempos sintéticos
a rendimiento de mercado. Los fallos intermedios de desarrollo están conservados.

## Alcance de las conclusiones

El criterio evalúa ajuste sobre A utilizado para entrenar al crítico. Un resultado
positivo no demuestra generalización, rentabilidad ni cumplimiento CVaR, y no
congela épocas definitivas. B forma parte del aprendizaje vía lambda; no es
validación externa. No se accede a validación cronológica ni conjunto final.
No se modifica la tesis ni se autoriza otra campaña por terminar P1.

## Resultado del criterio primario

**Cumplido en 3/3 semillas** (mínimo predefinido: 2/3). Las 18 corridas completaron sus dos iteraciones; sin fallos de integridad, valores no finitos, pausas ni reintentos. Los nueve pares semilla/condición verificaron mismo A inicial y actor posterior idéntico. Los tres controles por semilla repiten exactamente los MSE, hashes A y actor; no aumentan el número de réplicas independientes.

| Semilla | MSE post-A, 2 épocas | MSE post-A, 4 épocas | Reducción | Cumple ≥20% |
|---|---:|---:|---:|---|
| 510031 | 0.0191134948 | 0.0094144755 | 50.74% | Sí |
| 510047 | 0.0274345902 | 0.0113297886 | 58.70% | Sí |
| 510081 | 0.1399264058 | 0.0777488528 | 44.44% | Sí |

MSE media por transición, sobre los mismos 64 episodios y targets Monte Carlo completos. No se normalizaron targets ni se reajustó el normalizador. C0 se usa como fila representativa; C5/C10 son controles idénticos aquí, no evidencia económica adicional. Los hashes se cotejaron también con los parámetros de los 18 checkpoint-1 existentes, sin pasos de optimizador.

## Resultados por corrida

Tiempo = suma de las tres unidades supervisadas, con carga/guardado; diferencia pequeña frente al total global por orquestación. Las columnas MSE corresponden a después del crítico en A fijo de cada iteración, no pérdidas de minibatch.

| Corrida | Semilla | Épocas | Tiempo s | MSE post-A k=0 | MSE post-A k=1 | Alertas |
|---|---:|---:|---:|---:|---:|---:|
| run-00-C0-e2 | 510031 | 2 | 150.102 | 0.01911349 | 0.01166199 | 18 |
| run-01-C0-e4 | 510031 | 4 | 147.112 | 0.00941448 | 0.00823821 | 33 |
| run-02-C5-e2 | 510031 | 2 | 149.112 | 0.01911349 | 0.01166199 | 18 |
| run-03-C5-e4 | 510031 | 4 | 147.112 | 0.00941448 | 0.00823821 | 33 |
| run-04-C10-e2 | 510031 | 2 | 148.110 | 0.01911349 | 0.01166199 | 18 |
| run-05-C10-e4 | 510031 | 4 | 148.120 | 0.00941448 | 0.00823821 | 33 |
| run-06-C5-e4 | 510047 | 4 | 147.117 | 0.01132979 | 0.00891196 | 34 |
| run-07-C5-e2 | 510047 | 2 | 145.116 | 0.02743459 | 0.01071448 | 18 |
| run-08-C10-e4 | 510047 | 4 | 148.117 | 0.01132979 | 0.00891196 | 34 |
| run-09-C10-e2 | 510047 | 2 | 147.119 | 0.02743459 | 0.01071448 | 18 |
| run-10-C0-e4 | 510047 | 4 | 143.114 | 0.01132979 | 0.00891196 | 34 |
| run-11-C0-e2 | 510047 | 2 | 148.116 | 0.02743459 | 0.01071448 | 18 |
| run-12-C10-e2 | 510081 | 2 | 144.118 | 0.13992641 | 0.08018536 | 18 |
| run-13-C10-e4 | 510081 | 4 | 148.120 | 0.07774885 | 0.02480876 | 34 |
| run-14-C0-e2 | 510081 | 2 | 145.120 | 0.13992641 | 0.08018536 | 18 |
| run-15-C0-e4 | 510081 | 4 | 148.118 | 0.07774885 | 0.02480876 | 34 |
| run-16-C5-e2 | 510081 | 2 | 147.119 | 0.13992641 | 0.08018536 | 18 |
| run-17-C5-e4 | 510081 | 4 | 148.122 | 0.07774885 | 0.02480876 | 34 |

## Tiempo y presupuesto diario compartido

Ejecución P1: **20:57:30.868958–21:41:41.392234 UTC del 24/09/2026**, día local 24/09/2026 America/La_Paz. Pared global supervisada **2650.523273 s (44 min 10.523 s)**; tiempo activo del supervisor 2650.116934 s.

| Cargo al presupuesto del día | Segundos |
|---|---:|
| P0 ya cerrado | 1385.677054 |
| Preparación conservadora P1 desde creación de rama | 1387.837745 |
| Ejecución supervisada P1 | 2650.523273 |
| **Total registrado compartido** | **5424.038072** |

Total **1 h 30 min 24.038 s**, por debajo de 3h. Incluye desarrollo/pruebas/publicación en el intervalo de preparación cargado, además de carga/verificación/guardado/cierre del ejecutor. Redacción/exportación posterior separada de la ejecución; no nuevas sesiones ni aprendizaje. El tope diario no se reinició entre las 18 corridas. Cada corrida consumió una sesión de ese mismo día (18 de las 27 máximas de campaña), sin concurrencia. La evidencia de débitos de otras campañas se conserva en el registro global y preparation.json.

| Brazo | Trayectorias | Transiciones | Pasos actor | Pasos crítico | Pared unidades s | Tiempo fase crítico s |
|---|---:|---:|---:|---:|---:|---:|
| 2 épocas | 19152 | 3447360 | 144 | 144 | 1324.031279 | 0.207048 |
| 4 épocas | 19152 | 3447360 | 144 | 288 | 1325.053835 | 0.401509 |

Total: **38304 trayectorias / 6894720 transiciones / 288 pasos actor / 432 pasos crítico**. El brazo4 duplica pasos del crítico, no duplica trayectorias ni pasos actor. Los tiempos globales similares no significan costo adicional cero: la fase medida del crítico fue 0.207048 s frente a 0.401509 s; carga/recolección dominan esta configuración pequeña. No es una prueba estadística de equivalencia temporal ni una promesa para otras máquinas/tamaños.

Pico RSS observado del trabajador: **376410112 bytes (358.973 MiB)**; no es memoria total del sistema. 54 unidades completadas dentro de topes. Se conservaron los 54 checkpoints, sin selección por resultados. Tiempos por fase/unidad/condición/brazo y versiones completas en el JSON.

## Advertencias y diagnóstico secundario

Hubo **465 entradas de advertencia**, todas `critic_relative_mse`: 162 en brazo2 y 303 en brazo4. No comparar conteos brutos como tasa de inestabilidad: el brazo4 tiene más mediciones de minibatch (306 oportunidades frente a 162); tres de sus mediciones no superaron 1. No se dispararon otras alertas preespecificadas. Los diagnósticos nuevos de A completo se informan por separado y no añaden silenciosamente alertas al esquema P0.

Aun mejorando el ajuste, todos los MSE post-A completos permanecieron por encima del predictor cero. Tras primera actualización, razones MSE/media(G²) del brazo4: 1.709, 1.852 y 16.483; después de la segunda: 1.344, 1.689 y 4.228. El criterio de reducción relativa aprobado no equivale a un umbral de adecuación absoluta del crítico.

La segunda iteración también mostró menor MSE post-A en el brazo4 para las tres semillas, pero es secundaria. La igualdad del primer actor implica el mismo segundo A; distintos críticos previos producen distintas ventajas y pueden cambiar el segundo actor. No se atribuyen diferencias de B a eficacia poblacional del riesgo.

Todas las corridas C5/C10 tuvieron penalización y gradiente inicial de riesgo no nulos en k=1: C5 contó 6/3/5 trayectorias activas por semilla, C10 9/6/8, iguales entre brazos. En k=0 lambda era cero y el término no estuvo activo; C0 siempre mantuvo riesgo apagado. Las auditorías finales F_B de C5/C10 siguieron por encima de d. No hubo ajustes de d ni reemplazo de lotes.

## Cierre y siguiente paso

**P1 cerrado, criterio técnico cumplido.** La intervención apoya la hipótesis de mejor ajuste in-sample con cuatro épocas en este diseño acotado. No acredita convergencia, generalización, mejora del actor, rentabilidad ni CVaR poblacional. Cuatro épocas no quedan adoptadas automáticamente como parámetro definitivo. Corresponde revisar académicamente el resultado, la persistencia de error absoluto y el próximo protocolo antes de otra campaña. No hay autorización implícita de P2 ni de evaluación confirmatoria.

[Resultados completos](../evidence/p1-execution/campaign-results/results.json), [comprobación de cierre](../evidence/p1-execution/closure-checks.json), [log](../evidence/p1-execution/campaign.log) y [resumen académico](P1-resumen-academico.md).
