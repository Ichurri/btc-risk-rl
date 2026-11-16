# Evaluación final OOS v1.2: cierre y contraste pareado

**15/11/2026, America/La_Paz.** Este cierre corresponde exclusivamente a
los 108 checkpoints `K10` de `main-2018-2022`, distribuidos en 36 bloques
pareados de semillas y tres condiciones por bloque. No seleccionamos un
checkpoint por 2023 ni por el resultado final. El corte `wf-2021` se conserva
como diagnóstico descriptivo: sus 99 unidades y sus huellas son íntegras,
pero el bloqueo original no probó exclusividad. `wf-2022` y el entrenamiento
principal son independientes. El cargo conservador del 12/11 excedió el
límite global en la conciliación posterior; no se admitió una unidad después
del límite de admisión. Ambas salvedades quedaron registradas antes de abrir
2023 y no se borran por este resultado.

## Procedencia y puertas

El entrenamiento principal cerró 108/108 corridas, 36/36 ternas y
1.188/1.188 unidades. Su ledger tiene SHA-256
`c3e1d793997e6379739d01223876962260d988c892ed44c7b161878adfc81e6b`.
La [puerta técnica 2023](OOS-v1-2-evaluacion-2023-cierre-20261115.md)
evaluó las mismas 108 políticas, 2.190 transiciones cada una, sin selección
por desempeño; cierre SHA-256
`a2e33b16dc8f6e56e25ca0975afc080ca16348b9c2ee9b1dcfef42afdbd3d5e3`.
La [fuente final](OOS-v1-2-final-fuente-20261115.md) se adquirió después,
con 4.386 transiciones 2024–2025 y 43 velas de contexto concordantes con
2023. Manifiesto exportado SHA-256
`db842235decd93fef2e04e49fbfb4f20752e9239f1c99eecb84f9e3e6e742436`.
El normalizador quedó congelado, SHA-256
`a598a99c368f1d50bba9f78fca2f803e46d77702d05547ccc12d076771e57479`.

El permiso independiente de evaluación final se registró en `01dbe3a`,
SHA-256 `4706de79552b39969517925782e8b5cf3e5ab6197fbe3f1b1a8492de912e34e2`,
y se activó en `f762968` tras fijar código, fuente, cierre técnico y
presupuesto. La huella de código fijada fue
`b0cfbfcb6cb5c95b8c5455a2221be0c7d736a64b83e6fe1b438c65f043c793b3`.
La [comprobación previa](../evidence/oos-v12-evaluation-20261115/final-evaluation-preflight.json)
dio `ready`: CA conectada, batería 96 %, memoria disponible 13.242.314.752 B,
disco libre 83.574.996.992 B, `Linger=yes`, gestor de usuario `running`,
sin otra campaña y con saldo para las 108 unidades y reserva. Son mediciones
de ese instante.

## Ejecución y auditoría

Una sola sesión `oos-v12-final-eval-20261115-01.service`,
`InvocationID=f8647d06d9d64a90a69e3b24b63c4b1d`, arrancó a las
10:19:50 y cerró a las 10:39:57 hora de La Paz, `Result=success`.
La bitácora cargó **1.205,838761 s**; `systemd` informó 22 min 28,685 s de
CPU y pico de 7,4 GiB de memoria de cgroup.
Las 108 duraciones de unidad sumaron 481,585058 s (mediana 4,455435 s;
rango 4,122465–4,745521 s). La diferencia hasta el cargo de sesión
incluye comprobaciones y supervisión; no se atribuye toda a una sola fase.
Ledger
`artifacts/oos-v12-final-2024-2025-01/ledger.jsonl`: `completed`, 108/108
políticas, 36/36 bloques, `pending=null`, SHA-256
`b035e1fef6d5e95b2b75df660cc178382081552207be30358f632f49a7e513ad`.
Cada recorrido tuvo 4.386 transiciones en una cartera continua con acción
determinista `sigmoid(μ)`, costos y normalizador congelados. El contraste
original `artifacts/oos-v12-final-2024-2025-01/final-contrast.json` tiene
SHA-256 `636ba000cf4b3f9820ea56828e99b7ae7b4f6a9d9d83185064c3fce67ac1cf1c`.

