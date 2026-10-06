# Resumen académico: aislamiento físico del entrenamiento P2R

Se creó un derivado H1 exclusivo de entrenamiento para P2R, conservando
el calentamiento de 2017 y las rutas aceptadas de 2018–2022. Una
exportación separada verificó hashes H1 y comparó fila por fila los cinco
CSV derivados con el prefijo original. La lectura de bytes de 2023 se
limitó a esta comprobación de integridad; no se incorporaron al derivado
ni a cálculos de aprendizaje o diagnóstico. La segunda auditoría del
producto publicado confirmó 7.048 rutas, 10.054 transiciones, 15 segmentos
utilizables y 16/20/20 exclusiones. El normalizador H1 fue copiado sin
reajuste.

El manifiesto derivado se ancló en un commit independiente. Un preflight
instrumentado con vigilancia de aperturas leyó solo metadatos H1 y el
derivado; registró cero aperturas de los CSV compartidos, cero trayectorias
y cero actualizaciones. Este hito prueba aislamiento de acceso en esa
ruta de preflight e identidad con H1 en la exportación auditada. No evalúa
la calidad de una política, la generalización temporal ni el cumplimiento
de CVaR. El permiso de campaña continúa inactivo y la ejecución histórica
requiere otra autorización. Informe y evidencias:
[exportación](P2R-training-shard-export.md).
