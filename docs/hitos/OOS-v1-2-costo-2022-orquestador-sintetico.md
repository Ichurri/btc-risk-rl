# Orquestador de presupuesto del estudio WF 2022 exclusivo

**Estado: infraestructura sintética verificada; campaña histórica no
autorizada.** Se implementó el mecanismo de contabilidad definido en
[`OOS-v1-2-costo-2022-exclusivo-v1.md`](../proposals/OOS-v1-2-costo-2022-exclusivo-v1.md)
sin crear la aprobación, la raíz histórica ni la bitácora real. WF05
permanece cerrada e intacta. La evaluación fuera de muestra v1.2 no se
activó.

## Contrato implementado

[`wf_cost_2022_orchestrator.py`](../../src/btc_risk_rl/pilots/wf_cost_2022_orchestrator.py)
fija la identidad nueva `oos-v12-wf-cost-only-2022-01`, 11 unidades, cotas
120/180 s, 3.600 s propios diarios, 4.800 s acumulados, dos días activos,
600 s de reserva propia diaria y 2.700 s globales diarios para cierre.
La aprobación prevista es independiente de WF05 y el gate del nuevo perfil
permanece `False`, con SHA de registro `None`. El
[comando público](../../scripts/run_oos_wf_cost_2022.py) rechaza `--run`
antes de cargar datos o crear artefactos; **no contiene todavía un ejecutor
histórico**.

`BudgetAttempt` hace solo la comprobación estática del gate antes de escribir.
Con el bloqueo global adquirido, crea y sincroniza `start` en
`artifacts/shared-pilot-budget/wf-2022-only-01-attempts.jsonl` antes de
verificar el registro y antes de ejecutar cualquier comprobación. Los
eventos de comprobación se encadenan por SHA-256 y se sincronizan en una
bitácora separada. Un preflight bloqueado cierra el intento como `ready`
con motivo y consume su tiempo; un fallo de integridad lo cierra `failed`
y prohíbe reingreso. Una interrupción que deje `start` sin `end` bloquea
reingreso y se imputa conservadoramente como 10.800 s en cada fecha local
alcanzada. La huella y la cadena se revisan al abrir otro intento.

`reconcile` calcula la unión, con intervalos semiabiertos, de intento,
sesión supervisada y cobertura de ledger para cada día de
`America/La_Paz`. Usa el mayor exceso monotónico sobre tiempo de pared al
cierre y evita sumar dos veces pruebas o D si ya caen dentro de la
supervisión. Tanto el escáner de presupuesto compartido
`P2RSharedBudget` como el preflight de lectura `wf_cost.inspect_budget`
reconocen la bitácora nueva **incluso sin ledger**, y descuentan solo el
tramo adicional a sesiones y ledger. Estas rutas quedan inertes mientras
la bitácora futura no exista.

Antes de llamar un callback de unidad, `run_unit` exige una frontera
completa y verifica simultáneamente saldo propio diario, acumulado, saldo
global compartido, las dos reservas y tiempo hasta medianoche. Devuelve
`pause` o `incomplete` sin llamar el callback cuando no cabe la cota. Si
una unidad excede 120/180 s o pierde recursos una vez empezada, el intento
queda `failed`. El futuro ejecutor deberá **aceptar reporte/checkpoint solo
después** de que `run_unit` devuelva sin error, y mantener el fallo
irreversible en su ledger propio.

## Verificación ejecutada y alcance

Las [17 pruebas focales](../../tests/test_oos_wf_2022_orchestrator.py)
usan relojes y raíces temporales. Cubren primera comprobación anterior al
ledger, solapamiento de tres fuentes, cruce de medianoche, tercer día,
intento huérfano, fallo previo al ledger, preflight bloqueado y reingreso,
saldo global/propio, reservas, unidad no iniciada, cota excedida, pérdida
de recurso dentro de unidad, escáneres compartidos y registro falsificado.
No generaron trayectorias ni ejecutaron optimizadores. La suite completa
terminó **481 passed en 346,55 s** y Ruff pasó. La suite completa incluye
pruebas previas del repositorio; solo la prueba focal nueva verifica este
orquestador con datos sintéticos.

