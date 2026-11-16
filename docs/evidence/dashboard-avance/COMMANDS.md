# Verificación del dashboard local

Base `e1b7701`; rama nueva `codex/dashboard-avance-tesis`. Al iniciar, solo
existía la eliminación local de `.python-version`, que se conserva. Las fuentes
originales locales se inspeccionaron en solo lectura. No había servicios P3/WF
activos. El generador no importa modelos, fuentes de mercado ni ejecutores.

Comandos ejecutados:

```bash
uv run --frozen python scripts/build_thesis_dashboard.py
uv run --frozen pytest -q tests/test_thesis_dashboard.py
uv run --frozen ruff check .
uv run --with playwright==1.64.1 python scripts/check_thesis_dashboard_browser.py
xdg-open /home/ichurri/Desktop/personal_projects/btc-risk-rl/reports/avance-tesis/index.html
```

Resultados: cinco pruebas de integridad/comparabilidad pasan, Ruff pasa,
18 combinaciones P3 y tres semillas P1 verificadas en Chromium local. Se
probaron P0/P2/P2R/WF05 y sus selectores desactivados cuando no hay un desglose
semilla seleccionado. No hubo errores JavaScript ni desbordamiento a 390 px.
La prueba del navegador contrasta MSE mostrada con los datos exportados; las
pruebas Python contrastan todas las celdas con el JSON auditado original,
rechazan cobertura incompleta, MSE y denominador alterados, comprueban exportación
repetible y verifican SHA-256 de las fuentes antes/después de generar.

La dependencia Playwright 1.64.1 solo se usó para verificación mediante `--with`;
no cambia `pyproject.toml` ni `uv.lock`, ni es necesaria para abrir el HTML.
Un primer chequeo Ruff encontró imports y sentencias múltiples en el script de
navegador; se corrigieron y la comprobación final pasó. No se repitió la suite
completa de agentes: este cambio solo añade exportación e interfaz, sin alterar
el algoritmo, los permisos o la contabilidad.

Los JSON exportados incluyen rutas, SHA-256 completos y el commit de cada fuente
documental. Para P3 se exige además igualdad de hash entre ledger local,
cierre auditado y diagnóstico cruzado; los 18 reportes locales finales coinciden
con las huellas aceptadas. Los archivos CSV/NPZ/PT no se abren. Las capturas se
conservan fuera de Git en `reports/avance-tesis/`.

Objetivos: texto leído de la tesis de Drive en modo de solo lectura el
05/11/2026; extracto y enlace en `docs/DASHBOARD.md`. No se modificó Google Docs.

Ampliación de tablas: seis pruebas Python finales, conciliación de las 61
corridas con las unidades y tiempos del ledger, identidad de semilla/configuración
contra cada reporte original y rechazo de la unidad parcial P2. El navegador
verifica seis filas de campañas, 61 filas de corridas, nueve pares cruzados,
filtros P3/C10 y P2, las tres vistas y la descarga CSV. La primera prueba detectó
el nombre histórico `after_dual` de P0/P1; se especificó su frontera propia.
La prueba móvil detectó el ancho intrínseco del selector nuevo; se corrigió su
ancho máximo y pasó la repetición.
