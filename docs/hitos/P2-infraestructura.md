# P2 — infraestructura diagnóstica, exclusivamente sintética

Base `7357aa1`; código `41fcef3`; rama `codex/p2-infrastructure`. Diseño aceptado por el usuario,
ejecución de mercado **no autorizada**. Se conservan P0/P1, la propuesta original,
ADR-002, datos/normalizador, d y contrato H3. La eliminación previa de
`.python-version` permanece fuera de esta entrega.

## Implementación

El único calendario Q/A/B sigue en `agents/trainer.py`. Una extensión opcional
observa sus rutas y, después de dual, genera D con la copia congelada de pi_k.
No hay otro algoritmo PPO. El crítico anterior y posterior se evalúan sin autograd
sobre los mismos estados y retornos MC completos de D; también se registran A
pre/post, sesgo, segundo momento objetivo, razones, sumas y tercios del horizonte.
El hash de estado antes/después de D incluye redes, Adam, gradientes existentes,
eta/lambda, registros Q/A/B y RNG Python/NumPy/Torch. D usa otro Collector con
coordenadas [semilla,7002,k,0/1]; sus contadores no se suman como aprendizaje.

Archivos numéricos por realización, hashes de política/críticos/targets, identidad
de ruta y realización, y fragmentos fsync permiten auditar D. Un fallo conserva
fragmentos completados y el parcial disponible, invalida la unidad y no permite
reanudar desde dual. Un SIGKILL puede perder el fragmento todavía en memoria:
se conservan los fragmentos durables y el heartbeat como cota inferior explícita;
no se inventa una trayectoria completa ni se sustituye el lote.

La coincidencia temporal se calcula sobre los timestamps realmente observados,
no intervalos rellenados. Los segmentos H1 son disjuntos en UTC; una transición
observada identifica un único tiempo dentro de su segmento. Se registran inicios
exactos contra A y todo Q/A/B disponible, duplicados D, ocurrencias compartidas y
timestamps únicos, con sus denominadores. El resumen al cierre usa toda la corrida.
Los tests algebraicos incluyen solapamiento parcial sin coincidencia de inicio.

Las ventanas temprana/tardía agrupan SSE, suma G² y suma del error, no razones.
La regla exige simultáneamente los umbrales en la misma semilla y al menos 2/3
semillas de **cada** condición, únicamente al disponer de nueve corridas completas.
Z<=1e-12 requiere revisión. No hay parada ni selección por resultados.
Las tasas full-A/D pre/post, minibatches, auditorías B y activación de riesgo
mantienen denominadores separados. Las alertas/gradientes/shortfalls existentes
P0/P1 se conservan y no se confunde violación en B con shortfall en A.

## Persistencia y presupuesto

Checkpoints `p2_complete_boundary_v1` únicamente en after_q0 o after_dual_and_D:
redes/Adam, eta/lambda, generación/siguiente iteración, RNG por coordenadas y estado
Torch, hashes código/datos/configuración sintética, contadores Q/A/B y D, archivos
D referenciados con hash, métricas y huellas de rutas. La validación comprueba
identidades, ensamblaje H180, targets y archivos antes de consumir el token de
reanudación. Journal impide retroceder a un checkpoint después de fallo o carga.
La fuente sintética se distingue de cualquier fuente histórica.

El ledger de campaña referencia cada checkpoint y acumula recursos por corrida y
campaña; su cadena SHA detecta alteraciones inconsistentes y líneas parciales.
El truncamiento de un sufijo de líneas completas no se detecta por la cadena sola;
el journal/checkpoint añade coherencia de fronteras, pero esto sigue siendo una
limitación de auditoría si alguien manipula deliberadamente los archivos. Reutiliza
el bloqueo global y el débito de P0/P1, en una raíz canónica que no puede cambiarse
mediante --output. El reloj local es America/La_Paz, timestamps UTC; no se renuevan
límites al cambiar proceso/corrida. K10, máximo3 días activos/3 sesiones por corrida,
27 totales (sesión = invocación que inicia trabajo; varias unidades de la misma
corrida dentro de ella consumen una sesión), reserva1800s, límite global10800s,
preflight900s/trabajo8100s.
El watchdog existente conserva memoria10GiB y añade el subtope D900s dentro de la
unidad2700s. Los tiempos de carga, inferencia, escritura, hash y guardado consumen
el presupuesto. Las pausas se admiten antes de unidades completas; una muerte
intermedia invalida campaña y conserva evidencia.

El supervisor público sintético usa nueve fixtures pequeños K10, D2, A1/Q2/B2,
ocultas4, actor1 época/crítico4. No son parámetros de P2 mercado. La prueba del
supervisor ejecuta Q0 y dos unidades pequeñas en procesos separados, con pausas,
reanudación, ledger y consumo externo inventado explícitamente como fixture.
No se ejecutó la campaña sintética completa de nueve corridas desde CLI.

## Verificación y límites

La última ejecución sobre el commit de código: **221 pruebas pasadas en 94.31 s**,
Ruff sin errores, 282 huellas de P0/P1 verificadas; ver [evidencias](../evidence/p2-infrastructure/COMMANDS.md).
Incluyen equivalencia exacta D on/off de muestras, redes/Adam, eta/lambda,
gradientes/RNG; alineación de política y targets independientes; reanudación
sin regenerar D; diez iteraciones y D64 sintéticos; sumas/solapamientos/umbrales;
rechazo de D incompleto/corrupto; fallo deliberado en la segunda realización;
presupuesto compartido/medianoche/días y watchdog; bloqueo previo de mercado.
La suite completa conserva además las pruebas sintéticas de contabilidad H3,
colección, H5, P0/P1 y supervisión de memoria/muerte de proceso. No son nuevas
verificaciones sobre entrenamiento aceptado ni repeticiones de campañas previas.

La revisión independiente identificó y se corrigieron el posible reinicio del
presupuesto cambiando directorio, la pérdida de fragmentos ante fallo de D,
el conteo de sesiones separado de fechas y la reapertura de estados completados.
Se añadieron regresiones específicas. No se modificó el diseño metodológico.

Pendiente: autorización separada de ejecución histórica, registro de permiso y
conexión del perfil de mercado al supervisor, verificación de entrada/huellas y
calibración temporal real según los topes ya aceptados. La infraestructura no
registra P2 como permiso P0/P1; ni cambiar un JSON lo activa. La integración histórica
D no se probó en esta entrega. Cuatro épocas siguen provisionales, no confirmatorias.
No hay inferencia sobre mejora del crítico histórico, rentabilidad, convergencia,
generalización temporal o cumplimiento CVaR. No se accedió a validación/final.

## Futuro comando — NO EJECUTADO como campaña

```bash
uv run --frozen python scripts/run_p2.py --profile market --protocol docs/protocols/P2-infrastructure-v1.json
```

Actualmente rechaza antes de leer configuración/datos o generar trayectorias.
Se detiene aquí: la infraestructura no constituye autorización de mercado.
