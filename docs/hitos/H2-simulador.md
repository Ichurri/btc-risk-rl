# H2 — simulador causal sobre desarrollo aceptado bajo B

Fecha: 21 de septiembre de 2026. Este hito implementa un entorno Gymnasium
sin agente, optimizador, entrenamiento ni acceso al conjunto final.

## Contrato implementado

Cada observación contiene las diez características de mercado de H1, en su
orden original y con su normalizador persistido, más peso BTC al cierre y
`log(E/E_inicial)`. Las doce componentes son float64; no se recorta el z-score.
La observación y el estado de cartera son del cierre t. La acción es un peso BTC
objetivo w en [0,1]; el tamaño de la orden se resuelve usando la apertura t+1,
antes de conocer su cierre. Se valora el resultado al cierre t+1.

Cada recorrido comienza con 10000 USDT y cero BTC. Solo spot, fracciones ideales,
llenado completo, sin mínimos, cortos, préstamo ni interés del efectivo.
La acción inválida se rechaza sin avanzar ni cambiar la cartera.

### Contabilidad de la exposición posterior a costos

Sean c el efectivo, q los BTC y p la apertura siguiente. El patrimonio previo
al intercambio es V=c+q*p. La exposición se mide al precio de referencia p,
no al precio ejecutado con deslizamiento. Con f=0.001 y s=0.0005:

- Compra: precio ejecutado p*(1+s); cargo de efectivo delta*p*(1+s)*(1+f).
- Venta: precio ejecutado p*(1-s); abono de efectivo cantidad*p*(1-s)*(1-f).
- Comisión: f*abs(delta)*precio_ejecutado, pagada en USDT.
- Pérdida por deslizamiento: abs(delta)*p*s. No se cobra de nuevo como comisión.

El tamaño satisface q_post*p / V_post = w con V_post posterior a ambos costos.
Para compra, k_b=s+f+s*f y delta=(w*c-(1-w)*q*p)/(p*(1+w*k_b)).
Para venta, k_s=s+f-s*f y cantidad=((1-w)*q*p-w*c)/(p*(1-w*k_s)).
El término cruzado f*s no se omite. El lado de la orden depende del peso
marcado a la apertura; no del peso anterior al cierre ni del cierre futuro.

Los saldos usan expresiones algebraicamente equivalentes que evitan cancelación
al invertir o vender el 100%. No se aplica clipping, redondeo a lotes ni tolerancia
para ignorar órdenes pequeñas. Se comprueban las identidades de efectivo, BTC,
patrimonio y peso con una tolerancia de 64 eps float64 proporcional al patrimonio;
si no se cumplen, se lanza error. La tolerancia compara, no modifica los saldos.
Sin operación se cobra cero. No hay comisión inicial ni final automática.

La recompensa es `log(E_cierre_siguiente)-log(E_cierre_anterior)`, neta de costos.
Incluye el movimiento entre cierre y apertura sobre la posición heredada. La suma
por recorrido coincide con `log(E_final/E_inicial)` dentro del error float64.
Esta identidad no prescribe un descuento de PPO ni un estimador CVaR.

## Datos, índices y cortes

`AcceptedMarket` exige estado `accepted`, revisa límites de la fuente antes de
acceder a páginas y ejecuta la auditoría de H1. Al cargar barras, observaciones,
episodios y transiciones vuelve a comprobar sus hashes. No ajusta ni escribe el
normalizador. Selecciona entrenamiento por `episode_id` aceptado; no acepta un
rango arbitrario de mercado o una partición final.

Los recorridos hacen copias de arrays de solo lectura y comprueban timestamps
integrales, alineados, contiguos y anteriores a 2024. Los objetivos pertenecen a
una sola partición y un solo segmento. Un contexto anterior a la frontera aporta
la observación inicial, sin puntuar retornos fuera de la partición.

Entrenamiento usa 180 transiciones y 181 estados. Validación usa sus 2190
transiciones seguidas, una sola cartera y un único reset inicial. No se fragmenta
en ventanas ni se concatenan carteras de segmentos.

Al agotar un recorrido se devuelve la observación real de cierre, `truncated=True`
y `terminated=False`. Se informa `collection_window`, `segment_boundary` o
`partition_boundary`; no se liquida ni se genera una transición adicional. Otro
step exige reset explícito. Las anomalías de contabilidad provocan error, no una
terminalidad económica inventada.

