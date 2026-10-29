# Perfil WF de costos `...03`: infraestructura para revisión

**Estado: preparado; no autorizado para ejecución.** Base `9efe521`; código
en `0446164`. La raíz histórica
`artifacts/oos-v12-wf-cost-only-03/` y el registro independiente
`docs/protocols/OOS-v1-2-wf-cost-03-approval.json` están ausentes. El gate
del perfil y los de `...01`/`...02` siguen cerrados. No se lanzó unidad
histórica ni se leyó validación 2023 o prueba final.

## Identidad y alcance fijo

El [manifiesto del perfil](../protocols/OOS-v1-2-wf-cost-03-profile-v1.json)
fija por SHA-256 el protocolo original, el diseño de 22 unidades y el
derivado H1 exclusivo de entrenamiento. Su SHA-256 es
`1550e6755b90618fcb613c927ff744ac2a42cc4134e88dc305812585a8961256`.
Solo cambian raíz y registro de aprobación. La secuencia sigue siendo
`wf-2021` C10 semilla 276696733 Q0+10 Q/A/B+D, después `wf-2022` C10
semilla 498614892 Q0+10 Q/A/B+D; K=10, β=0, cuatro épocas del crítico,
D=64, d=−ln(0,90), calendario Q/A/B y normalizadores propios por corte.
Checkpoints únicamente en `after_q0` y `after_dual_and_D`.

El máximo es dos días activos `America/La_Paz`, 10.800 s globales/día,
2.700 s de reserva, 3.600 s productivos propios/día y 5.400 s acumulados.
Las cotas por unidad son 120 s para Q0 y 180 s para cada Q/A/B+D, suma
3.840 s. La admisión y contabilidad reutilizan el contrato WF vigente.
Ni Q0 ni archivo operativo de `...01`/`...02` se usa como entrada para las
22 unidades nuevas. El preflight solo los **lee para comprobar huellas**;
rechaza cualquier diferencia y no los modifica.

## Verificación sintética y límites

Una prueba llama al supervisor `run_units()` de `...03` en un proceso nuevo,
con raíz temporal ausente, bloqueo y ledger reales, fuente/worker fabricados.
Acepta Q0, crea checkpoint sintético `after_q0` y pausa con `ready`, una
unidad y sin `pending`. Un segundo proceso reingresa y conserva Q0 sin iniciar
la unidad 1. Otras pruebas rechazan una raíz huérfana sin escribirle,
identidad alterada sin aceptar unidad nueva y aprobación falsificada; un
fallo preledger deja `sessions.jsonl` cerrado `failed` y bloquea reingreso.
La ruta exportada de cortes queda ligada a `...03`, sin caer en `...01`.

Las pruebas focales dieron **40 passed**, la suite completa **428 passed**
(323,19 s) y Ruff `All checks passed!`. La suite preliminar se interrumpió
tras corregir el orden de imports indicado por Ruff; se ejecutó de nuevo
completa sobre el código final. Estas pruebas no demuestran costo histórico,
supervivencia a logout ni entrenamiento bajo `systemd` para `...03`.
Comandos y logs en [COMMANDS.md](../evidence/oos-v1-2-wf-cost-03-profile/COMMANDS.md).

## Preflight de solo lectura

La [captura vigilada](../evidence/oos-v1-2-wf-cost-03-profile/preflight.json)
es de **2026-10-29 15:04:08 UTC**, commit `0446164`, SHA-256
`630cbf531a224eb1ea90badf2466d2f175baa0054397e1de44596654a4315911`.
Resultado `blocked`: CA conectada, pero batería 33 % frente al mínimo 50 %;
falta además la aprobación independiente. Memoria disponible 5.530.570.752 B
(mínimo 4 GiB), disco libre 152.001.093.632 B (mínimo 20 GiB),
`Linger=yes`, gestor `systemd --user=running`, ninguna campaña activa.
Presupuesto del 29/10: 0 s globales cargados y 8.100 s antes de la reserva;
no es una promesa de disponibilidad futura. Código, manifiesto, productos
exclusivos de entrenamiento y 3.639/4.678 inicios (5.764/7.703 filas de
ajuste) pasaron. El vigilante observó 43 rutas pertinentes, ningún CSV H1
compartido con 2023, validación o final; cero trayectorias y pasos.

La [consulta histórica](../evidence/oos-v1-2-wf-cost-03-profile/budget-failed-02-day.json)
del **27/10/2026 23:50 America/La_Paz** muestra que la bitácora fallida de
`...02` entra en el presupuesto compartido con
`failed_or_unclosed_session`, **10.800 s cargados** y saldo 0 ese día. Su
huella es
`72e790c0daf96a8da188e47b3791d759de625d170813fdc98c60d6ae888cb276`.
La consulta del 29/10 no carga ese fallo en un día distinto. El preflight
vigente sigue bloqueado por batería y ausencia de permiso.

## Preservación

El [cotejo archivo por archivo](../evidence/oos-v1-2-wf-cost-03-profile/frozen-roots-check.json)
confirmó 15/15 archivos de `...01` y 2/2 de `...02` idénticos al antecedente:
mapas SHA-256 `b93caafafd20b7a61f86214b5cbecba3ff7942d3862a467e1748d636b74a010a`
y `e11a6cfa872ed91ed5f9d0b30f429071b884846125c4df2a4a9d694a664257fd`.
La aprobación histórica de `...02` conserva
`c0d6973d98951dabe1cbc0cfef2f79304c2662cba01e09ff58276547c453f242`.
La eliminación local de `.python-version` quedó fuera de los commits.

**Siguiente decisión:** revisar perfil, pruebas, preflight y presupuesto. Una
campaña requerirá autorización nueva, registro fijado en commit separado,
recursos conformes y preflight inmediato; este hito no los proporciona.
