# ADR-002 v2.1 — armonización con la tesis

**PROPUESTA PARA REVISIÓN, NO ADOPTADA.** Antecedente v2: `28cda8b`;
contrato técnico H2: `cc913b6`. [Documento completo](ADR-002-propuesta-v2-1.md).
V2 y todas sus evidencias se conservan intactas.

La revisión académica comunicada por el usuario considera resueltos el calendario
Q/A/B y la descripción de la evaluación continua como transferencia operacional.
Esta revisión no cambia esas secciones, el pseudocódigo de actualización, la
regla temporal, la cartera única ni el contrato H2.

## Métrica primaria armonizada

Se mantiene como métrica primaria el **Sortino anualizado fuera de muestra**:

\[
S_{anualizado}=\sqrt{2190}\,S_{4h}.
\]

Se conservan retornos simples netos de cuatro horas, MAR=0 y desviación bajista
calculada sobre todos los períodos. S_4h queda como auxiliar. La anualización
es una convención de reporte de la tesis, no un supuesto de independencia
entre velas ni una demostración de cómo escala el riesgo anual. Si la desviación
bajista es cero, ambos ratios siguen indefinidos; no se añade epsilon ni se
imputan valores.

## Procedimiento inferencial ya propuesto

Se incorpora el plan de tesis descrito por el usuario: diferencias pareadas de
Sortino anualizado por bloques de semillas para C5–C0 y C10–C0; bootstrap pareado
unilateral sobre la media de esas diferencias, centrado bajo la hipótesis nula;
corrección de Holm para la familia de dos contrastes, con significancia 0,05.

Se remuestrean bloques completos, con los mismos índices para ambos contrastes.
Las velas no se tratan como réplicas independientes. El documento explicita
H0: media≤0 frente a H1: media>0, centrado por columna, cola superior y regla
secuencial Holm (.025 y luego .05). Anualizar por una constante positiva común
cambia las unidades del efecto, pero no esas comparaciones con iguales remuestras.

**Pendientes antes de evaluación confirmatoria:** número de réplicas, remuestras,
semillas/composición de bloques, precisión y tratamiento inferencial de métricas
indefinidas. No se confunden esos parámetros con un procedimiento aún por elegir:
el procedimiento está propuesto. DD=0→indefinido está definido; la gestión de
esos bloques para inferencia todavía debe cerrarse, sin exclusión retrospectiva.

## Alcance y evidencia

Un Sortino superior no demuestra cumplimiento CVaR a 30 días. El contraste sigue
midiendo transferencia operacional de procedimientos completos. Una validación
usada para selección no constituye evidencia confirmatoria independiente.

[Comprobaciones y comandos v2.1](../evidence/adr002-proposal-v2-1/COMMANDS.md)
registran únicamente ejemplos sintéticos de anualización, bootstrap centrado y
Holm, además de preservación byte a byte de Q/A/B, regla temporal, v2 y H2.
No se ejecuta evaluación de políticas ni se valida un agente.

ADR-002 continúa abierto. No hay cambios operativos, agentes ni entrenamientos;
no se accedió a datos de mercado ni al conjunto final. Siguiente paso: revisar
esta armonización y cerrar los parámetros pendientes antes de la evaluación
confirmatoria; esta entrega no la autoriza.
