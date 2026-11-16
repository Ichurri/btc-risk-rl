# Métricas secundarias de la evaluación final OOS v1.2

**16/11/2026. Análisis descriptivo posterior al cierre de la prueba
confirmatoria.** Se utilizaron las 108 trazas aceptadas de BTC/USDT de
2024–2025, con 4.386 retornos simples netos de cuatro horas por política.
Cada condición incluye las 36 semillas y se conservó el apareamiento por
bloque. El contraste confirmatorio de Sortino se muestra con los valores
leídos de la auditoría original, incluidos sus valores p de Holm.

## Procedencia e integridad

Se cotejó el SHA-256 del ledger final
`b035e1fef6d5e95b2b75df660cc178382081552207be30358f632f49a7e513ad`.
Antes de calcular se verificaron los SHA-256 de las **108 trazas y los
108 reportes** contra ese ledger. Todos estaban disponibles. Se comprobó
que las fechas y precios de apertura y cierre eran idénticos entre trazas,
así como la coherencia entre patrimonio, cartera y retornos guardados. El
Sortino recalculado coincidió exactamente con los 108 valores de
[paired-blocks.csv](../evidence/oos-v12-evaluation-20261115/chapter-4/paired-blocks.csv).
La huella del CSV y el detalle numérico de la comprobación están en
[integrity.json](../evidence/oos-v12-secondary-metrics-20261116/integrity.json).

La referencia de comprar y mantener se reconstruyó desde los precios
coincidentes de las trazas. Se invirtieron los 10.000 USDT en la primera
apertura, con comisión de 0,1 % y deslizamiento de 0,05 %, y se conservó
la posición hasta la valoración final. La cantidad, el patrimonio, el
retorno y el Sortino concordaron con la
[referencia auditada](OOS-v1-2-buy-hold-referencia-20261115.md).
El error absoluto de Sortino fue 2,89 × 10⁻¹⁵. Los cierres, protocolos y
artefactos originales se conservaron en solo lectura. Las huellas y los
pasos para reproducir la entrega se documentan en
[COMMANDS.md](../evidence/oos-v12-secondary-metrics-20261116/COMMANDS.md).

## Reglas de cálculo

| Métrica | Regla |
| --- | --- |
| Retorno acumulado neto | Patrimonio final dividido por 10.000 USDT, menos uno. |
| Sharpe anualizado | Media de los retornos dividida por su desviación estándar muestral, multiplicada por √2190. Tasa libre de riesgo cero. |
| Sortino anualizado | Media dividida por la raíz de la media de los cuadrados de los retornos negativos, incluyendo los ceros de los demás períodos, multiplicada por √2190. MAR cero. |
| Maximum Drawdown | Máximo de 1 − patrimonio / máximo acumulado. La serie comienza con 10.000 USDT y la caída se presenta como magnitud positiva. |
| Calmar | ((patrimonio final / patrimonio inicial)^(2190/4386) − 1) / Maximum Drawdown. |
| CVaR periódico al 5 % | Media de pérdidas de los peores retornos netos de cuatro horas. Con pérdida = −retorno, la cola de 4.386 observaciones tiene masa 219,3, equivalente a 219 valores enteros y 0,3 del valor siguiente. Los empates en el límite tienen la misma contribución por unidad de masa. |
| Turnover anualizado | 2.190 por la media de los cambios absolutos del peso BTC valorado al cierre, incluida la primera transición desde exposición cero. Incluye cambios de peso por el precio. 100 % anual equivale a una unidad de exposición al año. |

La anualización es una convención. Un denominador cero produce una métrica
indefinida. Si una métrica tiene un valor indefinido dentro de una condición
o contraste, las agregaciones correspondientes quedan indefinidas y se
registra la cobertura. En este conjunto las siete métricas fueron definidas
para las 108 políticas y la referencia. La desviación estándar de la
referencia, con un recorrido, queda sin definir.

Las diferencias C5−C0 y C10−C0 corresponden a los mismos bloques.
Se usaron 20.000 remuestras con reemplazo de 36 bloques, PCG64 con semilla
912016 y percentiles 2,5 y 97,5 de su media. Se reutilizó la misma secuencia
de índices en cada métrica y comparación. Estos intervalos describen
variación entre semillas sobre un solo período histórico. El intervalo
descriptivo de Sortino de esta tabla y el del cierre pueden diferir por
el remuestreo. El informe muestra por separado el contraste original.

## Resultados y piezas para la tesis

- [Métricas de las 108 políticas](../evidence/oos-v12-secondary-metrics-20261116/metrics-by-policy.csv)
- [Resumen por condición y referencia](../evidence/oos-v12-secondary-metrics-20261116/summary-by-condition.csv)
- [Diferencias pareadas descriptivas](../evidence/oos-v12-secondary-metrics-20261116/paired-differences.csv)
- [Cuatro figuras, datos CSV e informe HTML](../evidence/oos-v12-secondary-metrics-20261116/)
- [Tablas, párrafos, pies de figura y ajustes propuestos](../tesis/insertar-en-tesis.md)

En los CSV los porcentajes se guardan como fracciones y se convierten a
porcentaje en las tablas y figuras. Las curvas presentan la mediana
punto a punto y la banda P5–P95 sobre las 36 políticas por condición.
La curva de caída se calcula primero para cada cartera. El gráfico de
exposición incluye también la media aritmética. La primera marca
representa el capital antes de ejecutar y las marcas posteriores el fin
UTC de cada intervalo de cuatro horas. El final coincide con el límite
de 01/01/2026 00:00 UTC, sin incluir una vela de 2026.

Las diferencias observadas de Drawdown y CVaR periódico son descriptivas.
El CVaR de cuatro horas y la restricción de CVaR de 180 transiciones del
entrenamiento miden riesgos distintos. La atribución a otras ventanas
de mercado requiere nueva evidencia. Los resultados de la simulación
no constituyen una recomendación de inversión.
