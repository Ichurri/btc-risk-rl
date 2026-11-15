# Texto propuesto para armonizar la tesis antes de consultar 2023

**Estado:** borrador de cambios, no aplicado a Google Docs. Lectura de solo
lectura del documento «Santiago_Iturri_formato_UCB_preliminares» el
11/11/2026, revisión `AHj4eMTGRhBNP0jpVha-4dOSSuNkWnnoj3RGb9aZBDHj5Q6OsraK7Fm7f6MVjLGtrjyiDC6Pl71ENcyboeK-2IgetphkrYxbZ9o4O_Nt`.
[Documento de la tesis](https://docs.google.com/document/d/1dNp8MbiV0Zqpu6S9-5u6vnL-R-v4YbYaR8g6232EBQ8/edit).
Si cambia la revisión antes de aplicar el texto, volver a comparar las
secciones. Este borrador no habilita acceso a datos protegidos.

## 2.7.2. Sustituir la regla operativa del cierre

> La partición cronológica mantiene separadas las funciones de ajuste,
> comprobación técnica y contraste final. La configuración común de los
> agentes y la regla de checkpoint se fijaron usando únicamente los
> diagnósticos de desarrollo 2018–2022 y antes de consultar 2023. En este
> estudio, 2023 se reserva para una única comprobación predefinida de
> viabilidad de las 108 políticas finales: recorrido completo y continuo,
> acciones, cartera y retornos finitos, contabilidad y costos auditables,
> normalizador congelado, huellas válidas y Sortino definido en cada
> corrida. No se usa su signo ni su magnitud para escoger arquitectura,
> semilla, hiperparámetros o checkpoint. Una falla de integridad o una
> métrica primaria indefinida detiene el acceso al conjunto final. Si 2023
> motiva un rediseño, se documentará todo lo observado y el nuevo diseño
> se considerará desarrollo; esa misma partición no volverá a presentarse
> como validación independiente. El período 2024–2025 conserva un permiso
> separado para un único contraste confirmatorio bajo reglas congeladas.

La explicación conceptual del sesgo de seleccionar el máximo sobre datos
ruidosos puede permanecer. La oración actual que asigna a validación 2023
la comparación/selección de configuraciones deja de describir este estudio.

## 2.7.3 y Tabla 4. Conservar teoría, sustituir promesa operativa

> La Tabla 4 compara posibilidades metodológicas. El estudio no ejecuta
> CPCV ni estima una distribución de caminos combinatorios. Por costo y
> por la cobertura indexada disponible, la revisión adoptó dos cortes
> cronológicos auxiliares con purga: entrenar 2018–2020 y observar 2021;
> entrenar 2018–2021 y observar 2022. Se separan 180 velas antes de cada
> período observado y se reajustan características, normalizador y agente
> únicamente dentro del pasado de cada corte. Cada corte usa tres semillas
> auxiliares por condición. Sus resultados son diagnósticos de desarrollo:
> 2021 y 2022 ya participaron en las decisiones previas y no constituyen
> validación temporal independiente. PBO y DSR solo se calcularán si
> existen los insumos definidos para cada estadístico; en caso contrario
> se informarán como no estimables.

Mantener la fila CPCV de la Tabla 4 como **descripción del método** y
añadir en su pie: «CPCV se describe para comparación; no se ejecutó en
este trabajo. Los controles auxiliares realizados son los dos cortes
walk-forward indicados, de alcance menor». No etiquetar esos cortes como
«CPCV reducido» ni atribuirles varios caminos fuera de muestra.

## 3.8.4. Sustituir por el procedimiento operativo

> Antes de consultar 2023 se fijaron una configuración común para C0,
> C5 y C10 (crítico ordinario β=0, cuatro épocas, diez iteraciones,
> D=64 observacional), 36 bloques nuevos de semillas pareadas y el orden
> rotado de las 108 corridas principales. Estos valores proceden de
> diagnóstico de desarrollo y viabilidad, no de una búsqueda que pruebe
> optimalidad. Las tres condiciones comparten datos, arquitectura,
> presupuesto y reglas temporales; solo cambia el mecanismo de riesgo.
> Los dos cortes cronológicos auxiliares se tratan por separado, con tres
> semillas adicionales compartidas entre condiciones. Su purga de 180
> velas y el reajuste por corte se auditan antes de interpretar métricas.
> El corte 2021 ejecutado con una ruta de bloqueo equivocada conservó
> íntegros sus 99 checkpoints y cabía en el presupuesto reconstruido,
> pero su exclusividad original no pudo demostrarse: se informa como
> diagnóstico descriptivo, sin atribuir cumplimiento estricto del
> supervisor. Las reglas de integridad de 2023 son técnicas y comunes a
> todas las políticas; no se usa allí rentabilidad o Sortino para elegir
> configuración. PBO y DSR quedan condicionados a insumos reales y no
> se informan como cero si no son estimables.

La afirmación actual «propuesta v1.2, aún no adoptada» y la frase que
mantiene abierto el papel de 2023 requieren actualizarse al estado del
protocolo cuando el documento se modifique. No declarar completados el
corte 2022 o las 108 corridas hasta que los ledgers cierren y se auditen.

## 3.8.5 y 3.9.2. Precisiones que deben quedar alineadas

> El checkpoint de evaluación es siempre K=10 en la frontera
> `after_dual_and_D`, sin selección por MSE, auditoría B, patrimonio,
> Sortino o CVaR. Se usa `sigmoid(μ)` determinista, reloj `h=1`, una sola
> cartera por política y normalizador ajustado solo en entrenamiento.
> La evaluación no actualiza parámetros. Una corrida fallida o un Sortino
> indefinido conserva su evidencia y no se sustituye selectivamente; si
> falta cualquiera de las 36 ternas finales no se emite el contraste
> primario confirmatorio. El contraste usa 19.999 remuestras pareadas por
> bloque de semillas, RNG 910031, diferencias centradas bajo la nula,
> prueba unilateral y corrección de Holm para C5–C0 y C10–C0 con
> significancia familiar 0,05. Se informa el efecto mínimo de interés
> propuesto de +0,50 unidades de Sortino anualizado, intervalos
> descriptivos y tamaño de efecto pareado. Un Sortino mayor no demuestra
> cumplimiento poblacional de CVaR.

Las 36 ternas y los dos cortes están en la congelación de entrenamiento;
la regla de evaluación está fijada en
`docs/protocols/OOS-v1-2-evaluation-method-freeze-20261111.json`.
La ruta histórica, sus permisos separados y la armonización efectiva de
la tesis siguen pendientes antes de abrir 2023/final.
