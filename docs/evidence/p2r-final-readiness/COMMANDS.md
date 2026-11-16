# P2R v2 — comprobaciones realmente ejecutadas el 06/10/2026

Base `dc6285c`, rama `codex/p2r-historical-executor`. No se inició unidad
histórica ni se creó permiso/registro/raíz de campaña.

```bash
git status --short --branch
git log -5 --oneline --decorate
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen pytest -q
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check .
sha256sum data/processed/p2r-training-h1/manifest.json docs/evidence/p2r-training-shard-export/manifest.json data/processed/segmented-B-h1/manifest.json artifacts/p0-approved-v1/ledger.jsonl artifacts/p1-approved-v1/ledger.jsonl artifacts/p2-approved-v1/ledger.jsonl
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python scripts/audit_p2r_preflight_opens.py
loginctl show-user ichurri -p Linger -p State -p Sessions
systemctl --user is-system-running
systemctl --user list-units --all 'p2r-*' 'p2-*' --no-pager
lslocks -o PATH,COMMAND,PID
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python -c 'from btc_risk_rl.pilots.p2r import read_power,check_resources; import json; print(json.dumps({"power":read_power(),"resource_guard":check_resources(stage="preflight",disk_path="artifacts")}))'
date -u '+%Y-%m-%dT%H:%M:%SZ'
TZ=America/La_Paz date '+%Y-%m-%dT%H:%M:%S%:z'
awk '/^```bash/{on=1;next} /^```/{if(on){on=0;print ""};next} on{print}' docs/hitos/P2R-preparacion-final-v2.md | bash -n
git diff --check
```

Resultados: `288 passed in 212.65s (0:03:32)`; Ruff `All checks passed!`.
El preflight guardado en [preflight-opens.json](preflight-opens.json) pasó
con cero aperturas compartidas. [anchors.sha256](anchors.sha256) contiene
seis huellas actuales; [h1-product-hashes.json](h1-product-hashes.json)
contiene los doce SHA-256 comprobados contra el manifiesto H1. Este último
comando fue una lectura de integridad **separada** del preflight, mediante
este programa Python de solo hash, sin cargar observaciones:

```bash
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python - <<'PY'
import hashlib
import json
from pathlib import Path
root = Path('data/processed/segmented-B-h1')
manifest = json.loads((root / 'manifest.json').read_text())
for name, expected in manifest['files'].items():
    digest = hashlib.sha256()
    with (root / name).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    assert digest.hexdigest() == expected, name
PY
```

El programa ejecutado añadió guardas de ruta, fecha UTC y salida JSON,
guardada en `h1-product-hashes.json`; el bloque anterior muestra su
comprobación esencial. `loginctl` y
`systemctl` fallaron primero desde el sandbox con `Operation not permitted`;
repetidos con acceso local de solo lectura devolvieron `Linger=yes`,
`State=active`, gestor `running` y cero unidades listadas. Alimentación:
CA conectada, batería 98 %, guardia `ready`. Solo `.python-version` seguía
eliminado localmente, sin versionar.

Las lecturas de host/presupuesto se tomaron alrededor de 18:47 UTC y no
son una reserva ni un pronóstico de una fecha posterior. El procedimiento
`systemd-run` del [informe](../../hitos/P2R-preparacion-final-v2.md) está
marcado **NO EJECUTADO**.
