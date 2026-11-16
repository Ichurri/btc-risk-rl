# P2R v2 — tiempos medidos y riesgo de presupuesto

**Análisis documental del 07/10/2026; P2R histórico no autorizado ni iniciado.** Se leyeron únicamente los ledgers y `unit-N.json` de P0, P1 y P2. El [cálculo reproducible](../../scripts/analyze_p2r_budget.py) exige sus SHA-256, comprueba estado, contadores y cada unidad aceptada, y publica [resultados numéricos](../evidence/p2r-budget-analysis/results.json). No se cargaron datos de mercado, pesos, validación ni prueba final; no hubo pasos de optimizador. P2 está `failed`: solo cuentan sus 57 unidades cerradas, nunca la unidad parcial de `run-05-C0`.

## Mediciones y denominadores

`seconds` es el tiempo de pared del ledger desde `begin` hasta `finish`, con carga, trabajo y guardado. Las medianas y rangos son de **unidades completas**, no de corridas independientes.

| Campaña | Q0: n, mediana [mín–máx] s | Q/A/B o Q/A/B+D: n, mediana [mín–máx] s | Suma de unidades s | Pared global cargada s |
|---|---:|---:|---:|---:|
| P0, K2, crítico 2, sin D | 9; 31,024 [29,025–32,029] | 18; 61,043 [58,039–67,041] | 1.384,957 | 1.385,677 |
| P1, K2, crítico 2/4, sin D | 18; 29,029 [27,031–30,021] | 36; 59,045 [56,042–61,042] | 2.649,085 | 2.650,523 |
| P2, K10, crítico 4, con D64 | 6; 29,038 [27,027–31,049] | 51; 69,067 [61,054–77,096] | 3.695,943 | **No recuperable** |

En P1, la mediana de las 18 iteraciones con cuatro épocas fue **59,044 s** y la de dos épocas **59,045 s**. La recolección y carga dominaron ese piloto; las medianas próximas no demuestran costo igual del crítico. P2 es el antecedente más próximo de Q/A/B+D: sus **51 fases D completas** sumaron **248,335 s**, mediana **4,801 s**, máximo **5,611 s**; la primera D tomó **4,604 s**. El guardado de esas 51 iteraciones sumó **50,095 s**. P2 cerró 11 iteraciones C0 y 20 de cada C5/C10; no inició la semilla 610081. P0/P1 no midieron D.

En esas unidades P2, la telemetría de fases nuevas midió Q **1.529,287 s
en 57 fases** (incluye seis Q0), A **222,248 s en 51**, B **1.360,610 s
en 51** y D **248,335 s en 51**. Actor y crítico sumaron 0,983 y
1,170 s, respectivamente, en 51 fases cada uno. Son tiempos del
algoritmo P2 y no incluyen por sí solos carga, guardado o el supervisor
P2R futuro.

Los `unit-N.json` repiten **telemetría acumulada** de la corrida. El script comparó cada prefijo con el informe anterior y sumó solo las fases nuevas; sumar todos los `report.telemetry` duplicaría tiempos. El cálculo también reconcilió los **3.695,943 s** y **248,335 s de D** con el cierre publicado de P2.

## Costos de supervisión medidos y límites de atribución

No todo tiempo fuera de `algorithm_seconds` pertenece al supervisor. La descomposición de unidades aceptadas es:

| Diferencia medida | P0 s | P1 s | P2 s | Qué incluye |
|---|---:|---:|---:|---|
| Pared global cargada − suma de unidades | 0,720 | 1,438 | indeterminada | Orquestación fuera de unidades; P2 carece de cierre fiable |
| Ledger `seconds` − `supervisor.wall_seconds` | 0,229 | 0,610 | 1,369 | Registro/admisión alrededor del proceso supervisado |
| `supervisor.wall_seconds` − `work_seconds` | 26,795 | 47,564 | 106,227 | Cola tras fin de trabajo, incluido guardado y salida del worker |
| `work_seconds` − `algorithm_seconds` | 51,414 | 93,866 | 201,262 | Carga, restauración y preparación dentro del worker; **no** es supervisor puro |
| `save_seconds`, incluido en la cola anterior | 0,555 | 1,143 | 50,469 | Guardado medido; P2 conserva trayectorias D numéricas |

La suma P2 de unidades **no** es tiempo global de campaña. El ledger quedó `running` al desaparecer el supervisor y luego se marcó `failed`; `active_seconds=0` indica cierre ausente, no duración cero. Se desconoce la duración de la parcial y del intervalo hasta detectar la interrupción. Tampoco puede atribuirse causalmente la diferencia P1–P2 a D: cambiaron corridas, estados, instrumentación y condiciones de ejecución. La fase D de P2 es una medición directa, no esa diferencia.

## Sensibilidad frente a 24.300 s

P2R requiere **9 Q0 + 90 Q/A/B+D = 99 unidades**. Tres días activos con hasta 8.100 s de trabajo cada uno permiten **como máximo 24.300 s** de ventanas de trabajo; el límite global es 10.800 s/día y la reserva de cierre 1.800 s/día. La media necesaria, antes de otros débitos y fragmentación diaria, es **<245,455 s por unidad**. Los topes de seguridad Q0=1.800 s y Q/A/B+D=2.700 s no son pronósticos: su suma para 99 unidades sería 259.200 s.

