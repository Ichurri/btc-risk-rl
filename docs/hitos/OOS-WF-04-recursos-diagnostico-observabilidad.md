# WF `...04`: diagnóstico de recursos y observabilidad prospectiva

**Dictamen:** el supervisor rechazó una lectura de recursos durante Q de la
unidad 8 el 30/10/2026 a las 02:13:15 `America/La_Paz`
(06:13:15 UTC). **No se puede identificar cuál recurso** incumplió la guarda
con la evidencia conservada. La campaña sigue `failed`, sin reanudación ni
repetición. Las raíces `...01`–`...04` y sus permisos cerrados permanecen
intactos.

## Hechos y cronología

El [ledger y supervisor originales](../evidence/oos-v1-2-wf-cost-04-session-02-20261030/audit.json)
registran ocho unidades aceptadas en total y `pending.unit=8`. La unidad 7
terminó a las **02:12:37,771**, y la unidad 8 comenzó a las
**02:12:37,898**. El último heartbeat de la unidad 8 fue a las
**02:13:10,931**, fase Q, con `rss_worker=514.101.248 B` y
`rss_supervisor=300.507.136 B`. En ese heartbeat aparecen contadores de
progreso del trabajador (64 pasos de actor y 128 de crítico), **no
contadores aceptados**; el ledger conserva 56 y 112, respectivamente.
El journal registra `supervisor_exit` `failed` a las **02:13:15,088** y el
[journal de systemd](../evidence/oos-v1-2-wf-cost-04-session-02-20261030/systemd-journal.txt)
muestra la excepción `WF cost resources lost during unit` en el callback
`tick`, seguida de `Result=exit-code`, código 1 a las **02:13:15,455**.
El pico de memoria del servicio fue **846.553.088 B**; es uso del servicio,
no memoria disponible del sistema. No hay reporte ni checkpoint aceptado
para la unidad 8.

El [preflight](../evidence/oos-v1-2-wf-cost-04-session-02-20261030/preflight.json)
de las **02:04:36** midió CA conectada, batería 97 %, `MemAvailable`
5.296.250.880 B y disco libre 144.849.342.464 B. Una
[lectura posterior](../evidence/oos-v1-2-wf-cost-04-session-02-20261030/host-after.json)
de las **02:24:36** midió CA=1, batería 97 %, `MemAvailable`
7.734.751.232 B y disco libre 144.144.793.600 B. **Ninguna de estas dos
lecturas mide el instante 02:13:15.** Los heartbeats registraban RSS y
progreso, pero no CA, batería, `MemAvailable` ni espacio libre. El código
histórico llamó `resource_ready(_unit_resources())` y descartó esa muestra
antes de lanzar un error genérico; esta ausencia de observación está
demostrada. El recurso que causó el rechazo sigue desconocido.

Se consultó el journal accesible de `systemd --user` y la ventana general
02:12:30–02:13:45. No apareció allí un valor contemporáneo de alimentación,
memoria disponible o disco. El journal del kernel devolvió `-- No entries --`
sin privilegios; `sudo -n journalctl` no pudo abrir el journal completo
porque requiere contraseña. Por tanto, **la falta de eventos visibles no
descarta eventos del kernel**. `upower.service` y `systemd-logind.service`
devolvieron `-- No entries --` en la ventana consultada sin privilegios.
`/var/log/sysstat/sa30` corresponde al **30/09/2026**, no al 30/10;
no ofrece una muestra de memoria del fallo. Tampoco se encontró un registro
de disco contemporáneo. Véanse [comandos y salidas pequeñas](../evidence/wf04-resource-diagnostic-20261030/COMMANDS.md).

## Corrección prospectiva

La función `resource_ready` y sus umbrales **no cambiaron**: CA requerida,
batería ≥50 %, `MemAvailable ≥4 GiB` y disco libre ≥20 GiB. En cada lectura
que causa una pausa entre unidades o un fallo durante una unidad, el
supervisor añade **antes de actuar** un evento `resource_guard_failed` al
journal encadenado y sincronizado. El evento guarda la muestra exacta usada
por la decisión, límites, comprobaciones fallidas, unidad, fase y destino
`pause`/`fail`. Si no se puede leer la alimentación, conserva los valores
sentinela que ya hacían fallar la guarda y marca explícitamente
`values_observed=false` y el error de sensor, para no presentarlos como
mediciones reales. Una muestra conforme no genera un evento de fallo.

Las [pruebas sintéticas](../evidence/wf04-resource-diagnostic-20261030/COMMANDS.md)
cubren por separado CA desconectada, batería 49 %, memoria y disco a un byte
del mínimo, los cuatro límites exactos, la pausa con cuatro fallos, la
persistencia de la cadena del journal, un sensor de alimentación ilegible y
la preservación de un ledger/checkpoint sintéticos. La comparación de
huellas de las cuatro raíces reales antes y después confirma que ninguna
fue modificada. No se lanzó una unidad histórica ni se probó una transición
real de alimentación o presión de memoria; esta instrumentación no explica
retrospectivamente el recurso de `...04`.

La prueba focal final dio **7 passed en 0,83 s**; la suite completa dio
**454 passed en 302,01 s** y Ruff pasó. Los [resultados de lectura](../evidence/wf04-resource-diagnostic-20261030/results.json)
tienen SHA-256
`866987791f96d9f8ce1ccfd2c82e22adda320962d0ee029307062cdca46db95c`;
el [script](../evidence/wf04-resource-diagnostic-20261030/checks.py),
`8f4352cb43c76ea8d5fe5a194b405903638a4094e6a5ad0de454070ad4e78b60`.
La auditoría compara las cuatro raíces archivo por archivo y no lee
observaciones de validación ni prueba final.

Los permisos `...01`–`...04` siguen cerrados. Este hito no prepara una raíz
nueva ni autoriza entrenamiento o evaluación fuera de muestra. Validación
2023 y prueba final continúan protegidas.
