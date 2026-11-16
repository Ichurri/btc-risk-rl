# WF `...05`: intento de reingreso del 02/11 bloqueado

**Resultado: no se inició ninguna unidad.** El preflight vigilado nuevo dio
`blocked` a las `2026-11-02T21:29:52.915844Z` (17:29:52 en
`America/La_Paz`) porque `MemAvailable=4.259.569.664 B`, **35.397.632 B
menos** que el mínimo fijo de 4 GiB (`4.294.967.296 B`). No se redujo el
umbral ni se repitió el preflight para buscar una lectura favorable.

## Estado comprobado antes de la suite

Rama `codex/oos-wf05-profile`, HEAD y origin
`4e2ab6a1b6c166711f7f75487f5255c7222a4166`. La eliminación local
previa de `.python-version` quedó fuera de Git. Ya era un día nuevo: 02/11
en La Paz; el 01/11 era el único día activo de los dos permitidos.

La auditoría publicada de la sesión 02 se reprodujo **byte por byte**:
ledger `ready`, **11/22** unidades aceptadas, `pending=null`, solo Q0 y las
diez actualizaciones `wf-2021`, ninguna `wf-2022`. Verifica cadena del
ledger, cada uno de los 11 reportes y checkpoints, contadores, fronteras,
bitácora, journal y huellas de las raíces `...01`–`...04`. La huella del
checkpoint `wf-2021/checkpoint-10/state.pt` siguió
`80626e96b6294492ca2ce116327f8ae32611f6419bede0219622cdb442f386cf`;
la del ledger siguió
`218ae4d4efad8f3440bb898a1f30f6ca33a09a26045c2b0bff0fe15c0303c1ba`.
No había ninguna unidad WF activa.

El presupuesto compartido leído antes de la suite indicó 0 s cargados por
otras campañas ese día y 8.100 s disponibles antes de la reserva global
de 2.700 s. WF05 había cargado conservadoramente 3.484,510403 s el día
anterior, incluidos intervalos entre sesiones, dejando 1.915,489597 s
del máximo propio acumulado de 5.400 s. La siguiente Q0 tiene cota de
120 s. Estos saldos eran suficientes **en la medición previa**, pero no
sustituyen la puerta de recursos del instante de lanzamiento.

## Verificaciones y puerta final

`uv run --frozen pytest -q` terminó con **463 passed in 390.45s**.
`uv run --frozen ruff check .` terminó con `All checks passed!`.
El preflight vigilado nuevo tuvo SHA-256
`cd3260e1ba5b76cd2aa959fd79d287dbb481ff75bfde51ade62000b63509ce4f`.
Registró CA conectada, batería 97 %, disco libre 133.235.302.400 B,
`Linger=yes`, gestor `systemd --user=running`, presupuesto externo 0,
huellas de código y entradas conformes, 1.920 archivos vigilados y **ninguna
apertura de CSV H1 compartidos ni de validación o prueba final**. Registró
cero trayectorias y cero pasos de optimizador. El único bloqueo fue la
memoria disponible de 4.259.569.664 B. En la medición anterior a la suite
había 4.814.450.688 B; esa diferencia demuestra que las muestras son
temporales, pero no identifica qué proceso consumió memoria.

El contador automático de presupuesto compartido informa 0 s para el
02/11 porque no se abrió una sesión de campaña. La suite consumió
390,45 s de pared fuera del ledger; ese tiempo **debe contabilizarse** al
evaluar el límite global del día, junto con preflight y cierre. No se lo
presenta como tiempo productivo de entrenamiento ni como saldo exacto
admisible. Aunque la memoria hubiera pasado, el gasto de comprobaciones
habría tenido que considerarse antes del lanzamiento.

El ledger y el checkpoint mantuvieron sus huellas tras el preflight. No
se creó unidad `systemd --user`, solicitud, trayectoria, reporte ni
checkpoint nuevo. El estado registrado sigue `ready`, 11/22 unidades y
ninguna pendiente. Un intento posterior dentro del 02/11 requeriría
suite/Ruff y preflight nuevos con recursos y presupuesto completos; esta
captura `blocked` no autoriza reingresar. Antes de planificar otra fecha
hay que adjudicar si las comprobaciones del 02/11 consumieron el segundo
día activo bajo el protocolo, pues se hicieron para la campaña y usaron
tiempo global aunque no abrieron ledger. **No se asumirá un tercer día**.
Si el máximo de dos días se agotó sin 22 unidades, corresponde informar
`incomplete` sin alterar retrospectivamente el ledger. Un ledger `failed`
no sería reanudable.

## Alcance académico

El corte 2021 tiene tiempos de costo observados en la sesión anterior;
**no existe medición del corte 2022** en este intento. Por tanto no se
puede sustituir todavía la extrapolación de ambos cortes ni decidir que
la propuesta de evaluación v1.2 cabe en 20 días. v1.2 sigue sin adopción
ni permiso. Este bloqueo de recursos no es resultado financiero ni prueba
de generalización o CVaR.

Comandos y hashes de capturas:
[`COMMANDS.md`](../evidence/oos-v1-2-wf-cost-05-reentry-blocked-20261102/COMMANDS.md).
