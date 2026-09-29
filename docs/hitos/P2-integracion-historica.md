# P2 — integración del perfil histórico aceptado; campaña inactiva

Base `5e81594` de `origin/codex/p2-infrastructure`, comprobada antes de editar;
rama `codex/p2-market-integration`. Alcance autorizado: integración, fixtures y
preflight de solo lectura. **No se autoriza ejecutar P2 ni optimizar con mercado.**
El diseño, ADR-002, los productos H1, P0 y P1 permanecen intactos. La eliminación
local previa de `.python-version` no forma parte de la entrega.

## Contrato conectado

`P2MarketSettings` exige por igualdad la configuración aceptada en
`P2-infrastructure-v1.json`: nueve corridas, K=10, semillas 610031/610047/610081,
orden rotado, N_A=64, N_Q=N_B=400, crítico de cuatro épocas provisionales,
actor de dos, D=64 por iteración, d=−ln(0,90), horizonte 180 y gamma=1.
No se creó otro algoritmo: `SyntheticExperiment` conserva Q/A/B y recibe
`TrainingMarket` solo con el permiso P2 específico. El supervisor usa una raíz
canónica, las nueve identidades de corrida y el mismo presupuesto global que
P0/P1. D usa otro `Collector` y exige un permiso válido incluso al invocar el
colector directamente; permanece la política congelada π_k, los objetivos MC
completos y la auditoría de que D no altere Q/A/B, redes, Adam, gradientes ni RNG
de aprendizaje. Los contadores de D son independientes, pero cuentan para
tiempo, memoria y límites de unidad.

La fuente es `TrainingMarket` con manifiesto H1 anclado, 7048 inicios uniformes
con reemplazo, scaler persistido y guardas de entrenamiento. El preflight
comprueba partición, inicio/fin, compatibilidad de configuración, huellas de
producto y scaler. Calcula SHA de archivos completos para detectar cambios;
esto no equivale a cargar observaciones numéricas de validación. La vista
numérica se restringió al prefijo de entrenamiento; no se pidió `environment()`.

`P2-market-registration-v1.json` queda **inactivo**, sin aprobación ni permiso.
Su huella está fijada en código y `MARKET_ACTIVATED=False`. Un JSON editado,
la CLI pública o una llamada directa a la unidad no pueden iniciar la campaña.
La ruta de supervisor/worker verifica registro y lease antes de abrir fuente o
crear archivos. La activación futura requeriría autorización explícita, revisión
y commit separado que modifique el registro y el guardia de código; no se
realizó aquí. Validación 2023 y final 2024–2025 no son fuentes disponibles en
esta ruta.

## Fronteras, fallos y presupuesto

Se preservan `after_q0` y `after_dual_and_D` como únicas fronteras reanudables.
Una muerte o D incompleto invalida la unidad; los fragmentos y diagnósticos
durables se conservan sin sustitución selectiva. La carga de checkpoint exige
permiso antes de leerlo, luego verifica perfil, procedencia y frontera mediante
el validador existente. El ledger registra por corrida y campaña trayectorias,
transiciones, actualizaciones y segundos; Q0 y Q/A/B+D tienen topes 1800/2700 s,
D subtope 900 s y watchdog de 10 GiB. El bloqueo global descuenta otras campañas
en el día America/La_Paz, con UTC en registros: 10800 s diarios, reserva 1800 s,
preflight 900 s, trabajo 8100 s, máximo tres días activos, tres sesiones por
corrida y 27 en campaña. No se abrieron ledgers de P2 mercado.

## Verificación de esta entrega

La suite usa fixtures H1 **fabricados** y la infraestructura sintética previa.
La ejecución final pasó **234 pruebas en 98,61 s** y Ruff sin errores.
Comprueba el rechazo de JSON alterado y de acceso sin lease antes de cargar
datos/salidas; identidad de H1, normalizador y partición; D sobre fixture con
π congelada y sin optimizador; presupuesto, reanudación, fallos y equivalencia
Q/A/B con D encendido/apagado mediante los tests sintéticos existentes. Los
comandos, salidas y el preflight completo están en
[`p2-market-integration`](../evidence/p2-market-integration/COMMANDS.md).

El preflight real informó 7048 inicios, primer/último objetivo
`1518796800000`/`1672516800000` ms UTC (antes de 2023), `fit_count=10073`,
`normalizer_refitted=false`, `validation_observations_loaded=false`, cero
trayectorias y cero actualizaciones. Manifest H1
`d7cd59b7cda003a0f69883a83a0bacf06a65c37f3653a2f466c249ddf41a6998`;
scaler `a598a99c368f1d50bba9f78fca2f803e46d77702d05547ccc12d076771e57479`.
El snapshot de presupuesto del 29/09/2026 La Paz halló 0 s cargados ese día;
es una fotografía de solo lectura, no reserva ni autorización. Memoria y disco
disponibles se consignan en el JSON, sin extrapolar rendimiento.

El presupuesto de aprendizaje calculado del diseño es 81 360 trayectorias y
5 760 de D, no ejecutadas. La aproximación de 5512,723 s deriva de medianas
P1 **solo para aprendizaje**; el costo real de D sobre mercado permanece sin
medir y no se sustituye por duración sintética. La primera medición temporal
histórica queda pendiente para una campaña autorizada, dentro de los topes
vigentes; no se generaron trayectorias históricas para medirla ahora.

La verificación de fixtures no demuestra calidad predictiva de D, mejora del
crítico fuera de A, rentabilidad, generalización temporal ni cumplimiento CVaR.
Cuatro épocas siguen como candidato provisional. No se seleccionaron
checkpoints, no se repitieron P0/P1, no se accedió a validación/final y la tesis
no se modificó.

## Comando futuro — NO EJECUTADO como campaña

```bash
uv run --frozen python scripts/run_p2.py --profile market --protocol docs/protocols/P2-infrastructure-v1.json
```

Actualmente termina bloqueado antes de cargar datos. El siguiente hito requiere
revisión de esta integración y autorización separada de activación/ejecución.
