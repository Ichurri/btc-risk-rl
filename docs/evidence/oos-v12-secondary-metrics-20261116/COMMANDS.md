# Reproducción y verificación

Análisis descriptivo posterior al cierre de la prueba confirmatoria.
Ejecutar desde la raíz del repositorio con las 108 trazas locales de la
campaña cerrada disponibles. NumPy 2.5.3 proviene de `uv.lock`.
Matplotlib 3.10.8 se instala en el entorno de ejecución de las figuras.

El código de generación quedó fijado en el commit `611bc29`.

## Generación original

```bash
uv run --frozen python scripts/compute_secondary_metrics.py
uv run --frozen --with matplotlib==3.10.8 python scripts/build_final_figures.py
uv run --frozen python scripts/build_final_report.py
```

La última orden escribe `reports/evaluacion-final/index.html` y una copia
idéntica en esta carpeta, además de `docs/tesis/insertar-en-tesis.md`.
Para abrirlo en Debian:

```bash
xdg-open reports/evaluacion-final/index.html
```

## Regeneración en un destino nuevo

```bash
tmp=$(mktemp -d /tmp/btc-oos-secondary-rebuild.XXXXXX)
uv run --frozen python scripts/compute_secondary_metrics.py --output "$tmp/evidence"
uv run --frozen --with matplotlib==3.10.8 python scripts/build_final_figures.py --evidence "$tmp/evidence"
uv run --frozen python scripts/build_final_report.py --evidence "$tmp/evidence" --report "$tmp/index.html" --thesis "$tmp/insertar-en-tesis.md"
```

Para cotejar solo las salidas versionadas:

```bash
(cd docs/evidence/oos-v12-secondary-metrics-20261116 && sha256sum -c SHA256SUMS)
```

## Comprobaciones

```bash
uv run --frozen pytest -q tests/test_oos_secondary_metrics.py
uv run --frozen ruff check .
uv run --frozen pytest
```

La prueba focal pasó con 7 casos. La suite completa obtuvo **716 aprobadas**
en 997,91 s, con dos advertencias de `fork()` en una prueba sintética
de reanudación. Ruff informó `All checks passed!`.

La regeneración en un destino temporal fue idéntica byte por byte para cada
CSV, PNG, JSON, la copia HTML y las notas de la tesis. Un cálculo independiente
con la biblioteca estándar reprodujo las siete métricas en el primer bloque
completo y en comprar y mantener (tolerancias absoluta y relativa de 10⁻¹³).

Se comprobaron las dimensiones de los cuatro PNG con Pillow y las siete
secciones del HTML con `html.parser`. Las cuatro imágenes son autocontenidas
y las anclas de navegación apuntan a secciones internas. La anchura de
cada figura es de 1.771 píxeles a 300 ppp, aproximadamente 15 cm.
