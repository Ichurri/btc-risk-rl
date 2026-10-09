# Visualización local de pilotos P0–P3

**Alcance:** informe HTML autónomo, reproducible desde los ledgers locales.
Solo diagnóstico de desarrollo sobre entrenamiento 2018–2022. No ejecuta
algoritmos, no selecciona checkpoints y no abre datos de mercado. El cierre
P3 se determina dinámicamente: un ledger `ready` no equivale a 18 corridas
terminadas. P2 se muestra `failed`/interrumpido; P2R conserva `review` como
decisión numérica y su alcance descriptivo por el marcador heredado.

## Reproducción y controles

El comando único consta en README. Requiere Python 3.11+ y biblioteca
estándar; no se añadieron paquetes al `uv.lock`. La salida debe quedar fuera
de `artifacts/` y `docs/evidence/`. El generador solo abre:

- `artifacts/<campaña>/ledger.jsonl` de las cinco campañas permitidas;
- el `unit-N.json` **último aceptado** de cada corrida listada en el ledger;
- los cierres auditados pequeños P0/P1/P2/P2R y dos evidencias de sesión P3
  disponibles en `docs/evidence`.

Comprueba JSON completo, SHA-256 de los ledgers frente a los cierres,
`previous_hash`/`state_hash` en P2/P2R/P3, huella de `unit-N.json` cuando
el ledger la contiene y huella de checkpoint *declarada en el reporte*
frente a la unidad aceptada. **No recalcula la huella de los archivos binarios
de checkpoint.** Las unidades parciales que no aparecen en el ledger se
ignoran, aunque exista su archivo. Los registros acumulativos se leen una
sola vez desde la última unidad aceptada por corrida. La marca temporal del
HTML procede del ledger, de modo que dos regeneraciones con las mismas
entradas producen el mismo archivo.

## Gráficos, fuentes y límites

| Vista | Métrica / población | Origen | Interpretación permitida |
| --- | --- | --- | --- |
| Avance | Corridas completas y previstas, cada campaña | ledger `runs` y `cursor` | No contar parciales como completas; P2 conserva cinco corridas y una parcial. |
| Tiempos | Mediana/máximo de segundos por unidad aceptada y D por fase | ledger `units`; `report.telemetry` | Costos observados, no estimación de otro equipo ni cargo diario completo. |
| Recursos | Trayectorias de aprendizaje y D; RSS máximo por fase en MiB | ledger `units`; `report.telemetry` | D no actualiza pesos; RSS del proceso no es RAM disponible. |
| Crítico P0 | MSE MC **antes** del ajuste sobre A por iteración | `report.stability` de P0 | No comparar causalmente con la curva post de P1. |
| Crítico P1 | MSE MC **después** del ajuste sobre A completo, con curvas separadas e2/e4; contraste inicial 2 vs 4 épocas | `report.stability` y cierre P1 `primary.seeds` | Tres bloques de semillas, no nueve réplicas independientes. Mismo A/targets solo en el contraste inicial. |
| Crítico P2/P2R/P3 | Medianas por iteración de MSE y Z post separadas para A y D; P3 también separa β=0/1 | `report.diagnostic.records` | A y D tienen trayectorias distintas; D es desarrollo sobre el mismo histórico, no generalización temporal. La composición de corridas cambia en P2/P3. |
| Riesgo | Medianas de `F_B(η_Q)`, cota `d` y λ en paneles de **unidades separadas**, por condición/brazo | `report.audits` | Auditoría B de entrenamiento; no demuestra cumplimiento poblacional CVaR. |
| Pares P3 | MSE D post β=0 y β=1, Δ=β1−β0 en última iteración común aceptada | `report.diagnostic.records` de ambos brazos, identidad en roster del ledger | Solo pares semilla-condición-iteración completos. Desde k≥1 cada brazo tiene política, rutas y objetivos propios; la diferencia no es causal por sí sola. |

Cada figura incluye su métrica, unidad, población/lote, cantidad y ruta de
origen; la sección de procedencia enumera los archivos exactos abiertos. No
se dibuja A–D como comparación pareada, ni se dibuja un par β incompleto. La
razón estabilizada `MSE/(Z+10⁻¹²)` no se usa para decidir o comparar con
predictor cero. No hay datos de evaluación fuera de muestra en el informe.

## Resumen para Ingeniería del Proyecto

P0 verificó el calendario de actualización con nueve corridas técnicas.
P1 mostró mejor ajuste del crítico sobre el mismo lote A inicial con cuatro
épocas en tres bloques de semillas. P2 introdujo D independiente durante más
iteraciones, pero la campaña fue interrumpida: no tiene conclusión global.
P2R completó nueve corridas nuevas con supervisor persistente; la regla
numérica quedó en `review` y sus resultados se adjudicaron únicamente como
diagnóstico descriptivo por una discrepancia de metadato. P3 estudia el
regularizador βV² del crítico con brazos separados; su avance y los pares
disponibles se toman del ledger en el momento de generar el informe.

Ninguno de estos pilotos demuestra rentabilidad, superioridad financiera
frente a C0, generalización temporal o cumplimiento poblacional de CVaR.
La evaluación fuera de muestra permanece pendiente y protegida.

## Verificación efectuada en el checkout aislado

El detalle de comandos, huellas de los cinco ledgers y del HTML/capturas está
en [`docs/evidence/experiment-report/results.json`](../evidence/experiment-report/results.json).
Las cinco pruebas sintéticas nuevas pasaron; Ruff pasó. Dos generaciones
consecutivas y entradas inmóviles produjeron el mismo SHA-256 del HTML.

La suite general produjo **341 aprobadas y 5 fallidas**. Ninguna de las cinco
es una prueba del nuevo generador: una es una carrera de `/proc` en la prueba
de muerte del supervisor; dos preflights P2R requieren ledgers no versionados
que no están en el worktree aislado; dos guardas P3 esperan la semántica de
la etapa anterior a la autorización de la campaña. Estos fallos se conservan
como resultados reales, sin alterar el supervisor, las guardas ni los datos
para hacer pasar la suite. La evidencia de origen P0/P1/P2/P2R/P3 quedó en
el checkout original; el único cambio local preexistente allí era la
eliminación de `.python-version`, preservada.