**ADR-002 sigue abierto:** los indicadores de truncación describen el corte de
recolección, no autorizan bootstrap, descuento ni uso de ventanas parciales para
CVaR. El caso de corte por interrupción requiere especial atención al resolver
ADR-002: no existe transición observada a través de ese hueco.

## Uso local sin entrenamiento

```python
from pathlib import Path
from btc_risk_rl.config import load_config
from btc_risk_rl.env.market import AcceptedMarket
from btc_risk_rl.env.trading import TradingEnv

config = load_config(Path("configs/initial.toml"))
data = AcceptedMarket(config, Path("data/raw/development"),
                      Path("data/processed/segmented-B-h1"))
env = TradingEnv(data.training_path(0), config)
observation, info = env.reset()
observation, reward, terminated, truncated, info = env.step(0.5)
validation = TradingEnv(data.validation_path(), config)
```

`MarketPath` también admite arrays sintéticos para pruebas unitarias, identificados
como tales; esa interfaz no convierte datos manuales en un producto aceptado.
El camino de mercado reproducible es el cargador auditado `AcceptedMarket`.

## Verificación

Las pruebas sintéticas incluyen un oráculo independiente Decimal de 60 dígitos
que encuentra el tamaño por bisección sobre flujos de efectivo; no reutiliza la
fórmula de producción. Cubren compra/venta total y parcial, costo cero, comisión
y deslizamiento por separado, carteras aleatorias deterministas, ausencia de
operación, acción inválida, precio siguiente, gap, datos futuros perturbados,
truncación sin venta, aislamiento de carteras y contrato Gymnasium.

El comprobador de Gymnasium advierte que los límites de las observaciones son
infinitos. Es intencional para z-scores y log patrimonio sin clipping; las pruebas
capturan esas dos advertencias y verifican que los valores reales sean finitos.

```bash
uv run --frozen python scripts/verify_installation.py --context local
uv run --frozen python scripts/verify_simulator.py --context local --output artifacts/simulator-h2/real
```

El segundo comando revisa todos los índices y ejecuta el primer y último episodio
de cada segmento apto, más una validación completa. Las acciones están prefijadas
como `WEIGHTS[(i//13+1)%6]`, con WEIGHTS=(0,.25,.75,1,.5,.9). Sirven para someter
la contabilidad a compras, ventas y exposición parcial; no se eligieron tras ver
resultados. Cada operación se contrasta con flujos de efectivo Decimal independientes.
Se conserva el libro de operaciones; no se suman rentabilidades entre episodios.

Evidencia pequeña versionada en `docs/evidence/simulator-h2/`; libro completo y
verificación real en `artifacts/simulator-h2/real/`, incluidos en el ZIP académico.
El informe de ejecución identifica plataforma, versiones, commit base, huellas
de código y fuentes, verificaciones, duración de pruebas y resultados reales.

Resultados locales ejecutados: configuración válida, Ruff pasa y **100 pruebas
aprobadas en 26.68 s** (41 nuevas sobre las 59 de H1). La comprobación funcional
revisó los 7048 índices; ejecutó 30 episodios de entrenamiento de los 15 segmentos
aptos y una validación continua de 2190 pasos: **31 recorridos, 7590 transiciones**.
Se ejercitaron los tres motivos de corte. Error máximo de efectivo frente al
cálculo Decimal: 3.637978807091713e-12 USDT. Error máximo de la identidad telescópica:
1.6653345369377348e-15. Las huellas de fuentes y escalador coinciden antes/después.
No se presentan estos recorridos como rendimiento de una estrategia entrenada.

## Límites y siguiente decisión

Continúan los supuestos ideales de llenado a apertura con deslizamiento fijo.
La cuarentena B no demuestra negociabilidad milisegundo a milisegundo y excluye
riesgo durante interrupciones. Este simulador no es un sistema de operación real.
No se modifican C0/C5/C10, las particiones ni el contrato de recompensa.
La siguiente decisión es cerrar ADR-002 antes de implementar PPO/CVaR-PPO o
planificar entrenamientos; no se adopta gamma, GAE-lambda ni regla de bootstrap aquí.
