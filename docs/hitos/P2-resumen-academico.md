# P2 — resumen académico de infraestructura

**Infraestructura implementada y verificada solo con sintéticos; P2 histórico no
ejecutado ni autorizado.** Antecedentes: P1 `811d882`, propuesta `7357aa1` y diseño
P2 aceptado por el usuario. [Informe técnico](P2-infraestructura.md) y
[contrato/permisos](../protocols/P2-infrastructure-v1.md).

**Vínculo con el objetivo específico 3:** esta entrega prepara la producción de
evidencia experimental comparable entre C0/C5/C10 mediante diagnóstico separado
del aprendizaje, trazabilidad y criterios fijados antes de resultados. Es un aporte
de infraestructura para ese objetivo, no su cumplimiento empírico ni una modificación
del texto de la tesis. El enunciado literal de OE3 no está versionado en este
repositorio; no se lo reformula ni se le atribuyen conclusiones nuevas.

P0 mostró que una alerta relativa alta y lambda positivo no bastan para identificar
un fallo o activación de riesgo. P1 mejoró MSE in-sample en 3/3 semillas, pero siguió
por encima del predictor cero. P2 permitirá observar diez iteraciones con cuatro
épocas provisionales y distinguir ajuste en A de error en realizaciones nuevas D.
D mantiene pi_k que generó A; ambos críticos comparten el mismo target MC. El post
está alineado con la política de ajuste; el pre puede incluir desfase respecto de
la política anterior. Las realizaciones nuevas del mismo histórico no prueban
generalización temporal y cualquier decisión posterior basada en D será desarrollo.

Se aceptaron nueve corridas con semillas nuevas, D64 por iteración, d=-ln(.90)
común, Q/A/B intacto y presupuesto equivalente, incluidos auxiliares C0. El avance
requiere criterios conjuntos en 2/3 semillas de cada condición, con tres bloques
independientes de semilla, no nueve réplicas. No es un contraste confirmatorio.
Sin brazo2, ninguna mejora posterior podría atribuirse causalmente a cuatro épocas.

Las pruebas sintéticas verifican aislamiento de D, correspondencia política/MC,
reanudación exacta, métricas y criterios algebraicos, presupuesto y bloqueos. Los
resultados numéricos de fixtures no estiman comportamiento financiero ni tiempo de
mercado. No se cambió d ni se seleccionaron checkpoints por desempeño. La referencia
del 10% no es un máximo individual de pérdida o drawdown ni garantía CVaR.

**Siguiente decisión:** revisar la infraestructura y, por separado, autorizar o no
la campaña histórica con sus guardas y calibración acotada. Hasta entonces el
comando de mercado está bloqueado; validación2023/final2024–2025 siguen protegidos.
