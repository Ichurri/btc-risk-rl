"""Package the committed documentary delivery, never market data or working-tree edits."""

import hashlib
import io
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def git(*args):
    return subprocess.check_output(['git', *args])


def main():
    commit = git('rev-parse', 'HEAD').decode().strip()
    output = Path('artifacts/releases')
    output.mkdir(parents=True, exist_ok=True)
    stem = f'btc-risk-rl-adr002-v2-{commit[:7]}'
    target = output / f'{stem}.zip'
    bundle = output / f'{stem}.bundle'
    receipt_path = output / f'{stem}.receipt.json'
    if any(p.exists() for p in (target, bundle, receipt_path)):
        raise FileExistsError('Delivery paths already exist')
    # Inspect path names only before reading archived file contents.
    names = git('ls-tree', '-r', '--name-only', 'HEAD').decode().splitlines()
    assert not any(n.startswith(('data/', 'artifacts/', '.venv/')) for n in names)
    historical_data_paths = git('log', '--format=', '--name-only', 'HEAD', '--', 'data').strip()
    assert not historical_data_paths, 'Do not include market files in history bundle'
    subprocess.run(['git', 'bundle', 'create', str(bundle), 'HEAD'], check=True)
    verified = subprocess.run(['git', 'bundle', 'verify', str(bundle)], check=True,
                              capture_output=True, text=True)
    readme = '''# Entrega académica ADR-002 v2

Estado: PROPUESTA PARA REVISIÓN, NO ADOPTADA. ADR-002 sigue abierto.
Leer docs/proposals/ADR-002-v2-resumen-academico.md y ADR-002-propuesta-v2.md.
El pseudocódigo completo está en la sección 6.4 de la propuesta.
Evidencia nueva: docs/evidence/adr002-proposal-v2/.

Incluye snapshot versionado y repository.bundle (historial), sin datos de mercado.
H2 mantiene el contrato de cc913b6. No hay agentes ni entrenamientos.
Los logs H1/H2 anteriores son antecedentes, no nuevas ejecuciones de esta entrega.
La eliminación local previa de .python-version no pertenece al commit exportado.

Para reproducir solo los cálculos (Python 3.12.13 usado originalmente):
  git clone repository.bundle revision-adr002-v2
  cd revision-adr002-v2
  python3 docs/evidence/adr002-proposal-v2/checks.py > /tmp/adr002-v2-checks.json
Los checks escriben v1-reproduction.json dentro de esa copia; no leen mercado.
Para repetir H2 se necesitan las dependencias fijadas por uv.lock:
  uv sync --frozen
  uv run --frozen ruff check .
  uv run --frozen pytest
No ejecutar fetch-development, verify_simulator ni entrenamientos para revisar v2.
DELIVERY.json identifica commit, comandos de empaquetado y hashes internos.
'''
    payload = {}
    with zipfile.ZipFile(io.BytesIO(git('archive', '--format=zip', 'HEAD'))) as archive:
        for name in archive.namelist():
            if not name.endswith('/'):
                payload[name] = archive.read(name)
    payload['repository.bundle'] = bundle.read_bytes()
    payload['LEEME-ACADEMICO.md'] = readme.encode()
    manifest = {
        'commit': commit, 'h2_base': 'cc913b629694641543e2b54375dbda5d55130544',
        'status': 'PROPUESTA PARA REVISIÓN, NO ADOPTADA',
        'utc': datetime.now(timezone.utc).isoformat(), 'market_data_included': False,
        'packaging_command': 'uv run --frozen python docs/evidence/adr002-proposal-v2/package_delivery.py',
        'git_commands': ['git archive --format=zip HEAD', f'git bundle create {bundle} HEAD',
                         f'git bundle verify {bundle}'],
        'bundle_verification': verified.stdout + verified.stderr,
        'sha256': {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()},
    }
    payload['DELIVERY.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in payload.items():
            archive.writestr(name, data)
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == set(payload)
        for name, digest in manifest['sha256'].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
    receipt = {'zip': str(target.resolve()), 'commit': commit, 'bytes': target.stat().st_size,
               'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
               'members': len(payload), 'integrity': 'CRC and all manifest hashes verified'}
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
