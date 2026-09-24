# BTC Risk RL

Tesis: Agente de aprendizaje por refuerzo sensible al riesgo para la toma de
decisiones de trading en Bitcoin. Santiago Andrés Iturri Vargas.

Repositorio de infraestructura experimental. P0-approved-v1 autoriza exclusivamente
el piloto técnico acotado sobre entrenamiento aceptado 2018–2022, con presupuesto
GLOBAL de 3h/día. Validación, prueba final y posteriores campañas siguen bloqueadas.
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
Repositorio en [GitHub](https://github.com/Ichurri/btc-risk-rl), remoto origin.
Compartir rama, commit y docs/HANDOFF.md entre este chat y Codex. No compartir únicamente cambios
descritos en una conversación sin archivos y evidencia.

## Protección
La configuración reserva 2024–2025 como prueba final. Los comandos de desarrollo
no pueden descargar ni preparar ese intervalo. No existe un flag para desbloquearlo.
No es una barrera de seguridad contra quien edita el código: es una guarda de
protocolo con pruebas. Una futura campaña final necesita un flujo separado y revisión.

## Estado
Consultar docs/hitos/ y docs/evidence/ para resultados reales, limitaciones y commits.
Agentes/recolector H4 y checkpoint/instrumentación H5 verificados; adaptador de
mercado solo para recolección congelada. experiments/ y
reporting/ siguen reservados; no representan una campaña experimental implementada. [ADR-002 v2.1 está adoptado](docs/decisions/ADR-002-risk-horizon.md);
H3 adapta el simulador; H4 implementa PPO/CVaR-PPO y recolector. Pilotos y
entrenamientos de mercado requieren autorización separada. Hay parámetros por congelar antes de comparar condiciones y de evaluar
confirmatoriamente; la prueba final permanece protegida.

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
técnica de desarrollo. El simulador H3 consume esos índices auditados, conservando los productos H1.
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
Los datos originales locales están en data/raw/ y excluidos de Git; GitHub
contiene sus manifiestos y huellas. Para reutilizarlos verificar el manifiesto.

## Simulador causal H3 — ADR-002 v2.1 adoptado

Conserva la contabilidad H2, exposición BTC posterior a costos, ejecución en apertura
siguiente, costos y recompensa logarítmica neta float64. Configuración schema 2;
observación de 13 componentes: diez de mercado, peso BTC, log patrimonio relativo
y reloj. Entrenamiento: H=180, gamma=1, reloj descendente, terminated=True en H,
sin bootstrap posterior ni liquidación. Validación: cartera continua, h=1 y
truncated=True solo al final de datos; es transferencia operacional.

Los checkpoints internos conservan estado y esperan H completo; no representan
muestras parciales de riesgo. Las rutas incompletas de entrenamiento se rechazan.
La compatibilidad con el manifiesto H1 se audita mediante cambios explícitos de
configuración, sin refit ni alteración de datos.

    uv run --frozen python scripts/verify_simulator.py --context local --output artifacts/simulator-h3/real

El destino debe ser nuevo; para repetir, elegir otro --output. Es una comprobación
contable con acciones prefijadas, no selección de estrategias.
[Contrato y compatibilidad H3](docs/hitos/H3-contrato-ADR002.md),
[resumen académico](docs/hitos/H3-resumen-academico.md) y
[evidencias nuevas](docs/evidence/simulator-h3/COMMANDS.md).
[H2](docs/hitos/H2-simulador.md) se conserva como antecedente: sus observaciones
y flags no deben suponerse compatibles con H3. No hay entrenamientos de mercado.


## H4 — agentes y recolector, solo sintéticos

Redes separadas CPU float64, acción logística-normal sin clipping, episodios
completos con política congelada, Monte Carlo H=180 y calendario Q/A/B adoptado.
La instalación usa PyTorch 2.8.0+cpu desde índice explícito CPU fijado en el lock.
No requiere CUDA ni cambios de drivers.

    uv run --frozen python scripts/verify_agents.py --output artifacts/agents-h4/synthetic-run

El destino debe ser nuevo. Ejecuta actualizaciones pequeñas de C0/C5/C10 y
equivalencia con riesgo apagado sobre rutas fabricadas; no admite archivos de
mercado. Los valores son de prueba, no hiperparámetros aprobados para pilotos.
La configuración operativa de datos H3 se conserva; AGENTS y SyntheticSettings
registran el alcance H4. Su training_enabled=false sigue bloqueando mercado.

[Informe H4](docs/hitos/H4-agentes-recolector.md),
[resumen académico](docs/hitos/H4-resumen-academico.md),
[evidencias](docs/evidence/agents-h4/COMMANDS.md) y
[propuesta de pilotos, aún no autorizada](docs/proposals/H4-pilotos-3h.md).

## Infraestructura H5

[Informe H5](docs/hitos/H5-infraestructura.md),
[resumen académico](docs/hitos/H5-resumen-academico.md),
[evidencias](docs/evidence/infrastructure-h5/COMMANDS.md) y
[P0 propuesto, no autorizado](docs/proposals/H5-P0-instrumentado.md).

```bash
uv run --frozen python scripts/verify_infrastructure.py --profile synthetic --output artifacts/h5-synthetic-new
uv run --frozen python scripts/verify_infrastructure.py --profile market-integration --output artifacts/h5-market-new
uv run --frozen python scripts/run_pilot.py --protocol protocolo-pendiente.json
```

El segundo requiere productos locales aceptados en data/processed/segmented-B-h1
anclados al manifiesto H1 versionado. Muestrea tres episodios prefijados, sin
optimización. El tercero devuelve bloqueo esperado (exit 2), sin leer datos.
Checkpoint completo solo en after_q0/after_dual, con journal obligatorio; un
fallo o una interrupción no permite recuperación selectiva. La reanudación se
verificó con datos sintéticos y exige compatibilidad de código/runtime/huellas.
Ningún tiempo sintético ni de recolección congelada dimensiona automáticamente
un piloto. Cota común d y protocolo de pilotos siguen pendientes de aprobación.

## P0 aprobado

Propuesta 7a379b7 adoptada con d=-ln(.90) y presupuesto diario global compartido.
[Protocolo](docs/protocols/P0-approved-v1.md) y
[configuración aprobada exclusivamente para P0](docs/protocols/P0-approved-v1.json).

```bash
uv run --frozen python scripts/run_pilot.py --protocol docs/protocols/P0-approved-v1.json
```

Única raíz artifacts/p0-approved-v1; sin overrides de semillas/lotes/límites.
El mismo comando retoma únicamente pausas válidas bajo la misma autorización.
Una campaña fallida permanece bloqueada; no borrar registros para reintentar.
La configuración histórica initial.toml se mantiene intacta para compatibilidad H1;
la excepción de ejecución es solo el perfil P0 registrado. El resto de JSON
(incluida la propuesta original) siguen rechazados. No se habilita entrenamiento general.
