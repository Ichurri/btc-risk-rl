# Evidencia y comandos — propuesta v1.2 (25/10/2026)

**Alcance:** documentación, lectura de la tesis en Google Drive y
cálculo estático sobre **dos resúmenes ya versionados**. No se abrió
ningún CSV, trayectoria, checkpoint, valor de mercado, archivo de
validación 2023 ni prueba final 2024–2025. No hubo entrenamiento,
evaluación ni modificación de P0–P3. La eliminación local previa de
`.python-version` quedó fuera de Git.

## Fuentes del cálculo y huellas exigidas

`costs.py` falla si cambian estos dos archivos; `checks.py` intercepta
la lectura y comprueba que no se abra ninguna otra ruta:

| Fuente versionada | SHA-256 |
| --- | --- |
| `docs/evidence/p3-market-2026-10-13/final-closure.json` | `1d96dd5ed2cb4af27a0f3993501ea7c40ece67ccc5862fe0f9d7b0049c033c6d` |
| `docs/evidence/pilot-closure-v1-1/cpcv-index-results.json` | `30c793e4765b6615169123117dfb6719b07b8ed662d4617df864a225acb6ff2c` |

Drive devolvió para la tesis indicada por el usuario el título
`Santiago_Iturri_formato_UCB_preliminares` y modificación
`2026-10-25T00:51:58.069Z`. Se leyó el texto del Doc mediante el
conector de Google Drive, sin editarlo. Se cotejaron §§2.7.2, 2.7.3,
3.5.2, 3.8.4, 3.9.2, 3.12.2, 4.3.3 y Tabla 4.

## Comandos ejecutados desde la raíz del repositorio

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git log -4 --oneline --decorate
git switch -c codex/oos-evaluation-v1-2
python3 docs/evidence/pilot-closure-v1-2/costs.py \
  > docs/evidence/pilot-closure-v1-2/results.json
python3 docs/evidence/pilot-closure-v1-2/checks.py
uv run --frozen ruff check docs/evidence/pilot-closure-v1-2
uv run --frozen pytest
uv run --frozen ruff check .
python3 docs/evidence/pilot-closure-v1-2/costs.py \
  > /tmp/pilot-closure-v1-2-reproduced.json
cmp docs/evidence/pilot-closure-v1-2/results.json \
  /tmp/pilot-closure-v1-2-reproduced.json
sha256sum docs/evidence/pilot-closure-v1-2/results.json
git diff --check
```

Resultados realmente observados: **4/4** checks algebraicos y de
lecturas pasaron; `cmp` devolvió **0**; Ruff de archivos nuevos y del
repositorio completo imprimió `All checks passed!`; Pytest terminó
**347 passed in 258,85 s**. El JSON reproducido tiene SHA-256
`28d014e92ac050d7e66070c1839bb6f37b2dee2969ca201b6a11afa28d27a5b5`.
El control de enlaces relativos de los tres documentos nuevos no halló
rutas ausentes; `git diff --check` devolvió 0.

## Lectura de los números

El único **tiempo medido** usado es el cierre P3 β=0: nueve corridas,
6.542,4198437 s de pared de unidad, con D incluida. Las nuevas
duraciones de entrenamiento son `número de corridas × 6.542,4198437/9`;
no predicen el costo de un corte reducido. Los 10.800 s para cada etapa
de evaluación y 21.600 s para auditoría/refit/inferencia son
**asignaciones máximas propuestas, no mediciones**. Se reservan 2.700 s
por día y se divide el trabajo por 8.100 s diarios para obtener el
**mínimo** de días activos; calendario real y suficiencia de cada tope
siguen sin comprobarse. La sensibilidad estadística usa SD pareadas
supuestas, no retornos de políticas fuera de muestra.
