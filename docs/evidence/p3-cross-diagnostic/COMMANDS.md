# P3: diagnóstico cruzado de D tardía — comandos y huellas

Rama `codex/p3-cross-diagnostic`, desde `56adb8f`. El código de la campaña y `artifacts/p3-approved-v1` son entradas de **solo lectura**. La eliminación local anterior de `.python-version` quedó sin versionar. El script abre solamente el ledger, el cierre auditado, 18 reportes finales, checkpoints `k=7..10` y archivos D `k=7,8,9` de esa raíz; no carga el derivado H1, CSV compartidos, validación ni final.

Secuencia ejecutada desde la raíz del repositorio:

```bash
git status --short --branch
git log -3 --oneline
git switch -c codex/p3-cross-diagnostic
uv run --frozen pytest -q tests/test_p3_cross_diagnostic.py
uv run --frozen ruff check docs/evidence/p3-cross-diagnostic/analyze.py tests/test_p3_cross_diagnostic.py
uv run --frozen python docs/evidence/p3-cross-diagnostic/analyze.py > docs/evidence/p3-cross-diagnostic/results.json
uv run --frozen pytest -q tests/test_p3_cross_diagnostic.py tests/test_p3_protocol_metrics.py
uv run --frozen ruff check docs/evidence/p3-cross-diagnostic/analyze.py tests/test_p3_cross_diagnostic.py
uv run --frozen python docs/evidence/p3-cross-diagnostic/analyze.py > /tmp/p3-cross-replay.json
cmp /tmp/p3-cross-replay.json docs/evidence/p3-cross-diagnostic/results.json
uv run --frozen python docs/evidence/p3-cross-diagnostic/check_report.py
uv run --frozen ruff check .
git diff --check
sha256sum artifacts/p3-approved-v1/ledger.jsonl docs/evidence/p3-market-2026-10-13/final-closure.json docs/evidence/p3-cross-diagnostic/analyze.py docs/evidence/p3-cross-diagnostic/results.json
```

El primer `pytest` falló como fase roja porque el script aún no existía (3 pruebas). Tras implementarlo, un caso sintético encontró una expectativa manual errónea de MSE (0,5 frente a 1,0); se corrigió **la expectativa**, sin cambiar la fórmula. Ruff señaló luego el orden de imports del test y se corrigió con `uv run --frozen ruff check --fix tests/test_p3_cross_diagnostic.py`. La última ejecución focal dio **10 passed** tras añadir el rechazo sintético de un checkpoint incompatible; Ruff focal y global dieron **All checks passed!**. El análisis de artefactos terminó con código 0 y la repetición fue idéntica byte a byte (`cmp` código 0). El verificador de tablas cotejó **36 celdas y tres resúmenes de bloque** con `results.json`. `git diff --check` no informó errores. No se ejecutó la suite completa: algunas pruebas de integración ajenas al diagnóstico podrían abrir entradas fuera del alcance autorizado; las pruebas pertinentes son las indicadas.

Huellas SHA-256 medidas:

| Archivo | SHA-256 |
| --- | --- |
| `artifacts/p3-approved-v1/ledger.jsonl` | `86b111b5365cda1760441d2f73d42e0463a4b4b2a7ddbc6e0e41f2a78751fcfe` |
| `docs/evidence/p3-market-2026-10-13/final-closure.json` | `1d96dd5ed2cb4af27a0f3993501ea7c40ece67ccc5862fe0f9d7b0049c033c6d` |
| `docs/evidence/p3-cross-diagnostic/analyze.py` | `723a6422d6cf419ad57739e3b141da4f2a941127b15e38e6287f5a82d1a503c7` |
| `docs/evidence/p3-cross-diagnostic/results.json` | `83457464c6f2806377db917a28df186deb5826c75bfffaf1364c12410fe222a6` |
| `docs/evidence/p3-cross-diagnostic/check_report.py` | `4c54c4441b477eba5485b3303e19317b0c3c91ea20d678d442564b142e53fb79` |
| `docs/hitos/P3-diagnostico-cruzado-D.md` | `79ee6760b7f40c132033d564f6045c906d74c5a57ffddba5015fe43c696f3678` |

El script verifica cada D contra el SHA-256 de su reporte final aceptado y cada estado de checkpoint contra el ledger. Los reportes finales incluyen todas esas huellas individuales; no se duplican los 3.456 hashes en Git. La identidad del actor del checkpoint `k` debe coincidir con la política generadora de D y la del crítico del checkpoint `k+1` con la reportada como posterior. Se verifica el hash de objetivos de cada D y se compara la diagonal con las sumas aceptadas.

Reproducción local, sobre **los mismos artefactos aceptados**:

```bash
uv run --frozen python docs/evidence/p3-cross-diagnostic/analyze.py > /tmp/p3-cross-replay.json
cmp /tmp/p3-cross-replay.json docs/evidence/p3-cross-diagnostic/results.json
```

Ninguno de estos comandos ejecuta un optimizador, genera trayectorias o inicia unidades.
