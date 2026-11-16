# Propuesta de estudio WF de costos íntegro y nuevo

**PROPUESTA PARA REVISIÓN; NO AUTORIZADA PARA EJECUCIÓN.** Esta medición
reemplazaría **íntegramente** el estudio parcial `...01`; no lo reanuda,
aprovecha ni combina con él. Tampoco adopta la evaluación fuera de muestra
v1.2. La raíz nueva propuesta es `artifacts/oos-v12-wf-cost-only-02/` y el
registro futuro sería
`docs/protocols/OOS-v1-2-wf-cost-replacement-approval.json`. Ambos deben
permanecer ausentes hasta una autorización posterior. El permiso operativo
actual sigue `MARKET_EXECUTION_ENABLED=False`.

## Dependencia y única modificación del diseño

El [protocolo de costos original](OOS-v1-2-costo-entrenamiento-cortes-v1.md)
(`SHA-256 f6d81fd9f10938aee29480c701a1a52c0b84eba1db0ea42a21d2d84c3004cbe4`)
y su [diseño](../protocols/OOS-v1-2-wf-cost-executor-v1.json)
(`SHA-256 66109d4400e04440c9450d1f1c0c7cc4332b66b9079703e3a1e62596032b5ad0`)
fijan expresamente la raíz `...01`. Esa cláusula es incompatible con una
campaña nueva. Este anexo propone sustituir **solo la identidad de raíz y
registro de aprobación**; las decisiones científicas y los límites se
heredan íntegros por la huella del diseño. El
[manifiesto candidato](../protocols/OOS-v1-2-wf-cost-replacement-proposal-v1.json)
permite comprobar que no aparecen otros cambios. El registro histórico
`OOS-v1-2-wf-cost-approval.json` y las cinco huellas de la ejecución parcial
se mantienen para auditoría; no pueden autorizar `...02`.

La nueva ejecución empieza desde Q0 para ambas corridas. Repetir el diseño
completo es una corrección prospectiva de infraestructura tras el defecto de
reingreso demostrado, **no** una repetición selectiva por resultados. La Q0
aceptada en `...01` no se incorpora a los 22 conteos ni al cálculo de costo
de `...02`. El tiempo y el fallo de `...01` se informarán por separado.

| Orden | Corte usado para entrenar | Semilla | Condición | Unidades |
| --- | --- | ---: | --- | ---: |
| 1 | 2018–02/12/2020 | 276696733 | C10 | Q0 + 10 Q/A/B+D |
| 2 | 2018–02/12/2021 | 498614892 | C10 | Q0 + 10 Q/A/B+D |
| **Total** | Dos fuentes y normalizadores propios | Dos semillas originales | C10 | **22** |

Se conservan β=0, cuatro épocas del crítico, K=10, D=64 por iteración,
Q/A/B, d=−ln(0,90), los tamaños de lote, horizonte, costos, recompensa,
muestreo y checkpoint solo en `after_q0`/`after_dual_and_D`. Los cortes se
derivan únicamente del H1 exclusivo de entrenamiento, con 3.639/4.678
inicios y 5.764/7.703 observaciones de ajuste respectivamente. No se abre
2023 ni la prueba final. No se seleccionan modelos ni se usan métricas de
rendimiento para decidir continuidad.

## Presupuesto y admisión sin doble cargo

La ejecución futura tendría como máximo **10.800 s globales por día** en
`America/La_Paz`, compartidos con otras campañas, con **2.700 s de reserva
de cierre**. Mantiene **3.600 s propios por día**, **5.400 s propios
acumulados** y **dos días activos**. La cota es 120 s por Q0 y 180 s por
Q/A/B+D: 2×120 + 20×180 = **3.840 s**. Quedan hasta 1.560 s del máximo
propio acumulado para preflight, reconstrucción de cortes, cambios de
unidad, auditoría y cierre. No es una estimación de duración: la campaña
parcial midió solo una Q0 y **ninguna** Q/A/B+D WF. Si la próxima unidad no
cabe con su cota íntegra y la reserva, pausa únicamente en frontera completa;
si se agotan dos días o el acumulado sin completar 22, `incomplete`. Nunca
se amplían límites ni se repiten unidades por sus tiempos o resultados.

