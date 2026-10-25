# Calibración técnica de costos para la propuesta fuera de muestra v1.2

**Calibración, no adopción del protocolo ni autorización de evaluación.** Rama
`codex/oos-v1-2-cost-calibration`, base `1195484`. Solo se reconstruyeron dos
cortes con el derivado H1 exclusivo de entrenamiento y se recorrieron series
fabricadas. No hubo gradientes, actualizaciones, campañas ni apertura de datos
de 2023 o 2024–2025.

## Procedencia y alcance de cada sonda

- Cortes: `data/processed/p2r-training-h1/{manifest.json,bars.csv}`; SHA-256
  del manifiesto `62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9`.
  Las barras llegan hasta 2022; las de diciembre de 2017 solo aportan
  calentamiento. Reconstrucción por segmento con la rutina H1, mismo historial
  de 42 barras y corte de entrenamiento el 02/12/2020 o 02/12/2021 UTC.
  `TrainScaler.fit` usa exclusivamente los timestamps de entrenamiento previos
  al corte. Los productos derivados quedan en una raíz nueva ignorada por Git.
- Carga: `artifacts/p3-approved-v1/run-00-C0-b0/checkpoint-10/state.pt`,
  corrida fijada por ruta y sin selección por desempeño. Se deserializó el
  checkpoint completo y se cargó solo el actor CPU float64, sin restaurar
  optimizadores ni reanudar la campaña. La huella concreta está en
  [results.json](../evidence/oos-v1-2-cost-calibration/results.json).
- Recorridos: 1.979, 2.190, 2.190 y 4.386 transiciones **sintéticas**. Son
  longitudes equivalentes a 2021, 2022, 2023 y el período final planeado;
  los nombres no significan que se abrieron esos años. Se fabricaron precios y
  diez componentes de mercado con RNG fijo, y se usó una sola cartera,
  `rebalance` float64, costos del contrato y reloj constante `h=1`. Esto mide
  inferencia y contabilidad en un bucle de calibración, **no** la ruta completa
  del futuro evaluador H3 con guardas y procedencia reales. Los retornos
  sintéticos se guardaron solo para medir métricas y auditoría; no son
  resultados experimentales.
- `Actor.deterministic_action` y `FrozenPolicy.deterministic_action` calculan
  `sigmoid(μ(o))`, mediana de la logística-normal. Se rechazan observaciones,
  distribuciones o acciones no finitas y saturación a 0/1; no hay clipping ni
  consumo de RNG. Las pruebas comprueban el valor analítico y repetibilidad.

## Mediciones en este equipo

Reloj `perf_counter`, cada fase en proceso separado; RSS pico de ese proceso.
Los tiempos internos no incluyen arranque de Python/importaciones, planificación
`systemd` ni cierre supervisor. Una sola medición por corte y longitud; cinco
cargas del mismo checkpoint, con caché de disco potencial. No son cotas.

| Fase | Segundos medidos | Pico RSS | Disco nuevo |
| --- | ---: | ---: | ---: |
| Corte 2021: reconstruir / refit+transformar / guardar | 0,262 / 0,014 / 0,085; total 0,392 | 268.936 KiB | 1.595.106 B |
| Corte 2022: reconstruir / refit+transformar / guardar | 0,338 / 0,003 / 0,118; total 0,478 | 273.976 KiB | 2.111.417 B |
| Checkpoint P3 fijo: deserializar + cargar actor | 3,520 en sonda aislada; media de cinco 3,557 | 557.012 KiB | lectura de 41 MB; no se copia |
| Bucle sintético 1.979 / 2.190 (corte 2022) pasos | 0,281 / 0,264 | ~557.000 KiB | 15.960 / 17.648 B retornos |
| Bucle sintético 2.190 (2023) / 4.386 pasos | 0,255 / 0,514 | ~557.000 KiB | 17.648 / 35.216 B retornos |
| Cálculo Sortino y auditoría SHA por recorrido | 0,0006–0,0007 total | ~247.000 KiB | JSON pequeño |