La auditoría de solo lectura repitió la huella de los 2.647 archivos WF05:
`0d034efccb2138c4fb975c86e504763ff69ce331f2a5fdbb9919f4e1d06931eb`.
La raíz, aprobación y bitácora previstas para 2022 siguen ausentes. WF05
conserva `MARKET_EXECUTION_ENABLED=False`; el nuevo perfil también.
El comando público nuevo salió con código 1 y `NOT AUTHORIZED`. Ver
[`COMMANDS.md`](../evidence/oos-v12-wf-2022-orchestrator/COMMANDS.md)
para comandos y resultados observados.

Los **346,55 s** de la suite son costo de implementar/verificar este hito
el 04/11/2026; no son costo medido del corte 2022 ni saldo gastado de la
eventual campaña. Cuando haya aprobación específica, su reloj empezará de
nuevo desde la primera comprobación de *esa* campaña, antes de la suite.
No hay estimación medida de Ruff, preflight, auditoría y cierre del futuro
perfil. Las asignaciones de 300/600 s de la propuesta siguen siendo
supuestos/reservas.

## Limitaciones y procedimiento para una autorización futura

Esta entrega **no** integra un trabajador histórico 2022, AcceptedMarket,
reconstrucción/refit del corte, checkpoints ni servicio `systemd --user`.
Por tanto, las pruebas de presupuesto no prueban todavía el ciclo histórico
Q0→Q/A/B+D, la verificación de archivos abiertos ni una interrupción real
durante optimización. `strace` no estaba disponible para vigilar aperturas;
esa comprobación sigue pendiente. Tampoco se midieron los recursos del
equipo para una futura admisión.

Antes de solicitar ejecución se debe:

1. Integrar el trabajador/supervisor **solo** para el corte 2022, con lease,
   11 unidades, indicadores de mercado y checkpoints auditables. Pasar el
   corte y la unidad exclusivamente por `BudgetAttempt.run_unit`; ninguna
   ruta alternativa debe aceptar una unidad.
2. Probar con fuentes controladas en procesos distintos Q0→pausa→unidad 1,
   rechazo de raíz/huellas/permiso alterados, fallo de preflight anterior al
   ledger e interrupción dentro de unidad. Auditar que el callback no puede
   aceptar unidad parcial después de una cota excedida.
3. Congelar código, lock, protocolo, configuración, derivado H1, normalizador
   e índices en un registro **nuevo**, ligado a la raíz/semilla/C10. Verificar
   preflight vigilado: solo entrenamiento del derivado H1, 4.678 inicios,
   7.703 filas de ajuste, ninguna apertura de CSV H1 compartidos,
   validación ni prueba final. Comprobar CA, batería ≥50 %, `MemAvailable`
   ≥4 GiB, disco ≥20 GiB, `Linger=yes`, gestor `running` y presupuesto
   compartido al instante.
4. Pedir **autorización específica posterior**. Solo entonces fijar la
   huella del registro y activar el gate nuevo mediante commit separado;
   WF05 continúa cerrado. Iniciar el orquestador autorizado bajo el bloqueo
   global, registrar `start`, ejecutar suite, Ruff y preflight dentro del
   intento, y solo con `ready` lanzar una sesión `systemd --user` con
   `Restart=no` e `InvocationID` único. Auditar Q0 antes de continuar y
   reingresar solo desde fronteras completas con nuevo intento/preflight.
5. Cerrar como `completed`, `failed` o `incomplete` según las 11 unidades,
   días y saldos, reconciliar bitácora/ledger/journals y cerrar el gate
   prospectivamente. Ningún checkpoint anterior permite reanudar `failed`.

No se ejecutó C10, no se abrió validación 2023 ni prueba final 2024–2025.
