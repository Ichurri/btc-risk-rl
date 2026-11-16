# Aprendizaje por refuerzo sensible al riesgo para trading en Bitcoin

Repositorio de la tesis de **Santiago Andrés Iturri Vargas**. El estudio
compara PPO neutral al riesgo con dos variantes que incorporan una restricción
de valor en riesgo condicional (CVaR), en un simulador de BTC/USDT con velas de
cuatro horas, comisiones y deslizamiento.

## Resultados de la evaluación final

Se evaluaron **108 políticas** sobre el período 2024–2025, en **36 bloques
pareados** por semilla. Cada política recorrió las mismas **4.386
transiciones**. Los checkpoints K10 se fijaron antes de consultar el
período final y la evaluación técnica de 2023 comprobó el funcionamiento
de la ruta sin seleccionar políticas por desempeño.

| Condición | Objetivo de entrenamiento | Sortino anualizado medio | Diferencia frente a C0 | p ajustado por Holm |
| --- | --- | ---: | ---: | ---: |
| C0 | PPO neutral al riesgo | 0,979688 | — | — |
| C5 | PPO con CVaR sobre el 5 % de cola | 0,980005 | +0,000317 | 0,4588 |
| C10 | PPO con CVaR sobre el 10 % de cola | 0,979888 | +0,000200 | 0,4588 |

Ninguna diferencia alcanzó el efecto mínimo de interés predefinido
(+0,50 unidades de Sortino) y la prueba no aportó evidencia de superioridad
de C5 o C10 frente a C0. La evaluación se limita a este período y diseño.
El Sortino no mide el cumplimiento poblacional de la restricción CVaR.

Comprar y mantener BTC, como referencia descriptiva sobre el mismo período,
obtuvo **1,421389** de Sortino anualizado y **+106,98 %** de retorno acumulado
neto. La inferencia pareada incluye únicamente los contrastes C5−C0 y C10−C0.

- [Informe final y contraste estadístico](docs/hitos/OOS-v1-2-final-evaluacion-cierre-20261115.md)
- [Resultados por bloque y figuras](docs/evidence/oos-v12-evaluation-20261115/chapter-4/)
- [Auditoría de comprar y mantener BTC](docs/hitos/OOS-v1-2-buy-hold-referencia-20261115.md)

## Metodología y evidencias

| Componente | Documentación |
| --- | --- |
| Datos, exclusiones y preparación segmentada | [H1](docs/hitos/H1-preparacion-segmentada.md) |
| Simulador, ejecución y valoración | [H3](docs/hitos/H3-contrato-ADR002.md) |
| Formulación del riesgo y horizonte de aprendizaje | [ADR-002](docs/decisions/ADR-002-risk-horizon.md) |
| Agentes, recolección y checkpoints | [H4](docs/hitos/H4-agentes-recolector.md) · [H5](docs/hitos/H5-infraestructura.md) |
| Pilotos de desarrollo | [Informes de los hitos](docs/hitos/) · [Evidencias](docs/evidence/) |
| Evaluación fuera de muestra | [Protocolo fijado antes de la evaluación](docs/protocols/OOS-v1-2-evaluation-method-freeze-20261111.json) |

El repositorio contiene el código, las pruebas, los protocolos y los
resultados resumidos. Las fuentes históricas, los checkpoints y las trazas
completas se conservan localmente. Sus manifiestos y huellas están
documentados en las evidencias. Los permisos históricos de evaluación
están cerrados.

## Instalación y comprobaciones

Requisitos para Debian o un entorno Linux equivalente. Git, uv y Python
3.11–3.13. El archivo `uv.lock` fija las dependencias, incluido PyTorch
para CPU.

```bash
git clone https://github.com/Ichurri/btc-risk-rl.git
cd btc-risk-rl
uv sync --frozen
uv run --frozen btc-risk config-check
uv run --frozen ruff check .
uv run --frozen pytest
```

Consulte [la guía de Debian](docs/DEBIAN.md) y, si dispone de las evidencias
locales, [el dashboard de avances](docs/DASHBOARD.md) o [el informe de
pilotos](docs/hitos/visualizacion-experimentos-local.md).

## Referencias del repositorio

Para citar código o evidencia, use el enlace de GitHub al commit concreto
que contiene el archivo. El [inventario de consolidación](docs/REPOSITORY-HISTORY.md)
identifica los commits de las antiguas ramas. Las instrucciones operativas
y los antecedentes se conservan en el [registro de continuidad](docs/HANDOFF.md).
