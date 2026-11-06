# Autorización del usuario para continuar desde el 06/11/2026

**Registro de alcance; no es el permiso técnico activo del trabajador.** El
usuario autorizó integrar, verificar y, solo con puertas conformes, ejecutar
una medición **nueva** del costo del corte 2022 y avanzar hacia la evaluación
confirmatoria. Se conserva WF05 como `incomplete`, con permiso cerrado y
artefactos originales intactos. No se reanudará su ledger técnico `ready`.

Para la medición nueva se mantiene la propuesta
[`OOS-v1-2-costo-2022-exclusivo-v1.md`](../proposals/OOS-v1-2-costo-2022-exclusivo-v1.md):
raíz `artifacts/oos-v12-wf-cost-only-2022-01/`, C10, semilla 498614892,
Q0 y diez unidades Q/A/B+D, cuatro épocas de crítico, β=0, D=64,
solo derivado H1 de entrenamiento y checkpoints completos. La autorización
no reutiliza Q0 ni pesos de WF05. El registro JSON y el gate se fijarán por
huella en un commit independiente **después** de aprobar integración,
pruebas y preflight; un JSON aislado no activa la ruta.

La ventana preferente de unidades es 23:00–08:00 `America/La_Paz`.
**No se aumenta el presupuesto por ser una ventana de nueve horas.** Se
conservan 10.800 s globales por fecha local, reserva global 2.700 s;
3.600 s propios diarios, 4.800 s propios acumulados y máximo dos fechas
activas para este estudio, con reserva propia 600 s por fecha. Cada unidad
debe caber con su cota 120/180 s, checkpoint y reserva antes de medianoche
o de las 08:00. La bitácora empieza antes de la primera comprobación
específica y descuenta suite, Ruff, preflight, servicio, auditoría y cierre,
sin duplicar intervalos. Los registros llevan timestamps UTC y día La Paz.
Un fallo dentro de unidad bloquea reingreso; solo se retoma desde una
frontera `ready` completa con guardas nuevas. Dos días consumidos sin 11
unidades dan `incomplete`, no ampliación tácita.

La evaluación v1.2 sigue siendo [propuesta para
revisión](../proposals/cierre-pilotos-evaluacion-fuera-muestra-v1-2.md).
La autorización del usuario permite preparar el ejecutor, congelar el
protocolo y ejecutar la campaña cuando sus puertas estén resueltas; **no
convierte automáticamente las decisiones científicas propuestas en
metodología adoptada**. Antes de consultar el conjunto final deben quedar
resueltos los cambios de tesis sobre CPCV frente a dos cortes walk-forward,
el rol técnico de 2023, la configuración común, los 36 bloques, la inferencia,
las reglas de fallos y el presupuesto. Los tiempos de la nueva medición
informarán la viabilidad; no se abrirá 2023 ni 2024–2025 durante ella.

La entrega solicitada es el 16/11/2026. La v1.2 suma 134.794 s de trabajo
**extrapolado o asignado**, más 2.700 s de reserva por día, y calcula 17
fechas activas mínimas bajo sus supuestos. Entre el 06/11 y el 16/11 hay
11 fechas locales como máximo; el horario nocturno comparte fechas entre
sesiones. Por ello el calendario confirmatorio v1.2 actual no cabe dentro
del límite diario sin una revisión previa del alcance o del presupuesto.
La medición 2022 no corrige por sí sola ese desfase. No se recortarán
semillas ni reservas según resultados.
