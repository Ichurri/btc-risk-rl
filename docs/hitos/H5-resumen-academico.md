# H5 — resumen para revisión académica

Infraestructura implementada y verificada; **no se ejecutaron pilotos ni
actualizaciones de parámetros con mercado**. ADR-002 v2.1, calendario Q/A/B,
política logística-normal, recompensa y contabilidad permanecen sin cambios.

1. Adaptador AcceptedMarket de entrenamiento: 7048 inicios H1, mu uniforme con
   reemplazo, normalizador persistido sin refit. Comprobación real prefijada:
   tres episodios/540 transiciones, política congelada, cero pasos Adam, huellas
   invariantes. No se cargaron observaciones de validación. Se verificaron en
   bytes los hashes de archivos H1 compartidos de desarrollo; no se accedió al final.
2. Checkpoint completo en after_q0 o after_dual, con dos optimizadores, estado de
   riesgo, RNG/coordenadas, configuración, contadores, huellas y diagnósticos.
   Reanudación sintética idéntica a continua, incluidas muestras y recursos.
   Journal bajo bloqueo rechaza rollback de objetos viejos y recuperación de
   corridas fallidas; pausa planificada no equivale a fallo/interrupción.
3. Instrumentación por fase, memoria, estabilidad y presupuesto preventivo con
   reserva. No existe todavía estimación validada del costo de entrenar mercado.
   Los tiempos de carga/recolección congelada y de aprendizaje sintético no la
   sustituyen. Control temporal basado en estimaciones, no garantía de tiempo duro.
4. P0 actualizado, comando separado cerrado. Deben aprobarse especialmente
   **cota económica común d de C5/C10**, tamaños/tasas/arquitectura/semillas,
   precisión/criterios de parada y protocolo de recursos de hasta 3h diarias,
   incluyendo Q/B de todas las condiciones. Ningún valor sintético es definitivo.

Nueva verificación: **164 pruebas y Ruff aprobados**. Los tests sintéticos
comprueban implementación y reanudación, no validez de un agente ni cumplimiento
poblacional de CVaR. El contraste inferencial y Sortino anualizado adoptados
no cambian; un Sortino superior no demuestra la restricción de riesgo.

Rama `codex/h5-infrastructure`, implementación `3cbd342`; el commit documental
posterior conserva este informe y sus evidencias.
[Informe técnico](H5-infraestructura.md),
[comandos/resultados](../evidence/infrastructure-h5/COMMANDS.md),
[P0 pendiente de autorización](../proposals/H5-P0-instrumentado.md).
