# P3 — infraestructura del ejecutor histórico, verificada sin campaña

**Estado:** infraestructura implementada y probada con datos sintéticos. La
campaña histórica P3 no está autorizada: `MARKET_EXECUTION_ENABLED=False`,
`REGISTRATION_SHA256=None` y no existe registro de aprobación P3. No se
generaron trayectorias históricas ni se actualizaron pesos con mercado.

## Contrato integrado

El perfil P3 es independiente de P2R y conserva las 18 identidades ordenadas
`(semilla, condición, β)` de [P3 v1.1](../proposals/P3-protocolo-v1-1.md):
710031/710047/710081, C0/C5/C10 y β=0/1, diez iteraciones por corrida.
Cada corrida tiene directorio, política, RNG, objetivos D, reportes y
checkpoints propios. El trabajador reutiliza Q0 y Q/A/B+D del ejecutor
común y la pérdida del crítico ya verificada: β=0 es MSE; β=1 suma
`mean(V²)` en los mismos minibatches A. D64 evalúa la política congelada
de su propio brazo. Se mantienen H180, γ=1, d=−ln(0,90), datos de
entrenamiento aceptados, normalizador, costos y recompensa. Los cuatro
epochs del crítico son provisionales, no parámetros confirmatorios.

La configuración operativa queda en
[P3-executor-infrastructure-v1.json](../protocols/P3-executor-infrastructure-v1.json).
Es una especificación de infraestructura, **no** un permiso de campaña.
Las rutas de entrada verifican el diseño adoptado, el derivado H1 exclusivo
de entrenamiento y los ledgers anteriores. El acceso histórico requiere
dos condiciones independientes que aquí permanecen inactivas: bandera en
código y registro aprobado con huella fijada. Un JSON editado o el comando
público por sí solos fallan antes de cargar datos o crear una raíz.

El supervisor guarda Q0 en `after_q0` y cada iteración completa en
`after_dual_and_D`. Antes de aceptar una unidad contrasta perfil y
procedencia, brazo, reporte, huellas del checkpoint, frontera, contadores
de trayectorias y D, pasos completos de **ambos** optimizadores y el
marcador `market_training_executed`. Q0 exige `false`; una iteración
histórica íntegra exige `true`. Una unidad parcial o un reporte incoherente
dejan el ledger `failed`; un checkpoint anterior conservado no autoriza
reanudar esa campaña. El presupuesto sigue siendo compartido: 3 h por día
en America/La_Paz, máximo tres días activos, reserva de cierre, topes por
unidad, admisión por condición/tipo usando el máximo medido en ambos
brazos, y hasta 3 sesiones por corrida/54 de campaña. Las pausas ocurren
solo entre unidades completas.

La evaluación P3 acumula SSE, ΣG², error y n sobre A/D, pre/post,
ventanas temprana/tardía y tercios H180. La razón exacta `M/Z`, el sesgo
`ē/√Z` y el umbral `M≤0,95Z` deciden; `M/(Z+10⁻¹²)` es únicamente
descriptiva. `Z>10⁻¹²` se exige por separado en D temprana, D tardía,
A tardía y tercio 3 de D tardía **para cada brazo**. Las diferencias
pareadas usan los objetivos y denominadores de cada brazo. Se evalúan
los 18 cierres y diez D completos por corrida; el bloque independiente
es la semilla, y el avance exige la regla conjunta de P3 v1.1 en las
tres condiciones de al menos dos bloques. Sin integridad completa,
`not_evaluable`; con integridad y umbrales no alcanzados, `review`.

## Evidencia ejecutada y límites

Las pruebas sintéticas cubren las cuatro unidades de un par β=0/1 con
Q0 y una Q/A/B+D, sus reportes/checkpoints separados, equivalencia β=0
con el camino previo, pausa/reanudación reproducible y fallo irreversible
por señal o manipulación del marcador. Sobres sintéticos de perfil
histórico comprueban contadores, optimizadores, fuente y marcador sin
construir trayectorias de mercado. La auditoría de preflight fue **solo
lectura**: 7.048 inicios aceptados, cero trayectorias y cero pasos de
optimizador. [El registro de aperturas](../evidence/p3-historical-infrastructure/preflight-opens.json)
enumera cada ruta de repositorio y recuento; abrió los productos del
derivado exclusivo de entrenamiento y solo `manifest.json` del H1
compartido, sin intentar abrir sus CSV. Tampoco abrió validación ni prueba
final. Las huellas de manifiesto, normalizador, código, protocolo,
configuración y ledgers se contrastaron en ese preflight.

Esta verificación no ejecutó una matriz sintética de 198 unidades ni una
unidad histórica bajo `systemd --user`; la matriz completa se ejercitó
con sobres sintéticos para probar agregación, integridad y regla de
decisión. No prueba tiempos ni consumo de D/β en mercado, continuidad
real del servicio P3, interrupción física, ni desempeño del crítico.
Los criterios son exploratorios, elegidos tras P2R; un eventual avance
sería discusión de desarrollo, no generalización temporal, rentabilidad
o cumplimiento CVaR poblacional. P2R mantiene sus 99 reportes y su
adjudicación `review` solo descriptiva; P2 permanece fallido.

La suite completa de este estado aprobó **340 pruebas** y omitió una
prueba antigua por la ventana real de medianoche de La Paz. Ruff pasó.

El preflight medido el 07/10/2026 La Paz señaló **recursos bloqueados**:
~3,29 GB de memoria disponible frente al umbral operativo 4 GiB. El
disco tenía ~178,84 GB libres y la alimentación estaba conectada; el
saldo compartido observado era ~3.906,90 s después de P2R. Son medidas
del instante, no una reserva para un futuro lanzamiento. No se redujo
ningún umbral. Ver [comandos y resultados](../evidence/p3-historical-infrastructure/COMMANDS.md).

## Antes de solicitar permiso histórico por separado

Revisar código, contrato de métricas y evidencias; confirmar memoria,
alimentación, disco, `Linger`, gestor de usuario y presupuesto vigente
en un preflight nuevo bajo el entorno de ejecución previsto. Registrar
la autorización específica, raíz nueva y huellas en un commit separado;
solo entonces habilitar la bandera P3 y verificar el rechazo/aceptación
del permiso, la vigilancia de archivos y la primera unidad con tiempo D
real, sin ajustar el protocolo a los resultados. Una campaña requerirá
supervisión `systemd --user`, admisión unidad por unidad y los límites
adoptados. Este hito se detiene antes de esos pasos.
