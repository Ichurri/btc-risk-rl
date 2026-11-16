# Protocolo propuesto para cronometrar entrenamiento en dos cortes

**PROPUESTA PARA REVISIÓN. NO AUTORIZADA PARA EJECUCIÓN.** Complementa la
[propuesta fuera de muestra v1.2](cierre-pilotos-evaluacion-fuera-muestra-v1-2.md)
y la [calibración sintética de proceso completo](../hitos/OOS-v1-2-evaluador-sintetico.md).
No adopta los 36 bloques, no activa un permiso de mercado y no habilita
validación 2023 ni prueba final 2024–2025.

## Objetivo y diseño congelado de la medición

Estimar el costo de **entrenamiento** de dos cortes purgados del histórico de
desarrollo usando una corrida nueva por corte. Se elige **C10** en ambos para
incluir el mecanismo de riesgo, con β=0, cuatro épocas del crítico, K=10,
D=64, Q/A/B, d=−ln(0,90), horizonte y tamaños de lote de la propuesta v1.2.
La elección de C10 es de cobertura computacional, no una elección por
rendimiento; una sola condición **no demuestra** que C0 y C5 tarden igual o
menos. No se compararán políticas ni se seleccionarán checkpoints.

| Orden fijo | Corte de entrenamiento | Semilla exclusiva de costo | Condición | Unidades exactas |
| --- | --- | ---: | --- | ---: |
| 1 | 2018–02/12/2020, observar 2021 solo después de otro permiso | 276696733 | C10 | Q0 + 10 Q/A/B+D = 11 |
| 2 | 2018–02/12/2021, observar 2022 solo después de otro permiso | 498614892 | C10 | Q0 + 10 Q/A/B+D = 11 |
| **Total** | Dos entrenamientos independientes | Dos semillas | C10 | **22** |

Las semillas se obtuvieron, respectivamente, de los primeros ocho bytes de
`SHA256("btc-risk-rl/oos-v1.2/wf-cost-only/2021")` y `/2022`, como entero
big-endian, con `1 + entero mod (2³¹−1)`. El cálculo versionado verifica que
son distintas entre sí y disjuntas de las 36 semillas principales, las tres
auxiliares de v1.2 y las semillas P0–P3. **No se emplean en la inferencia
final ni reemplazan las tres auxiliares por corte.**

La raíz reservada para una eventual autorización es
`artifacts/oos-v12-wf-cost-only-01/`, que **no se crea en este hito**.
Cada corrida usaría subcarpeta, ledger, checkpoints y generadores propios;
ningún estado P0–P3 se restaura o reutiliza. Las dos corridas avanzan en el
orden de la tabla, sin concurrencia. Las unidades aceptables terminan solo en
`after_q0` o `after_dual_and_D`. No se computan métricas de rendimiento como
puerta de continuación.

## Entradas y puertas previas

Antes de un eventual lanzamiento se requiere autorización separada y un
ejecutor específico verificado. El preflight deberá comprobar, **antes de la
primera trayectoria**, Git/lock/configuración y código fijados, permiso de
esta medición, raíz nueva, ausencia de campañas activas, alimentación CA,
batería ≥50 %, memoria disponible ≥4 GiB, disco libre ≥20 GiB, `Linger=yes`,
gestor `systemd --user`, presupuesto compartido y huellas del derivado H1
exclusivo de entrenamiento. Los dos productos de corte necesitan manifiestos
auditados propios: exactamente 3.639/4.678 inicios H180 y 5.764/7.703
observaciones de ajuste, exclusiones/segmentos intactos y ningún byte de 2023.
Los productos de la calibración anterior miden reconstrucción, pero no son
por sí solos permiso ni aceptación para entrenar.

El ejecutor solo podrá abrir el derivado de entrenamiento y los productos
auditados de corte. Rechazará CSV H1 compartidos, validación y final antes de
recolectar trayectorias. Debe registrar cada archivo abierto y sus SHA-256.
Los modelos, normalizadores y rutas de cada corte estarán aislados.

## Tiempo, admisión y parada predefinidos

- El día se define por `America/La_Paz`; todos los eventos llevan UTC. Máximo
  **10.800 s globales/día** compartidos con cualquier actividad autorizada,
  incluyendo preflight, carga, unidades, guardado y cierre; descontar gasto ya
  registrado. Reservar **2.700 s/día** para cierre. Esta medición puede usar
  **hasta 3.600 s productivos por día**, como máximo dos días activos, y
  **5.400 s productivos acumulados**, sin reiniciar al cambiar de corte.
- Cota de admisión por unidad: **120 s para Q0** y **180 s para cada
  Q/A/B+D**. Las 22 cotas suman 3.840 s; quedan 1.560 s del cupo de 5.400
  para preflight, carga, cambios de unidad, auditoría y cierre. Se exige que
  la cota completa de la próxima unidad quepa simultáneamente en el saldo
  diario global después de reserva, el saldo diario propio y el acumulado.
  Si no cabe, pausa solo en una frontera completa y reanudación otro día
  después de repetir preflight; no reducir unidades ni reserva.
- Superar una cota de unidad, perder supervisor, señal dentro de una unidad,
  no finitud, reporte/contador/checkpoint incoherente o cambio de huellas
  deja el estudio `failed` irreversible. Conservar unidad parcial, ledger y
  checkpoints anteriores como evidencia; su conservación **no habilita
  reanudación**. Al agotarse dos días o 5.400 s sin completar 22 unidades,
  declarar `incomplete`, sin ampliar límites ni repetir selectivamente.
- No se detiene por MSE, retorno, shortfall, auditoría B o coste observado
  desfavorable. La variación temporal se informa íntegra; no se elige el
  menor tiempo ni el checkpoint más favorable. Si una de las dos corridas
  falla, no se sustituye semilla ni condición.

Las cotas son límites propuestos, **no estimaciones medidas para estos cortes**.
El ledger P3 midió máximos de 33,477 s en Q0 y 86,828 s en iteración para
sus unidades, en el histórico de entrenamiento completo; no valida el costo
de los nuevos cortes. Los máximos y semillas se reproducen en
[results.json](../evidence/oos-v1-2-synthetic-evaluation/results.json).

## Evidencia y lectura permitida

Por unidad: registro de autorización, solicitud, inicio/fin UTC, `InvocationID`,
journal de `systemd --user`, wall/CPU/RSS/disco, contadores Q/A/B y D,
versiones de política, identidad de ruta y realización, checkpoint completo
con hash, reporte con hash y ledger encadenado. Por corte: huellas de datos,
normalizador, índices, código, configuración, conteos y presupuesto restante.
Cierre: 22/22 unidades o estado `failed`/`incomplete`, sin limpieza de evidencia.

La comparación de tiempos de los dos cortes puede sustituir **solo** la
extrapolación de costo de las 18 corridas auxiliares por una extrapolación
basada en sus dos C10. No demuestra costo de C0/C5 ni convierte el diseño de
36 bloques en viable. La decisión de los 20 días se vuelve a calcular con
todos los gastos, condiciones y reservas; si no cabe, se revisa el protocolo
antes de otra campaña. Ningún resultado de esta medición es evidencia de
rentabilidad, generalización ni cumplimiento de CVaR.
