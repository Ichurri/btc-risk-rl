# Ruta sintética completa de evaluación continua — calibración v1.2

**Hito técnico, no adopción de la propuesta fuera de muestra.** Rama
`codex/oos-v1-2-synthetic-evaluator`, base `1d976d9`. Las cinco unidades
`systemd --user` procesaron exclusivamente series fabricadas. No se ejecutó
entrenamiento ni se abrió validación 2023 o prueba final 2024–2025.

## Ruta implementada y alcance

El comando [run_oos_synthetic_evaluation.py](../../scripts/run_oos_synthetic_evaluation.py)
admite **solo** longitudes 1.979, 2.190 o 4.386 y una semilla sintética; no
acepta ruta de mercado. La entrada pública solo escribe dentro de una raíz
`artifacts/oos-synthetic-evaluation-*` nueva. El trabajador rechaza una
solicitud alterada o una ubicación en artefactos históricos antes de leerla.

El trabajador verifica SHA-256 del checkpoint fijo P3 y del manifiesto y
normalizador H1 **exclusivos de entrenamiento**. Carga el actor CPU float64
con pesos congelados; genera OHLCV sintético con 42 barras de calentamiento
en un calendario ficticio de 2010, calcula las diez características H1 y
aplica el normalizador persistido sin refit. En una cartera única, con reloj
`h=1`, calcula `sigmoid(μ)`, ejecuta en la siguiente apertura mediante
`rebalance`, y guarda acciones, caja, BTC, comisiones, deslizamiento,
patrimonio, retorno simple neto de cuatro horas y recompensa logarítmica.
No hay resets, gradientes ni selección de checkpoints.

El trabajador escribe la traza completa y métricas: media neta, desviación
bajista sobre **todos** los períodos, Sortino anualizado con `√2190`, retorno
logarítmico acumulado y máximo drawdown. `σ₋=0` se representa como indefinido.
El padre supervisa tiempo y RSS, relee la traza serializada, verifica
continuidad, autofinanciación, exposición objetivo, costos y retornos, coteja
métricas y huellas, y solo entonces escribe `audit.json` y `closure.json`
atómicos. Una unidad parcial, reporte incoherente o fallo del trabajador
queda `failed`, sin aceptación. Los eventos y el log se conservan.

**Límite:** es una ruta completa **para series sintéticas**, con el contrato
contable H3 y entradas H1 congeladas. No sustituye el futuro evaluador
histórico sujeto a particiones, índices, normalizador de cada corte y permisos
separados. No hay inferencia financiera a partir de los retornos fabricados.

## Medición del proceso completo en Debian

Se usaron cinco unidades transitorias nuevas bajo `systemd --user`, sin
concurrencia. La medición externa de Bash `time` comienza antes de pedir la
unidad y termina después de su parada; incluye `systemd`, arranque de Python,
carga, recorrido, supervisión, serialización, auditoría y cierre. Es una
medición local con caché y carga del equipo de ese momento, **no una cota**.
Raíz local final: `artifacts/oos-synthetic-evaluation-20261026-final/`.

| Longitud fabricada | Wall externo | Wall de supervisor | Carga checkpoint+scaler+config | Bucle contable | Memoria pico systemd | Archivos de corrida |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1.979 | 6,727 s | 5,326 s | 3,709 s | 0,286 s | 622,7 MB reportados | 598.574 B |
| 2.190 A | 6,631 s | 5,220 s | 3,572 s | 0,318 s | 622,7 MB | 662.117 B |
| 2.190 B | 6,833 s | 5,328 s | 3,588 s | 0,325 s | 622,9 MB | 662.115 B |
| 4.386 | 7,080 s | 5,628 s | 3,601 s | 0,644 s | 622,6 MB | 1.321.791 B |
| 2.190, control final de costos | 7,916 s | 6,127 s | 4,112 s | 0,371 s | 622,7 MB | 662.121 B |

