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