Los recuentos regenerados coinciden con la auditoría indexada: 3.639 y 4.678
inicios H180; 5.764 y 7.703 observaciones para ajuste. El archivo local de
sondas ocupa 3,8 MB en total. Había aproximadamente 152,4 GB libres al medir;
es una observación momentánea. El mayor RSS de la sonda fue 557.312 KiB.
No se midió la memoria ni el disco del entrenamiento de 126 corridas. La
campaña P3 existente ocupa 5.326.594.447 B; escalarla a 126 corridas sería
solo una extrapolación de almacenamiento, no una reserva garantizada.

## Presupuesto recalculado sin confundir sondas con campaña

La tasa **medida en P3** para nueve corridas β=0 fue 726,936 s/corrida.
Aplicarla a las 126 corridas nuevas da **91.593,878 s extrapolados**: 78.509
principales y 13.085 en cortes. Los topes aún **no medidos** de la v1.2 suman
43.200 s: 10.800 para la comprobación 2023, 10.800 para el final si se
autoriza y 21.600 para auditoría, refit, inferencia y cierre. Su suma con el
entrenamiento extrapolado es **134.793,878 s**. Con 20 días activos × 8.100 s
productivos quedan **27.206,122 s condicionales**; otros 2.700 s/día están
reservados para cierre dentro del máximo global de 3 h/día.

Las sondas permiten descomponer una parte del rubro pendiente: repetir de modo
aritmético 234 cargas separadas, los cuatro bucles sintéticos según sus 9/9/108/108
recorridos, guardados y auditorías más los dos cortes medidos daría **921,401 s**
de trabajo interno. Es **extrapolación de una sonda**, no costo real del
ejecutor ni permiso para sustituir los 43.200 s de asignaciones. No contempla
importaciones por proceso, supervisión, preflight, lecturas de evaluación,
serialización/inspección de 126 entrenamientos o variación del host.

| Factor supuesto sobre tasa P3 de entrenamiento | Trabajo con los otros topes intactos | Días productivos mínimos | ¿Cabe aritméticamente en 20? |
| ---: | ---: | ---: | --- |
| 1,00 | 134.794 s | 17 | Sí, condicionado |
| 1,20 | 153.113 s | 19 | Sí, condicionado |
| 1,30 | 162.272 s | 21 | No |
| 1,50 | 180.591 s | 23 | No |

Si los otros topes se mantienen, el promedio máximo de entrenamiento sería
**942,857 s/corrida**, 1,297 veces la tasa P3. Incluso bajo ese promedio,
unidades largas pueden no caber antes de la reserva diaria y obligar pausas en
fronteras completas. **No se puede establecer aún que 20 días sean suficientes.**
Faltan exactamente (1) el costo por unidad y variación de entrenamiento en
los dos cortes reconstruidos y en la nueva campaña, (2) una medición de la
ruta de evaluación continua completa con cargas, guardas, registros y
supervisión, que requeriría autorización distinta para 2023/final, y (3) el
costo de auditoría y cierre reales a escala de 126 corridas. No se deben
inferir estas magnitudes de la sonda sintética.

## Integridad y límites

Los archivos abiertos por la sonda están enumerados en cada JSON local. El
origen de cortes fue **solo** el derivado exclusivo de entrenamiento; no se
abrieron CSV H1 compartidos. El checksum agregado de los 47.487 archivos
P3 permaneció `73949350733bf3f8e3939e2dfcf7a28920668e738b0e5d910bd070a010fdcbec`,
igual a la auditoría anterior. Los hashes de ledgers P0/P1/P2/P2R/P3 y de
cada resultado están en [COMMANDS.md](../evidence/oos-v1-2-cost-calibration/COMMANDS.md)
y [results.json](../evidence/oos-v1-2-cost-calibration/results.json).
P0–P3, permisos, reportes y checkpoints originales no se editaron. La
propuesta v1.2, 36 bloques y 20 días siguen **para revisión, no adoptados**.
Pruebas focales 17/17, suite final 351/351 y Ruff sin hallazgos. Una pasada
intermedia de la suite tuvo una carrera en un test antiguo del supervisor P0;
se registró y la repetición aislada y completa pasó. Ver comandos y resultado
exacto en el registro enlazado.
