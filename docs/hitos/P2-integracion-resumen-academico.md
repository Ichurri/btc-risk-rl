# P2 — resumen para Ingeniería del Proyecto

Se preparó la conexión del piloto P2 con el entrenamiento aceptado 2018–2022,
sin ejecutar la campaña. El diseño conserva nueve corridas de diez iteraciones,
tres semillas, crítico provisional de cuatro épocas y lote diagnóstico D=64.
Q/A/B sigue en una única implementación; D emplea la copia congelada de π_k,
un generador separado y los mismos retornos MC para los críticos anterior y
posterior. El permiso de campaña permanece inactivo y anclado a código y
registro; ni editar el JSON ni invocar el comando público habilita P2.

El preflight de solo lectura confirmó la identidad de los 7048 inicios H1,
el normalizador persistido y el límite temporal de entrenamiento; no generó
episodios ni pasos de optimizador. Las pruebas de integración usan barras
fabricadas, identificadas como fixtures; la equivalencia del aprendizaje con
D encendido/apagado se verifica sintéticamente. La primera comprobación de
trayectorias diagnósticas sobre el histórico y su duración real exigen una
autorización posterior de campaña. El cálculo temporal basado en P1 cubre
solo aprendizaje y no mide el costo de D.

Esta entrega demuestra preparación técnica y bloqueo de acceso, no desempeño
del agente. P2 aún debe ejecutarse para estudiar error del crítico en nuevas
realizaciones del mismo entrenamiento; aun entonces no probará generalización
temporal ni cumplimiento poblacional CVaR. No se usaron validación 2023,
prueba final 2024–2025 ni la tesis.
