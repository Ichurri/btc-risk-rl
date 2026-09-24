# Revisión independiente previa a mercado

Revisión de supervisor, ledger, permiso P0, worker y calendario; sin acceso a
mercado por el revisor. Hallazgos corregidos antes de ejecutar:

1. La guarda rechazaba risk_enabled=False del checkpoint C0. Regresión
   c0-resume-red.log; ahora False solo permitido en C0, no en C5/C10.
2. Invocar fuera de la ventana diaria invalidaba pausa/completed. Regresiones
   closing-red.log; salida temprana conserva estado y deadlines.
3. Guardado debe poder usar reserva. Marker atómico tras frontera íntegra,
   supervisor con deadlines de trabajo/cierre y ledger que estima exclusivamente
   work_seconds. closing-green.log conserva un fallo intermedio (se seguía
   incluyendo guardado al estimar); corregido antes de la suite final.

No quedaron otros defectos materiales en el alcance revisado. Suite final
posterior: 186 pruebas aprobadas, pytest-verified.log; Ruff-verified sin errores.
Incluye muerte real de supervisor y terminación del trabajador por parent-death
SIGKILL, timeout y RSS con procesos sintéticos.
