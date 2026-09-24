# Revisión previa a mercado P1

Revisión independiente de código, sin acceso a mercado ni modificaciones por el
revisor. Configuración/orden, contadores 2/4, reanudación, comparación inicial y
contabilidad de fallos revisados. No quedaron bloqueos tras corregir:

1. Mover el bloqueo/débito compartido al runner público, protegiendo tanto P0
   como P1 y llamadas directas. Prueba de exclusión y de presupuesto persistente.
2. Añadir pruebas de diagnósticos habilitados/deshabilitados: actores, críticos,
   Adam, eventos/auditorías idénticos; RNG y gradientes existentes sin cambios.
3. Usar literalmente MSE4<=0.8*MSE2 incluso en cero/cero; porcentaje indefinido.
   Prueba RED específica y corrección antes de mercado.

La prueba histórica de supervisor sintético empleaba expected_resources con un
argumento. Se preservó esa interfaz en P0; P1 añade épocas explícitamente.
No se cambió Q/A/B ni se seleccionaron hiperparámetros durante la revisión.
