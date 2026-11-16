# Reproducción y verificación

Análisis descriptivo posterior al cierre de la prueba confirmatoria.
Ejecutar desde la raíz del repositorio con las 108 trazas locales de la
campaña cerrada disponibles. NumPy 2.5.3 proviene de `uv.lock`.
Matplotlib 3.10.8 se instala en el entorno de ejecución de las figuras.

El código del cálculo original quedó fijado en `611bc29`. La versión
publicada de las figuras distingue C0 (azul), C5 (naranja), C10 (verde)
y comprar y mantener (violeta). Los estilos de línea, tramas y marcadores
permiten distinguir las condiciones también en escala de grises.

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

## Regeneración de figuras y HTML desde los CSV

Se regeneraron las cuatro figuras usando los CSV publicados, sin recalcular
métricas ni leer las trazas. El HTML incorpora los nuevos PNG. El material
para la tesis se reprodujo byte por byte.

```bash
evidence=docs/evidence/oos-v12-secondary-metrics-20261116
tmp=$(mktemp -d /tmp/btc-oos-color.XXXXXX)
cp "$evidence"/*.csv "$evidence/integrity.json" "$tmp/"
uv run --frozen --with matplotlib==3.10.8 python scripts/build_final_figures.py --evidence "$tmp"
uv run --frozen python scripts/build_final_report.py --evidence "$tmp" --report "$tmp/report.html" --thesis "$tmp/insertar-en-tesis.md"
```

Se verificaron el color, el tamaño de 1.771 píxeles de ancho, los 300 ppp
y la igualdad entre los PNG publicados y los incorporados en el HTML.
Pasaron Ruff y 10 pruebas focales de métricas y figuras.
