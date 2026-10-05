# Resumen académico — P2R v2 para revisión

**Estado: PROPUESTA PARA REVISIÓN, NO ADOPTADA.**
[P2R v2](P2R-protocolo-v2.md) propone repetir desde cero las nueve corridas
del diseño P2: semillas 610031/610047/610081, condiciones C0/C5/C10 con
orden rotado, K=10, Q0 y diez unidades Q/A/B+D por corrida. La campaña P2
interrumpida por un apagado permanece separada y fallida; sus cinco corridas
terminadas no integran la matriz P2R. Se mantienen ADR-002, d común,
recompensa, normalizador, H180, muestreo H1 de entrenamiento y cuatro épocas
provisionales del crítico. D64 evalúa ambos críticos sobre los mismos retornos
completos de trayectorias nuevas generadas por la copia congelada de `π_k`;
no modifica el aprendizaje.

El objetivo es describir la evolución del error de valor sobre A y D en el
histórico de entrenamiento, con criterios técnicos conjuntos ya fijados para
P2. Para que las razones de la regla conjunta sean informativas, se exige
`Z>10⁻¹²` **por separado** en D temprana, D tardía y A tardía, tras agregar
cada ventana; un estabilizador numérico no sustituye ninguna de las tres
puertas. D no es un período temporalmente separado: rutas y transiciones pueden
solaparse con aprendizaje. Ni un resultado favorable ni la supervivencia del
supervisor demostrarían generalización, rentabilidad, cumplimiento
poblacional de CVaR o validez confirmatoria. La v2 mantiene las fronteras
`after_q0` y `after_dual_and_D`, presupuesto global de tres horas por día
America/La_Paz durante hasta tres días activos y fallo irreversible ante una
unidad incompleta; un checkpoint anterior no autoriza reanudar selectivamente
una campaña fallida.

Las sondas sintéticas permiten precisar el alcance del preflight: la 01
terminó Q0 pero falló por suspensión posterior; la 02 verificó continuidad
de Q0 tras logout completo con `Linger=yes` y sin suspensión hasta el nuevo
ingreso, aunque incumplió la cadencia de heartbeat. La 03 corrigió y midió
seis intervalos ≤5 s en Q0 breve. Las 04/05 mostraron fallo permanente por
SIGTERM durante Q0; tras corregir la salida de la CLI, systemd indicó fallo.
Estas mediciones no equivalen a prueba de señal durante Q/A/B+D, conservación
con huellas de un checkpoint previo tras fallo de la unidad siguiente, ni
continuidad ante apagado físico. Las pruebas automatizadas sintéticas cubren
parte de esos estados, pero no una campaña histórica bajo el servicio.

Antes de una eventual adopción se debe revisar el contrato científico y
cerrar las brechas de infraestructura. Después harían falta un ejecutor
histórico train-only, huellas congeladas, pruebas sintéticas de equivalencia
y recuperación, preflight vivo y un permiso de campaña P2R nuevo y separado.
Esta entrega es documental: no habilita ni ejecuta P2R sobre mercado,
validación 2023 o prueba final 2024–2025, y no modifica la tesis.
