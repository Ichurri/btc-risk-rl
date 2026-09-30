# P2 histórico — autorización de campaña

El usuario autorizó el 30/09/2026, zona `America/La_Paz`, activar el permiso
específico y ejecutar P2 sobre el entrenamiento aceptado 2018–2022 desde
`2f01d6c`. Esta autorización queda registrada antes de iniciar el piloto; el
registro técnico es `P2-market-registration-v1.json` y el guardia de código
fija su SHA256. No se modifica `P2-infrastructure-v1.json`, cuya huella sigue
anclada como diseño aprobado.

Alcance exacto: nueve corridas en el orden rotado aprobado, semillas
610031/610047/610081, C0/C5/C10, K=10, crítico provisional de cuatro épocas,
D=64 tras cada iteración, N_A=64 y N_Q=N_B=400. Se conserva d=−ln(0,90),
ADR-002, Q/A/B, horizonte, normalizador, costos y recompensa. D se genera
con π_k congelada y no actualiza parámetros. No se eligen checkpoints por
resultado ni se repiten selectivamente fallos.

Presupuesto: máximo global de 10800 s por día en `America/La_Paz`, incluyendo
carga, preflight, trabajo, guardado y cierre; hasta tres días activos, sin
concurrencia. Se descuenta el consumo registrado de otras campañas. Reserva,
topes por unidad y D, memoria, fronteras y estados de fallo permanecen los del
protocolo P2. Si no cabe una unidad, pausar antes de empezarla en frontera
completa. La primera unidad Q/A/B+D mide D real sin variar el diseño.

Validación 2023, prueba final 2024–2025, evaluación confirmatoria y cambios a la
tesis no están autorizados. Las conclusiones serán diagnóstico de desarrollo
sobre el mismo histórico de entrenamiento, no generalización temporal,
superioridad financiera ni garantía poblacional de CVaR.

Esta autorización sustituye únicamente el bloqueo anterior de P2 histórico.
P0/P1 cerrados y sus evidencias siguen inmutables. Cualquier campaña posterior
necesita su propia autorización.
