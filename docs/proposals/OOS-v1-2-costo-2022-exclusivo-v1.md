# Propuesta de medición exclusiva del costo del corte 2022

**PROPUESTA PARA REVISIÓN; NO AUTORIZADA PARA EJECUCIÓN.** Parte del cierre
WF05 en `977e852`. WF05 sigue metodológicamente `incomplete` (11/22), con
ledger histórico `ready` y permiso operativo cerrado. Este protocolo propone
**una corrida nueva** para el corte 2022; no reanuda WF05, no incorpora su Q0
ni cambia sus artefactos. La evaluación fuera de muestra v1.2 sigue sin
adopción ni permiso. Los productos de 2023 y 2024–2025 permanecen cerrados.

## Identidad y alcance científico

| Elemento | Propuesta fija |
| --- | --- |
| Raíz exclusiva, ausente hasta autorización | `artifacts/oos-v12-wf-cost-only-2022-01/` |
| Registro de aprobación independiente, ausente | `docs/protocols/OOS-v1-2-wf-cost-2022-only-approval.json` |
| Bitácora de presupuesto previa al ledger, ausente | `artifacts/shared-pilot-budget/wf-2022-only-01-attempts.jsonl` |
| Fuente | Derivado H1 exclusivo de entrenamiento `data/processed/p2r-training-h1`; corte de entrenamiento anterior al 02/12/2021 UTC |
| Corrida | `wf-2022`, semilla de costo original **498614892**, C10, β=0, cuatro épocas del crítico, K=10, D=64 por iteración |
| Orden | Q0 → iteraciones 1,…,10 de Q/A/B+D: **11 unidades**, sin concurrencia |
| Fronteras aceptables | `after_q0` y `after_dual_and_D` únicamente |

Se conserva el contrato de acción, horizonte 180, γ=1, normalización por
corte, costos, recompensa, d=−ln(0,90), tamaños Q/A/B y generadores
separados del [protocolo original](OOS-v1-2-costo-entrenamiento-cortes-v1.md).
El corte 2022 tiene **4.678 inicios H180 y 7.703 observaciones de ajuste**
según la auditoría de desarrollo; el ejecutor futuro debe volver a comprobar
los recuentos y las huellas. Los 11 checkpoints y resultados del corte 2021
de WF05 sirven **solo como evidencia de costos**, nunca como estado inicial
de esta corrida. El resultado no selecciona una política ni mide rentabilidad.

El perfil ejecutor y el registro serán distintos de `...01`–`...05`. El
registro futuro debe fijar por huella esta propuesta, una configuración
ejecutable exclusiva, código/lock, derivado H1, normalizador e índices del
corte, raíz y semilla. Un JSON escrito o el comando público por sí solos no
habilitan el trabajador: gate de código inactivo hasta autorización
específica, tipo de permiso explícito y lease de unidad asociado al ledger.
Esta propuesta **no crea** el perfil ejecutor, el registro ni la raíz.

## Presupuesto propuesto y reparación de la contabilidad

El día es `America/La_Paz`; los eventos conservan timestamp UTC y reloj
monotónico. Se proponen **dos días activos como máximo**. Una fecha cuenta
desde la primera comprobación específica, aunque el preflight bloquee el
lanzamiento y aunque no se abra una sesión histórica. Los límites son:

| Límite | Segundos | Aplicación |
| --- | ---: | --- |
| Global diario compartido | 10.800 | Incluye otras campañas y toda actividad de esta medición |
| Reserva global de cierre | 2.700/día | La siguiente unidad solo cabe si queda íntegra después de la reserva |
| Propio diario, desde primera comprobación | 3.600 | Suite, Ruff, preflight, carga, supervisión, auditoría y cierre |
| Reserva propia de cierre | 600/día activo | Impide iniciar una unidad si su cota la invade; dentro, no adicional al tope |
| Propio acumulado | 4.800 en hasta dos días | Más estricto que los 5.400 s del estudio de dos cortes |
| Cota Q0 / cada Q/A/B+D | 120 / 180 | **1×120 + 10×180 = 1.920 s** de cotas de unidades |

La reserva acumulada inicial es **1.200 s** para poder cerrar dos días;
después de cerrar el primero se conserva 600 s para el segundo. Si todo
termina el primero, la parte no usada no se gasta. La reserva propia y la
global son **espacio libre exigido**, no segundos añadidos al gasto real.
Ninguna cota es una predicción del costo 2022.

