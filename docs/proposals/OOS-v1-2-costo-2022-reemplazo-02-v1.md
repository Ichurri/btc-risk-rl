# Reemplazo técnico WF 2022-02 tras fallo previo al ledger

**PROPUESTA DE CONTINUIDAD PROSPECTIVA; gate cerrado, 07/11/2026.** Sustituye únicamente
la identidad operativa del intento `2022-01`, que terminó `failed` durante
la suite previa a Q0. La autorización del usuario para corregir fallos
recuperables y medir el corte 2022 no permite reescribir ni reanudar aquel
intento. Los hechos y huellas se conservan en
`docs/hitos/OOS-v1-2-costo-2022-primer-intento-fallido.md`.

| Identidad | Reemplazo exclusivo |
| --- | --- |
| Raíz nueva | `artifacts/oos-v12-wf-cost-only-2022-02/` |
| Aprobación nueva | `docs/protocols/OOS-v1-2-wf-cost-2022-only-02-approval.json` |
| Intentos previos al ledger | `artifacts/shared-pilot-budget/wf-2022-only-02-attempts.jsonl` |
| Comprobaciones durables | `artifacts/shared-pilot-budget/wf-2022-only-02-checks.jsonl` |
| Servicio por sesión | `oos-wf-cost-2022-02-session-NN.service`, `Restart=no` |

**Sin cambio científico:** una corrida C10 nueva, semilla 498614892,
β=0, cuatro épocas del crítico, K=10, D=64, d=−ln(0,90), corte 2022
reconstruido únicamente del derivado H1 de entrenamiento. Q0 y diez
Q/A/B+D dan 11 unidades; ningún peso, Q0, trayectoria ni checkpoint de
`2022-01` o WF05 es elegible. El orden y las fronteras `after_q0` y
`after_dual_and_D` son los del
[`protocolo original`](OOS-v1-2-costo-2022-exclusivo-v1.md).

**Sin ampliación temporal:** 10.800 s globales por fecha La Paz con 2.700 s
de reserva; 3.600 s propios por día con 600 s de reserva; 4.800 s propios
acumulados en máximo dos días activos; cotas 120 s Q0 y 180 s por
Q/A/B+D. La ventana 01:00–09:00 incluye preparación y cierre y no amplía
esos límites. Cada unidad requiere tiempo para cota, checkpoint y reserva
antes de medianoche y las 09:00.

El intento `2022-01` carga conservadoramente **10.800 s globales el
07/11/2026**, aunque duró 440,610179 s. El presupuesto compartido del
reemplazo y de otras campañas debe seguir leyendo su bitácora original.
Por tanto, el reemplazo **no puede iniciar unidades el 07/11**. La bitácora
`2022-02` inicia antes de cualquier comprobación específica de esa campaña
en una fecha posterior; sus cargos propios no se mezclan con los de
`2022-01`, pero ambos se reconcilian en el límite global de cada fecha.

Antes del permiso técnico: reparar la prueba contextual de P2R, verificar
la suite y Ruff, probar que un intento `2022-01` fallido consume el global
aun con la nueva identidad, y probar primer arranque y reingreso de
`2022-02` con fuente controlada. El registro nuevo debe fijar por huella
código, este protocolo, configuración, derivado H1 y autorización de
continuidad; el gate permanece cerrado hasta completar esas pruebas. En
una fecha nueva, solo con CA, batería ≥50 %, memoria ≥4 GiB, disco ≥20 GiB,
`Linger=yes`, gestor `running`, huellas y presupuesto conformes, ejecutar
suite/Ruff y preflight vigilado **dentro de la bitácora nueva**. Una unidad
fallida o una bitácora `failed` no se reanuda; se conserva toda evidencia.

Esta medición sigue siendo **costo**, no selección de política ni evaluación
financiera. Validación 2023 y prueba final 2024–2025 permanecen cerradas;
la propuesta confirmatoria v1.2 no se activa con este reemplazo.