La [reauditoría independiente](../evidence/oos-v12-evaluation-20261115/final-contrast-audit.json)
abrió el ledger cerrado, cotejó las 108 huellas de reportes y trazas,
recalculó el contraste con el método congelado y obtuvo igualdad exacta.
Los 108 Sortino son definidos. Ningún recorrido ni lote parcial entró a
inferencia. Los originales locales no se modificaron. El resumen de
presupuesto al cierre registró 6.245,352197 s cargados el 15/11 y
41.454,647803 s antes de la reserva de 2.700 s; este saldo es una captura
posterior a la sesión, no una autorización de repetirla. La preparación
incluyó cargos de pared reconstruidos conservadoramente, distintos del
tiempo CPU medido. Los cuatro gates de evaluación se cerraron
prospectivamente después de verificar el contraste; los registros de
aprobación históricos permanecen para auditoría.

La verificación y preparación de esta publicación consumió tiempo después
del cierre de la sesión final. Se registró en la bitácora compartida un
intervalo **conservador de pared** desde las 10:39:57 hasta las 14:48:15
locales, **14.898,529470 s**. Incluye la suite y el trabajo posterior; no
es tiempo CPU ni una medición de una nueva unidad. Una excepción `KeyError`
ocurrió al construir el JSON de evidencia **después** de que el intervalo
quedara cerrado en la bitácora; se verificó la cadena y se escribió
[el comprobante](../evidence/oos-v12-evaluation-20261115/postclose-budget-debit.json)
sin cargarlo por segunda vez. El saldo tras ese cargo fue
**21.143,881667 s** gastados el 15/11 y **26.556,118333 s** antes de la
reserva. Los artefactos finales originales mantuvieron sus huellas.

## Contraste congelado

Métrica primaria: Sortino anualizado, `sqrt(2190) × Sortino_4h`, usando
retornos simples netos de cuatro horas, MAR=0 y desviación bajista sobre
todos los períodos. La anualización es una convención de reporte, sin
suponer independencia temporal. Se comparó por bloque de semilla,
`C5−C0` y `C10−C0`, mediante bootstrap pareado unilateral de 19.999
remuestras centrado bajo la nula y ajuste de Holm con error familiar 0,05.
Los intervalos de 95 % son descriptivos, no la regla unilateral de decisión.
El efecto mínimo de interés fijado antes del final fue **+0,50 unidades**
de Sortino anualizado.

| Contraste | Diferencia media | IC descriptivo 95 % | `d_z` pareado | `p` unilateral | `p` Holm | Decisión |
|---|---:|---:|---:|---:|---:|---|
| C5−C0 | +0,000317 | [−0,000657; +0,001323] | +0,102 | 0,26285 | 0,4588 | No rechazar H0; no alcanza +0,50 |
| C10−C0 | +0,000200 | [−0,000330; +0,000745] | +0,118 | 0,22940 | 0,4588 | No rechazar H0; no alcanza +0,50 |

Medias descriptivas de Sortino anualizado: C0 **0,979688**, C5
**0,980005**, C10 **0,979888**. Son 36 políticas por condición sobre un
único período final, no 108 períodos independientes. La decisión
estadística es **no rechazar** las hipótesis nulas de superioridad de C5 y
C10 frente a C0. No equivale a demostrar igualdad o inferioridad. Tampoco
demuestra rentabilidad, generalización a otros regímenes ni cumplimiento
poblacional de CVaR. El Sortino continuo mide transferencia operacional;
el objetivo CVaR de entrenamiento corresponde a episodios de 180
transiciones. PBO y DSR no son estimables con los insumos y rutas realmente
ejecutados; los dos cortes cronológicos no producen caminos CPCV.

