# P2 histórico: comandos, registros y alcance de verificación

Fecha 30/09/2026; día de presupuesto `America/La_Paz`, timestamps UTC.
Rama `codex/p2-execution`; activación `18bc767`. Configuración aprobada
`docs/protocols/P2-infrastructure-v1.json` (SHA256
`d5fa2f2726cd6458df3c290e7b58c591f11310c7a9b645c47a5fb6bd419e5238`).

## Antes de mercado

- Se comprobó Git local/origin desde la base `2f01d6c`; se conservó la
  eliminación local preexistente de `.python-version`.
- El [preflight activo](preflight.json), después de publicar el commit de
  permiso, quedó `ready_for_authorized_execution`. Registró 7048 inicios
  aceptados, normalizador sin reajuste, versiones locales y huellas de
  código/datos/protocolo. [Integridad previa](prior-campaign-integrity.json):
  36 artefactos P0 y 72 P1, sin discrepancias ni otra campaña activa.
- `UV_CACHE_DIR=/tmp/uv-cache uv run --frozen ruff check .`: aprobado.
- `UV_CACHE_DIR=/tmp/uv-cache uv run --frozen pytest`: 234 pruebas aprobadas
  en 93.36 s. Son comprobaciones previas a la campaña; no se repitieron para
  sustituir evidencia posterior.
- La preparación consumió 456.151 s medidos más 60 s de margen debitado:
  516.151 s, en `artifacts/p2-preparation-approved-v1/ledger.jsonl` local.

## Ejecución autorizada

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --frozen python scripts/run_p2.py \
  --profile market --protocol docs/protocols/P2-infrastructure-v1.json \
  > docs/evidence/p2-execution/campaign.log 2>&1
```

La sesión terminó sin entregar resultado final al cliente. El log de campaña
y `run-05-C0/worker-2.log` están vacíos; los logs por unidad y los archivos
voluminosos permanecen localmente en `artifacts/p2-approved-v1`. El último
progreso parcial se guardó a las 06:20:12.742 UTC. No se conoce el instante ni
la causa exacta de la terminación del proceso. La inspección posterior encontró
el bloqueo de campaña libre y el ledger en `running` con unidad 2 pendiente.

Para aplicar la regla de interrupción del ejecutor se instanció **solo el
ledger**, con identidad exacta del último estado y sin cargar entorno ni
optimizadores. Su inicialización detectó la unidad pendiente, añadió estado
`failed` con razón `interrupted_supervisor_or_unit` y rechazó continuar.
No se invocó otra vez el comando de campaña.

## Cierre de solo lectura

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --frozen python \
  docs/evidence/p2-execution/check_results.py \
  --output docs/evidence/p2-execution/campaign-results
```

El resultado íntegro inicial del cierre se conservó localmente en
`artifacts/p2-approved-v1/closure-results-full.json`. Se volvió a ejecutar
**solo el comprobador de lectura**, ya con salida escalar reducida, hacia
`artifacts/p2-approved-v1/closure-summary`; su `results.json` es la copia
versionada aquí. Ambos recorridos dieron `failed`, cursor 5, 57 unidades y
3264 archivos D verificados, sin nuevas trayectorias ni actualizaciones.

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --frozen python \
  docs/evidence/p2-execution/check_results.py \
  --output artifacts/p2-approved-v1/closure-summary
```

Resultado: `status=failed`, `cursor=5`, 176 estados del ledger, 57 unidades
cerradas, 3264 archivos D y hashes de checkpoints verificados. Los
[resultados por corrida](campaign-results/results.json) conservan métricas,
contadores, tiempos, memoria y advertencias con denominadores. La evidencia
versionada de preflight y resultados sustituye únicamente las rutas
absolutas del checkout local por `<repo>/`; las cifras y huellas no cambiaron.
Los originales de campaña siguen en `artifacts/`. La
[instantánea de interrupción](interruption.json) distingue la unidad parcial
de las unidades cerradas. `check_results.py` lee artefactos; no instancia
entorno de mercado ni ejecuta pasos de optimizador. Las pruebas sintéticas
previas validaron el ejecutor, no la calidad de un agente de mercado. Los
criterios de P2 no se calcularon porque faltan corridas completas.

Después del cierre se recalcularon los SHA256 de los ledgers P0, P1 y
preparación P1 contra el preflight: los tres coincidieron. `uv run --frozen
ruff check .`, `git diff --check` y la validación JSON de los resultados de
cierre también pasaron. No se repitió la suite de 234 pruebas después de la
campaña, porque no se modificó el código operativo.

No hubo acceso a validación 2023 ni a la prueba final 2024–2025. No se
seleccionaron checkpoints ni se repitieron corridas. La tesis no se modificó.
