# Resumen académico — trazabilidad prospectiva antes de P3

P3 v1.1 se adoptó como protocolo exploratorio de diagnóstico de
desarrollo, pero este hito **solo** implementa una condición previa de
integridad. Se corrigió la semántica de `market_training_executed`: el
valor verdadero exige procedencia aceptada exclusivamente de
entrenamiento y pasos completados de ambos optimizadores. El supervisor
comprueba el reporte contra el perfil, los deltas de recursos y el
checkpoint íntegro antes de incorporar una unidad al ledger.

Las pruebas usaron trayectorias sintéticas y sobres fabricados con
metadatos de entrenamiento. En la matriz Q0/iteración ×
sintético/entrenamiento, el supervisor aceptó los marcadores coherentes
y rechazó los contrarios. Un falso en una iteración con contadores
positivos de entrenamiento deja el ledger `failed`, sin aceptar la
unidad y sin alterar la huella del checkpoint Q0 anterior. Ese resultado
verifica el mecanismo de trazabilidad, **no** un entrenamiento histórico.

P2R conserva sus 99 reportes originales y su adjudicación `review`
únicamente descriptiva; el requisito de preflight omitido no queda
subsanado retrospectivamente. Tampoco se implementó βV² ni se habilitó
P3. Una campaña histórica requeriría revisión, infraestructura restante,
permiso separado y preflight nuevo. Validación 2023 y prueba final
2024–2025 permanecen protegidas.
