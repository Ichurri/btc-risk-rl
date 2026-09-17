# ADR-004: política B de cuarentena y segmentos

Estado: APROBADO metodológicamente el 17 de septiembre de 2026;
implementación y aceptación de datos pendientes.

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
No modifica ADR-002, no acepta datos ni habilita el simulador.

## Aplicación pendiente

Conservar `missing_bar_policy = "fail"` hasta implementar una ruta explícita
de preparación segmentada. No rellenar huecos ni sustituir datos originales.
La máscara derivada debe identificar motivos y segmentos; los indicadores
deben reiniciarse y calentarse en cada segmento, sin transiciones ni episodios
que crucen sus límites o las fronteras de las particiones.

Antes de aceptar los datos: verificar características causales, definir
explícitamente las observaciones elegibles para ajustar el normalizador solo
en entrenamiento, persistirlo y reutilizarlo sin refit, comprobar el índice
de episodios y reportar cobertura. Los conteos del diagnóstico son evidencia
de la propuesta, no resultados de una preparación ya implementada.

La aprobación no autoriza entrenamientos ni acceso al conjunto final.
