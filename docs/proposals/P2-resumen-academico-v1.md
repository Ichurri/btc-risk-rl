# P2 — resumen académico de la propuesta

**PROPUESTA PARA REVISIÓN, NO AUTORIZADA PARA EJECUCIÓN.**
Antecedente: P1 cerrado en 811d882. No se implementó ni ejecutó P2.

Recomendación: **nueve corridas, K=10**, semillas 610031/610047/610081, condiciones
C0/C5/C10 en orden rotado, **cuatro épocas provisionales del crítico** y un lote
**D de 64 episodios nuevos por iteración**. Actor, Q/A/B, datos 2018–2022, índices,
normalizador, H180, gamma=1, costos/recompensa y d=−ln(.90) permanecen iguales.

P1 redujo MSE sobre A en 3/3 semillas (50.74%,58.70%,44.44%), pero las medidas
post-A siguieron peor que predictor cero. P0 mostró que alertas no equivalen a
divergencia y que incumplir d en B no implica shortfalls activos en A. P2 pregunta
si el crítico mejora durante más iteraciones y si esa mejora aparece también en
realizaciones que no participaron en su ajuste. No compara causalmente 2 vs4 épocas.

**Correspondencia de política resuelta:** conservar pi_k que genera A_k. Después
del Q/A/B y dual ordinarios, D_k se genera con esa misma pi_k congelada. Evaluar
phi_k y phi_(k+1) sobre D_k fijo, con targets Monte Carlo completos de pi_k.
El post-crítico fue entrenado con esa política; el pre puede arrastrar desfase
respecto a pi_(k−1) y se interpreta como capacidad de adaptación, no como error
puro para la política anterior. Usar pi_(k+1) para D confundiría ese diagnóstico.

D tendrá RNG independiente de aprendizaje y nunca ajustará actor/crítico/eta/lambda
ni modificará Q/A/B. Registrar coincidencias de inicios y solapamiento de
transiciones, sin rechazarlos. Nuevas realizaciones sobre el mismo histórico
**no demuestran generalización temporal**. Si D orienta decisiones, es desarrollo.
No se usa validación 2023 ni conjunto final 2024–2025.

Métricas: MSE, segundo momento de G, razón contra predictor cero, sesgo firmado y
normalizado, estadísticas de V/G, comparación A/D pre/post y tercios del horizonte.
Ventanas fijas temprana k=0–2 y tardía k=7–9; agregar sumas, no promediar ratios.
Mantener eta/lambda, shortfalls A, gradiente de riesgo y auditorías B separados de D.

**Criterio de avance propuesto**, al completar todas las corridas: en al menos
dos de tres semillas de cada condición, simultáneamente, R_D tardía<=1 y <=0.8×
R_D temprana; |sesgo normalizado tardío|<=0.25; brecha R_D−R_A tardía<=0.5;
denominadores informativos e integridad. Son umbrales técnicos para revisión,
no significancia estadística. Si no se cumplen, revisar; no alargar ni elegir
checkpoints. Fallos de integridad/no-finitos/recursos detienen; alertas de desempeño
se reportan como tasas con sus propios denominadores, sin parada favorable.

Presupuesto candidato: hasta tres días activos con **3h global/día** La Paz/UTC,
descontando otras campañas; reserva 30min, límites de P1, D subtope15min dentro de
unidad combinada45min. Calibración en primera unidad programada, sin muestras extra.
Pausar solo en Q0 o tras dual+D completos; conservar snapshots/RNG/contadores y no
repetir diagnóstico parcial tras un fallo. No hay ejecutor para estas reglas aún.

P1 brazo4 midió 58.457 s por iteración (mediana). Proxy de aprendizaje P2:
~91.879 min; **D y la instrumentación nueva no están medidos**. No se promete un
día ni se usa ese proxy para admitir unidades. Aprendizaje: 81360 trayectorias;
diagnóstico: 5760; total 87120 (15681600 transiciones). Pasos actor/crítico:
720/1440. Igual presupuesto por condición; costos D separados.

Pendiente de revisión: K/semillas/D/frecuencia, umbrales técnicos y ventanas,
tres días máximos y frontera compuesta. Después se necesita autorización explícita
de implementación/verificación y ejecución. Cuatro épocas siguen provisionales.
Nada aquí acredita rentabilidad, CVaR poblacional ni congela diseño confirmatorio.

[Protocolo completo y criterios](P2-protocolo-v1.md) ·
[Configuración candidata](P2-candidate-v1.json) ·
[Comprobaciones estáticas/algebraicas](../evidence/p2-proposal/COMMANDS.md).