El supervisor de `...02` debe iniciar su bitácora durable de sesiones tras
el permiso y el bloqueo global, **antes** del preflight completo y de cargar
ambos cortes. Para cada día se carga la unión temporal de sesión y ledger:
solo el tramo de bitácora fuera del intervalo ya imputado por el ledger se
añade a la admisión. El preflight y `P2RSharedBudget` deben leer también una
bitácora sin ledger. Las sesiones sin cierre impiden reingreso y cargan
conservadoramente 10.800 s en cada fecha alcanzada; los fallos cerrados son
irreversibles para esa raíz. Los cruces de medianoche se dividen por fecha
local, y ambas fechas cuentan para el límite de dos días. El preflight
verifica una misma identidad de roster tras serializar tuplas Python a listas
JSON y sigue rechazando cualquier semilla, condición u orden distinto.

El día de la campaña parcial tiene segundos previos al ledger no medidos en
él. Para no subcargarlos, el estudio nuevo **no podrá iniciar en ese mismo
día local**; si se pretendiera compartirlo, se imputarían conservadoramente
10.800 s a la campaña parcial y no habría admisión. Esta regla preserva el
ledger histórico y no cambia sus cifras.

## Puertas antes de una autorización o lanzamiento futuro

1. Revisar y aprobar expresamente esta sustitución de raíz/registro y la
   repetición íntegra de las dos corridas. Implementar un perfil ejecutor
   exclusivo de `...02`, con permiso independiente fijado en un **commit
   separado**. El perfil `...01` conserva su gate cerrado. Un JSON editado
   o la CLI, por sí solos, nunca habilitan la campaña.
2. Ejecutar preflight **nuevo y de solo lectura**: Git y código fijados;
   hashes del protocolo, diseño, manifiesto H1 y normalizadores; raíz `...02`
   y registro nuevo ausentes antes de autorizar; raíz `...01` y aprobación
   histórica íntegras; archivos abiertos limitados al derivado de
   entrenamiento y metadatos. Confirmar 3.639/4.678 inicios y los ajustes
   por corte, sin abrir CSV H1 compartidos con 2023.
3. Comprobar alimentación CA, batería ≥50 %, memoria disponible ≥4 GiB,
   disco libre ≥20 GiB, `Linger=yes`, gestor `systemd --user=running`, otra
   campaña inactiva y saldo global real, incluida la bitácora de sesiones.
   Son mediciones del instante, no garantías permanentes. Registrar UTC,
   `InvocationID`, fecha La Paz, archivo abierto y SHA-256.
4. Repetir en el perfil nuevo el ensayo sintético de Q0 aceptada → pausa de
   auditoría → proceso nuevo → admisión de unidad 1, rechazo de roster
   cambiado, fallo antes del ledger, huérfano y cruce de medianoche. La
   verificación de esta propuesta usa componentes con `tmp_path`; **no
   prueba todavía el ejecutor histórico de `...02` ni `systemd --user`**.
5. Solo con las puertas anteriores y una autorización posterior específica,
   ejecutar bajo un servicio nuevo `systemd --user`. Auditar Q0 de `...02`
   antes de continuar. Conservar ledgers, bitácora, journals, reportes,
   checkpoints y unidad parcial ante cualquier fallo.

## Aceptación y alcance del resultado

Cada unidad se acepta solo con fuente de entrenamiento exclusiva, ruta y
semilla previstas, política congelada donde corresponde, contadores y
marcador coherentes, reporte/checkpoint completos y hashes coincidentes,
sin exceder la cota ni el presupuesto. Una interrupción dentro de unidad,
registro incoherente, huella cambiada, pérdida de recursos o sesión sin
cierre produce `failed` irreversible. Una pausa es válida solo con
`ready`, sin `pending`, en `after_q0` o `after_dual_and_D`, y requiere
preflight nuevo antes de otra sesión. No se reemplaza una corrida fallida.
Se acepta como medición completa de costos únicamente `completed`, 22/22
unidades aceptadas, dos corridas C10 nuevas y auditoría de todos los cargos
globales y propios. `failed` o `incomplete` se informa tal cual.

El costo medido de estas dos C10 permitiría revisar una extrapolación de
tiempo para la propuesta v1.2, pero no probaría costo de C0/C5, viabilidad
de 36 bloques, rentabilidad, generalización ni cumplimiento CVaR. No
convierte el estudio en evaluación confirmatoria.

## Estado de esta entrega

El [preflight estático](../evidence/oos-v1-2-wf-cost-replacement/preflight.json)
queda **blocked** por ausencia deliberada de autorización y de perfil
ejecutor `...02`. Comprueba solo huellas y rutas, sin crear la raíz ni abrir
filas de mercado. Las [pruebas sintéticas](../evidence/oos-v1-2-wf-cost-replacement/COMMANDS.md)
ejercitan los componentes de reingreso y bitácora. La autorización de la
nueva campaña y su ejecutor histórico son decisiones y trabajo posteriores;
no se infieren de esta propuesta.
