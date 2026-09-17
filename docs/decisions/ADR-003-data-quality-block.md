# ADR-003: bloqueo observado en la serie histórica

Estado: diagnóstico real; no se modifica la política de datos para evitar el fallo.

Se descargaron 14 páginas de la API primaria para [2017-12-01, 2024-01-01).
Cobertura esperada: 13.332 velas. Recibidas: 13.316. Faltan 16 aperturas.
20 velas poseen cierre anterior a open_time + 4h - 1ms.
OHLCV y aperturas de los registros recibidos: sin anomalías detectadas.
Los detalles exactos están en docs/evidence/quality-real.json.

No se ha establecido la causa de esos eventos. No atribuirlos automáticamente a
mantenimiento ni afirmar que una segunda fuente los confirma.
La reconsulta puntual conserva respuestas originales y no reemplaza la descarga.

## Consecuencia
El control estricto de calidad FALLA. El pipeline no genera train.csv,
validation.csv ni scaler.json aceptados. No se implementa el simulador sobre
un dataset rechazado. Las 28 pruebas del código pasan sobre casos sintéticos
identificados; eso no convierte el histórico en un dataset aprobado.

## Siguiente tarea técnica
Resolver el tratamiento documentado de períodos sin barras y cierres abreviados:
1. Examinar respuestas puntuales y, si corresponde, metadatos/fuente histórica.
2. Separar diferencias de metadatos de ausencia real de operaciones.
3. Proponer una regla explícita que preserve causalidad: por ejemplo segmentos
   contiguos con reinicio y calentamiento tras interrupciones. No aplicarla aún.
4. Cuantificar barras/episodios excluidos antes de ejecutar agentes; sin elegir
   exclusiones por retornos o desempeño. Validación sigue cronológica.
5. Registrar el cambio metodológico, pruebas de fronteras y nuevo manifiesto.

No resolver mediante forward-fill, inventando velas, seleccionando fechas por
rentabilidad ni permitiendo saltos temporales como una transición ordinaria.
Las particiones y el test final se mantienen intactos.
