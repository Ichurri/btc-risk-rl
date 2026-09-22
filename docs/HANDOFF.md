# Traspaso entre este chat y Codex local/remoto

Leer AGENTS.md y los ADR. Consultar git status y git log antes de editar.
El paquete inicial se entrega como repositorio Git local con historial. No existe
remoto configurado. El usuario elegirá proveedor/cuenta y añadirá el remoto.

Git es la fuente de verdad del código; la tesis se actualiza en el otro chat.
Un chat no envía automáticamente su conversación a otro proceso Codex.
Para continuar, compartir URL/rama/commit o un paquete actualizado y este archivo.

Al terminar tarea: commit, comandos ejecutados, salida relevante, artefactos,
estado del conjunto final y siguiente tarea. No atribuir a Debian local las
pruebas ejecutadas en el entorno de construcción del paquete.

## Estado de entrega
- H0 código: b215268, repositorio/configuración/reglas.
- H1 código: f92574e, datos/características/controles/reconsulta.
- 28 pruebas pasan; Ruff pasa. Evidencia en docs/evidence/ y docs/hitos/.
- Datos reales rechazados: 16 huecos, 20 cierres abreviados; persisten en reconsulta.
- No hay simulador, agente o entrenamiento. Test final sin acceso.

## Siguiente tarea para Codex local o remoto
Leer ADR-003 y los informes de calidad/reconsulta. Investigar el tratamiento
de interrupciones de Binance sin rellenar precios y sin unir segmentos.
Diseñar una regla documentada para segmentos/calentamiento y sus criterios de
aceptación; conservar el dataset original y las fechas de partición.
No debilitar la guarda de prueba final. No implementar el simulador hasta
resolver esta aceptación. No implementar agentes hasta cerrar ADR-002.

## Mensaje mínimo para continuar en otro entorno
«Trabaja sobre el commit actual de btc-risk-rl. Lee AGENTS.md, docs/HANDOFF.md,
docs/hitos/H1-datos.md y ADR-003. Continúa la tarea de calidad de datos indicada.
No entrenes ni accedas al conjunto final. Registra decisiones, pruebas y commit».

Sin remoto configurado: este chat no puede acceder automáticamente a cambios
en tu disco. Para revisar cambios, proporcionar repo/rama/commit accesibles o
un archivo actualizado. Los resultados locales deben indicar máquina y versiones.

## Actualización: diagnóstico, iteración 02

El estado anterior de 28 pruebas queda como evidencia histórica. Ahora hay 32
pruebas remotas aprobadas y Ruff pasa. Revisar docs/DIAGNOSTICO-HISTORICO.md,
docs/DEBIAN.md y docs/hitos/H1-diagnostico.md.

36 anomalías en 20 bloques; 18 archivos mensuales corroboran los huecos, con dos
diferencias exclusivas de close_time. No afirmar causa verificada para todos.
Política B propuesta: 36 intervalos más 20 reaperturas en cuarentena, segmentos
contiguos. 7048 inicios posibles de 180 pasos; NO se aplicó la política.
Próximo paso: registrar la decisión metodológica del usuario y después implementar
preparación segmentada, verificar características y aceptar datos antes del simulador.
Verificación Debian local pendiente de resultados del usuario. Sin entrenamientos.

## Verificación local: 17 de septiembre de 2026

Ejecutada en el repositorio abierto del equipo local, sobre el commit
`d097f5c948f4f2250e04682c5cc47b9bf5932fb2`. Debian 13.7 (trixie),
kernel `6.12.107+deb13-amd64`, Python 3.12.13 y uv 0.11.18.
La eliminación previa de `.python-version` se conservó; el árbol no estaba limpio.

- `uv sync --frozen`: completado, 21 paquetes instalados desde el lock.
  El primer intento falló por caché de solo lectura y el segundo por DNS en
  el entorno restringido. El reintento con acceso de red terminó con código 0.
  Se utilizó `UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache` para sync y verificación.
- `uv run --frozen python scripts/verify_installation.py --context local`:
  código 0; config-check válido, Ruff sin errores y **32 pruebas aprobadas
  en 1.24 s**. Son resultados locales nuevos, separados de la evidencia remota.
- Evidencia: [verification.json](evidence/local-20260917T083436Z/verification.json),
  [versiones](evidence/local-20260917T083436Z/versions.json), logs `0.log`,
  `1.log`, `2.log` y logs de instalación en esa misma carpeta. Originales en
  `artifacts/verification-local-20260917T083436Z/` y
  `artifacts/local-installation-20260917/` (excluidos de Git).

No se modificaron código, configuración, lock ni decisiones metodológicas.
No se instalaron PyTorch/CUDA ni se modificaron drivers. No se ejecutaron
entrenamientos ni se accedió al conjunto final. Las pruebas sintéticas no
constituyen aceptación de datos de mercado.

