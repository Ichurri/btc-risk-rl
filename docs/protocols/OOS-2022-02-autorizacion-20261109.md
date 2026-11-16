# Alcance autorizado de la medición WF 2022-02

El 09/11/2026 Santiago autorizó expresamente la medición independiente
`2022-02` y el trabajo necesario para completarla, sin confirmaciones entre
etapas, después del intento `2022-01` fallido antes del ledger. Este registro
de alcance **no es por sí solo un permiso técnico de ejecución**. El gate
requiere un JSON independiente fijado por huella, pruebas, Ruff, preflight
vigilado y admisión presupuestaria actual antes de abrir la raíz o recolectar
trayectorias de entrenamiento.

El diseño científico es el de
[`OOS-v1-2-costo-2022-reemplazo-02-v1.md`](../proposals/OOS-v1-2-costo-2022-reemplazo-02-v1.md):
una C10 nueva del corte 2022, semilla 498614892, β=0, cuatro épocas del
crítico, K=10, D=64, Q0 más diez Q/A/B+D. Usa exclusivamente el derivado
H1 de entrenamiento, sin copiar Q0, pesos ni checkpoints de WF05 o
`2022-01`. La raíz, aprobación y bitácoras de `2022-02` son nuevas.

Se conservan 10.800 s globales por fecha La Paz y reserva 2.700 s;
3.600 s propios diarios, 4.800 s acumulados en máximo dos días activos,
reserva propia 600 s por fecha y cotas 120/180 s por unidad. La ventana
01:00–09:00 incluye preparación, guardado y cierre; no amplía los límites.
El intento fallido `2022-01` conserva su cargo global de 10.800 s el
07/11 y no se reanuda. La bitácora de `2022-02` empieza antes de la primera
comprobación específica formal, y la admisión verifica cada unidad y su
checkpoint completo antes de las 09:00.

Un fallo durante una unidad o un intento `failed` se conserva sin repetición
selectiva. Solo se reingresa desde una frontera completa `ready`, con
comprobaciones y presupuesto nuevos. WF05 sigue cerrado `incomplete`;
validación 2023, prueba final 2024–2025 y evaluación confirmatoria v1.2 no
forman parte de este permiso.
