# P2 — comprobaciones documentales y algebraicas

Base local/origin verificada: 811d882ccadf3aadb78219dec095a3b17b18dc20.
Rama nueva codex/p2-proposal. El primer git fetch no llegó a ejecutarse porque la
revisión automática de permisos falló por límite de uso. Tras la continuación del
usuario el 25/09/2026, git fetch origin funcionó; no hay commits posteriores en
origin/codex/p1-critic-epochs. Se preserva la eliminación previa de .python-version.

Lecturas: AGENTS, HANDOFF, informe P1, configuración P1 y los JSON pequeños de
resultados P0/P1. No lectura de OHLC, de validación/final, de checkpoints ni nueva
simulación. Los tiempos citados son antecedentes medidos, no mediciones de P2.

Comandos realmente ejecutados:

```bash
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff format docs/evidence/p2-proposal/checks.py
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check docs/evidence/p2-proposal/checks.py
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python docs/evidence/p2-proposal/checks.py > docs/evidence/p2-proposal/checks.log 2>&1
```

El primer Ruff detectó E731 en una lambda del cálculo algebraico. Los nueve grupos
de comprobaciones pasaron; results.json conserva esa primera salida. Se sustituyó
la lambda por def, sin modificar las fórmulas, y el destino exclusivo por
results-verified.json para no sobrescribir la evidencia. Después se ejecutó:

```bash
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff format docs/evidence/p2-proposal/checks.py
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python docs/evidence/p2-proposal/checks.py > docs/evidence/p2-proposal/checks-final.log 2>&1
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check . > docs/evidence/p2-proposal/ruff.log
git diff --check
```

**Resultado vigente: 9 grupos pasan; Ruff pasa; diff --check pasa.**
[Resultados](results-verified.json): indicadores de no autorización, invariantes
P1 salvo K/épocas candidata, semillas/orden, aritmética de recursos, coordenadas
D separadas sin sorteos, sumas MC y ejemplo de desfase de política, MSE/sesgo/ratios
agregados, umbrales algebraicos, solapamiento de intervalos sintéticos y presupuesto,
extracción de tiempos de JSON anteriores y ausencia de cambios operativos.

Esto no valida un agente, un recolector D ni el ejecutor futuro. No se ejecutó
pytest completo porque contiene actualizaciones de aprendizaje fuera del alcance
actual. No se reutilizan las 198 pruebas de P1 como resultados de esta entrega.
La candidata contiene authorized=false/executable=false; no se ha registrado
ningún permiso P2. El script usa salida exclusiva: no borrar evidencias para repetir.