Estos son **escenarios aritméticos, no predicciones**. La base construye 9×Q0 + 90×iteración con medianas o máximos observados **solo en P2**. `δ` es un **supuesto** de segundos *incrementales por unidad* de P2R frente a la pared P2, que ya incluía su propia supervisión. Nadie ha medido `δ`. El saldo supone tres días íntegros, cero débito externo y empaquetado perfecto; no incorpora preflight, pausas de admisión ni pérdida de recursos.

La comparación es deliberadamente conservadora: usa `seconds` del ledger, que
**incluye guardado**, frente a una ventana de 24.300 s definida por las
marcas de fin de **trabajo**. En P2, `work_seconds` sumó 3.588,347 s frente
a 3.695,943 s de pared de unidad; al escalar sus medianas/máximos de
`work_seconds`, las bases serían 6.254,352/6.935,330 s. Parte del guardado
puede usar la reserva de cierre si el trabajo terminó a tiempo. Como no
se sabe qué fracción de `δ` correspondería a trabajo o cierre, la tabla
es una prueba de sensibilidad de pared, **no** una decisión exacta de
admisión del ledger.

| Base P2 | δ=0: total s | δ=30: total s | δ=120: total s | δ=180: total s | δ que agota 24.300 s |
|---|---:|---:|---:|---:|---:|
| Medianas (Q0 29,038; iteración 69,067) | 6.477,375 | 9.447,375 | 18.357,375 | 24.297,375 | 180,027 s/unidad |
| Máximos observados (Q0 31,049; iteración 77,096) | 7.218,059 | 10.188,059 | 19.098,059 | **25.038,059** | 172,545 s/unidad |

Con `δ=180`, la fila de máximos rebasa la **comparación de pared** con el
techo por **738,059 s**; la de medianas deja solo **2,625 s**. Esto es
una alerta de factibilidad, no prueba matemática de fracaso: el reparto
real de trabajo/guardado sigue desconocido. Los máximos P2 tampoco son
cotas futuras. La admisión inicial exige 1.800/2.700 s disponibles aunque
la unidad real pudiera ser breve. Después exige 1,5×el máximo completo
medido de igual condición/tipo, sin elevar topes. Por eso una suma inferior
a 24.300 s **no garantiza** que 99 unidades quepan en tres días. También
pueden existir débitos externos, menos tiempo antes de medianoche o pausas.

## Qué sigue sin medirse en Q/A/B+D de P2R

P2 midió Q, A, B, D y guardado en su ejecutor, pero **no** el incremento de P2R bajo `systemd --user`: heartbeats observados y `fsync` del journal cada ~4 s, verificaciones repetidas de alimentación/RSS/reloj, contadores publicados, carga desde el shard H1 exclusivo, identidad en cada worker, checkpoint atómico, cadena del ledger y cierre de sesión. Las sondas sintéticas verificaron integridad/cadencia bajo otras cargas, no ese costo histórico. Faltan 42 unidades que P2 no cerró: 3 Q0 y 39 iteraciones, incluida toda la semilla 610081. Se desconoce la variación allí de D y guardado, así como el débito externo, tiempo hasta medianoche y recursos **en una eventual fecha de campaña**. El apagado P2 impide estimar su pared global final.

## Regla de presupuesto y parada, fijada antes de P2R

1. **Hoy: no iniciar.** `MARKET_EXECUTION_ENABLED=False`, sin registro ni raíz de campaña; este análisis no altera el gate.
2. **Si se autoriza aparte:** al entrar cada día descontar el débito externo global y limitar `hard_deadline` al menor entre tres horas disponibles y medianoche La Paz; exigir preflight ≤900 s, trabajo ≤8.100 s y cierre reservado de 1.800 s. Conservar el saldo entre corridas y procesos. Rechazar huellas, recursos o lock incompatibles antes de abrir unidad.
3. **Antes de cada unidad:** si el tiempo hasta `work_deadline` no alcanza la admisión vigente (1.800/2.700 s sin medición; luego 1,5×máximo completo por condición/tipo, sin elevar topes), **pausar antes de crearla** en la última frontera completa. Continuar la misma campaña solo en otra sesión válida dentro de tres días activos y límites de sesiones.
4. **Dentro de unidad:** aplicar topes Q0=1.800 s, Q/A/B+D=2.700 s, D=900 s, RSS, heartbeat y reserva. Unidad parcial, señal, watchdog, identidad corrupta o invasión de reserva deja `failed`, evidencia intacta y **sin reanudación selectiva**. Si pasan tres días o sesiones máximas sin 99 unidades aceptadas, `incomplete`; no reducir D, alterar orden ni ampliar presupuesto.
5. Tras la **primera Q/A/B+D histórica** autorizada, registrar costo total y D por separado y actualizar solo el diagnóstico de factibilidad. Un escenario desfavorable es alerta, **no** licencia para cambiar parámetros ni descartar resultados.

La regla operativa es la admisión por unidad y los topes ya adoptados, no un umbral retrospectivo derivado de estas extrapolaciones. P2R seguiría siendo diagnóstico de desarrollo sobre entrenamiento 2018–2022; ningún escenario demuestra rentabilidad, generalización o CVaR poblacional.
