# Resumen académico — infraestructura histórica P2R v2

Se integró el perfil de **entrenamiento aceptado 2018–2022** al supervisor
P2R, manteniendo la misma implementación Q/A/B+D y las fronteras
`after_q0` y `after_dual_and_D` que se verifican con datos sintéticos. La
matriz metodológica sigue siendo nueve corridas nuevas, semillas
610031/610047/610081, C0/C5/C10 en orden rotado, K=10, crítico de cuatro
épocas provisional, D64, `d=−ln(0.90)` y presupuesto de tres horas globales
por día durante hasta tres días activos.

El ejecutor incorpora control de identidad de protocolo, código, datos H1 y
normalizador; comprueba que el histórico ofrecido pertenece únicamente a
entrenamiento. Exige un supervisor `systemd --user`, recursos mínimos,
admisión presupuestaria antes de cada unidad, registro durable, y un
checkpoint publicado atómicamente solo al cerrar una frontera completa.
Si una unidad falla, el ledger queda `failed`: el checkpoint anterior se
conserva como evidencia y no habilita reanudación de esa campaña.

El preflight de solo lectura encontró 7048 inicios aceptados, sin reajuste
del normalizador ni observaciones de validación cargadas. La verificación
SHA-256 heredada de H1 sí lee archivos completos que incluyen filas 2023;
solo se materializa el prefijo de entrenamiento. Esta distinción debe
revisarse si se exige cero lectura física de filas de validación. **No se inició
ninguna unidad histórica, no hubo trayectorias de mercado ni actualizaciones
de parámetros con ese histórico.** Los tests sintéticos verifican Q0,
Q/A/B+D, pausas, reanudación desde fronteras completas, rechazos y fallos
permanentes. La prueba de señal en la sonda 06 ocurrió antes de los cálculos
Q/A/B+D; no se ha probado una señal dentro de un paso del optimizador ni un
apagado físico.

Esta entrega acredita preparación de infraestructura, no una campaña P2R,
evolución del crítico, desempeño financiero, generalización temporal o
cumplimiento poblacional de CVaR. La campaña histórica requiere una
autorización y registro separados tras revisar el ejecutor y repetir el
preflight en la fecha de ejecución. Validación 2023 y prueba final
2024–2025 permanecen fuera del alcance.
