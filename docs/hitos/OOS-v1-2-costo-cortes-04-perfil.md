# Perfil aislado WF de costos `...04`: entrega para revisión

**Estado: infraestructura preparada, permiso cerrado, preflight `blocked`.**
Base `2d3b6a4`; implementación `5d232c8`. No existe la raíz histórica
`artifacts/oos-v12-wf-cost-only-04/` ni el registro independiente
`docs/protocols/OOS-v1-2-wf-cost-04-approval.json`. El gate del comando
público y del trabajador es `MARKET_EXECUTION_ENABLED=False` con
`REGISTRATION_SHA256=None`. No se lanzaron unidades históricas ni se
activó evaluación fuera de muestra.

## Diseño conservado

El [perfil fijado](../protocols/OOS-v1-2-wf-cost-04-profile-v1.json)
(SHA-256 `b188f93b0248d230dc4b122ed0e650be1c545dd7464184b744c69ef231772fbb`)
remite al diseño y protocolo WF originales mediante sus huellas. Solo
cambian la raíz y el nombre del registro de aprobación. Se mantienen:

| Orden | Condición | Semilla | Corte | Unidades |
|---|---|---:|---:|---:|
| 1 | C10 | 276696733 | 2021 | Q0 + 10 Q/A/B+D |
| 2 | C10 | 498614892 | 2022 | Q0 + 10 Q/A/B+D |

K=10, β=0, cuatro épocas del crítico, D=64, d=−ln(0,90), calendario
Q/A/B, normalizador propio por corte y checkpoints solo en `after_q0` y
`after_dual_and_D`. Dos días activos como máximo en `America/La_Paz`,
10.800 s globales por día con reserva de 2.700 s, 3.600 s productivos
propios por día, 5.400 s propios acumulados, 120 s por Q0 y 180 s por
Q/A/B+D (3.840 s de cotas de unidad). El tipo de permiso `...04` se añadió
a la lista de **tipos exactos** autorizables, con raíz exclusiva y lease
verificado; estar en esa lista no habilita el gate.

## Comprobación sintética

La prueba con fuente fabricada recorre Q0 y unidad 1 por el trabajador
`...04` en **procesos trabajadores diferentes**. Cierra y vuelve a abrir
`WFCostLedger` entre las unidades; valida la cadena de hashes, el estado
`ready` sin unidad pendiente, los manifiestos y bytes de ambos checkpoints,
la conservación de Q0 y los contadores acumulados 8 pasos de actor y 16
de crítico tras la unidad 1. Cada proceso lee la solicitud, comprueba su
lease, ejecuta `complete_unit` y el algoritmo Q/A/B+D, incluido D. El
supervisor de prueba sigue siendo el mismo proceso de pytest: esto prueba
reingreso del **ledger**, no un nuevo proceso supervisor ni `systemd`.
El objeto `TrainingMarket` de la prueba contiene exclusivamente una ruta
`SyntheticMarket` fabricada; el marcador de la unidad 1 es una comprobación
del contrato, **no evidencia de entrenamiento histórico**.

Las pruebas focales dieron **18 passed**; la suite completa, **446 passed
en 318,33 s**; Ruff, `All checks passed!`. Se registran en
[COMMANDS.md](../evidence/oos-v1-2-wf-cost-04-profile/COMMANDS.md)
y sus logs pequeños. Los rechazos del comando y trabajador con gate cerrado
ocurren antes de crear la raíz. La prueba no mide tiempos de mercado, costo
de D ni continuidad de una sesión `systemd`.

## Preflight vigilado de solo lectura

La [captura](../evidence/oos-v1-2-wf-cost-04-profile/preflight.json) corresponde
a `5d232c8` y **2026-10-29 19:33:37 UTC**; SHA-256
`bf89c4cb7f76c69ff3c74d6a0314d1720958696dc2d786b2e10bd90f04efcd15`.
Resultado `blocked` por dos razones independientes: ausencia de permiso
`...04` y saldo global del día insuficiente para admitir Q0. La campaña
fallida `...03` carga conservadoramente **10.800 s** el 29/10/2026; saldo
antes de reserva **0 s**. No hay otra campaña activa. Son observaciones de
ese instante, no disponibilidad futura.

CA conectada; batería **100 %** (mínimo 50 %); memoria disponible
**6.699.925.504 B** (mínimo 4 GiB); disco libre **151.727.833.088 B**
(mínimo 20 GiB); `Linger=yes`; `systemd --user=running`. Integridad de
entradas `ok`; cortes con 3.639 y 4.678 inicios y 5.764/7.703 filas de
ajuste. El vigilante registró **56 rutas abiertas**, listadas una por una en
el JSON. Incluyen CSV del **derivado exclusivo de entrenamiento** H1 y
evidencias previas. No abrió CSV H1 compartidos con 2023, validación ni
prueba final; cero trayectorias generadas y cero pasos de optimizador.
La huella agregada del código del perfil fue
`99582cfc42b3d1ce289b09cb2e99f0e8bf9324c2e2190567757ed496f271eb96`.

## Preservación y siguiente decisión

La [auditoría archivo por archivo](../evidence/oos-v1-2-wf-cost-04-profile/frozen-roots-check.json)
coincidió con las huellas fijadas para `...01` (15/15 archivos, mapa
`b93caafafd20b7a61f86214b5cbecba3ff7942d3862a467e1748d636b74a010a`),
`...02` (2/2, `e11a6cfa872ed91ed5f9d0b30f429071b884846125c4df2a4a9d694a664257fd`)
y `...03` (10/10, `34270a3a26901de2472d203662e1717827cc93d8073a7f996b01f0b8174bbb57`).
Ninguna raíz previa se usó como checkpoint o lote de `...04`; se leyeron
solo para la auditoría. La eliminación local previa de `.python-version`
queda fuera de los commits.

Para una campaña histórica eventual harían falta autorización distinta,
registro fijado en commit separado, día con presupuesto admisible, preflight
inmediato y revisión de esta entrega. El perfil presente no concede esos
permisos.
