# Comprobaciones de MSE tardía P2R

Ejecutar desde la raíz del repositorio:

```bash
.venv/bin/python docs/evidence/p2r-late-mse-review/checks.py \
  > docs/evidence/p2r-late-mse-review/results.json
.venv/bin/python docs/evidence/p2r-late-mse-review/checks.py \
  > /tmp/p2r-late-mse-check-again.json
cmp /tmp/p2r-late-mse-check-again.json \
  docs/evidence/p2r-late-mse-review/results.json
.venv/bin/ruff check .
git diff --check
```

El script lee exclusivamente el cierre versionado, ledger, nueve reportes
finales y nueve checkpoints finales existentes. Verifica SHA-256 del ledger
y de los estados; exige igualdad exacta de los registros diagnósticos
entre `unit-10.json` y `state.pt`. Agrupa SSE, `ΣG²`, sesgo y conteos antes
de calcular razones; reconstruye medias, desviaciones y covarianza con
identidades algebraicas y verifica su cierre. Comprueba que los diez lotes
D de cada semilla comparten IDs de rutas entre C0/C5/C10. No carga
`TrainingMarket`, archivos de mercado ni trayectorias, y no ejecuta
actualizaciones o evaluación de políticas. `V/2` es una **sensibilidad
algebraica retrospectiva**, no un modelo entrenado ni criterio de P2R.

La primera comprobación Ruff detectó únicamente el orden de importaciones
del auditor nuevo; se corrigió antes de generar `results.json`. Se
repitió el auditor y `cmp` coincidió byte a byte. Ruff terminó
`All checks passed!`; `git diff --check` no informó errores. SHA-256:

- `results.json`:
  `cce0e2a5c3a6ba2a5a13fdc0cbd45555f10ee1f13cdc24f223b7d8da490db583`.
- `p3-static.json`:
  `944d853478e239aa8990069705531127b0523e7dca7bf7e52f3682c85c1464da`.

La comprobación aritmética de P3, sin ejecutar unidades, fue:

```python
import json
from pathlib import Path

x = json.loads(Path("docs/evidence/p2r-market-2026-10-07/results.json").read_text())
runs = 3 * 3 * 2
units = runs * 11
learning = runs * (400 + 10 * (64 + 400 + 400))
diagnostic = runs * 10 * 64
assert (runs, units, learning, diagnostic) == (18, 198, 162720, 11520)
print(json.dumps(dict(
    status="proposal_not_authorized", runs=runs, units=units,
    learning_trajectories=learning, learning_transitions=learning * 180,
    diagnostic_trajectories=diagnostic, diagnostic_transitions=diagnostic * 180,
    actor_updates=runs * 10 * 8, critic_updates=runs * 10 * 16,
    p2r_measured_charged_seconds=x["charged_wall_seconds"],
    doubling_scenario_seconds=2 * x["charged_wall_seconds"],
    max_global_daily_seconds=10800, max_active_days=3,
    max_work_seconds_if_three_full_days=3 * 8100,
), sort_keys=True, indent=2))
```

Su salida es [`p3-static.json`](p3-static.json). La duplicación del tiempo
P2R es un escenario aritmético, no una estimación medida para P3.
Ninguna suite de aprendizaje o campaña se repitió en este hito.
