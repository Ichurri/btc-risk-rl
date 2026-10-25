# Comandos y huellas — calibración técnica v1.2

Rama: `codex/oos-v1-2-cost-calibration`; base `1195484`.
La eliminación local previa de `.python-version` se conservó sin versionar.
La raíz local nueva `artifacts/oos-cost-v12-20261025/` está ignorada por Git.
No hay comando de entrenamiento, evaluación con datos de 2023/final ni permiso.

## Comandos ejecutados

```bash
git status --short --branch
git log -1 --oneline
uv run --frozen pytest -q tests/test_agent_math.py -k deterministic_median
# Primera ejecución roja: AttributeError esperado antes de implementar el método.
uv run --frozen python scripts/calibrate_oos_v12.py --phase fold-2021 --output artifacts/oos-cost-v12-20261025/fold-2021
uv run --frozen python scripts/calibrate_oos_v12.py --phase fold-2022 --output artifacts/oos-cost-v12-20261025/fold-2022
uv run --frozen python scripts/calibrate_oos_v12.py --phase checkpoint --output artifacts/oos-cost-v12-20261025/checkpoint
uv run --frozen python scripts/calibrate_oos_v12.py --phase synthetic-2023-equivalent --output artifacts/oos-cost-v12-20261025/synthetic-2023-equivalent
uv run --frozen python scripts/calibrate_oos_v12.py --phase synthetic-final-equivalent --output artifacts/oos-cost-v12-20261025/synthetic-final-equivalent
uv run --frozen python scripts/calibrate_oos_v12.py --phase synthetic-wf-2021-equivalent --output artifacts/oos-cost-v12-20261025/synthetic-wf-2021-equivalent
uv run --frozen python scripts/calibrate_oos_v12.py --phase synthetic-wf-2022-equivalent --output artifacts/oos-cost-v12-20261025/synthetic-wf-2022-equivalent
uv run --frozen python scripts/calibrate_oos_v12.py --phase fold-2021 --output artifacts/oos-cost-v12-20261025/fold-2021-products
uv run --frozen python scripts/calibrate_oos_v12.py --phase fold-2022 --output artifacts/oos-cost-v12-20261025/fold-2022-products
uv run --frozen python scripts/calibrate_oos_v12.py --phase audit --input artifacts/oos-cost-v12-20261025/synthetic-2023-equivalent --output artifacts/oos-cost-v12-20261025/audit-2023-final-code
uv run --frozen python scripts/calibrate_oos_v12.py --phase audit --input artifacts/oos-cost-v12-20261025/synthetic-final-equivalent --output artifacts/oos-cost-v12-20261025/audit-final-final-code
uv run --frozen python scripts/calibrate_oos_v12.py --phase audit --input artifacts/oos-cost-v12-20261025/synthetic-wf-2021-equivalent --output artifacts/oos-cost-v12-20261025/audit-wf-2021-equivalent
uv run --frozen python scripts/calibrate_oos_v12.py --phase audit --input artifacts/oos-cost-v12-20261025/synthetic-wf-2022-equivalent --output artifacts/oos-cost-v12-20261025/audit-wf-2022-equivalent
uv run --frozen python docs/evidence/oos-v1-2-cost-calibration/checks.py
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen python docs/evidence/p3-permit-closure/audit_artifact_tree.py
sha256sum artifacts/p0-approved-v1/ledger.jsonl artifacts/p1-approved-v1/ledger.jsonl artifacts/p2-approved-v1/ledger.jsonl artifacts/p2r-approved-v2/ledger.jsonl artifacts/p3-approved-v1/ledger.jsonl data/processed/p2r-training-h1/manifest.json
du -sb artifacts/oos-cost-v12-20261025
```

Las dos primeras sondas de cortes no serializaban productos; se repitieron
**solo esas mediciones** en carpetas nuevas `fold-*-products` para medir
guardado y tamaño. Las primeras auditorías quedaron como antecedentes; las
carpetas `audit-*-final-code` registran la versión con guarda de entrada
sintética. Ninguna repetición corresponde a campañas ni a selección de
resultados. Hubo un fallo inicial de importación en el test nuevo y otro
de ruta en su fixture, corregidos; Ruff detectó primero un import no usado y
luego el orden de imports, corregidos. Los resultados finales aparecen abajo.

## Verificación

- Pruebas focales finales: **17/17**.
- Suite completa tras el código final: **351/351**, 242,77 s en la tercera
  ejecución. La primera había dado 351/351, 238,10 s; la segunda dio 350/351
  por una carrera preexistente en `test_supervisor_death_kills_worker`:
  `/proc/<pid>/status` desapareció entre la comprobación y su lectura.
  Esa prueba aislada pasó (1/1) y la suite completa siguiente pasó sin
  modificar el supervisor ni esa prueba.
- Ruff final: **sin hallazgos** (`uv run --frozen ruff check .`).
- [results.json](results.json) contiene hashes individuales de las 11 sondas
  usadas, costos y cálculo reproducible del presupuesto.
- Entorno observado: Python 3.12.13, Debian Linux 6.12.113+deb13-amd64,
  PyTorch 2.8.0+cpu, NumPy 2.5.3, pandas 2.3.3. El CPU fue el dispositivo
  usado; no se instaló ni usó CUDA.
- SHA-256 del código de sonda `scripts/calibrate_oos_v12.py`:
  `65abe55dada6bee5c51cd0c2d7ac8f0f6f2ce44c967fac9ba944ff11d96e2534`;
  módulo de actor `src/btc_risk_rl/agents/models.py`:
  `ed2f2522cb4e44e6b86a48f986b67cd2cf31d87db25a21f95e8dbcace0adea1a`.
- Salidas locales nuevas: 3.813.599 B en `artifacts/oos-cost-v12-20261025/`.
- Árbol P3: 47.487 archivos, 5.326.594.447 B,
  SHA-256 `73949350733bf3f8e3939e2dfcf7a28920668e738b0e5d910bd070a010fdcbec`.
- Ledgers originales SHA-256:

| Campaña | SHA-256 |
| --- | --- |
| P0 | `1d1ee72ca0ac49529f205b30942a68f381d86037e336091c490c624098339b8c` |
| P1 | `926eab40bc764e1cae88a74e6718ba70b50e2df0626e8e34964078cc4ba55755` |
| P2 | `e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8` |
| P2R | `fe443e5e32d26a7de075fa6e34771c8f20651bbe566f9097bfdb367d17d0b866` |
| P3 | `86b111b5365cda1760441d2f73d42e0463a4b4b2a7ddbc6e0e41f2a78751fcfe` |
| Derivado H1, manifiesto | `62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9` |

Los JSON de sonda enumeran explícitamente los archivos abiertos; cortes:
`manifest.json`, `bars.csv` del derivado y `configs/initial.toml`; recorridos:
checkpoint P3 fijo; auditorías: solo retornos sintéticos generados aquí.
No se abrieron CSV H1 compartidos ni archivos de 2023 o 2024–2025.

## Reproducción de resultados pequeños

Con la raíz local de sondas disponible:

```bash
uv run --frozen python docs/evidence/oos-v1-2-cost-calibration/checks.py
sha256sum docs/evidence/oos-v1-2-cost-calibration/results.json
```

Los productos históricos de cortes, retornos fabricados y checkpoints se
mantienen fuera de Git. `checks.py` lee los JSON de la calibración y la tabla
v1.2, comprueba cobertura, longitud y repetibilidad; no abre datos de mercado.
