# P0-approved-v1 — AUTORIZADO SOLO PARA P0

Autorización expresa del investigador en esta tarea sobre propuesta commit
7a379b7. Se preservan intactos P0-protocolo-v1.md y P0-candidate.json como
antecedentes. Configuración congelada: [P0-approved-v1.json](P0-approved-v1.json).

Se aprueban N_A=64, N_Q=N_B=400, K=2, redes/Adam/tasas/clip/hilos y criterios
numéricos de la propuesta. Tres bloques 410031, 410047, 410081 con órdenes
C0/C5/C10, C5/C10/C0, C10/C0/C5. Una implementación Q/A/B, auxiliares C0 incluidos.
Estos parámetros no son definitivos para el experimento confirmatorio.

Cota común C5/C10: **d=-ln(0.90)=0.10536051565782628**. Referencia económica del
10% expresada en pérdida logarítmica para el objetivo de 180 transiciones,
elegida antes de observar resultados. No es máximo de pérdida individual ni
de drawdown. No ajustar para obtener cumplimiento favorable.

Cambio aprobado respecto de §1 de la propuesta: se permiten varias corridas
consecutivas por día, en orden, sin concurrencia. **Tres horas GLOBAL por día**
para toda la campaña, incluidos carga, comprobaciones, ejecución, guardado y
cierre; nunca reiniciar al cambiar corrida/proceso. Día America/La_Paz, timestamps
UTC. Se conservan 15 min preflight, 135 min trabajo y 30 min reserva, topes Q0
30 min/iteración 45 min, margen 1.5, tres sesiones diarias distintas por corrida,
27 sesiones de campaña, criterios de integridad, advertencias y parada.

Se implementa una ventana diaria conservadora, anclada una sola vez por fecha;
los reinicios el mismo día conservan los deadlines absolutos. El tiempo offline
no abre otra ventana. Registrar además tiempo activo por invocación. El límite
absoluto se acorta en medianoche local y el trabajo acaba 30 min antes; no
iniciar unidades que no quepan, ni cargar sesiones del día siguiente al anterior.
Ninguna unidad cruza medianoche. No se promete completar nueve corridas si los
topes o fallos lo impiden. Sesión de una corrida se cuenta al empezar una unidad
en una fecha distinta; una pausa antes de Q0 no gasta una sesión de esa corrida.

Autorizado: registrar protocolo, implementar ejecutor/supervisor, verificar
sintéticamente tiempo/memoria/persistencia/reanudación/presupuesto compartido;
si pasa, ejecutar exclusivamente P0 sobre train aceptado 2018–2022. No volver a
solicitar permiso para estos pasos. Ante fallo, detener campaña y conservar
evidencia. Ante falta de tiempo, pausa en frontera completa y continuación otro
día bajo esta misma autorización. No selección de checkpoints por rendimiento.
Validación, final, posteriores campañas y cambios de tesis quedan fuera.
