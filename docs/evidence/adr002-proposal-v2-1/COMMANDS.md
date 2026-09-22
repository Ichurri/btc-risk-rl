# Evidencia de armonización ADR-002 v2.1

Fecha: 22-09-2026 UTC. Base documental `28cda8b3dc9803f9c2e3e37057865dbb9baa0de9`;
contrato H2 `cc913b629694641543e2b54375dbda5d55130544`.
Se conservó el único cambio local inicial: eliminación previa de `.python-version`.

## Comandos ejecutados en el repositorio local

```bash
git status --short
git log -1 --oneline
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python docs/evidence/adr002-proposal-v2-1/checks.py > docs/evidence/adr002-proposal-v2-1/results.json
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check . > docs/evidence/adr002-proposal-v2-1/ruff.log
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen pytest > docs/evidence/adr002-proposal-v2-1/pytest.log
git diff --check
```

Se consultaron AGENTS, HANDOFF, ADR-002, README, configuración, propuesta y
resumen v2, comprobaciones y empaquetador v2. La búsqueda local no encontró
una especificación autónoma de bootstrap/Holm: se incorporó el plan de tesis
comunicado explícitamente por el usuario. Se consultó el artículo original de
Holm enlazado en v2.1; no se afirma acceso al documento de tesis.

## Resultados y separación de alcances

- Checks, salida 0: tres grupos aritméticos/de especificación afectados y uno
  de preservación; resultados exactos y huellas en results.json.
- Anualización: retornos simples, MAR=0, DD sobre todos los períodos, factor
  fijo sqrt(2190); cero DD conserva ambos ratios indefinidos, incluso con media
  positiva. No se sustituye el factor por sqrt(T).
- Bootstrap: enumeración exacta de 27 remuestras de tres bloques **sintéticos**;
  centrado bajo H0, índices comunes a dos columnas y cola unilateral. P exactos
  4/27 y 17/27; control sin centrar 17/27 y 17/27. La aritmética del conteo Monte
  Carlo corregido se prueba aparte: no hubo remuestreo aleatorio ni se fijó B
  para una evaluación real. La anualización conserva las excedencias.
- Holm: cinco casos con p ajustados, orden original, umbral familiar .05 y
  comprobación independiente mediante parada secuencial. Incluye el caso donde
  no se rechaza ninguno aunque el segundo p bruto sea menor que .05.
- Preservación: secciones Q/A/B, decisión temporal y recorrido iguales byte a
  byte a v2; archivos v2 iguales a 28cda8b; src/configs/tests/scripts/lock/pyproject
  iguales a H2. No se ejecutaron de nuevo los checks v2 ni se modificaron sus logs.
- Ruff, salida 0: `All checks passed!`. Se repitió tras añadir el empaquetador.
- Pytest, salida 0: **100 passed in 21.73s**. Suite H2 existente con fixtures
  sintéticos; es una nueva ejecución local, no validación de un agente o de
  la inferencia sobre rendimientos reales.

No se implementó el módulo de evaluación, no se entrenó, no se cargó mercado
ni se accedió al conjunto final. La política inferencial para métricas indefinidas
sigue pendiente; los checks no implementan imputación ni exclusión selectiva.

## Paquete académico

Después del commit documental:

```bash
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen python docs/evidence/adr002-proposal-v2-1/package_delivery.py
```

El empaquetador usa snapshot de HEAD y Git bundle, conservando antecedentes v2,
pero excluyendo datos de mercado, artifacts y cambios locales sin commit.
Verifica bundle, CRC y hashes internos. DELIVERY.json y el recibo externo
registran commit, comandos, tamaño y SHA-256. No modifica el contrato H2.
