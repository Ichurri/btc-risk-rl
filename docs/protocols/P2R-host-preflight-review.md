# P2R: verificación separada del host antes de considerar mercado

**PROCEDIMIENTO PARA REVISIÓN; NO ES PERMISO DE CAMPAÑA.** Este documento
describe comprobaciones futuras. No cambia `systemd`, alimentación, memoria,
disco ni los umbrales de [P2R v1](../proposals/P2R-protocolo-v1.md). Las pruebas
sintéticas del supervisor no sustituyen una salida completa de sesión ni
demuestran supervivencia ante apagado físico.

## 1. Persistencia del gestor de usuario

En el host y usuario que ejecutarían la campaña, registrar hora UTC, UID y
salida de solo lectura de:

```bash
date -u --iso-8601=seconds
loginctl show-user "$UID" -p Linger -p State
systemctl --user is-system-running
```

La condición previa es `Linger=yes` y un gestor de usuario operativo. Si la
lectura falla o devuelve `Linger=no`, el preflight se bloquea. En la revisión
anterior se observó `Linger=no`; en esta integración la consulta actual de
`loginctl` desde el entorno de herramientas devolvió `Operation not permitted`.
Por tanto, **no se ha verificado `Linger=yes`**. Habilitarlo, si el usuario lo
decide, es una acción administrativa separada; este trabajo no ejecuta
`loginctl enable-linger` ni cambia el servicio.

## 2. Logout completo con trabajo sintético

Después de satisfacer la condición anterior y con una sesión de observación
externa preparada, lanzar **solo** una unidad sintética `p2r-*.service` bajo
`systemd --user` en una raíz nueva. Registrar nombre de unidad, invocation ID,
PID, cgroup, UTC, hash inicial del journal y estado del ledger. Cerrar **todas**
las sesiones interactivas de ese usuario; salir de Codex o del terminal
lanzador por sí solo no cuenta. Volver a iniciar sesión y comprobar mediante
`systemctl --user status`, `journalctl --user -u <unidad>`, journal P2R y ledger
que la unidad continuó después del último logout y llegó a una frontera
completa. Comparar tiempos UTC y hash de la cadena; comprobar ausencia de
worker huérfano. Hacer una segunda sonda con `SIGTERM` durante una unidad
sintética y verificar estado `failed`, sin checkpoint aceptado para esa unidad
ni posibilidad de reanudarla. Conservar comandos y salidas completos.

Estas pruebas requieren coordinación con el usuario porque implican cerrar
su sesión; **no se realizaron en esta integración**. Tampoco se simula un
apagado físico ni se atribuye al servicio una garantía contra pérdida de
energía. Una discrepancia, ausencia de registros o cadena corrupta bloquea
el futuro preflight, sin repetir selectivamente la unidad fallida.

## 3. Recursos mínimos y presupuesto

Medir en el momento del preflight y **antes de cada unidad** usando la raíz
real de artefactos, no `/tmp` ni una ruta alternativa más holgada:

```bash
cat /sys/class/power_supply/*/{type,online,capacity,scope} 2>/dev/null
awk '/^MemAvailable:/ {print $2 * 1024}' /proc/meminfo
df -B1 --output=avail <raíz-de-artefactos>
```

La comprobación automática `check_resources` distingue batería del sistema
de periféricos y rechaza sensores ausentes o incoherentes. Debe constar AC
conectada, batería legible ≥50 % en preflight y ≥40 % antes de unidad,
`MemAvailable` ≥4 GiB y espacio libre ≥10 GiB. El supervisor limita además el
RSS del worker a 10 GiB. Registrar valores y UTC junto con la admisión de
presupuesto: 10800 s globales por día America/La_Paz, reserva de 1800 s,
topes Q0/iteración y débitos de otras campañas. Una medición apta hoy no
garantiza disponibilidad en la fecha de una campaña.

Si un requisito falla, se informa y se espera una condición futura apta o
una nueva decisión metodológica explícita. **No se reducen los umbrales** ni
se declara aptitud a partir de fixtures. Este procedimiento solo prepara la
revisión del host; validación y conjunto final permanecen fuera de alcance.
