# P3 — resumen para el chat académico

Se implementó la infraestructura de una campaña P3 nueva de diagnóstico
de desarrollo, separada de P2R. El contraste propuesto mantiene 18
corridas ordenadas por tres semillas, tres condiciones y dos pérdidas
del crítico; cada brazo tiene política, trayectorias, objetivos D y
checkpoints propios. La regla de decisión usa la comparación exacta con
el predictor cero y razones pareadas con el denominador de cada brazo.

Las pruebas realizadas fueron sintéticas: verificaron Q0, Q/A/B+D,
equivalencia β=0, separación de brazos, reanudación entre unidades,
presupuesto compartido y rechazo irreversible de unidades o reportes
incoherentes. El preflight de solo lectura confirmó el derivado H1
exclusivo de entrenamiento y 7.048 inicios; registró los archivos abiertos
y no abrió CSV H1 compartidos ni conjuntos de validación/final. En la
medición actual la memoria libre quedó por debajo del umbral operativo.

No hubo entrenamiento histórico ni permiso de campaña. La infraestructura
no demuestra que β=1 mejore el crítico, ni permite inferencias de
generalización o CVaR. Antes de pedir autorización histórica deben
revisarse las evidencias, repetirse el preflight de recursos y servicio,
y fijarse por separado registro, raíz y huellas de la campaña. P2R
continúa con resultado `review` descriptivo y sus 99 reportes intactos.