El pico RSS del trabajador supervisado fue de 566–568 MB; el pico de
`systemd` incluye el conjunto de procesos de la unidad. La raíz completa,
incluidos logs, journals y salidas de Bash, ocupó **3.269.017 B**; la raíz
adicional del control final, **668.232 B**. Las tres
trazas de 2.190 pasos tienen la misma SHA-256
`07ffbf7dc177251a…` (huella íntegra en el JSON), pese a iniciar
procesos y unidades separados. Los cinco cierres son
`completed_synthetic`, los cinco `Result=success`; los `InvocationID`,
journals y hashes individuales están en
[results.json](../evidence/oos-v1-2-synthetic-evaluation/results.json).
`systemd --user` estaba en estado `degraded` por `swaync.service`, pero las
cinco unidades de sonda finalizaron con éxito; esto no convalida un
preflight para campaña histórica futura.

La primera raíz `artifacts/oos-synthetic-evaluation-20261026/` conserva las
cuatro sondas previas a dos controles finales añadidos al auditor (cotejo de
exposición objetivo y SHA del normalizador). La tabla anterior usa
**exclusivamente** la segunda raíz. Tras añadir el cotejo de totales de
costos del trabajador, una quinta unidad en
`artifacts/oos-synthetic-evaluation-20261026-guard/` verificó el código
definitivo y reprodujo la misma traza de 2.190 pasos. Su pared mayor muestra
variación del host: una sola duración no es un límite. Se repitió solo la
calibración sintética, sin modificar ni repetir campañas de mercado.

## Presupuesto v1.2 actualizado

El wall externo medido incluye la parte que faltaba en `1d976d9`. Repetir
**aritméticamente**, no ejecutar, 9 recorridos de 1.979 pasos, 9 de 2.190,
108 de 2.190 y 108 de 4.386 daría **1.659,003 s** usando la media de los
tres procesos de 2.190 pasos.
Es extrapolación de 234 procesos fabricados, no tiempo histórico. No se
sustituyen por ella los topes propuestos de evaluación/auditoría.

El cálculo v1.2 conserva **91.593,878 s extrapolados** para 126
entrenamientos y **43.200 s de asignaciones aún no medidas** para
evaluación, auditoría, refit y cierre: 134.793,878 s productivos. Veinte días
de tres horas globales con reserva de 2.700 s/día permiten 162.000 s
productivos: margen **27.206,122 s**, **solo si** la tasa P3 y las
asignaciones se sostienen. El promedio máximo de entrenamiento bajo esos
supuestos es 942,857 s/corrida, frente a 726,936 s medidos en P3. Si el
estudio de costo de cortes propuesto consume íntegramente sus 5.400 s
**dentro del mismo cupo de 20 días**, el margen baja a 21.806,122 s,
18 días mínimos y umbral medio de 900 s/corrida. Si se presupuestara como
fase previa con días activos propios, no se añadiría retrospectivamente a la
campaña; en cualquier fecha rige el máximo diario global compartido.

**No puede afirmarse que 20 días basten.** La medición pendiente decisiva es
el wall por unidad de entrenamiento en los cortes purgados y la variación de
las nuevas 126 corridas; tampoco se midió la carga de recorridos históricos
autorizados, sus guardas y auditoría real a escala. El
[protocolo acotado de cortes](../proposals/OOS-v1-2-costo-entrenamiento-cortes-v1.md)
fija cómo medir la primera brecha, **sin ejecutarla**. La propuesta v1.2
sigue sin adoptarse y el permiso histórico P3 permanece cerrado.

## Integridad y pruebas

El registro [COMMANDS.md](../evidence/oos-v1-2-synthetic-evaluation/COMMANDS.md)
conserva comandos, fallos esperados y pruebas. La sonda abre únicamente
checkpoint P3 fijo, manifiesto y scaler del derivado de entrenamiento y
`configs/initial.toml`; los nombres de longitud equivalentes a otros años
no son archivos. Pruebas analíticas verifican Sortino, contabilidad de dos
pasos, continuidad, costos, exposición, rechazo de traza parcial y datos
alterados, hash corrupto y equivalencia de ejecuciones repetidas. Los
ledgers P0/P1/P2/P2R/P3 y la huella agregada P3 se cotejan sin editarlos.
La suite final pasó **360/360** y Ruff no reportó hallazgos. Una prueba
antigua de P0 se corrigió para tratar `ProcessLookupError` como proceso ya
terminado al leer `/proc`; no se tocó el supervisor ni la evidencia P0.