**Resumen trasladable al capítulo 4.** En el período final 2024–2025 se
evaluaron de forma continua las 108 políticas fijadas al terminar el
entrenamiento, en 36 ternas pareadas. Las diferencias medias de Sortino
anualizado fueron +0,000317 para C5 y +0,000200 para C10 frente a C0.
Tras bootstrap pareado unilateral y corrección de Holm, ambos valores
ajustados fueron 0,4588, por lo que no se rechazaron las hipótesis nulas
de ausencia de superioridad. Las diferencias tampoco alcanzaron el efecto
mínimo de interés predefinido, +0,50. Estos datos delimitan el resultado
de este período y este diseño; no acreditan una garantía CVaR poblacional.

## Material reproducible para el capítulo 4

El [CSV de 36 bloques](../evidence/oos-v12-evaluation-20261115/chapter-4/paired-blocks.csv)
conserva las tres métricas y ambas diferencias por semilla. La
[figura de bloques](../evidence/oos-v12-evaluation-20261115/chapter-4/paired-blocks.svg)
presenta 72 diferencias pareadas: el eje horizontal indica **bloques**, no
tiempo. La [figura de contraste](../evidence/oos-v12-evaluation-20261115/chapter-4/paired-inference.svg)
muestra medias e intervalos descriptivos de las dos comparaciones.
Todas indican período, unidad, población y fuente. El generador solo lee
el contraste original y su auditoría, comprueba la huella y vuelve a
calcular la inferencia congelada; no abre velas ni checkpoints.

```bash
uv run --frozen python scripts/render_oos_final.py \
  --contrast artifacts/oos-v12-final-2024-2025-01/final-contrast.json \
  --audit docs/evidence/oos-v12-evaluation-20261115/final-contrast-audit.json \
  --output docs/evidence/oos-v12-evaluation-20261115/chapter-4
```

## Comandos y comprobaciones realmente ejecutados

```bash
uv run --frozen pytest -q                       # 694 passed, 2 warnings antes del gate de cierre
uv run --frozen ruff check .                     # conforme
uv run --frozen python -m btc_risk_rl.evaluation.historical_final_supervisor final-preflight
# ready; evidencia en final-evaluation-preflight.json
systemd-run --user --unit=oos-v12-final-eval-20261115-01 \
  --property=Restart=no --property=WorkingDirectory=/home/ichurri/Desktop/personal_projects/btc-risk-rl \
  /home/ichurri/.local/bin/uv run --frozen python -m btc_risk_rl.evaluation.historical_final_supervisor run-final
# Result=success; 108 aceptadas
uv run --frozen pytest -q tests/test_oos_final_figures.py tests/test_oos_v12_evaluation_access.py tests/test_oos_v12_final_supervisor.py
# 18 passed tras cerrar gates
uv run --frozen pytest -q                       # 698 passed, 2 warnings tras cerrar gates, 905,39 s
uv run --frozen ruff check .                     # conforme tras cerrar gates
```

Una primera ejecución de la suite posterior al cierre se interrumpió
porque se movió el generador gráfico fuera del paquete ejecutable para
preservar exactamente la huella de código fijada antes de la campaña.
Las dos pruebas de reingreso WF señaladas en esa salida parcial se
repitieron en estado estable: 2 passed; la suite completa estable terminó
698 passed. La huella ejecutable postcierre siguió
`b0cfbfcb6cb5c95b8c5455a2221be0c7d736a64b83e6fe1b438c65f043c793b3`.
La [verificación postcierre](../evidence/oos-v12-evaluation-20261115/final-postclose-verification.json)
resume el resultado estable de suite, Ruff, huella de código y figuras.
Las huellas pequeñas quedan en
[`docs/evidence/oos-v12-evaluation-20261115/`](../evidence/oos-v12-evaluation-20261115/).
No se ejecutó otra actualización de aprendizaje ni se seleccionó un
checkpoint por el resultado final.
