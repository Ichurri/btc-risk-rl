# Comprobaciones de la propuesta v1.1 — 24/10/2026

**Alcance:** auditoría documental, algebraica y de **índices de entrenamiento**.
No se ejecutaron políticas, entrenamiento, CPCV, evaluación, validación 2023
ni prueba final. El auditor no modifica entradas.

## Archivos realmente leídos por el cálculo

`checks.py` intercepta `Path.open` durante `audit()` y exige exactamente
estas seis rutas. `cpcv-index-results.json` contiene sus SHA-256:

1. `data/processed/p2r-training-h1/manifest.json` — `62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9`;
2. `data/processed/segmented-B-h1/manifest.json` — `d7cd59b7cda003a0f69883a83a0bacf06a65c37f3653a2f466c249ddf41a6998`;
3. `data/processed/p2r-training-h1/episodes.csv` — índice exclusivo de entrenamiento;
4. `data/processed/p2r-training-h1/transitions.csv` — índice exclusivo de entrenamiento;
5. `data/processed/segmented-B-h1/fit_observations.csv` — índice de fechas elegibles de entrenamiento, sin valores de características;
6. `docs/evidence/p3-market-2026-10-13/final-closure.json` — metadatos de duración y estado de P3.

Los SHA-256 de los tres CSV de índices figuran en el JSON reproducible. El
auditor coteja la huella del manifiesto derivado fijada en el ejecutor P3,
las huellas de cada índice y el límite anterior a 2023. No abre CSV H1
compartidos, precios, valores de características, trayectorias ni pesos.
Durante la inspección preliminar de cabeceras, antes de escribir el auditor,
un comando `head -4 data/processed/p2r-training-h1/observations.csv` mostró
tres filas **normalizadas de entrenamiento**; no se usaron en los cálculos.

## Comandos y resultados de esta revisión

Desde la raíz del repositorio:

```bash
python3 docs/evidence/pilot-closure-v1-1/cpcv_index_audit.py > /tmp/pilot-closure-v1-1-reproduced.json
cmp docs/evidence/pilot-closure-v1-1/cpcv-index-results.json /tmp/pilot-closure-v1-1-reproduced.json
python3 docs/evidence/pilot-closure-v1-1/checks.py
uv run --frozen ruff check docs/evidence/pilot-closure-v1-1
git diff --check
sha256sum docs/evidence/pilot-closure-v1-1/cpcv-index-results.json
```

- Reproducción `cmp`: **idéntica, código 0**.
- Pruebas: **4/4 OK** en 2,452 s. Cubren fronteras semiabiertas,
  embargo, rechazo de hash/partición y lista cerrada de archivos abiertos.
- Ruff: **All checks passed!**; `git diff --check`: código 0.
- Resultado JSON: `30c793e4765b6615169123117dfb6719b07b8ed662d4617df864a225acb6ff2c`.
- Primer Ruff de desarrollo encontró solo orden de importaciones de
  `cpcv_index_audit.py`; se aplicó `ruff --fix` y el comando final pasó.

También se ejecutaron los comandos de verificación general de `AGENTS.md`:

```bash
uv run --frozen ruff check .
uv run --frozen pytest
```

- Ruff general: **All checks passed!**
- Pytest: **344 aprobadas, 2 fallidas**, 254,93 s. Fallaron
  `tests/test_p3_market_guard.py::test_public_and_worker_commands_fail_before_loading_or_creating_artifacts`
  y `::test_editing_approval_json_cannot_activate_p3`. Ambas pruebas aún
  esperan el permiso P3 **inactivo**, mientras el código aprobado en
  `p3_market.py` tiene `MARKET_EXECUTION_ENABLED=True` y registro fijado
  para la campaña histórica ya cerrada. La primera recibió el rechazo de
  contexto `systemd --user` antes de cargar mercado; la segunda recibió
  `P3 market approval hash mismatch` ante un JSON falsificado en vez de
  `NOT AUTHORIZED`. No se modificó código operativo ni pruebas históricas
  en esta revisión documental. Estos fallos no afectan los cuatro checks
  del auditor, pero la suite general **no pasó** y requiere mantenimiento
  de expectativas en otro hito.

El auditor calcula cobertura **potencial** de índices, no ejecuta folds.
Los escenarios de tiempo multiplican las duraciones P3 β=0 observadas;
las precisiones usan supuestos explícitos sobre la dispersión pareada,
no retornos de 2023 ni estimaciones empíricas de potencia.