La corrección exigida antes de cualquier autorización operativa es un
**orquestador de intentos** bajo el bloqueo global, separado del ledger de
unidades. Debe escribir y `fsync` un `start` durable en la bitácora indicada
**antes de leer huellas, inspeccionar recursos o lanzar la suite**. Toda
verificación de campaña, incluidos pytest, Ruff, preflight vigilado,
reconstrucción/carga, servicio `systemd --user`, auditoría y cierre, se
ejecutará dentro de un intento medido. El `end` guarda estado y ambos
relojes. Un nuevo día o intento requiere `start` nuevo. Si una comprobación
se hace fuera del orquestador, su costo debe reconciliarse con evidencia
temporal antes de admitir otra unidad; si no se puede acotar, se bloquea la
admisión de ese día. Así se evita repetir el contador artificial de **0 s**
que omitió la suite de 390,45 s de WF05 el 02/11.

Para cada día se calcula la **longitud de la unión** de intervalos de
intentos, sesiones y cobertura del ledger, con extremos semiabiertos. Los
tiempos de fase, pytest, Ruff, journal y checkpoint se muestran desglosados
pero no se suman de nuevo si ya están dentro de un intervalo cargado. Un
intervalo que cruza medianoche se divide en dos fechas locales, que cuentan
como dos días activos. El exceso de reloj monotónico sobre pared se carga
conservadoramente al día de cierre. Un intento sin `end` bloquea reingreso
y carga 10.800 s por cada día local alcanzado hasta la inspección; un fallo
dentro de una unidad deja ledger `failed` irreversible. El presupuesto
global compartido y el preflight deben leer esta bitácora aun cuando no
exista ledger ni raíz de campaña. La bitácora de presupuesto se crea solo
después de autorización, pero **antes** de cualquier comprobación de la
campaña. La lectura de una propuesta no constituye un intento.

Antes de Q0 y de cada iteración, bajo el mismo bloqueo se recalculan cargos
externos y propios. Para una unidad con cota `c` se exige simultáneamente:

```
gasto_global_día + c + 2700 <= 10800
gasto_propio_día + c + 600 <= 3600
gasto_propio_acumulado + c + reserva_propia_pendiente <= 4800
```

La `reserva_propia_pendiente` vale 1.200 s mientras pueden usarse dos días y
600 s en el segundo día. Se verifica además tiempo real hasta medianoche y
ausencia de otra campaña activa. La auditoría/cierre se miden y se cargan;
si consumen la reserva se informa el exceso, sin retroceder el ledger. Un
saldo automático de 0 sin bitácora válida **no** significa presupuesto
íntegro. Si una campaña anterior del mismo día tiene gastos previos al
ledger imposibles de acotar, ese día queda sin admisión hasta adjudicación;
no se reutiliza un preflight antiguo.

### Desglose de planificación, sin convertirlo en medición 2022

| Concepto | Segundos | Naturaleza y fuente |
| --- | ---: | --- |
| Suite completa inicial | 390,45 | **Medido en WF05 el 02/11**; solo referencia para una suite futura |
| Ruff, preflight, carga, auditoría intermedia | 300 | **Asignación supuesta** para explorar cabida; duración futura desconocida |
| Servicio 2022 Q0+10 iteraciones | 749,205481 × factor | **Extrapolación** de dos sesiones WF05 del corte 2021; incluye D y supervisión, no el intervalo entre sesiones |
| Cierre del día | 600 | **Reserva propuesta**, no tiempo observado |
| Cotas admitidas de las 11 unidades | 1.920 | Límite contractual, no predicción; la sobrecarga fuera de unidades se carga aparte |

| Escenario de costo del servicio 2022 | Servicio extrapolado | Total con 390,45 + 300 + 600 | Margen frente a 3.600 |
| --- | ---: | ---: | ---: |
| Igual a servicio 2021 (factor supuesto 1) | 749,205481 s | 2.039,655481 s | 1.560,344519 s |
| 1,5 veces | 1.123,808221 s | 2.414,258221 s | 1.185,741779 s |
| 2 veces | 1.498,410961 s | 2.788,860961 s | 811,139039 s |
| Todas las unidades en su cota | 1.920 s **de unidades**, no servicio medido | 3.210,45 s más sobrecarga de servicio no incluida en 300 | 389,55 s antes de esa sobrecarga |

