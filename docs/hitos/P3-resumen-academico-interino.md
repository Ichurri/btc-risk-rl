# P3 v1.1 — resumen académico tras la primera sesión

P3 compara de forma pareada dos pérdidas del crítico: MSE (β=0) y
MSE+mean(V²) (β=1), en 18 corridas nuevas de entrenamiento 2018–2022.
La campaña aprobada es un diagnóstico de desarrollo motivado por la MSE
D tardía de P2R; no utiliza validación ni prueba final y no reinterpreta
las nueve corridas P2R. La autorización, los hiperparámetros provisionales,
las semillas, el orden y el presupuesto quedaron fijados antes de
observar resultados P3.

El preflight histórico pasó y la primera sesión `systemd --user` cerró
sin fallos por el límite de admisión presupuestaria. Completó diez de
dieciocho corridas y dejó una undécima después de cinco actualizaciones
íntegras. El ledger está `ready`, con 116 unidades aceptadas y ningún
trabajo parcial pendiente. Se cotejaron las cadenas del ledger/journal y
las huellas de los reportes y checkpoints aceptados.
La primera pareja C0 de 710031 cerró sus 22 unidades con checkpoints
completos, 9.040 trayectorias de aprendizaje y 640 D por brazo.
La identidad inicial esperada entre brazos se verificó; el término β
modificó el crítico. La sesión consumió 8.016,088 s del presupuesto
global del 8 de octubre: 95.120 trayectorias de aprendizaje, 6.720 D,
840 pasos de actor y 1.680 de crítico. D ocupó 524,157 s medidos en los
reportes acumulados de cada corrida. Aun con diez corridas completas,
no hay decisión conjunta de avance ni evidencia confirmatoria.
La interpretación final requerirá las
18 corridas y todas las puertas y diferencias de P3 v1.1, con la semilla
como bloque independiente y la razón exacta frente al predictor cero.
Este uso repetido del mismo histórico de entrenamiento es diagnóstico
de desarrollo: no demuestra generalización temporal, superioridad
financiera ni cumplimiento poblacional de CVaR.
