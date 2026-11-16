# P2 histórico: resumen para el objetivo específico 3

La campaña P2 buscaba seguir el ajuste del crítico durante diez iteraciones y
comparar su error en el lote de aprendizaje A con un lote diagnóstico D de 64
trayectorias nuevas por iteración, generadas por la política congelada que
produjo A. Se conservaron tres semillas, las condiciones C0/C5/C10, Q/A/B,
la cota común de riesgo y los datos aceptados de entrenamiento 2018–2022.

La ejecución se interrumpió durante la sexta de nueve corridas. Cinco corridas
completaron K=10; la sexta cerró una iteración y dejó la segunda parcial. El
ledger quedó `failed` por pérdida del supervisor, sin reanudación ni repetición
selectiva. Las 57 unidades completas y sus 3264 trayectorias D se verificaron
por cadena y hashes; la parcial se conserva como evidencia no reanudable. La
causa exacta de la pérdida de sesión no está demostrada.

Los diagnósticos de las corridas terminadas registran advertencias frecuentes
del crítico y error D posterior aún superior al predictor cero al final de
ambos bloques de semillas iniciados. Son observaciones de desarrollo sobre el
mismo histórico, con denominadores y métricas por iteración disponibles en el
[informe](P2-ejecucion-interrumpida.md) y los
[resultados](../evidence/p2-execution/campaign-results/results.json). Los
criterios conjuntos predefinidos no se aplican: falta una semilla y una
condición de la segunda. La campaña no demuestra generalización temporal,
rentabilidad, convergencia ni cumplimiento poblacional de CVaR. Tampoco
permite atribuir causalmente ningún cambio a cuatro épocas sin el brazo de
dos épocas.

El paso siguiente requiere revisión del fallo operativo y, para cualquier
ejecución adicional, un protocolo y autorización nuevos que conserven intacta
la campaña fallida. No se utilizaron validación 2023 ni prueba final
2024–2025 y no se modificó la tesis.
