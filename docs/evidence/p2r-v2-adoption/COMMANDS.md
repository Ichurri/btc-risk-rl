# Adopción metodológica P2R v2 — verificaciones documentales

Base `119de48`; precisión de las tres ventanas `Z` registrada primero en
`36ed24d`. No se ejecutaron unidades, workers, recolectores, optimizadores ni
accesos a datos de mercado. La adopción se comprobó con lectura de documentos,
huellas preexistentes y un ejemplo algebraico sintético.

```bash
git status --short --branch
git log -4 --oneline
.venv/bin/python docs/evidence/p2r-v2-documental/checks.py > docs/evidence/p2r-v2-adoption/results.json
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen ruff check .
git diff --check
git diff --cached --check
```

El [resultado estático](results.json) confirma nueve corridas, los conteos
previstos, diez huellas de fuentes/P2/sonda 01, 32 archivos de sonda 02,
18 de 03 y 28 de 04/05, doce enlaces locales, estado documental adoptado y
las tres expresiones `Z` separadas. El ejemplo sintético calculó
`Z_D,temprana=0.0004`, `Z_D,tardía=0.0001` y `Z_A,tardía=0`; solo la tercera
puerta falla y el conjunto resulta inelegible. Es álgebra ilustrativa, no
prueba de un ejecutor o de resultados de mercado.

La primera versión de la comprobación documental de adopción no admitía
espacios distintos alrededor de `>` en el registro; se corrigió el lector,
sin cambiar la regla. La ejecución final pasó. Ruff devolvió
`All checks passed!`, y los controles de espacios de Git devolvieron cero.
No se repitió `pytest` porque no se modificó el algoritmo operativo ni sus
pruebas. La eliminación local previa de `.python-version` se conservó fuera
de los commits.
