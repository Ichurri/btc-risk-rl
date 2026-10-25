# Resumen académico — propuesta de evaluación v1.2

**Para revisión, sin adopción ni ejecución.** Se propone cerrar la serie
de pilotos P0–P3 conservando su evidencia y pasar a una única
configuración común de desarrollo: crítico β=0, cuatro épocas y K=10.
P1 mostró mejor ajuste del crítico sobre A; P2 terminó interrumpido;
P2R quedó `review` con alcance descriptivo; P3 cerró `review` y no
justificó incorporar la penalización β=1. La configuración β=0 no se
declara óptima ni acreditada en precisión fuera de entrenamiento.

El diseño candidato usa **36 semillas nuevas pareadas** y C0/C5/C10
en cada bloque, con el mismo aprendizaje y diferente mecanismo de
riesgo. El efecto mínimo de interés propuesto es +0,50 unidades de
Sortino anualizado. Para 36 bloques, una aproximación normal da
potencia de 85 % si la SD pareada fuera 1,0, pero solo 52 % si fuera
1,5; no existe una estimación de esa SD fuera de muestra. La inferencia
propuesta remuestrea bloques completos, centra la nula y aplica Holm
para dos contrastes. Un Sortino superior no demuestra la restricción
CVaR H180.

La auditoría de índices H1 mostró que CPCV tiene cobertura potencial,
pero exige reentrenamiento y refit por partición. Se propone sustituir
su promesa metodológica por **dos cortes walk-forward purgados** dentro
de 2018–2022, con tres semillas auxiliares de desarrollo por corte. Son
diagnósticos retrospectivos sobre años ya conocidos en los pilotos, no
una distribución CPCV ni evaluación independiente. La partición 2023
se reservaría para **una puerta técnica predefinida**, sin seleccionar
hiperparámetros; si exige rediseño, 2023 quedará reconocido como
desarrollo observado. La prueba final 2024–2025 sigue cerrada.

Nueve corridas P3 β=0 midieron 6.542 s de pared; escalar su promedio a
108 corridas principales y 18 auxiliares produce 91.594 s de entrenamiento
**extrapolado**. Con asignaciones no medidas de 6 h para evaluación
(2023 + final), 6 h para refit/auditoría/inferencia y 45 min de reserva
por día, el plan ocupa **al menos 17 días activos** de 3 h globales bajo
esos supuestos. Se propone un tope de 20 días para revisión. Exigir las
36 semillas también en cada corte elevaría el mínimo a 35 días; esa
variante no cabe en el tope. Si el presupuesto propuesto no se puede
financiar, la alternativa de 12 bloques principales queda expresamente
**exploratoria**, con potencia nominal de ~41 % para SD=1,0 y el efecto
propuesto. Ningún escenario es una medición de entrenamiento futuro.

Antes de cualquier ejecución se requiere armonizar §§2.7.2, 2.7.3 y
3.8.4, Tabla 4 y apartados relacionados de la tesis; verificar un
ejecutor y la acción determinista, medir costos faltantes y aprobar
un protocolo y presupuesto nuevos. Ni esta nota ni su cálculo estático
autorizan entrenamiento, consulta de 2023 o acceso al período final.
