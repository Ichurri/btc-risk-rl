# P1 — comandos de preparación realmente ejecutados

Base 42152c3 verificada local/origin tras git fetch; rama codex/p1-critic-epochs.
Aprobación y configuración congeladas en 7eb9738. Todos los uv usan
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache y --frozen.

- pytest tests/test_p1.py -q → red.log: 3 fallos esperados (módulos/métricas ausentes).
- pytest tests/test_p1.py -q → green-first.log: 3 pasan.
- pytest test_p1.py::test_p1_pair_integrity_rejects_different_initial_A -q
  (ruta tests/) → pair-red.log: función ausente, luego implementada.
- pytest → pytest-first.log: 192 pasan, 1 fallo de interfaz del launcher sintético
  histórico; se preservó la firma P0 de expected_resources.
- pytest tests/test_p1.py -q → pytest-p1.log: 8 pasan.
- pytest → pytest-verified.log: 196 pasan en 68.63 s.
- pytest tests/test_p1.py -q → pytest-reporting.log: 11 pasan en 8.15 s.
- pytest tests/test_p1.py::test_primary_literal_zero_pair_keeps_reduction_undefined -q
  → criterion-red.log: reproduce condición extra no adoptada; corregida.
- pytest → pytest-final.log: **198 pasan, 68.45 s**.
- ruff format sobre archivos cambiados; ruff check . --fix sobre imports;
  ruff check . → ruff-verified.log detectó dos nombres ambiguos en tests;
  corregidos sin cambiar lógica; ruff-final.log es el resultado vigente.

Pruebas fabricadas, incluidos procesos sintéticos de supervisor/RSS y reanudación
exacta. Ningún test usa mercado real ni prueba final. La propuesta y el diagnóstico
P0 no se modifican. Revisiones en REVIEW.md. No atribuir tiempos sintéticos a P1.

La preparación de P1 se cargará conservadoramente al presupuesto desde la creación
de su rama (timestamp Git) hasta el lanzamiento, incluyendo desarrollo y pruebas
en ese intervalo. Recibo inmutable separado de preparación, más débito de P0;
el supervisor usa únicamente el remanente diario. No son trayectorias de mercado.

## Ejecución autorizada

Antes del lanzamiento se comprobaron los hashes de todos los archivos P0
anclados por el diagnóstico y la ausencia de ledger P1 previo. preparation.json
registra el intervalo 20:34:23–20:57:30.837745 UTC del 24/09/2026: 1387.837745 s,
leído de creación de rama y reloj real. artifacts/p1-preparation-approved-v1/
ledger.jsonl lo carga al presupuesto compartido junto a 1385.677054 s de P0.

```bash
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python scripts/run_p1.py --protocol docs/protocols/P1-approved-v1.json > docs/evidence/p1-execution/campaign.log 2>&1
```

Fuente publicada antes de ejecutar: 7617d84. No cambios de código/configuración
operativa durante la campaña. Los logs pytest RED conservan whitespace original;
diff --check de código/documentos excluyendo *.log pasa. Hubo un timeout de
revisión automática de permisos de git add; reintento autorizado funcionó.

## Cierre realmente ejecutado

Log final: completed, cursor 18; ledger actualizado a
2026-09-24T21:41:41.392234+00:00. No se volvió a ejecutar run_p1 tras completar.

```bash
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python scripts/report_p1.py --output docs/evidence/p1-execution/campaign-results > docs/evidence/p1-execution/export.log 2>&1
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff format docs/evidence/p1-execution/check_results.py
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check docs/evidence/p1-execution/check_results.py --fix
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python docs/evidence/p1-execution/check_results.py > docs/evidence/p1-execution/closure-checks.log 2>&1
```

Export y check: exit 0. Comprobación independiente del criterio (tres semillas),
recursos, límites, hashes de código y 72 artefactos; parámetros de actor/crítico
de los 18 checkpoint-1 cargados solo para cotejo, sin optimizadores ni aprendizaje.
Todos los archivos P0 anclados en diagnóstico permanecen intactos. El exportador
leyó solo logs/manifiestos; la comprobación de cierre además bytes/checkpoints
existentes, no OHLC ni nuevas trayectorias. Evidencias pequeñas con destinos nuevos.

shared-budget.jsonl es copia exacta del registro global de entrada/salida;
preparation.json y días de results.json explican el débito diario. Informe y
resumen se derivaron de estos registros. No se repitió pytest tras los cambios
exclusivamente documentales del cierre; las 198 pruebas son de esta entrega,
antes de mercado. Ruff final de entrega en ruff-delivery.log.
