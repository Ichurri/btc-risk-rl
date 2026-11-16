# P3 crítico: comandos y alcance de evidencia

Ejecutados en `codex/p3-critic-synthetic` con `UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache`:

```bash
uv run --frozen python docs/evidence/p3-critic-synthetic/beta0_probe.py --profile legacy --output docs/evidence/p3-critic-synthetic/beta0-before.json
uv run --frozen pytest -q tests/test_p3_critic_synthetic.py
uv run --frozen python docs/evidence/p3-critic-synthetic/beta0_probe.py --profile p3_beta0 --output docs/evidence/p3-critic-synthetic/beta0-after.json
python3 -c "import json,pathlib; p=pathlib.Path('docs/evidence/p3-critic-synthetic'); a=json.loads((p/'beta0-before.json').read_text()); b=json.loads((p/'beta0-after.json').read_text()); assert all(a[k]==b[k] for k in a if k!='profile')"
uv run --frozen python docs/evidence/p3-marker-supervisor/checks.py
uv run --frozen ruff check .
uv run --frozen pytest -q
git diff --check
```

La primera sonda se ejecutó **antes** de la edición productiva. El primer
pytest falló durante colección por ausencia del módulo, como control de
prueba previa. La prueba nueva de checkpoint falló una vez al mostrar que
el cargador no reconocía el perfil sintético P3; se corrigió ese despacho.
Tras implementarlo, el test focalizado dio **8 aprobados**;
la suite completa dio **320 aprobados en 230,89 s** y Ruff dio
`All checks passed!`. El auditor de artefactos informó que los ledgers
originales conservaban sus huellas y que los 99 reportes P2R seguían
intactos. `git diff --check` pasó. `beta0-before.json` y
`beta0-after.json` difieren solo en la etiqueta del perfil; las otras
13 claves son iguales, incluidas huellas de pesos y optimizadores.

Estos comandos usan `SyntheticMarket` generado en memoria. No cargan el
derivado histórico, validación ni prueba final; no inician campaña.
