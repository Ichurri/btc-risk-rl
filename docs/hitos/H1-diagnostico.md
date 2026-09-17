# H1 — diagnóstico histórico: resumen para el chat académico

Versión de código y diagnóstico: fa11d21 (rama diagnosis/historical-anomalies).
El commit que contiene este resumen añade únicamente documentación y evidencia.

Decisiones adoptadas: mantener originales, fechas, guarda del test y bloqueo del simulador; distinguir irregularidad del contrato temporal de corrupción. No se adoptó aún la política B (ADR-004 propuesto).

Implementado: inventario de 36 intervalos UTC, corroboración mediante archivos mensuales y registros 1h de Binance, cálculo diagnóstico de segmentos, verificador local/remoto y guía Debian. No se modificó el pipeline de preparación.

Resultados reales: 13332 aperturas nominales = 186 calentamiento + 10956 entrenamiento + 2190 validación; 13316 recibidas. Los 16 huecos están en entrenamiento; los 20 cierres abreviados también. Sin solapamiento de categorías; 20 bloques. 18 archivos mensuales corroboran todos los huecos, 18 cierres coinciden y dos difieren solo en metadatos. 20 agregaciones horarias reproducen OHLCV. Evidencia causal oficial disponible para algunos eventos; no se afirma causa ni irrecuperabilidad universal.

Propuesta B: excluir en máscara derivada 36 intervalos y 20 reaperturas; 21 segmentos, 15 aptos para 180 transiciones, 7048 inicios posibles, 10054 transiciones tras calentamiento y 9733 objetivos alcanzables por episodios completos. Validación 2023 conserva 2190 transiciones con contexto previo. No aplicar reinicios ni exclusiones silenciosos a evaluación.

Pruebas ejecutadas remotamente sobre fa11d21 y árbol limpio: config-check correcto, Ruff sin errores, 32 pruebas aprobadas (1.09 s). Cuatro pruebas nuevas: mínimo 223 barras, calentamiento tras hueco, contexto previo a frontera y segmento corto. Registro completo en docs/evidence/diagnosis/verification-remote/. Reproducción exacta del inventario/impacto y hashes de 38 archivos corroborantes en offline-verification.json.

Verificación Debian del usuario: PENDIENTE. Las comprobaciones remotas no acreditan instalación local. Seguir docs/DEBIAN.md y aportar verification.json y logs.

Cambios metodológicos a trasladar si se aprueba B: población de entrenamiento restringida a ventanas contiguas elegibles, calentamiento por segmento, cobertura explícita y posible sesgo por exclusión de interrupciones. Distinguir cierre abreviado de vela aún abierta. No presentar este diagnóstico como resultado de trading, aceptación de datos ni implementación del simulador.

Próximo paso: decisión metodológica sobre ADR-004; luego preparación segmentada y verificación causal antes de implementar simulador. ADR-002 mantiene bloqueado CVaR-PPO. Sin entrenamientos ni acceso al test final.
