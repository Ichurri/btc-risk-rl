# Preparación segmentada B — plan de implementación

**Objetivo:** aplicar ADR-004 al histórico de desarrollo identificado por sus huellas,
verificar los productos persistidos y cerrar H1 antes del simulador.
**Arquitectura:** comando separado `prepare-segmented-development`; máscara y núcleo
puro en `data/segmentation.py`, persistencia en `data/segmented_pipeline.py` y auditoría
independiente en `data/segmented_audit.py`. Se reutilizan calidad y características.
**Tecnología:** Python, pandas/NumPy float64, JSON/CSV, pytest y uv.lock existente.

## Diseño dentro del alcance aprobado

La ruta estricta no cambia. Una ruta genérica que cuarentene cualquier anomalía
ampliaría ADR-004; por ello la ruta nueva exige coincidencia exacta con el inventario,
reaperturas y huellas del diagnóstico aprobado. Los originales se leen sin modificar.
La máscara cubre la rejilla completa con motivo, presencia y segmento; las ausencias
no tendrán precios. Todos los registros retenidos se conservan en bars.csv.

Cada segmento reinicia características: primera observación finita en índice 42,
primera transición en índice 43. Se permiten indicadores con contexto cronológico
anterior a una frontera, nunca retornos puntuados fuera de ella. Se conserva la
etiqueta de partición de cada barra. episodes.csv contiene solo entrenamiento,
180 objetivos y 181 estados por ventana. validation usa todas sus transiciones
continuas; no se fragmenta en episodios de 180 pasos.

Ajuste del normalizador: todas y solo las observaciones finitas cuyo timestamp
pertenece a entrenamiento, una vez por timestamp, incluidos segmentos cortos y
estados terminales. Excluye calentamiento, cuarentena, validación y test. El conjunto
de ajuste se publica en fit_observations.csv, media/std poblacional y parámetros
se persisten; validar y auditar carga parámetros y nunca invoca fit.

La aceptación exige integridad de fuentes, coincidencia exacta del inventario,
OHLCV/timestamps válidos incluso en cuarentena (salvo cierres abreviados aprobados),
segmentos contiguos, causalidad, finitud, normalización reproducible, cobertura e
índice completo de episodios. Se compara cada segmento contra impact.json. Si falla
un criterio no se escribe status accepted. La aceptación es técnica para desarrollo
bajo B: no certifica negociabilidad de cada apertura ni autoriza entrenamiento.

## Secuencia y archivos

- [x] Pruebas sintéticas en `tests/test_segmentation.py`: cuarentena y causas exactas,
  reinicio causal, 222/223 barras, ajuste sin validación, episodios y fronteras,
  anomalías no aprobadas, datos finales bloqueados, productos adulterados.
  Ejecutar primero `uv run --frozen pytest tests/test_segmentation.py -q` y conservar fallo.
- [x] Implementar núcleo `src/btc_risk_rl/data/segmentation.py`: máscara completa,
  características por segmento e índices, sin E/S de mercado ni ajustes implícitos.
- [x] Implementar pipeline y auditoría: validar manifiesto antes de páginas,
  cotejar inventario y cobertura, persistir y recargar scaler, verificar hashes,
  tablas e índices antes de aceptación. CLI para preparar y verificar sin red.
- [x] Ejecutar pruebas y `uv run --frozen ruff check .`; corregir fallos concretos.
- [x] Ejecutar preparación real exclusivamente desde `data/raw/development`,
  comprobar huellas antes/después, auditoría por segundo proceso y reproducción
  en otro destino. Guardar logs, versiones, manifiestos y comparación en evidencia.
- Actualizar ADR-004, README, DEBIAN, HANDOFF e informe del hito con resultados,
  alcance de aceptación, limitaciones y siguiente paso. Cerrar con commit explícito
  sin incluir la eliminación local de .python-version.
- Entrega posterior al commit: crear ZIP desde archivos versionados más los originales de desarrollo y el
  producto aceptado explícitamente enumerados; incluir commit, hashes y Git bundle.
  Excluir entornos, cachés, credenciales y otros datos. Verificar archivo y hashes.

## Ejecución

Se ejecuta en esta sesión sobre el repositorio abierto, autorizado por el usuario.
No se crea otro proyecto, no hay entrenamiento ni lectura del conjunto final.
