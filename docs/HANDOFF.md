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