Al terminar esa verificación, B seguía propuesta y pendiente de aprobación.

## Decisión local: aprobación de B, 17 de septiembre de 2026

El usuario confirmó explícitamente: «Si, apruebo la politica B.» Se registró
la aprobación metodológica en [ADR-004](decisions/ADR-004-segment-proposal.md).
Este estado reemplaza las referencias anteriores a B como propuesta pendiente;
la política todavía no está implementada ni aplicada y los datos no están aceptados.

Siguiente paso técnico: implementar preparación segmentada conforme a ADR-004,
con máscara de motivos, calentamiento causal por segmento, normalizador ajustado
solo en entrenamiento, índice de episodios y verificación de cobertura y fronteras.
Mantener el bloqueo estricto de la ruta actual hasta disponer de la ruta explícita.
El alcance de esta actualización es documental; no se ejecutaron nuevas pruebas
de código. Se conserva la evidencia de verificación local anterior, sobre d097f5c.
ADR-002 sigue abierto. Sin entrenamientos ni acceso al conjunto final.

## Cierre documental local

Antes del commit se repitió el verificador local: configuración válida, Ruff
sin errores y 32 pruebas aprobadas en 1.17 s, con código de salida 0.
Evidencia nueva en [verification.json](evidence/local-20260917T084415Z/verification.json)
y sus tres logs. El registro identifica el commit base d097f5c y los cambios
documentales presentes durante la ejecución. El commit de cierre incorpora
la evidencia local y la aprobación de B; excluye la eliminación previa de
`.python-version`. El siguiente trabajo sigue siendo la preparación segmentada.

## H1 cerrado: preparación segmentada B, 17 de septiembre de 2026

La ruta explícita `prepare-segmented-development` aplica ADR-004 y
`verify-segmented-development` audita los productos sin modificarlos ni reajustar
el normalizador. `missing_bar_policy = "fail"` y la ruta estricta se conservan.
Los datos de desarrollo están **aceptados técnicamente bajo B**, con las
limitaciones del [informe del hito](hitos/H1-preparacion-segmentada.md).

- Máscara exacta: 16 ausencias, 20 cierres abreviados y 20 reaperturas; sin imputación.
- Entrenamiento: 10900 barras retenidas, 21 segmentos, 10054 transiciones,
  7048 episodios posibles de 180 transiciones en 15 segmentos aptos.
- Ajuste: 10073 observaciones finitas de entrenamiento, una vez por timestamp;
  incluye segmentos cortos y estados terminales. Validación solo transforma.
- Validación: 2190 transiciones continuas, sin episodios de evaluación de 180 pasos.
- Coincidencia exacta con el escenario B del diagnóstico, incluidos límites
  por segmento. Reproducción en otro destino: mismos hashes de derivados.
- Verificación local final: configuración válida, Ruff pasa y 59 pruebas
  aprobadas en 13.85 s. Originales intactos, hashes antes/después verificados.

Evidencias, versiones y comandos: [docs/evidence/segmented-h1](evidence/segmented-h1/COMMANDS.md).
Producto fuera de Git: `data/processed/segmented-B-h1/`. El ZIP académico incluye
los archivos versionados, el producto, las páginas originales de desarrollo y
un Git bundle; el descriptor de entrega identifica el commit y los hashes.
La evidencia de ejecución referencia 108847e como base previa al commit del hito
y registra huellas de los archivos ejecutados. Se conserva fuera del commit la
eliminación local de `.python-version`.

Siguiente hito: simulador causal float64 con contabilidad y costos exactos sobre
los índices aceptados. **No se inició el simulador en esta entrega.** ADR-002
sigue pendiente; no hay PPO/CVaR-PPO ni entrenamientos. Conjunto final sin acceso.

## H2 cerrado: simulador causal, 21 de septiembre de 2026

Implementados `env/accounting.py`, `env/market.py` y `env/trading.py`:
observaciones float64 de 10 características y 2 variables de cartera, objetivo
BTC posterior a costos marcado a apertura de referencia, ejecución en apertura
siguiente con comisión sobre precio ejecutado, deslizamiento adverso y recompensa
logarítmica neta que incluye el gap. Sin clipping de acciones o saldos.

El cargador exige aceptación y auditoría H1. Entrenamiento solo por índice
aceptado de 180 transiciones; validación mantiene 2190 pasos y una sola cartera.
Los cortes devuelven observación final y truncación, sin venta obligatoria.
Se distingue fin de ventana, segmento y partición. ADR-002 permanece abierto:
no se decide descuento, bootstrap ni estimador de riesgo.

