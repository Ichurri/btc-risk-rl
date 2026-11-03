# Resumen académico: cierre WF05

WF05 se cierra **`incomplete`**: aceptó Q0 y diez actualizaciones del
corte de desarrollo 2021 (11/22 unidades), sin iniciar el corte 2022. El
preflight del 02/11/2026 falló por memoria disponible inferior a 4 GiB.
Se adjudica conservadoramente ese día como el segundo activo, pues la
campaña consumió tiempo en suite, auditoría y preflight aunque no abriera
otra sesión supervisada. El ledger histórico continúa `ready` como último
estado técnico, pero el permiso operativo ya está cerrado y no permite
reanudarlo.

La conciliación suma sin solapamiento el intervalo ledger/bitácora del
01/11 (3.484,510 s) y la primera suite anterior al ledger (339,63 s):
**3.824,140 s como mínimo distinto**, 224,140 s sobre el tope propio diario
de 3.600 s. Las otras suites de ese día quedaron dentro del intervalo ya
cargado. El 02/11, el contador automático marcó 0 s, pero la suite midió
390,45 s y la envolvente de auditoría a cierre fue 560 s. Los tiempos
individuales de Ruff, preflight y cierre no quedaron disponibles; no se
fabrican ni se añaden dos veces. La suma conservadora de envolventes de
los dos días fue 4.726 s, menor que el tope acumulado de 5.400 s, sin
resolver la desviación diaria ni autorizar un tercer día.

El estudio aporta una medida del costo del corte 2021, pero ninguna del
2022. Por ello no permite declarar viable el presupuesto de la propuesta
de evaluación v1.2. El resultado no evalúa rentabilidad, generalización
ni cumplimiento CVaR. Informe y fuentes:
[cierre](OOS-v1-2-costo-cortes-05-cierre-incomplete.md).
