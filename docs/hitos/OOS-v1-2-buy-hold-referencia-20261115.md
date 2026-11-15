# Referencia descriptiva comprar y mantener BTC — apartado 4.4.1

**15/11/2026, America/La_Paz.** Esta referencia se calculó **después** de
cerrar el contraste principal C5/C10 frente a C0. No se incorporó como
tercera condición, no alteró la selección K10 ni los 108 reportes. La
autorización de Santiago se registró en el permiso limitado
[`OOS-v1-2-buy-hold-reference-approval.json`](../protocols/OOS-v1-2-buy-hold-reference-approval.json),
SHA-256 `3688c0ef758515d86a9faec1f87f2fbed693e2b6a770010bc573045a4a6440fd`.
El ejecutor y sus pruebas se fijaron antes del permiso en `31f2f9a` y
`1499ae8`; el gate propio se activó en `d9fc938` y se cerró
prospectivamente en `9a7256e`. Los cuatro gates anteriores de evaluación
de políticas permanecieron cerrados en todo momento.

## Fuente, población y regla

Se leyó únicamente la exportación final auditada
`data/processed/oos-v12-final-2024-2025-01/`: manifiesto SHA-256
`db842235decd93fef2e04e49fbfb4f20752e9239f1c99eecb84f9e3e6e742436`,
CSV SHA-256
`d123935a385001082a0c7915071980d5d85706970e509ff856ff1f024775759d`.
El [informe de fuente](OOS-v1-2-final-fuente-20261115.md) ya había
verificado cinco páginas crudas, 43 velas de contexto, OHLCV, continuidad
y normalizador de entrenamiento congelado. La huella del manifiesto crudo
es `85ab10e5d189e3bec0508bfd29f8da2d64ff8a6139c4d4363040c1e0a5232dbe`.
La ruta incluye exactamente **4.386 transiciones** de cuatro horas, de
2024-01-01 00:00 UTC a la última vela que abre 2025-12-31 20:00 UTC.
El cierre de esa última vela, usado para la valoración, corresponde a
2025-12-31 23:59:59,999 UTC. El campo `last_valuation_ms` del JSON
identifica **la apertura de la vela final**, igual que el índice del
evaluador; no es la hora de su cierre.

La cartera inicia con **10.000 USDT y cero BTC**. Tras la observación
inicial de 2023-12-31 20:00 UTC, compra en la primera apertura ejecutable,
2024-01-01 00:00 UTC a 42.283,58 USDT/BTC. La misma función H3
`rebalance` aplica peso objetivo 1, comisión 0,1 % sobre el valor ejecutado
y deslizamiento 0,05 % en la compra. Queda en caja cero y mantiene
**0,2361440890593785 BTC** sin nuevos trades ni interés. La valoración
final usa el cierre **87.648,22 USDT/BTC**, sin venta final. El capital,
ejecución, costos y marcado a cierre son los de la evaluación final de las
políticas; comprar y mantener no usa actor, checkpoint ni normalizador
para decidir acciones.

## Resultado y auditoría

| Magnitud | Valor | Alcance |
|---|---:|---|
| Comisión de compra | 9,990010 USDT | Una compra; incluida en la cantidad BTC adquirida |
| Deslizamiento de compra | 4,992509 USDT | Una compra; incluido en la cantidad BTC adquirida |
| Patrimonio final | 20.697,609070 USDT | Valoración a cierre, sin liquidación |
| Retorno acumulado neto | **+106,976091 %** | Patrimonio final / 10.000 − 1 |
| Sortino anualizado | **1,421389** | 4.386 retornos simples netos de 4 h; MAR=0 |

El retorno medio simple de cuatro horas fue
`0,0002188526727209249` y la desviación bajista, calculada **sobre todos
los períodos**, `0,007205449909682891`. Se informó
`sqrt(2190) × media / desviación_bajista`; la anualización es una
convención de reporte y no supone independencia temporal. El
[resultado original](../evidence/oos-v12-buy-hold-20261115/result.json),
SHA-256 `177745bf76a575ba8c9bbd8c1e24f4386dbd8cb3686c7ac78977cc7ce9b905a7`,
incluye precio, cantidad, costos, patrimonio, retornos y huellas.

