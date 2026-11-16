# Diagnóstico P0 — resumen académico

Base e0a2dfc; rama `codex/p0-diagnosis`. **Comportamiento explicado; no defecto
operativo demostrado en los cálculos examinados.** Algoritmo y d intactos.

Las 162 alertas del crítico corresponden a 18 lotes completos antes de actualizar
y 144 minibatches. Estos últimos se registran después de Adam, pero su pérdida
fue calculada antes del paso actual. La razón divide MSE por media(G²)+1e-12,
no por varianza. Por eso no es una curva postactualización sobre muestra fija.

Se reconstruyeron los 18 A originales con checkpoints congelados y streams
originales. Coinciden exactamente rutas, identidades, diagnósticos de recolección
y hashes de observaciones/acciones/retornos/valores/ventajas/coeficientes.
La MSE comparada sobre cada A fijo disminuyó en 18/18 casos, pero permaneció
por encima del predictor cero. Hay mejora in-sample, no demostración de
estabilidad prolongada ni generalización. El informe aporta predicciones,
targets, denominadores y desglose por semilla, condición e iteración.

C0/C5 de semilla 410031 coinciden por una causa concreta: primera iteración
lambda=0; segunda iteración C5 usa lambda=0.01798010270375307, pero
max(L_A)=0.23189034740200398 < eta=0.23453061174429735. Los 64 shortfalls y
la penalización son cero. Coeficientes, actor y Adam coinciden con C0;
los actores sí se actualizaron. El incumplimiento observado en B no implica
shortfalls en A, ni d es el umbral eta.

En la segunda iteración de las otras cinco corridas sensibles al riesgo hay
shortfalls, coeficientes modificados y gradiente de riesgo inicial no nulo:
C5/410047: 6; C5/410081: 5; C10/410031: 4; C10/410047: 9; C10/410081: 11.
Esto acredita activación del mecanismo, no eficacia ni cumplimiento CVaR.

Limitación: no se guardaron pesos intermedios de minibatch. Se comprobaron los
gradientes iniciales y normas originales, sin reconstruir pasos Adam. Todos los
archivos originales conservaron sus hashes. No se repitió P0, no hubo pasos de
optimizador ni acceso a validación/final. Las reconstrucciones son diagnósticas,
no mediciones que estuvieran presentes originalmente.

P1 **propuesto, no autorizado ni ejecutado**: comparar 2 frente a 4 épocas del
crítico, única intervención, con semillas nuevas y resto del protocolo fijo.
Criterio candidato: mejora ≥20% de MSE post-A tras la primera actualización en
al menos dos de tres semillas, sin fallos; controlar igualdad del actor en esa
frontera. No contar las condiciones como réplicas independientes de ese control.
El resultado solo probaría ajuste in-sample. Protocolo detallado y presupuesto
candidato en el informe; d no cambia y no se seleccionan checkpoints por B.

[Informe completo](P0-diagnostico.md) ·
[Resultados](../evidence/p0-diagnosis/results.json) ·
[Comandos](../evidence/p0-diagnosis/COMMANDS.md).
