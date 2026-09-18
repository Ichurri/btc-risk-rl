# ADR-004: política B de cuarentena y segmentos

Estado: APROBADO metodológicamente el 17 de septiembre de 2026;
implementado y verificado para desarrollo; evidencia en
../hitos/H1-preparacion-segmentada.md.

## Decisión y procedencia

El usuario aprobó explícitamente en la sesión local: «Si, apruebo la politica B.»
La confirmación respondió a la consulta sobre poner en cuarentena los 36
intervalos anómalos y las 20 velas de reapertura, conservando originales y
separando segmentos. Esta aprobación queda registrada aquí; no se infiere
de conversaciones externas.

Referencia completa: ../DIAGNOSTICO-HISTORICO.md.
Se adopta B: 16 aperturas ausentes, 20 cierres abreviados y 20 velas de
reapertura en una máscara separada; indicadores y episodios sin cruzar segmentos.
Mantener los originales y las particiones. Validación 2023 continua.
No aplicar segmentación automáticamente a evaluación ni sumar curvas con reinicios.
Las causas de todos los bloques no están demostradas; la cuarentena se fundamenta
en idoneidad para el contrato temporal, no en declarar corruptos todos los datos.
La aprobación por sí sola no acepta datos ni modifica ADR-002. La aceptación
técnica posterior requiere los controles de preparación descritos abajo.

## Contrato de aplicación

Se conserva `missing_bar_policy = "fail"` en la ruta estricta. La ruta explícita
`prepare-segmented-development` aplica B sin rellenar huecos ni sustituir originales.
La máscara derivada debe identificar motivos y segmentos; los indicadores
deben reiniciarse y calentarse en cada segmento, sin transiciones ni episodios
que crucen interrupciones. Todos los objetivos puntuados de un episodio deben
pertenecer a entrenamiento; ninguno puede alcanzar validación. La observación
inicial y el calentamiento pueden usar contexto contiguo anterior a una frontera,
sin puntuar retornos de ese contexto, como especifica el diagnóstico. Validación
usa una sola trayectoria de objetivos 2023, nunca episodios de 180 pasos.

El normalizador se ajusta una sola vez por timestamp a todas las observaciones
de entrenamiento con las diez características finitas, incluidos los segmentos
cortos sin episodios y estados terminales. No se pondera por frecuencia de aparición
en episodios. Se excluyen calentamiento anterior a entrenamiento, cuarentena,
observaciones sin historia suficiente y validación. Media y desviación poblacional
persistidas; columnas constantes usan escala 1, sin clipping. Validación y auditoría
recargan los parámetros y no ejecutan ajuste.

La aceptación requiere comprobar las tablas persistidas, causalidad por segmento,
índice exhaustivo de episodios, hashes de fuentes/productos y coincidencia exacta
con inventario, reaperturas y cobertura del diagnóstico. Anomalías adicionales,
fuentes modificadas o validación incompleta bloquean la aceptación. La aceptación
se limita al desarrollo bajo B y conserva las limitaciones sobre negociabilidad,
sesgo de selección y riesgo durante interrupciones.

La aprobación no autoriza entrenamientos ni acceso al conjunto final.
