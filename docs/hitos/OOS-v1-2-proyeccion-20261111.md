# Proyección separada de entrenamiento y evaluación — 11/11/2026

**Corte de esta proyección:** 21:10 `America/La_Paz`. La segunda sesión
`oos-v12-training.service`, `InvocationID`
`9d306358db424a7c87ac4abe8c2cacba`, seguía activa. Este documento no
es cierre de campaña ni evaluación de políticas.

**Actualización posterior:** esa sesión pausó a las 21:31 con seis ternas
completas. La [auditoría de cierre](OOS-v1-2-sesion-02-20261111.md) reemplaza
las cifras de entrenamiento de esta captura: **68.212,696 s extrapolados
de unidades restantes** y 47.008,738 s de débito protocolario, del cual
12.801,316 s corresponden a un hueco entre sesiones cobrado de forma
conservadora. La estimación de evaluación y sus límites no cambiaron.

## Entrenamiento hasta el 16/11 a las 09:00

El ledger principal auditado al cierre anterior tenía SHA-256
`d0d4562da56e585f081c8bc7558f9c8db8b66c78fbcf216290cd5cbab1bf0b44`,
`ready`, 16 corridas completas y 186 unidades aceptadas. Cinco ternas
semilla–C0/C5/C10 estaban completas. La verificación cotejó la cadena de
562 estados y las 558 huellas de checkpoint, reporte y solicitud; el
último checkpoint aceptado entonces fue `run-16-C0-b0/checkpoint-9`, SHA-256
`c33ff5961c1cbff19e81bb159155d31bf59957e03e7faa66ef287417878153a8`.
La sesión nueva continúa desde esa frontera; sus unidades posteriores solo
cuentan al aceptarse en el ledger.

| Bloque | Semilla | Tiempo medido de 33 unidades (s) |
| ---: | ---: | ---: |
| 0 | 1869792951 | 2.258,869 |
| 1 | 309092095 | 2.246,075 |
| 2 | 391604748 | 2.266,412 |
| 3 | 133987343 | 2.329,475 |
| 4 | 495937704 | 2.258,195 |

La media medida es **2.271,805 s por terna**. Multiplicar por las 31
restantes da **70.425,961 s = 19,563 h de unidades**, una extrapolación
que todavía no descuenta las unidades aceptadas de la sexta terna ni
incluye suite, Ruff, preflight, carga, auditoría o cierre por sesión.
El cargo global reconciliado al cerrar la sesión anterior fue
**31.675,357 s** el 11/11; quedaban **16.024,643 s antes de la reserva
obligatoria de 2.700 s**. La segunda sesión sigue consumiendo ese saldo;
el saldo final del día se medirá al pausar. El límite prospectivo es
50.400 s globales por fecha `America/La_Paz`, reserva de 2.700 s,
20 días activos y corte de presentación el 16/11 a las 09:00.

Si se mantienen la tasa de estas cinco ternas, la alimentación, la memoria
y la admisión diaria, el tiempo de unidades remanente cabe antes del corte
de presentación. Un cierre alrededor del 13/11 es **escenario condicional**,
no fecha comprometida: las siguientes sesiones añaden gastos aún variables,
y una guarda de recursos o un fallo de unidad puede detener el diseño.
No se acortan las 36 ternas para producir un contraste parcial.

## Evaluación, estimación independiente

El [inventario de solo metadatos](https://github.com/Ichurri/btc-risk-rl/blob/7f140e8/docs/hitos/OOS-v1-2-fuentes-evaluador-20261111.md)
identificó 2023 en H1: cobertura declarada **2.190/2.190 velas**, un
segmento y cero exclusiones; requiere 2.233 velas con contexto. No abrió
sus filas ni sustituye la auditoría de origen/exportación al autorizar
esa partición. **No hay fuente local identificada** para 2024–2025;
requiere 4.429 velas con contexto, 4.386 transiciones y cotejo exacto de
43 velas de contexto con H1. Existe un descargador paginado **interno,
apagado y probado con respuestas inventadas** para Binance spot BTCUSDT
4 h; obtener cobertura real y fijar huellas sigue pendiente del permiso
final separado. No se solicita ahora que el usuario ubique un archivo.

La sonda supervisada **sintética** anterior midió 6,631, 6,833 y 7,916 s
para 2.190 pasos, y 7,080 s para 4.386. Extrapolar aritméticamente da
**769,680 s (12,83 min)** para 108 políticas en 2023 y **764,640 s
(12,74 min)** para 108 políticas en el final, **1.534,320 s (25,57 min)
sumados**. No son tiempos medidos de 216 evaluaciones históricas ni cotas:
faltan adquisición de la fuente final, exportación/auditoría de ambas
fuentes, 108 cargas y cierres por partición, presupuesto y supervisor
histórico. Los topes anteriores de 10.800 s por partición son asignaciones,
no tiempos observados.

La evaluación **no puede calendarizarse firmemente para el 16/11** hasta
que cierren y se auditen las 36 ternas, se integre/verifique el supervisor
histórico, se armonice la tesis y se fijen permisos separados con huellas.
2023 será una comprobación técnica predefinida de las 108 políticas, sin
selección por desempeño; solo un cierre técnico íntegro permite abrir el
final. Ninguna fuente protegida se abrió para esta proyección.

## Comandos de consulta realmente ejecutados

```bash
systemctl --user show oos-v12-training.service -p ActiveState -p SubState -p MainPID -p InvocationID
uv run --frozen python -  # cálculo de cinco ternas y huellas con el ledger aceptado; ver reporte-codex.md
uv run --frozen python -  # inspect_oos_debit/read_budget sobre los ledgers y la bitácora existentes
```

La tabla de fuentes, sus huellas y los comandos de inventario están en el
informe enlazado. Los cálculos de esta nota usan únicamente el histórico
de entrenamiento aceptado y los metadatos ya publicados.
