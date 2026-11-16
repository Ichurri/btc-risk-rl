# P2R v2 — revisión del marcador de entrenamiento histórico

**Estado: diagnóstico de solo lectura y decisión metodológica PROPUESTA PARA
REVISIÓN, NO ADOPTADA.** La campaña `p2r-approved-v2` permanece cerrada;
ningún reporte, ledger, checkpoint, parámetro o resultado numérico se editó.
El resultado de la regla técnica sigue siendo **`review`**. Esta revisión no
accede a datos de validación ni finales y no genera trayectorias.

## Hallazgo causal

`SyntheticExperiment._report()` define
`market_training_executed` exclusivamente por pertenencia de
`settings.purpose` al conjunto `authorized_p0_only`, `authorized_p1_only`
([código](../../src/btc_risk_rl/agents/trainer.py)). El perfil histórico
P2R es `authorized_p2r_only`
([configuración](../../src/btc_risk_rl/pilots/p2r_market.py)); por tanto la
expresión devuelve `false` en cualquier reporte P2R, con independencia de
las trayectorias, pasos de optimizador o pesos. Se observó exactamente esa
predicción en **99/99** `unit-N.json`. El valor es una clasificación de
reporte, calculada *después* de `run.run(...)`; una búsqueda en el código
operativo solo encuentra la escritura de este campo, no una lectura que
controle Q/A/B+D, la fuente de datos, el guardado o la admisión.

El [trabajador de unidades](../../src/btc_risk_rl/pilots/p2_runner.py) llama
`run.run(pause_after=unit)`, valida el estado, guarda el checkpoint y
escribe el reporte. El supervisor
([`_verify_completion`](../../src/btc_risk_rl/pilots/p2r_units.py)) comprueba
estado, contadores, huella de checkpoint, frontera, perfil, procedencia y
configuración, pero **no** comprueba `market_training_executed`. Por ello
las 99 unidades pasaron sus controles aunque la etiqueta fuese falsa. El
protocolo adoptado [§5](../proposals/P2R-protocolo-v2.md) exigía
corregir/verificar el metadato antes de congelar el código histórico; esa
tarea no se cumplió antes del lanzamiento. Esta omisión de preflight y la
etiqueta incorrecta son defectos demostrados de trazabilidad. No se ha
encontrado una vía por la que la etiqueta alterase el aprendizaje.

## Contraste independiente con los artefactos existentes

El [auditor de este hito](../evidence/p2r-metadata-review/checks.py) leyó
los 99 reportes, 99 manifiestos y estados `state.pt`, y cotejó cada uno con
el ledger. Las huellas de ledger y supervisor son, respectivamente,
`fe443e5e32d26a7de075fa6e34771c8f20651bbe566f9097bfdb367d17d0b866`
y `dc5d3901ab3ba2ce14dd7db3c4d80e6186b9a20291d27bd5d0b8b1300c091486`.
Los resultados pequeños están en
[`results.json`](../evidence/p2r-metadata-review/results.json).

| Evidencia comprobada | Resultado | Alcance |
| --- | --- | --- |
| Perfil en reporte y manifiesto | `authorized_p2r_only` en 99/99 | Mismo perfil que la expresión excluye |
| Marcador | `false` en 99/99 | Determinista por el código de reporte |
| Q0 | 9/9 en `after_q0`, 0 pasos de actor/crítico | `false` no contradice por sí solo la ausencia de optimización en Q0; sí hubo 400 trayectorias Q por corrida |
| Q/A/B+D | 90/90 en `after_dual_and_D`, +8 pasos de actor y +16 de crítico por unidad | `false` contradice la optimización histórica efectuada |
| Estados del optimizador | Pasos acumulados idénticos a contadores en 90/90 | Total de 720 actor y 1440 crítico; no es solo un contador de reporte |
| Pesos | Huellas de actor y crítico cambiaron en 90/90 frente a la frontera anterior | Confirma cambios de parámetros, sin evaluar su utilidad |
| Origen del mercado | Procedencia `accepted_train_collection_only` y manifiesto del derivado `62ad23a6…e3b9` en 99/99 | La ruta de ejecución apunta al derivado H1 exclusivo de entrenamiento |
| Identidad del código | SHA-256 de `trainer.py` en 99 manifiestos igual al archivo auditado, `7a0f46a9…b150e2` | La causa encontrada corresponde al código de la campaña |

