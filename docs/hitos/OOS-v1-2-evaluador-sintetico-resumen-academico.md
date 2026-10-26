# Resumen académico — evaluación sintética y costo de cortes v1.2

Se completó una ruta **sintética** de evaluación continua antes de decidir
si se adopta el protocolo fuera de muestra v1.2. El proceso verifica un
checkpoint fijo y el normalizador exclusivo de entrenamiento, calcula
características de OHLCV fabricado, aplica la acción determinista
`sigmoid(μ)`, mantiene una cartera, cobra costos H3, registra retornos y
recompensas, calcula métricas y audita una traza completa antes del cierre.
Cinco unidades nuevas `systemd --user` midieron entre **6,631 y 7,916 s**
de pared externo para 1.979–4.386 transiciones; el pico de memoria informado
por systemd fue **622,6–622,9 MB**. Tres ejecuciones idénticas de 2.190 pasos
produjeron la misma huella. Son **mediciones de infraestructura con datos
fabricados**, no resultados de rentabilidad, riesgo o generalización.

El presupuesto de 20 días sigue siendo condicional: 91.594 s de entrenamiento
extrapolado más 43.200 s de asignaciones aún no medidas dejan 27.206 s de
margen productivo. La extrapolación de 234 procesos sintéticos completos es
1.659 s, pero no sustituye la carga y auditoría de recorridos históricos ni
estima entrenamientos nuevos. Se propone, **sin autorización de ejecución**,
medir dos corridas C10 nuevas, una por corte 2021/2022, con semillas disjuntas,
22 unidades exactas y 5.400 s acumulados como máximo dentro del presupuesto
diario global. Esa medición informaría el costo de cortes; no seleccionaría
políticas ni probaría que C0/C5 tienen el mismo costo. No se consultó
validación 2023 ni el conjunto final.
