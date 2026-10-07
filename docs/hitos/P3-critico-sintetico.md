# P3 — intervención del crítico verificada con rutas sintéticas

**Alcance:** implementación del contraste β=0/1 de P3 v1.1, sin ejecutor
histórico, permiso de campaña ni acceso a validación o prueba final. El
protocolo P3 v1.1 está adoptado como diagnóstico de desarrollo; este hito no
autoriza su ejecución histórica.

## Contrato implementado

En cada minibatch A de las cuatro épocas provisionales del crítico,
con los targets Monte Carlo congelados, se calcula

`Lβ = mean((V(o) − G)²) + β mean(V(o)²)`.

La rama β=0 devuelve directamente el tensor MSE preexistente, sin añadir
un cero al grafo de autograd. β=1 reutiliza exactamente las predicciones
del mismo minibatch para ambos términos. Se conservan el orden de actor
antes del crítico, Q/A/B, D, gamma, recompensa, RNG, ventajas y regla dual.
La telemetría `mc_mse` sigue representando **solo** MSE; en β=1 se añaden
`critic_penalty` y `critic_objective`, medidos antes del paso corriente del
minibatch aunque registrados después. Son mediciones sintéticas; no son
rendimiento ni generalización.

La configuración `P3SyntheticSettings` admite solo β entero 0/1 y fuente
`SyntheticMarket`. El checkpoint completo guarda β en el manifiesto,
restituye el perfil sintético y conserva contadores y frontera. No se
agregó β a `P2RMarketSettings`: el diseño histórico P2R exige igualdad
exacta de su configuración congelada, por lo que añadir un campo común
rompería compatibilidad. Este punto se identificó antes de la edición y
se resolvió aislando P3 en un perfil sintético; el perfil histórico P3
queda pendiente de otro hito.

## Verificación y evidencias

Antes de modificar producción se ejecutó `beta0_probe.py --profile legacy`
y se fijó `beta0-before.json`. Tras la edición, el perfil P3 β=0 dio
igualdad exacta en las huellas del actor, crítico, ambos optimizadores,
A congelado, rutas, versiones, pasos y conteos (`beta0-after.json`). El
único campo distinto es la etiqueta del perfil.

Un minibatch analítico con predicciones `[1,2]` y objetivos `[0,1]` dio:
β=0: MSE 1, penalización 0, gradiente `[1,1]`; β=1: MSE 1,
penalización 2,5, objetivo 3,5 y gradiente `[2,3]`. En dos corridas
sintéticas pareadas, A inicial y primer actor coincidieron; cambió el
crítico β=1. D de la primera iteración usó la misma versión de política
y los mismos objetivos sintéticos; cada corrida conservó identidad
propia. La prueba de checkpoint pausó tras `after_dual_and_D`, verificó
β=1, 2/8 pasos de actor/crítico y continuó a 4/16.

Las pruebas no establecen el efecto sobre el histórico ni la comparación
P3 de 18 corridas. Desde k≥1 los brazos pueden divergir en política,
trayectorias y targets; cada D deberá evaluar su propio brazo. Los
artefactos P0/P1/P2/P2R no se escribieron.

**Comprobaciones ejecutadas:** test focalizado 8/8, suite completa 320/320
(230,89 s), Ruff sin observaciones y `git diff --check` sin errores. El
auditor de solo lectura confirmó los ledgers P0/P1/P2/P2R y los 99
reportes P2R. Los comandos y las dos salidas de la sonda β=0 están
versionados en `docs/evidence/p3-critic-synthetic/`.

## Próxima integración pendiente

Requiere autorización nueva para implementar el perfil histórico P3,
su registro y permiso separados, identidad `(semilla, condición, β)`,
reanudación supervisada por frontera completa, preflight y presupuesto
común. La prueba sintética del marcador y supervisor es antecedente,
pero debe verificarse su integración con reportes y checkpoints P3.
Después habrá que ejecutar pruebas sintéticas del ejecutor completo y
preflight de solo lectura antes de solicitar cualquier campaña histórica.
Ninguna decisión de este hito congela cuatro épocas ni demuestra mejora
del crítico fuera de A.
