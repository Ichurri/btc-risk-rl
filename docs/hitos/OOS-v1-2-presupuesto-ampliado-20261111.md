# Enmienda prospectiva del presupuesto OOS — 11/11/2026

## Alcance

Santiago sustituyó la ventana fija de 01:00–09:00 por ejecución a cualquier hora en Debian y autorizó ampliar prospectivamente el presupuesto con base en tiempos medidos. La [enmienda fijada](../protocols/OOS-v1-2-training-budget-amendment-20261111.json) conserva el protocolo científico, roster, fuentes y topes por unidad. El protocolo de entrenamiento original y las aprobaciones v1/v2 permanecen como evidencia histórica. Validación 2023 y prueba final 2024–2025 siguen cerradas: la enmienda autoriza entrenamiento, no evaluación.

Límite nuevo: **50.400 s globales por fecha de `America/La_Paz`**, máximo 20 días activos y **2.700 s reservados para cierre**. Cada admisión termina como máximo en la medianoche local o en el corte de presentación del 16/11 a las 09:00, el que llegue antes. Los topes Q0 de 1.800 s, Q/A/B+D de 2.700 s y preparación formal de 900 s no cambian. El servicio tiene `Restart=no` y un máximo de pared de 15 h, mayor que el límite diario de 14 h para permitir el cierre.

## Base temporal y conciliación

| Concepto | Segundos | Naturaleza |
| --- | ---: | --- |
| `wf-2021`, nueve corridas, unidades aceptadas | 6.401,296 | Medición del ledger; incluida en la sesión siguiente. |
| Sesión completa del 11/11, preparación y 99 unidades | 6.942,163 | Unión medida de bitácora y ledger, sin duplicación. |
| Suite posterior a esa sesión | 539,80 | Medida fuera de la bitácora original. |
| Ajuste adicional del 11/11 | 3.857,837 | **Cargo conservador**, no tiempo medido: eleva el débito anterior a nuevo trabajo a 10.800 s y cubre la suite y tareas no cronometradas con exactitud. Se suma al tiempo nuevo, no se aplica `max` al total, para no regalar los primeros 3.857,837 s posteriores. |
| Una C10 del corte 2022-03, supervisión de 11 unidades | 716,202 | Medición de costo; otra campaña. |
| P3, nueve corridas β=0 | 6.542,420 | Medición de desarrollo comparable como referencia temporal, no garantía de OOS. |

Quedan nueve corridas `wf-2022` y 108 principales. A 716,202 s por corrida, **117 corridas ≈ 83.795,634 s (23,28 h)** de unidades por extrapolación: `wf-2022` ≈ 6.445,818 s (1,79 h) y 36 ternas principales ≈ 77.349,816 s (21,49 h). La propuesta v1.2 asignó además topes, **no mediciones**, de 10.800 s (3 h) para la comprobación técnica 2023, 10.800 s (3 h) para evaluación final y 21.600 s (6 h) para auditoría, preflight, refit, inferencia y cierre. Sumados a la nueva extrapolación de entrenamiento, esos topes darían **126.995,634 s (35,28 h) pendientes**; falta comprobar si alcanzan. La propuesta anterior estimó 37,44 h para el programa completo, usando otra tasa de entrenamiento. Tres fechas completas bajo el límite ampliado ofrecen 39,75 h antes de reservas, pero hoy parte del presupuesto se consumió y el costo confirmatorio real aún no se midió. No se promete finalizar el 16/11.

## Adjudicación del corte 2021

La cadena del ledger y las huellas de 99 checkpoints, reportes y solicitudes se verificaron. La reconstrucción conservadora halló que 99/99 unidades habrían cabido con reserva y cero cargos ajenos registrados. No demuestra que el supervisor original tuviera el bloqueo global correcto: escribió bajo `artifacts/artifacts/`. Por ello se conserva como **entrenamiento íntegro y diagnóstico descriptivo de desarrollo**, sin declararlo prueba de cumplimiento estricto de exclusividad. El corte 2022 y las corridas principales arrancan con fuentes y estados propios; no reutilizan checkpoints 2021. El protocolo clasifica los cortes walk-forward como controles de integridad y cobertura, sin seleccionar por desempeño. Esta adjudicación no modifica los 99 archivos ni sus hashes.

## Reglas de operación

La preparación durable, el supervisor y los tres perfiles usan el mismo `artifacts/shared-pilot-budget/global.lock`. La bitácora empieza antes de suite; su unión con el ledger carga cada intervalo una vez. La admisión Q0 o Q/A/B+D verifica saldo global, reserva y plazo local; un fallo dentro de unidad deja `failed` sin reanudación. Cada nueva sesión exige suite formal, Ruff y preflight vigilado actuales, CA, batería ≥50 %, `MemAvailable` inicial ≥6.026.846.208 B, guarda operativa ≥4 GiB, disco ≥20 GiB, `Linger=yes`, gestor `running` y huellas. El timer diario se usa como reintento, no como única ventana: el lanzamiento manual del 11/11 se hace solo después del nuevo permiso, pruebas y preflight.

La evaluación v1.2 aún necesita congelación y permiso propios. Una tabla/figura de entrenamiento puede mostrar unidades, tiempos y recursos; ninguna curva de entrenamiento demuestra Sortino fuera de muestra, generalización ni cumplimiento poblacional de CVaR.
