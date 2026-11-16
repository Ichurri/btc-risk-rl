# H5 — integración aceptada, checkpoint e instrumentación

Estado: **infraestructura verificada; pilotos y entrenamiento de mercado bloqueados**.
Fecha: 2026-09-23. Base H4 `19fa2e63d973a1ac6951a9d32cd3432113a4a5a3`;
rama `codex/h5-infrastructure`; implementación `3cbd34271cef6931359706823ec6bcb52f839366`.
Se verificó la coincidencia local/origin antes de crear la rama. Se conserva fuera
del commit la eliminación local previa de `.python-version`. Sin force push,
retrocesos, cambios de tesis, CUDA ni drivers. No se accedió al conjunto final.

## Integración y alcance

`TrainingMarket` conecta Collector con `AcceptedMarket.training_only` y mantiene
los **7048 inicios**, elección uniforme con reemplazo e índices/normalizador H1.
La vista ancla el manifiesto aceptado mediante SHA, verifica todos sus productos,
compatibilidad H1/H3, momentos del scaler y transformaciones persistidas, sin
ajuste. Es una verificación de productos ya aceptados, no una nueva auditoría
del histórico bruto. H1, contabilidad/costos/recompensa H3 y ADR no se modificaron.

Los CSV compartidos H1 se leen en bytes completos para verificar sus hashes
(incluyen productos de desarrollo 2023). Solo se interpretan valores del prefijo
anterior a 2023, con contexto inicial de calentamiento. En la primera línea de
frontera solo se examina el timestamp; no se cargan observaciones de validación
ni se exponen rutas de esa partición. No confundir hashing de integridad con
recorrido de evaluación. El conjunto final no forma parte de estos productos.

El algoritmo Q/A/B sigue único en SyntheticExperiment, cuyo constructor rechaza
fuentes de mercado antes de crear optimizadores. Collector acepta los perfiles
sintético y de entrenamiento aceptado; H5 usa este último exclusivamente con una
política congelada. El nombre SyntheticExperiment expresa el alcance operativo
actual. No se añadió un segundo algoritmo para mercado.

## Checkpoint completo y fronteras

Esquema `h5_complete_boundary_v1`: actor, crítico, dos Adam (momentos/pasos), eta,
multiplicador, generación, próxima iteración, configuración, contadores,
auditorías, eventos, diagnósticos, presupuesto y RNG CPU torch. Los streams NumPy
son funciones de semilla, rol, iteración y fase; su estrategia versionada y
coordenada siguiente bastan en estas fronteras. No hay streams NumPy vivos que
atraviesen la frontera ni uso de random Python. Se conservan datos/config,
huellas de fuente/normalizador, código Python, lock, versiones y runtime/hilos.
El commit Git se registra; la compatibilidad exige hashes de código y runtime,
permitiendo commits posteriores puramente documentales.

| Frontera | Estado coherente | Próximo trabajo |
|---|---|---|
| `after_q0` | Q0 completo, eta0; generación 0, lambda0 | A0 |
| `after_dual` | A/actor/crítico/Q nuevo/B/dual completos; eta y lambda siguientes | A de próxima iteración o fin |
| `before_q0` / `in_unit` | sin frontera completa | no guardable/reanudable |

No se serializan fragmentos como episodios de riesgo. Si no cabe una iteración,
se pausa antes de A, conservando Q/eta anteriores. Guardado en carpeta nueva,
estado fsync, hash y manifiesto publicado al final; carga CPU `weights_only=True`.
Se rechazan ausencia/corrupción/incompatibilidad, contadores/Adam incoherentes,
fallos e interrupciones. El journal duradero acompaña al checkpoint: no basta
copiar state.pt a otra corrida. Ruta local del journal estricta: portabilidad a
otra máquina/ruta no implementada. No es una defensa contra edición deliberada
de código/journal; sí contra recuperación selectiva por las API del proyecto.

Cada append exige la revisión vigente bajo flock; un objeto viejo no puede
sobrescribir la historia. La carga consume el permiso de reanudación: un proceso
interrumpido tras cargar, o en mitad de unidad, no reutiliza ese checkpoint.
Una corrida fallida no se vuelve pausa válida. Guardado fallido deja estado
`checkpointing`, cerrado a recuperación automática. Se prioriza trazabilidad
sobre recuperación de fallos parciales.

