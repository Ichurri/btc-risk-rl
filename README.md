# BTC Risk RL — primera iteración

Tesis: Agente de aprendizaje por refuerzo sensible al riesgo para la toma de
decisiones de trading en Bitcoin. Santiago Andrés Iturri Vargas.

Repositorio de infraestructura experimental; no hay entrenamientos autorizados.
Leer AGENTS.md, docs/HANDOFF.md y docs/decisions/ antes de continuar con Codex.

## Debian local / entorno remoto
Requisitos: Git, Python 3.11–3.13 y uv disponible. Dentro de esta carpeta:

```bash
uv sync --frozen
uv run --frozen ruff check .
uv run --frozen pytest
```

No requiere GPU para datos ni pruebas. No modifica drivers. El lock fija las
dependencias; registrar Python/SO/dispositivo en cada ejecución. Los 6 GiB de
VRAM son estimación del usuario, pendientes de medir localmente.

## Coordinación
El repositorio incluye historial Git local; no hay proveedor remoto creado.
Tras elegirlo, añadirlo como origin y sincronizar las ramas. Compartir commit
y docs/HANDOFF.md entre este chat y Codex. No compartir únicamente cambios
descritos en una conversación sin archivos y evidencia.

## Protección
La configuración reserva 2024–2025 como prueba final. Los comandos de desarrollo
no pueden descargar ni preparar ese intervalo. No existe un flag para desbloquearlo.
No es una barrera de seguridad contra quien edita el código: es una guarda de
protocolo con pruebas. Una futura campaña final necesita un flujo separado y revisión.

## Estado
Consultar docs/hitos/ y docs/evidence/ para resultados reales, limitaciones y commits.
Las carpetas agents/, experiments/ y reporting/ están reservadas; no representan
funciones ya implementadas. ADR-002 bloquea CVaR-PPO hasta cerrar sus definiciones.

## Módulo de datos implementado

```bash
uv run --frozen btc-risk config-check
uv run --frozen btc-risk fetch-development
uv run --frozen btc-risk prepare-development
uv run --frozen btc-risk recheck-anomalies
```

Cada comando que escribe exige una carpeta de destino nueva; no sobrescribe
evidencia previa. Para otra ejecución usar --output con una ruta diferente.
prepare-development falla deliberadamente si detecta huecos o datos inválidos;
el detalle queda en quality.json y no se emiten características aceptadas.

La descarga real inicial contiene 16 aperturas ausentes y 20 cierres abreviados.
La ruta estricta sigue rechazando esos datos, como documenta ADR-003. La preparación
segmentada aprobada en ADR-004 dispone ahora de una ruta separada y aceptación
técnica de desarrollo. El simulador H2 consume esos índices auditados.
No retirar las validaciones estrictas.

## Preparación segmentada B (sin red)

```bash
uv run --frozen btc-risk prepare-segmented-development --output data/processed/segmented-B
uv run --frozen btc-risk verify-segmented-development --prepared data/processed/segmented-B
```

La preparación exige un destino nuevo y el histórico original identificado por
el diagnóstico; no descarga datos ni acepta anomalías nuevas automáticamente.
El verificador es de solo lectura. Emite máscara auditable, barras retenidas,
características, parámetros del normalizador, observaciones e índices temporales.
El ajuste usa cada observación finita de entrenamiento una sola vez; validación
reutiliza parámetros. Los episodios de 180 transiciones son solo de entrenamiento;
validación mantiene un único recorrido continuo. Consulte criterios, cobertura,
evidencias y límites en [H1 segmentado](docs/hitos/H1-preparacion-segmentada.md).

La configuración/CLI no exponen comandos de entrenamiento o prueba final.
Las pruebas usan fixtures sintéticos, salvo la auditoría real documentada.
Los datos de desarrollo originales acompañan el paquete en data/raw/ con sus
huellas; están excluidos de Git. Para reutilizarlos verificar el manifiesto.

## Simulador causal H2

Implementa exposición BTC posterior a costos, ejecución en apertura siguiente,
comisiones y deslizamiento adverso, contabilidad float64 y recompensa logarítmica
neta. Entrenamiento usa índices de 180 transiciones; validación es un recorrido
continuo. Los cortes truncan sin liquidar. No hay agente ni entrenamiento habilitado.

```bash
uv run --frozen python scripts/verify_simulator.py --context local --output artifacts/simulator-h2/real
```

El destino debe ser nuevo. Es una comprobación contable con acciones prefijadas,
no selección de estrategias. Uso, ecuaciones, límites y evidencia en
[H2 simulador](docs/hitos/H2-simulador.md). ADR-002 mantiene pendientes descuento,
horizonte y bootstrap antes de implementar PPO/CVaR-PPO.
