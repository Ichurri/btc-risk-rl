# P3 v1.1 — resumen para revisión académica

**Estado: PROPUESTA PARA REVISIÓN, NO AUTORIZADA.** P3 sigue siendo un
diagnóstico de desarrollo sobre entrenamiento 2018–2022. Compara β=0 y
β=1 para la regularización `V²` del crítico, en tres bloques de semillas
y C0/C5/C10: 18 corridas previstas, K=10, con presupuesto global de
3 h diarias y hasta tres días activos. La elección de β y de umbrales
exploratorios se hizo después de inspeccionar P2R; no es evidencia
confirmatoria.

La v1 afirmaba que `MSE/(Z+10⁻¹²)≤0,95` descartaba el predictor cero.
Esto es falso: con `Z=MSE=10⁻¹¹`, el predictor cero obtiene
`Rε=10/11≈0,9091`, a pesar de que `Z>10⁻¹²`. La v1.1 exige
`MSE≤0,95Z` y `Z>10⁻¹²`, por lo que cero no pasa. Define también
razones exactas `MSE/Z` y sesgo `media(V−G)/√Z`, con sus casos
indefinidos, para contrastar β=1 menos β=0 dentro de cada semilla y
condición. Cada brazo utiliza sus propios targets: después de la primera
actualización las políticas pueden divergir y las diferencias miden el
efecto total de la intervención, no una diferencia bajo política fija.

La regla ahora comprueba por separado `Z` en D temprana, D tardía,
A tardía **y el último tercio de D tardía**, en ambos brazos. Que D
tardía completa tenga señal no garantiza señal en su último tercio.
Las comparaciones se hacen sin estabilizador; la razón estabilizada
queda disponible únicamente como descripción compatible con P2R. Los
casos de baja señal no se transforman en aparentes aprobaciones.

La [propuesta completa](../proposals/P3-protocolo-v1-1.md), las
[diferencias con v1](../proposals/P3-v1-1-cambios.md) y las
[comprobaciones algebraicas](../evidence/p3-v1-1-algebra/COMMANDS.md)
son entregables de revisión. Las comprobaciones usan números sintéticos,
sin agentes entrenados ni trayectorias de mercado. Antes de cualquier
implementación habría que corregir prospectivamente
`market_training_executed` y hacer que el supervisor rechace reportes
incoherentes; después requeriría autorización separada. P2R y sus 99
reportes permanecen intactos. P3 no permite inferir generalización
temporal, rendimiento financiero ni cumplimiento poblacional de CVaR;
validación 2023 y prueba final 2024–2025 siguen protegidas.
