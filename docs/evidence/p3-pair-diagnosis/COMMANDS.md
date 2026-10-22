# Reproducción del diagnóstico pareado P3

Base leída: `0142d4a1fda37c4d93ae49805090beb4f0decbfe`, rama de trabajo `codex/p3-pair-diagnosis`. Todas las operaciones sobre `artifacts/p3-approved-v1` fueron de **lectura**. La eliminación local preexistente de `.python-version` no se incorporó. No se abrieron validación 2023 ni prueba final 2024–2025.

Desde la raíz del repositorio, comandos efectivamente ejecutados:

```bash
git status --short --branch
git rev-parse HEAD
uv run --frozen python docs/evidence/p3-pair-diagnosis/analyze.py > docs/evidence/p3-pair-diagnosis/results.json
uv run --frozen ruff check docs/evidence/p3-pair-diagnosis/analyze.py
uv run --frozen pytest -q tests/test_p3_protocol_metrics.py tests/test_p3_critic_synthetic.py
uv run --frozen ruff check .
uv run --frozen python docs/evidence/p3-pair-diagnosis/analyze.py > /tmp/p3-pair-diagnosis-replay.json
cmp /tmp/p3-pair-diagnosis-replay.json docs/evidence/p3-pair-diagnosis/results.json
sha256sum artifacts/p3-approved-v1/ledger.jsonl docs/evidence/p3-market-2026-10-13/final-closure.json docs/evidence/p3-pair-diagnosis/analyze.py docs/evidence/p3-pair-diagnosis/results.json
```

El análisis y la repetición terminaron con código 0; `cmp` no halló diferencias. Las pruebas focales dieron **13 passed** y Ruff global **All checks passed!**. `results.json` informa 3.456 archivos D de `k=7,8,9`, 54 parejas pre/post de checkpoints, nueve pares de brazos y reproducción exacta de las puertas guardadas en el ledger. En un primer borrador de la auditoría se exigió erróneamente `end_reason=collection_window` para toda trayectoria completa; seis archivos terminan en `segment_boundary` justo en el paso 180. Se corrigió esa **suposición de auditoría**, se verificaron horizonte/reloj/terminalidad completos y se repitió el análisis; no se cambió el ejecutor ni los artefactos de P3.

SHA-256: ledger `86b111b5365cda1760441d2f73d42e0463a4b4b2a7ddbc6e0e41f2a78751fcfe`; cierre `1d96dd5ed2cb4af27a0f3993501ea7c40ece67ccc5862fe0f9d7b0049c033c6d`; `analyze.py` `65db88f0841d645798704c73e582285ddd44aaae37fdaf2b8931337ce1f54aeb`; `results.json` `96a60b36729d76d858582a8328b87c1100a25e66dd75af561e09cc2105bafc20`.

Para repetir el cálculo en otra copia local que conserve los artefactos originales y la misma base:

```bash
uv sync --frozen
uv run --frozen python docs/evidence/p3-pair-diagnosis/analyze.py > /tmp/p3-pair-diagnosis-replay.json
cmp /tmp/p3-pair-diagnosis-replay.json docs/evidence/p3-pair-diagnosis/results.json
sha256sum artifacts/p3-approved-v1/ledger.jsonl docs/evidence/p3-market-2026-10-13/final-closure.json docs/evidence/p3-pair-diagnosis/analyze.py docs/evidence/p3-pair-diagnosis/results.json
```

El script falla cerrado si difiere el ledger o el cierre; coteja también hashes y contenidos de los reportes, archivos D y checkpoints que utiliza. Los archivos D y checkpoints son datos locales voluminosos y permanecen fuera de Git. No llamar al script con rutas de validación o final.
