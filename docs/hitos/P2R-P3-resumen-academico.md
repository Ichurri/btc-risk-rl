# P2R adjudicado y P3 propuesto — resumen para la tesis

Los 99 reportes P2R conservan `market_training_executed=false`. Se
demostró que el campo excluye el perfil P2R aunque 90 unidades contienen
pasos reales de optimizador y cambios de pesos. La verificación del campo
**faltó antes del preflight**, requisito expreso de P2R v2. La
[adjudicación](../protocols/P2R-adjudicacion-metadato-v1.md) mantiene
`review` como resultado numérico, conserva todos los artefactos y limita
su interpretación a **diagnóstico descriptivo de desarrollo**. No declara
cumplido retrospectivamente el requisito ni convierte P2R en evidencia
confirmatoria.

La [auditoría de MSE](P2R-error-valor-tardio.md) encuentra que, en las
semillas 610031 y 610047, C0/C5/C10 reducen mucho la MSE D desde el
inicio, pero terminan con `R_D`≈1,046 y ≈1,105 frente al predictor cero.
El exceso se debe algebraicamente a `E[V²]>2E[VG]`: la variación de las
predicciones no queda compensada por su covariación con los objetivos.
En 610047 el sesgo medio es pequeño, así que no basta atribuirlo a un
desplazamiento de la media. El último tercio del horizonte tiene R>1
incluso en 610081, cuyo agregado global sí baja de uno. Estas son
observaciones del mismo histórico, no una causa de modelado demostrada
ni generalización temporal.

Se [propone P3](../proposals/P3-protocolo-v1.md) como estudio pareado de
un único cambio: penalización `β·V²` en la pérdida del crítico con β=0
frente a β=1. Tendría 18 corridas K10, tres semillas nuevas, C0/C5/C10,
D64 y presupuesto de hasta tres días activos de 3 h globales/día. Un
criterio conjunto predefinido exige mejora de D tardía frente al brazo
control y al predictor cero, especialmente en el último tercio, sin
degradación excesiva en A. P3 es una **propuesta no autorizada**; no se
implementó ni ejecutó. Antes de cualquier futura campaña deberán
corregirse prospectivamente el marcador y su comprobación por el
supervisor, y obtenerse autorización separada. Ni P2R ni P3 propuesto
demuestran rentabilidad o cumplimiento poblacional de CVaR.
