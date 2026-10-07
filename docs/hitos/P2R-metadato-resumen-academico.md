# P2R v2 — resumen académico de la discrepancia de metadatos

La revisión de solo lectura comprobó que `market_training_executed=false`
en los 99 reportes P2R resulta de una condición fija del generador de
informes: reconoce P0/P1, pero excluye el perfil `authorized_p2r_only`.
Nueve reportes corresponden a Q0, sin pasos de optimizador; los otros 90
corresponden a Q/A/B+D y tienen, cada uno, ocho pasos de actor y dieciséis
de crítico. Los estados de optimizador y las huellas de pesos en los 99
checkpoints corroboran los contadores. Todos conservan la procedencia del
derivado H1 exclusivo de entrenamiento y el mismo hash del código que
produce el campo. La etiqueta no fue utilizada para decidir muestras,
actualizaciones o aceptación de unidades.

El defecto sí incumple una condición expresa de P2R v2: verificar o
corregir ese metadato antes de congelar el ejecutor. Recomendamos mantener
el resultado **numérico `review`**, sin reescribir artefactos, y suspender
la aceptación metodológica formal hasta que la revisión académica
adjudique explícitamente la desviación. Las cifras sirven como diagnóstico
descriptivo de desarrollo, no como validación temporal ni demostración de
rentabilidad o cumplimiento poblacional de CVaR. Una decisión estricta de
inelegibilidad o una excepción motivada requerirían un acta separada;
ninguna implica repetir P2R ni cambiar el cálculo numérico.

[Informe y propuesta](P2R-metadato-entrenamiento-revision.md) ·
[auditoría reproducible](../evidence/p2r-metadata-review/COMMANDS.md) ·
[resultados](../evidence/p2r-metadata-review/results.json).
