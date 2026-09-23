# H5 — plan de implementación y verificación

Base 19fa2e6 local/remota; rama codex/h5-infrastructure; preservar .python-version.
Autorización: infraestructura, aprendizaje sintético pequeño e integración de
entrenamiento aceptado sin optimización. Pilotos y mercado entrenado bloqueados.

1. Pruebas RED de vista AcceptedMarket solo entrenamiento y adaptador del recolector.
   Verificar hashes del manifiesto H1 aceptado/anclado, productos y scaler.
   No cargar valores de validación: lectura de prefijos anteriores a 2023.
   Mu uniforme con reemplazo sobre los 7048 ids; no cambios de particiones o refit.
2. Instrumentación común: tiempo por fase, RSS, contadores, diagnósticos PPO/MC,
   gradientes, exposición/costos y riesgo. Presupuesto con estimaciones etiquetadas
   por perfil: Q0 e iteración completa indivisibles, reserva de guardado.
3. Refactor mínimo de un único calendario Q/A/B: límites after_q0 y after_dual,
   next_iteration/generation explícitos. Pausa planificada antes de comenzar unidad.
   Fallo invalida corrida; journal persistente impide reusar checkpoint anterior
   si una continuación falló o fue interrumpida en mitad de una unidad.
4. Checkpoint: estado torch weights_only, manifiesto JSON con hash, versiones,
   código/config/datos/scaler, RNG por coordenadas, optimizadores/eta/lambda,
   counters/auditorías/instrumentación. Publicación por carpeta nueva y commit
   final de manifiesto; sin sobrescritura. Rechazar estado corrupto/incompatible.
5. Pruebas sintéticas pausa/carga/continuación exacta contra ejecución continua:
   pesos, Adam, siguientes muestras y presupuesto. Pruebas de fallos/rechazos.
6. Comando piloto separado siempre bloqueado hasta protocolo autorizado registrado.
   Cargar un JSON que diga autorizado no levanta el bloqueo. Sin defaults de H4.
7. Verificador acotado de mercado: actor congelado, 3 episodios uniformes (semilla
   20260923), sin optimizador ni selección. Evidencias pequeñas; datos sin cambios.
8. Revisión, Ruff, pytest; informe H5, resumen, P0 actualizado sin ejecución,
   AGENTS/README/HANDOFF. Commits y push sin force.

Se conserva algoritmo, política logística-normal y contabilidad. El checkpoint
solo retoma en fronteras completas; no guarda fragmentos ni replay para aprender.
Unidades temporales estimadas no son garantía de tiempo real; sobrepaso invalida
y registra la corrida. Estimaciones sintéticas no habilitan presupuesto de mercado.
