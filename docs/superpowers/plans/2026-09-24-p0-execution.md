# Ejecución P0 aprobada — plan

Diseño autorizado sobre 7a379b7 con presupuesto diario GLOBAL y d=-ln(.90).
Mantener repo local, cambios previos y algoritmo Q/A/B.

1. Versionar aprobación/configuración separadas, actualizar AGENTS/HANDOFF.
2. Pruebas primero: admisión temporal sin estimación, presupuesto compartido y
   persistente, cambio de fecha La Paz, tope sesiones, fallo irrecuperable,
   watchdog real de tiempo/memoria sobre procesos sintéticos.
3. Registro de campaña con lock exclusivo, snapshots append-only, reloj UTC y
   monotónico, deadlines persistentes. Un proceso hijo por unidad completa,
   journal running antes de iniciar; matar/invalidate por tiempo/memoria/fallo.
4. Reutilizar SyntheticExperiment mediante perfil P0 estrictamente validado,
   checkpoints completos tras Q0/dual y autorización con hash de protocolo.
   Mantener SyntheticSettings/guardas de fuentes ajenas y no permitir editar
   límites por CLI. Reanudar solo checkpoint y journal más recientes.
5. Pruebas sintéticas de reanudación y resultados iguales, diagnósticos sin
   selección, persistencia de recursos y campañas. Ruff y pytest antes de mercado.
6. Revisión independiente del supervisor/guardas. Commit de código verificado.
7. Ejecutar una campaña canónica P0 bajo supervisor; medir, informar progreso,
   parar ante fallo o presupuesto. No relanzar una corrida fallida.
8. Versionar evidencia pequeña, informe/resumen/HANDOFF y publicar commits.
