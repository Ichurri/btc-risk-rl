# Revisión independiente H5

Revisión de checkpoint/journal/presupuesto, adaptador entrenamiento, calendario y
verificador por agente de revisión; sin leer datos de mercado.

Hallazgo reproducido sintéticamente: un objeto pausado antiguo podía guardar
un checkpoint después de que otro objeto reanudado completara una generación,
retrocediendo el journal. La prueba `stale-red.log` reproduce el defecto.
Se corrigió con revisión SHA del journal por instancia, comprobación bajo flock
antes de cada append y antes de crear la carpeta del checkpoint. Prueba de
regresión y de escritor competidor añadidas; resultado en pruebas finales.

Segunda revisión estática: confirmó la corrección y la separación de recolección
congelada de mercado respecto de aprendizaje sintético; sin hallazgos materiales
abiertos. No atribuir a esa segunda revisión ejecución adicional de pruebas.