## Instrumentación y presupuesto

Tiempo monotónico y CPU por Q/A/B, eta, actor, crítico y auditoría/dual; RSS máximo
del proceso, trayectorias, transiciones y pasos Adam. Diagnósticos: consistencia
old logprob, ratios/rango/fracción fuera de clip y clip activo, pérdidas, error
crítico MC, normas de gradiente sin clipping, exposición/costos/recompensas,
eta/empates/masa/rho_Q/rho_B/F_B y lambda. Son diagnósticos, no criterios de
selección. No cambian política, streams o parada por rendimiento.

TimeBudget exige estimaciones positivas etiquetadas por perfil y reserva; no
comienza Q0 o iteración completa si estimación+reserva no caben. Conserva consumo
en checkpoint, añade tiempo de guardado y prohíbe reemplazar el presupuesto
restaurado. El tiempo en pausa offline no se cuenta. No es preempción dura: un
sobrepaso de reserva detectado al finalizar unidad invalida la corrida. La reserva
y las estimaciones deben dimensionarse posteriormente; no existe garantía de
que una estimación cubra todo caso. Checkpoints/outputs nunca sobrescriben rutas.

## Verificaciones nuevas realmente ejecutadas

[Comandos y logs](../evidence/infrastructure-h5/COMMANDS.md).
**164 pruebas aprobadas (54.74 s) y Ruff pasa** sobre implementación `3cbd342`.
Incluye regresiones H1/H2/H3/H4 y 15 pruebas H5. Los fixtures de pytest son
sintéticos; no son pruebas adicionales del mercado real.

- Reanudación sintética exacta tras Q0 y tras una iteración: pesos, ambos Adam,
  eta/lambda, eventos, muestras posteriores y presupuesto de trayectorias/pasos.
- Rechazos: corrupto, incompatible, payload incompleto, frontera parcial, fallo
  posterior, token consumido, escritor obsoleto/concurrente y reset temporal.
- Vista H1 sintética: 7048 inicios, normalización preservada, guardas y mu.
- Verificador sintético independiente: dos corridas lógicas C5 de 2 iteraciones
  (una continua y otra pausada/reanudada), 12 trayectorias/2160 transiciones cada
  una; coincide estado/muestras/presupuesto. Valores exclusivamente sintéticos.
- Integración real acotada: semilla 20260923, actor aleatorio ancho 8 congelado,
  ids **5708, 1154, 2367**, **3 trayectorias / 540 transiciones**, **0 actualizaciones**.
  Actor y hashes de productos invariantes; entrenamiento anterior a 2023, sin
  selección por recompensas. Fragmentos de 60 ensamblados en episodios de 180.
- CLI de piloto: rechazo esperado, exit 2, sin cargar protocolo/datos/optimizar.

Resultados completos pequeños: [sintéticos](../evidence/infrastructure-h5/synthetic-results.json)
y [mercado congelado](../evidence/infrastructure-h5/market-results.json).
Los archivos de checkpoint/journal quedan en artifacts ignorado por Git; su hash
se conserva en evidencia. Los logs RED documentan fallos antes de correcciones,
no fallos vigentes. La revisión independiente detectó el rollback obsoleto;
[revisión y corrección](../evidence/infrastructure-h5/REVIEW.md).

La carga/hashing de mercado midió 0.226 s y la recolección 0.260 s en esta
comprobación; RSS alto del proceso 288628736 bytes. Hubo otras verificaciones
en paralelo: **no son benchmark ni estimación validada de entrenamiento de mercado**.
Los tiempos sintéticos tampoco se extrapolan. No se midió una iteración de
aprendizaje sobre mercado ni se evaluó rendimiento de un agente entrenado.

## Pendientes / siguiente tarea

Revisar [P0 instrumentado](../proposals/H5-P0-instrumentado.md), fijar cota común d,
configuración, semillas, criterios y calibración temporal, y autorizar un protocolo
separado antes de habilitar pilotos. H5 no convierte SyntheticSettings o candidatos
H4 en hiperparámetros aprobados. Presupuesto diario propuesto 3h con margen;
repartir corridas entre días requiere protocolo explícito, no reset de contadores.
Checkpoint de aprendizaje de mercado aún no verificado porque ese aprendizaje
no está autorizado. No se modificaron tesis ni inferencia confirmatoria.
