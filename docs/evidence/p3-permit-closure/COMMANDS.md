# Comandos realmente ejecutados — cierre del permiso P3

Desde la raíz del repositorio, con `.python-version` ya borrado localmente
por el usuario y **sin incluir esa eliminación en el commit**:

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git log -5 --oneline --decorate
git switch -c codex/p3-close-market-permit
```

Base `842fdd1`; la única modificación previa era ` D .python-version`.
No se editó ninguna entrada histórica congelada.

## Huellas originales: antes y después

```bash
uv run --frozen python docs/evidence/p3-market-2026-10-13/final-audit.py \
  | cmp - docs/evidence/p3-market-2026-10-13/final-closure.json
python3 docs/evidence/p3-permit-closure/audit_artifact_tree.py
```

Ambos comandos se ejecutaron **tres veces**: antes del cambio, después
de cerrar la bandera y tras la suite completa. `cmp`: código 0 en las
tres. Huella de la raíz P3 idéntica en las tres:
47.487 archivos, 5.326.594.447 bytes,
`73949350733bf3f8e3939e2dfcf7a28920668e738b0e5d910bd070a010fdcbec`.
El auditor de cierre comprueba por separado los 198 hashes de reportes y
checkpoints contra el ledger, sin escribir en la raíz.

```bash
sha256sum artifacts/p3-approved-v1/ledger.jsonl \
  artifacts/p3-approved-v1/supervisor.jsonl \
  docs/protocols/P3-market-approval.json \
  docs/evidence/p3-market-2026-10-13/final-closure.json
```

Resultado, en el mismo orden: `86b111b5365cda1760441d2f73d42e0463a4b4b2a7ddbc6e0e41f2a78751fcfe`,
`3edba2fc24bbf6288423d6f0fad90e40d2d8db361dbf505ba9634f6738076b82`,
`66675a4931ae8aea2175c20c1c38f2cba2d5db0512ecc84da61ef6dfeba54597`,
`1d96dd5ed2cb4af27a0f3993501ea7c40ece67ccc5862fe0f9d7b0049c033c6d`.

## Prueba primero, luego cambio

```bash
uv run --frozen pytest -q tests/test_p3_market_guard.py
```

Con la bandera aún activa: **2 fallos y 4 aprobadas**. El comando público
alcanzó la guarda de `systemd` y el JSON falsificado llegó a la lectura;
ambos fallos demostraron la ruta que debía bloquearse. Tras cambiar solo
la bandera operativa y aclarar docstrings: **6 aprobadas en 1,67 s**.

```bash
python3 - <<'PY'
import subprocess
for command in [
    ['uv','run','--frozen','python','scripts/run_p3_market.py'],
    ['uv','run','--frozen','python','-m','btc_risk_rl.pilots.p3_worker',
     '/tmp/p3-forged-closed-request.json'],
]:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    print(command, result.returncode, result.stderr.strip().splitlines()[-1])
    assert result.returncode != 0
    assert 'P3 market campaign NOT AUTHORIZED' in result.stderr
PY
```

Ambas entradas devolvieron **código 1** y `NOT AUTHORIZED`. La ruta de
solicitud falsificada no existía; el trabajador rechazó antes de leerla.

```bash
uv run --frozen pytest
uv run --frozen ruff check .
systemctl --user list-units 'p3-market*' --all --no-legend --no-pager
```

Resultados: **347 passed in 246,05 s**, **All checks passed!** y ninguna
unidad P3 listada al momento de leer `systemd --user`.