Si hicieran falta dos días, otra suite de 390,45 s, otra asignación de
300 s y otra reserva de 600 s elevarían el escenario de cotas a
**4.500,90 s**, 299,10 s bajo el acumulado de 4.800 s, **solo si** no hay
sobrecargas o demoras adicionales. La admisión usa gastos reales, no esta
tabla. La fase D de WF05 2021 sumó 47,817987 s y **ya está incluida** en
el servicio y las unidades; no se vuelve a sumar. El corte 2022 podría
superar cualquiera de estos escenarios. No se infiere que 20 días de la
propuesta v1.2 sean suficientes.

## Puertas, pausas y aceptación

Antes de implementar/lanzar se requieren pruebas sintéticas del orquestador
real: primer intento → suite/Ruff/preflight → Q0 → pausa → proceso nuevo →
unidad 1; bitácora creada antes del ledger; descuento sin duplicar
solapamientos; gasto externo compartido; medianoche; intento huérfano;
fallo previo al ledger; raíz huérfana; identidad/huellas o lease alterados;
comando público y trabajador rechazados sin permiso. La suite completa y
Ruff deben pasar con el código **final**, antes del preflight nuevo.

El preflight vigilado de solo lectura de mercado debe verificar aprobación
y huellas fijadas, Git/lock, derivados/normalizador/índices 2022, 4.678
inicios, acceso exclusivamente al H1 de entrenamiento, archivos realmente
abiertos y ausencia de CSV H1 compartidos, validación 2023 y prueba final.
También exige CA, batería ≥50 %, `MemAvailable ≥ 4 GiB`, disco libre ≥20 GiB,
`Linger=yes`, `systemd --user=running`, ninguna otra campaña activa, raíz
nueva y presupuesto compartido íntegro. Las cifras de recursos se registran
en el instante de cada decisión y se repiten al reingresar. Un `blocked`
impide lanzar; su tiempo ya cuenta como día activo de esta medición.

La ejecución eventual usaría `systemd --user`, `Restart=no`, nombre e
`InvocationID` únicos por sesión. Una Q0 aceptada termina en `after_q0`;
una iteración aceptada termina en `after_dual_and_D`. Cada aceptación exige
fuente de entrenamiento exclusiva, contadores y marcador coherentes,
reporte y checkpoint completos, SHA-256, ledger encadenado y cota temporal.
La pausa solo ocurre entre unidades con ledger `ready`, `pending=null` y
checkpoint íntegro; el reingreso exige preflight y presupuesto nuevos. Un
fallo dentro de unidad, señal, pérdida de supervisor/recursos, reporte o
huella incoherente deja `failed`, sin repetición ni reanudación selectiva.
Si se consumen dos días, 4.800 s acumulados o el saldo diario sin terminar
las 11 unidades, el cierre metodológico es **`incomplete`**. No se amplía
ningún límite ni se escoge un checkpoint por resultado.

Tras `completed`, `failed` o `incomplete` se cerrará prospectivamente el
gate del perfil nuevo en un commit propio. El registro de aprobación y los
artefactos quedarán como evidencia histórica, sin habilitar otra ejecución.

La medición completa requiere 11/11 unidades aceptadas, ledger `completed`,
auditoría de bitácora/ledger/journals y presupuesto global/propio
reconciliado. Se publicarán por separado tiempo de unidad, D, sesión,
preparación, cierre, RSS, disco y cargos. Solo podrá informar el costo de
una C10 del corte 2022; no prueba tiempos de C0/C5, la viabilidad de 126
corridas, desempeño financiero, generalización ni CVaR poblacional.

## Estado de esta propuesta

Los [cálculos algebraicos y sintéticos](../evidence/oos-v12-wf-2022-cost-proposal/results.json)
comprueban el desglose y la unión de intervalos, **no** el ejecutor futuro.
Antes de solicitar permiso de campaña faltan: perfil aislado con gate cerrado,
orquestador/bitácora previa implementados en ambas rutas de presupuesto,
pruebas de integración indicadas, auditoría de huellas y preflight vigilado
actual. El permiso específico deberá otorgarse después de revisar esos
resultados. No se ejecutó ninguna unidad ni se abrió 2023/final.