Los eventos Q/A/B inspeccionados contienen solo IDs `accepted-train:`; el
recuento de 467.280 **ocurrencias acumuladas** incluye la reiteración de
eventos en reportes sucesivos y no equivale a trayectorias únicas. El
[cierre original](P2R-ejecucion-historica-v2.md) ya verificó la cadena
completa, las 99 huellas de checkpoint, 5.760 archivos D y los totales
separados de 81.360 trayectorias de aprendizaje y 5.760 diagnósticas.
La auditoría actual no reinterpreta D como validación temporal.

La evidencia respalda que hubo **entrenamiento P2R con datos del derivado
H1 de entrenamiento**; el `false` no es una medición del aprendizaje. La
fuente histórica se construye mediante `TrainingMarket` y
`training_only_shard` y rechaza rutas fuera de entrenamiento. El preflight
vigilado previo tuvo cero aperturas de CSV H1 compartidos. Esta auditoría
no dispone de una traza de aperturas de archivos durante las 99 unidades;
por tanto no convierte esos controles y huellas en una afirmación de
vigilancia exhaustiva de todas las lecturas del proceso. Tampoco demuestra
generalización temporal, rentabilidad ni cumplimiento poblacional de CVaR.
Los reportes de unidad no están individualmente anclados por hash en el
ledger; se cotejan con sus checkpoints y recursos, cuya integridad sí fue
verificada.

## Alcance de la desviación y decisión propuesta

La desviación alcanza **100 % de reportes** y el requisito temporal de
verificación/corrección antes de congelar el ejecutor. No hay evidencia de
cambio en ADR-002, Q/A/B+D, `d`, lotes, normalizador, calendario, datos o
la regla numérica. El criterio de integridad del [§6](../proposals/P2R-protocolo-v2.md)
distingue nueve corridas íntegras de un fallo de integridad; aplicar
retrospectivamente una excepción silenciosa a §5 sería improcedente.

**Recomendación para revisión académica:** conservar literalmente el
resultado numérico **`review`** y todos los artefactos originales; clasificar
la campaña como **operativamente completa, con desviación documentada de
metadatos/preflight y aceptación metodológica formal suspendida**. Presentar
las métricas únicamente como diagnóstico descriptivo de desarrollo. Este
dictamen no concede una excepción ni transforma `review` en
`advance_to_discussion`. Si la revisión decide aplicar estrictamente
`not_evaluable` por el incumplimiento de integridad de §5, debe registrar esa
decisión **por separado** y explicar que es un juicio de elegibilidad, no
un nuevo cálculo ni una modificación del resultado numérico guardado. Si
considera la desviación no invalidante, necesita un acta de adjudicación
explícita que reconozca el requisito incumplido, justifique por qué no
afecta las medidas y mantenga los límites de desarrollo. Ninguna opción
autoriza editar reportes, seleccionar checkpoints o repetir corridas.

Para cualquier campaña **futura y separadamente autorizada**, proponer una
comprobación sintética del marcador derivada del tipo de fuente y de pasos
de optimizador, más una aserción en `_verify_completion` coherente con Q0
y Q/A/B+D. Esto es una prevención prospectiva, **no** una corrección
aplicada a P2R cerrado. No se ha implementado en este hito.

## Comprobaciones realmente ejecutadas

El [registro de comandos](../evidence/p2r-metadata-review/COMMANDS.md)
identifica la auditoría de solo lectura y Ruff. No se ejecutaron pruebas
de aprendizaje ni la suite completa, porque solo se añadieron documentos
y un auditor que lee artefactos. La eliminación local previa de
`.python-version` permanece fuera del commit.