Verificación local real: configuración válida, Ruff pasa y **100 pruebas pasan
en 26.68 s**. Casos sintéticos con oráculo Decimal independiente de 60 dígitos,
incluidos 120 portafolios aleatorios deterministas. Comprobación funcional real:
7048 índices revisados, 30 episodios extremos de los 15 segmentos aptos y una
validación continua; 31 recorridos y 7590 transiciones. Acciones prefijadas sin
aprendizaje ni selección por resultados. Error máximo de efectivo 3.64e-12 USDT;
error telescópico máximo 1.67e-15. Fuentes y normalizador intactos.

Informe: [H2-simulador.md](hitos/H2-simulador.md). Evidencias y comandos:
[simulator-h2/COMMANDS.md](evidence/simulator-h2/COMMANDS.md). Libro completo:
`artifacts/simulator-h2/real/ledger.csv`, incluido en el ZIP académico junto con
código, evidencia, datos de desarrollo y Git bundle. La evidencia registra
57e0885 como commit base y hashes del código ejecutado; DELIVERY.json del ZIP
identifica el commit de cierre. `.python-version` sigue eliminado localmente,
fuera de este commit, por el cambio previo del usuario.

Siguiente paso: resolver metodológicamente ADR-002 antes de agentes o entrenamientos.
No se instaló PyTorch/CUDA, no se modificaron drivers y no se accedió al test final.

## Propuesta ADR-002 para revisión — 22 de septiembre de 2026 (UTC)

Sobre H2 `cc913b629694641543e2b54375dbda5d55130544` se preparó
[la propuesta metodológica y técnica](proposals/ADR-002-propuesta.md), todavía
**NO ADOPTADA**. Recomienda H=180 finito, gamma=1 y CVaR sobre la misma suma neta
logarítmica; distingue completitud de trayectoria y procedencia del corte,
requiere tiempo restante y propone validación continua con horizonte móvil.
Explicita que esa evaluación mide transferencia operacional, no garantiza la
restricción de entrenamiento ni optimiza el retorno anual. Incluye alternativas,
fuentes primarias, gradiente de riesgo, parámetros pendientes y migración futura.

Evidencia nueva: [comandos y resultados](evidence/adr002-proposal/COMMANDS.md).
Seis grupos sintéticos independientes aprobados; Ruff pasa; **100 pruebas pasan
en 22.47 s**. Los hashes verifican código/configuración/pruebas/scripts/lock
idénticos a H2. No se hizo nueva auditoría de mercado ni se atribuyen sus
resultados anteriores a esta ejecución. `.python-version` sigue eliminado por
el cambio previo, fuera de esta entrega.

Siguiente paso: revisión académica conjunta del objetivo finito, alcance de la
restricción y regla de despliegue continuo. ADR-002 permanece abierto. No cambiar
el contrato del simulador ni implementar agentes hasta revisar la propuesta;
no entrenar ni acceder al conjunto final. No hubo acceso a datos de mercado en
esta tarea ni modificaciones a la tesis.

## ADR-002 v2 — revisión académica incorporada, 22-09-2026 UTC

[Propuesta v2](proposals/ADR-002-propuesta-v2.md) y
[resumen de respuesta](proposals/ADR-002-v2-resumen-academico.md), sobre v1
`082db3e` y simulador H2 `cc913b6`. Estado **PROPUESTA PARA REVISIÓN, NO ADOPTADA**.
V1 y sus evidencias se conservan. Se reconoce explícitamente que h=1 con cartera
heredada está fuera del soporte conjunto de entrenamiento; se mantiene evaluación
continua móvil como transferencia operacional, sin garantía CVaR a 30 días.
El contraste Sortino mide los procedimientos completos, con posible interacción
entre mecanismo de riesgo y cambio de soporte.

Se define procedimiento único: Q estima eta mediante cuantil empírico, A nuevo
actualiza actor y luego crítico separado; política nueva genera Q nuevo y B
independiente; el dual usa F_B al eta de Q. Eta y lambda quedan fijos en las
épocas PPO. B es diagnóstico y señal dual, no prueba confirmatoria independiente.
La cota d es común y congelada; el presupuesto incluye auxiliares también en C0.
Pseudocódigo, reutilización, sesgos, empates y cortes están en la propuesta.

[Evidencia local v2](evidence/adr002-proposal-v2/COMMANDS.md): seis grupos v1
reproducidos y seis adicionales (tres algebraicos/tres de especificación), Ruff
pasa y **100 pruebas H2 pasan en 21.72 s**. No se modificó src/configs/tests/scripts,
lock ni pyproject; huellas iguales a H2. No se cargó ningún dato de mercado,
no hubo agentes ni entrenamientos y no se accedió al conjunto final. La
reproducción del chat académico es información del usuario, distinta de estos logs.
Se conserva la eliminación local previa de `.python-version` fuera del commit.

El ZIP académico contiene snapshot del commit documental, historial Git bundle,
propuestas/evidencias y descriptor de huellas; no datos de mercado. Próximo paso:
revisión de v2 antes de cualquier cambio al contrato H2. ADR-002 sigue abierto.
