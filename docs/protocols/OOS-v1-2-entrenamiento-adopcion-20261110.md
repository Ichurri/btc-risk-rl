# Adopción operativa de entrenamiento v1.2 — 10/11/2026

**Alcance:** Santiago autorizó preparar, verificar y ejecutar hasta el
16/11/2026 el entrenamiento que quepa bajo los límites vigentes, sin esperar
otra aprobación académica entre etapas. Esta adopción fija **solo la parte de
entrenamiento** de la propuesta [v1.2](../proposals/cierre-pilotos-evaluacion-fuera-muestra-v1-2.md).
La tesis no se modifica aquí. Validación 2023 y prueba final 2024–2025
permanecen cerradas hasta que se congelen y comprueben sus puertas técnicas.

El contrato legible por máquina es
[`OOS-v1-2-training-freeze-20261110.json`](OOS-v1-2-training-freeze-20261110.json),
SHA-256 `0651f396f3157eaa5abd6bb7faf7ec1c6463210d255fa2fbd8a932e2999870a0`.
Fija explícitamente 126 identidades nuevas y disjuntas: primero nueve
entrenamientos en el corte 2021, después nueve en el corte 2022 y por último
36 tripletes principales C0/C5/C10 sobre 2018–2022. En cada bloque de
semilla se rota el orden. Las semillas proceden de la lista propuesta v1.2
SHA-256 `74785abcea1f1517818d92f7402dd21035f720a0efa8540d482d9e48e7a8523d`.
No se reutilizan políticas, checkpoints ni corridas P3, WF05 o WF 2022-03.

Configuración común: actor y Q/A/B de ADR-002, crítico ordinario β=0,
cuatro épocas provisionales, K=10, D=64 solo observacional, horizonte 180,
γ=1 y cota común `d=−ln(0,90)`. El checkpoint elegible es exclusivamente
`after_dual_and_D` de la unidad 10 de cada corrida; no se elige por
desempeño. Cada corte reconstruye características, normalizador e índices
desde el prefijo de entrenamiento anterior, con purga de 180 velas.

La ventana operativa es **01:00–09:00 America/La_Paz**, con 10.800 s globales
por fecha y reserva de cierre de 2.700 s. El tope de campaña sigue siendo
20 días activos, pero este permiso termina al cerrar la ventana del
**16/11/2026**. Antes de cada unidad se exige CA, batería ≥50 %, memoria
disponible ≥4 GiB, disco ≥20 GiB y admisión por tiempo; el lanzamiento
requiere 6.026.846.208 B de memoria inicial. Cada Q0 y Q/A/B+D conserva
los topes de 1.800 s y 2.700 s y termina solo en frontera completa.
La suite, Ruff, preflight vigilado, carga y cierre se cargan desde el primer
registro durable; el presupuesto es compartido con campañas previas.

Una unidad interrumpida invalida su corrida/campaña; no se repite ni se
reemplaza selectivamente una semilla. Una pausa por presupuesto o recursos
solo permite reingreso desde checkpoint completo con guardas nuevas.
Resultados financieros de los dos cortes son diagnóstico de desarrollo,
sin selección retrospectiva. Si el 16/11 no hay 36 tripletes principales
completos, se informará avance parcial **sin contraste confirmatorio**.

El contraste previsto sigue siendo Sortino anualizado `√2190 × S_4h`,
retornos simples netos, MAR=0, desviación bajista sobre todos los períodos;
`σ₋=0` queda indefinido. Con 36 tripletes y acceso futuro autorizado al
final, las diferencias pareadas C5−C0 y C10−C0 usarían 19.999 remuestras
centradas con semilla 910031 y Holm unilateral familiar 0,05. El efecto
mínimo de interés es +0,50. No se imputan métricas indefinidas, no se
eliminan bloques y PBO/DSR solo se calculan si existen sus insumos reales.
Un Sortino mayor no demuestra cumplimiento poblacional de CVaR.

## Viabilidad calculada antes de lanzar

La [cuenta reproducible](../evidence/oos-v12-training-prep-20261110/costs.py)
lee solo ledgers aceptados y metadatos: WF05 midió 743,408 s para once
unidades 2021, WF 2022-03 midió 710,691 s para once unidades 2022, y las
nueve corridas P3 β=0 midieron 726,936 s por corrida. **Extrapolar** 18
corridas auxiliares da 13.087 s; 108 principales, 78.509 s. Desde el cierre
2022-03 hasta el 16/11 inclusive hay como máximo 55.452 s productivos.
Sin ningún gasto adicional, el techo aritmético es 19 tripletes principales;
con 500 o 900 s diarios supuestos de verificaciones, 17 o 16. Son escenarios,
no duraciones prometidas. Los 36 bloques no caben antes del 16/11 bajo
estas tasas y topes. Se conserva su tamaño: la presentación mostrará el
avance y el contraste completo requerirá fechas posteriores.

**Actualización de ventana el 10/11 a las 10:24 La Paz:** al terminar la
implementación, la ventana de ese día ya había cerrado. La primera fecha
admisible es el 11/11; quedan seis fechas y como máximo 48.600 s
productivos, suponiendo saldo íntegro en cada una. Bajo las mismas tasas,
el techo aritmético baja a **16 ternas principales** sin ningún gasto
adicional, o 14/13 con 500/900 s diarios supuestos. El tiempo de suite y
preflight se medirá y descontará en cada sesión; estas cuentas no prometen
un número de bloques.

**Puerta de lanzamiento:** código y registro de aprobación independientes,
suite completa, Ruff, preflight vigilado, huellas, gestor `systemd --user`
`running`, `Linger=yes`, fuente aceptada y saldo suficiente. Hasta fijar esa
aprobación en un commit separado, el ejecutor permanece cerrado.
