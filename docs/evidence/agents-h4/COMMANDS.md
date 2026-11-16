# H4 — comandos y evidencia local

Base H3: 8f027c53696976602260eb498698ef51ffd5d711.
Alcance/dependencias: 31b4c87. Código: a6c391a537b7fcea12e98b8a968ed9ffa9585821.
Rama codex/h4-agents-collector, creada desde H3. Local y remoto coincidían;
main remoto seguía en e4e2e8f. Se conservó fuera de commits la eliminación previa
de .python-version. No reset, force push o modificación de visibilidad.

Comandos desde el repositorio local con UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache.
uv.lock fija todas las dependencias; PyTorch se restringió al índice CPU explícito.

## Instalación y pruebas

| Comando | Registro | Resultado |
|---|---|---|
| uv lock | uv-lock.log | resolución completada |
| uv sync --frozen | uv-sync.log | torch 2.8.0+cpu y dependencias instaladas, sin CUDA; fallback de hardlink a copia entre filesystems |
| uv run --no-sync pytest -q tests/test_agent_math.py | math-red.log | 7 fallos por módulos H4 ausentes |
| uv run --frozen pytest -q tests/test_agent_math.py | math-first.log | 6 pasan, 1 falla por exigir igualdad exacta de 3 frente a redondeo float64 |
| mismo comando tras tolerancia analítica, sin cambiar fórmula | math-green.log | 7 pasan |
| uv run --frozen pytest -q tests/test_collector.py antes de implementar | collector-red.log | 5 fallos por módulo ausente |
| mismo comando después | collector-green.log | 5 pasan |
| uv run --frozen pytest -q tests/test_agent_schedule.py antes de implementar | schedule-red.log | 6 fallos por módulo ausente |
| mismo comando después | schedule-green.log | 6 pasan |
| uv run --frozen pytest -q tests/test_agent_math.py tests/test_collector.py tests/test_agent_schedule.py | targeted.log | 27 pasan, incluidas ampliaciones |
| uv run --frozen pytest -q tests/test_collector.py -k 'provenance or serialization' | review-red.log | 4 fallos: motivo de fin/serialización ausentes |
| uv run --frozen pytest -q tests/test_collector.py | review-green.log | 11 pasan |
| uv run --frozen ruff check . y uv run --frozen pytest | pytest-first.log | suite intermedia: 148 pasan |
| uv run --frozen pytest -q tests/test_collector.py -k serialized_rewards | serialization-red.log | 1 fallo: corrupción de rewards aún aceptada |
| uv run --frozen pytest -q tests/test_collector.py | serialization-green.log | 12 pasan tras validación por transición |
| uv run --frozen ruff check . | ruff.log | sin errores |
| uv run --frozen pytest | pytest.log | **149 pasan en 58.40 s** |
| uv run --frozen python scripts/verify_agents.py --output artifacts/agents-h4/synthetic-run | synthetic-run.log, results.json | passed, 5 corridas sintéticas, equivalencia exacta |

Se ejecutaron ruff check --fix y ruff format sobre los módulos/pruebas nuevos y
el verificador antes de las comprobaciones finales. Los logs RED y el fallo
intermedio se conservan como historia de pruebas, no son errores pendientes.

## Ejecución adicional autorizada

results.json contiene schema h4_synthetic_verification_v1, comando exacto, Python,
SO, versiones, commit, estado Git, hashes, configuración sintética, eventos Q/A/B,
coeficientes escalares congelados, cuantiles, masas/empates, auditorías y recursos.

Cinco corridas: C0, C5, C10, C5_off, C10_off; dos iteraciones cada una.
Por corrida: Q0=3 y 2*(A=2+Q=3+B=3) = 19 trayectorias; 3420 transiciones;
8 actualizaciones actor y 8 crítico. Total del verificador: **95 trayectorias,
17100 transiciones y 40+40 pasos de optimizador**. Las pruebas pytest ejecutan
además sus propios casos pequeños; estos totales no pretenden incluirlos.

Tiempo medido del bloque sintético adicional: **9.983122481 s**, CPU, un hilo torch
y algoritmos deterministas. Incluye cinco corridas y muestras serializadas; no es
un benchmark de entrenamiento de mercado ni una previsión para pilotos.
Las masas Q/B son .15 o .30, deliberadamente pequeñas para pruebas de software;
no acreditan precisión estadística de CVaR.

Los resultados de C5_off/C10_off coinciden exactamente con C0 en actor/crítico.
La suite también verifica igualdad de estados Adam y aislamiento del RNG A
al cambiar cantidades auxiliares de C0. Las corridas de riesgo activado parten
con lambda0=0 y prueban su efecto en la segunda iteración.

Una muestra NPZ por condición está en artifacts/agents-h4/synthetic-run/, fuera
de Git. Sus hashes están en results.json. No sobrescribir para repetir: elegir
otro --output. Las muestras no son datos de mercado ni checkpoints de optimizadores.

## Integridad y revisión

delivery-checks.json registra torch.version.cuda=None, ausencia de paquetes
nvidia/triton en el lock, conservación del código/configuración H3 y propuesta
adoptada, historial HANDOFF y cambio previo .python-version.
La comprobación usó tomllib sobre uv.lock, metadatos de torch y git diff contra
H3; no leyó los archivos de mercado.

Revisión independiente estática (sin optimizaciones adicionales): detectó la
pérdida de end_reason y después la falta de validación de rewards al cargar NPZ.
Ambas se reprodujeron con pruebas rojas y se corrigieron. Revisó el cierre en
a6c391a y no dejó hallazgos abiertos. Las limitaciones de checkpoint integral
y adaptación futura a mercado quedan documentadas.

No se ejecutaron comprobaciones reales H1/H3 de mercado ni propuestas algebraicas
históricas fuera de la suite; no se atribuyen resultados anteriores a H4.
No entrenamiento de mercado, pilotos, evaluación confirmatoria, test final,
CUDA, cambios de drivers o de tesis. No ZIP.
