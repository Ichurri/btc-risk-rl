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
Por ello esta entrega NO contiene un dataset aprobado ni un simulador. ADR-003
describe el bloqueo y el siguiente trabajo. No corregirlo quitando validaciones.

La configuración/CLI no exponen comandos de entrenamiento o prueba final.
Las pruebas usan fixtures sintéticos, salvo la auditoría real documentada.
Los datos de desarrollo originales acompañan el paquete en data/raw/ con sus
huellas; están excluidos de Git. Para reutilizarlos verificar el manifiesto.
