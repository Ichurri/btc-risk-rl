# Ejecutor histórico P2R v2 — integración y verificación sin campaña

**Estado:** implementación para revisión; permiso de campaña inactivo.
Base `ccb010a`, commit de código `395c766`, rama
`codex/p2r-historical-executor`. El usuario autorizó
construir/verificar infraestructura, **no** generar trayectorias ni ejecutar
aprendizaje histórico. El protocolo metodológico P2R v2 sigue adoptado para
diagnóstico de desarrollo, separado de la evaluación confirmatoria.

## Contrato implementado

El perfil `P2RMarketSettings` deriva sus campos del JSON P2 congelado:
nueve corridas en el orden adoptado, semillas 610031/610047/610081,
K=10, Q400/A64/Q400/B400/D64, H180, actor dos épocas y crítico cuatro
provisionales. `d=0.10536051565782628` sigue común a C5 y C10; C0 conserva
Q/B auxiliares. No se cambió la lógica Q/A/B+D ni el cálculo diagnóstico D.

El supervisor común ahora puede avanzar entre corridas y asigna una unidad
Q0 seguida de diez unidades indivisibles Q/A/B+D por corrida. Acepta
exclusivamente `after_q0` y `after_dual_and_D`; comprueba deltas de
trayectorias, transiciones y pasos actor/crítico antes de registrar el
checkpoint. Los estados del actor/crítico, optimizadores, RNG, eta,
multiplicador, generadores y diagnósticos continúan en el checkpoint P2
versionado. Para P2R, el checkpoint se escribe en un directorio parcial,
se sincroniza y se publica mediante renombrado atómico; la aceptación
requiere además manifiesto, journal y ledger coherentes. Un parcial o un
checkpoint anterior de una campaña `failed` no permite reanudarla.

La entrada histórica `scripts/run_p2r_market.py` y el trabajador propio
rechazan la ejecución **antes** de leer solicitudes, datos o crear la raíz:
`MARKET_EXECUTION_ENABLED=False` y `REGISTRATION_SHA256=None`. Un JSON
editado y el comando por sí solos no conceden permiso. Una autorización
posterior necesitaría registrar un permiso P2R con huella fijada en un
commit separado. El trabajador exige token ligado al PID padre, roster,
unidad pendiente, hash de solicitud y ruta canónica `artifacts/p2r-approved-v2`;
no reutiliza el permiso ni la raíz P2.

La fuente es `TrainingMarket` con manifiesto H1 fijado: 7048 inicios,
muestreo uniforme con reemplazo, normalizador persistido sin refit y rutas
anteriores a 2023. El preflight de solo lectura compara huellas de protocolo
v2, adopción, configuración P2, H1, configuración TOML, código, paquetes,
datos/scaler y ledgers P0/P1/P2. Comprueba AC, batería, memoria ≥4 GiB y
espacio ≥10 GiB. La ejecución futura exigirá además `systemd --user` con
`Linger=yes`, un único escritor, hasta tres días activos, 10800 s globales
por día America/La_Paz, 900 s de preflight, 8100 s de trabajo y 1800 s de
reserva de cierre. Q0 tiene tope 1800 s; Q/A/B+D, 2700 s, con D ≤900 s.
El débito de una campaña externa fallida con unidad pendiente se considera
conservadoramente como día agotado.

## Preflight ejecutado sin trayectoria

El [registro completo](../evidence/p2r-historical-executor/preflight.json) se
tomó el **06/10/2026 15:32:01 UTC**. Reportó 7048 inicios aceptados,
última transición objetivo `1672516800000` ms UTC (antes del inicio de
validación), normalizador sin reajuste y cero observaciones de validación
cargadas. Huellas SHA-256: protocolo
`3372045783747399290cf2baa1e48c82f59c3e917d49f1e9f6ef8e1d08677f79`,
adopción `7b420e180620d5512aac0f7cf696ec38b075b4d4a56ac2a33540b6debb3dfe0b`,
manifiesto H1 `d7cd59b7cda003a0f69883a83a0bacf06a65c37f3653a2f466c249ddf41a6998`
y scaler `a598a99c368f1d50bba9f78fca2f803e46d77702d05547ccc12d076771e57479`.
En esa lectura había 8 292 823 040 bytes de memoria disponible y
182 421 082 112 bytes libres en disco; AC conectada y batería 100 %.
El saldo externo del día leído fue 0 s. Son medidas **del instante**, no
una reserva para otro día. El resultado registra `market_execution_enabled=false`,
`market_trajectories_generated=0` y `optimizer_updates=0`.
El registro se tomó con el código aún sin commitear; sus 50 huellas de
archivos coinciden con los bytes del commit de código posterior.

Los ledgers P0, P1 y P2 conservaron sus huellas SHA-256 fijadas. En
particular, P2 siguió en
`e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8`;
no se tocó su unidad parcial ni se reanudó. Las sondas 01–06 tampoco se
ejecutaron ni modificaron.

## Verificación y límites

Las pruebas sintéticas dirigidas cubren la equivalencia del supervisor con
el algoritmo existente, fronteras Q0/Q/A/B+D, dos corridas secuenciales,
reanudación desde fronteras completas, rechazo de perfiles/solicitudes,
fallo permanente tras SIGTERM, conservación de la huella anterior y
publicación atómica incluso si falla la escritura. Las pruebas de protección
verifican que el comando histórico y un JSON editado no activan mercado.
Los comandos y salidas reales están en
[COMMANDS.md](../evidence/p2r-historical-executor/COMMANDS.md).

**Límite de lectura del preflight:** el cargador H1 `training_only` verifica
SHA-256 de archivos de producto completos; algunos contienen también filas
de 2023. Esa verificación leyó sus bytes para integridad, aunque solo
materializó prefijos anteriores a 2023 y no cargó observaciones ni rutas de
validación. Si «no acceder a validación» incluye la lectura física para hash,
este punto requiere una variante de huellas de prefijo de entrenamiento
revisada **antes de activar** la campaña. No se usaron valores de validación
para aprendizaje, selección, diagnósticos ni resultados.

**No se probó una señal dentro de los cálculos del optimizador.** La sonda
systemd 06 terminó durante una espera sintética antes de esos cálculos;
las pruebas automatizadas de señal pueden interrumpir la unidad en otro
punto. Tampoco se midió el costo real de D histórico, continuidad ante
apagado físico ni comportamiento de aprendizaje con mercado. El preflight
deberá repetirse en la fecha de una eventual campaña y revisarse antes de
activar un permiso. La prueba final 2024–2025 permaneció inaccesible; no se
modificó la tesis.
