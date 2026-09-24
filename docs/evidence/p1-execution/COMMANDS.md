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