El cálculo operativo reutilizó `rebalance` y `summarize_returns`. Una
[auditoría independiente](../evidence/oos-v12-buy-hold-20261115/independent-audit.json),
SHA-256 `9ff9955ccba52ba6e5f1d5392f5e05989332d4275251b3c0bdebb161f59f7133`,
releyó el CSV tras cotejar el permiso, verificó 4.429 filas con contexto y
la continuidad temporal, calculó directamente
`q = 10000/[P_apertura(1+s)(1+f)]`, luego `E_t=q×P_cierre,t`, los 4.386
retornos y el Sortino. Reprodujo +106,97609069576006 % y
`1,421388537238099` (diferencias de redondeo de coma flotante). No
ejecutó una política ni abrió o modificó las 108 trazas.

Antes y después, el ledger final conservó SHA-256
`b035e1fef6d5e95b2b75df660cc178382081552207be30358f632f49a7e513ad`
y el contraste principal
`636ba000cf4b3f9820ea56828e99b7ae7b4f6a9d9d83185064c3fce67ac1cf1c`.
La comprobación de cierre confirmó que el comando público rechaza otra
lectura con `PermissionError: Buy-and-hold reference disabled`.

La [bitácora de presupuesto](../evidence/oos-v12-buy-hold-20261115/budget-charge.json)
registra un único intervalo conservador de 2.346,955736 s para preparar,
calcular y auditar esta referencia, sin solaparlo con el cargo anterior.
Su SHA-256 es
`c60a9fc6c807a9481b109669824f06588e2b1504e0dac81e7f937a6c9ccd139f`.
El gasto global del 15/11 quedó en 23.490,837403 s, con 24.209,162597 s
antes de la reserva de 2.700 s. Esta medición no fue una nueva sesión de
evaluación de políticas.

## Comandos realmente ejecutados

```bash
uv run --frozen pytest -q tests/test_oos_buy_hold_reference.py tests/test_oos_synthetic_evaluation.py tests/test_oos_v12_evaluation_export.py tests/test_oos_v12_evaluation_runner.py
# 26 passed tras cerrar el gate; Ruff conforme
uv run --frozen ruff check .
# All checks passed!
uv run --frozen python scripts/oos_buy_hold_reference.py
# Una sola ejecución autorizada, durante el commit d9fc938; escribió result.json
sha256sum data/processed/oos-v12-final-2024-2025-01/manifest.json data/processed/oos-v12-final-2024-2025-01/bars.csv
sha256sum artifacts/oos-v12-final-2024-2025-01/ledger.jsonl artifacts/oos-v12-final-2024-2025-01/final-contrast.json
```

El comando de cálculo es reproducible con el código, fuente y permiso
fijados. **En el estado actual el gate está cerrado y la salida ya existe**:
otra ejecución requiere un permiso nuevo y una ruta de evidencia nueva;
no se reescribe esta medición. `sha256sum -c` sobre las evidencias pequeñas
verifica ahora su integridad sin reabrir la fuente.

## Párrafo propuesto para la tesis, §4.4.1

> Como referencia descriptiva se simuló comprar BTC en la primera apertura
> ejecutable del período 2024–2025 y mantener la posición hasta la
> valoración final, con 10.000 USDT iniciales, la misma comisión de 0,1 %,
> el mismo deslizamiento de 0,05 % y sin liquidación al cierre. Sobre 4.386
> transiciones de cuatro horas, la cartera terminó en 20.697,61 USDT,
> equivalente a un retorno acumulado neto de 106,98 %. El Sortino
> anualizado fue 1,4214, calculado con retornos simples netos, MAR=0,
> desviación bajista sobre todos los períodos y el factor convencional
> `sqrt(2190)`. Esta referencia se calculó tras cerrar el contraste
> principal y no participa en las pruebas pareadas C5−C0 o C10−C0; su
> resultado tampoco demuestra cumplimiento de una restricción CVaR.
