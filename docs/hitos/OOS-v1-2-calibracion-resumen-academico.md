# Resumen académico de la calibración v1.2

La propuesta fuera de muestra v1.2 continúa sin adoptarse. Se reconstruyeron,
sin actualizar agentes, los dos cortes retrospectivos a partir del derivado H1
exclusivo de entrenamiento: se reprodujeron 3.639 y 4.678 inicios de episodio
de 180 transiciones y se reajustaron normalizadores con 5.764 y 7.703
observaciones previas a cada corte. La carga de un checkpoint fijo de P3 tomó
3,520 s en una medición aislada; una sonda de evaluación continua con cartera
única y política determinista `sigmoid(μ)` tardó 0,255 s para 2.190 pasos y
0,514 s para 4.386 pasos **fabricados**. Se midieron aparte guardado, métricas,
auditoría, memoria y disco. Estas cifras describen infraestructura, no
desempeño financiero ni evaluación temporal.

El presupuesto v1.2 conserva 91.594 s extrapolados de entrenamiento y 43.200 s
de asignaciones aún no medidas. Así, 20 días de 3 h globales, con 2.700 s de
reserva diaria, dejan 27.206 s productivos condicionales. Una tasa de
entrenamiento 30 % mayor que la media P3 ya excedería ese tope, aun si las otras
asignaciones bastaran. Antes de afirmar viabilidad faltan costos de
entrenamiento por corte y de la ruta completa de evaluación y cierre; la sonda
sintética no los acredita. No se consultó 2023 ni el conjunto final, y no se
inició la campaña de 126 corridas.
