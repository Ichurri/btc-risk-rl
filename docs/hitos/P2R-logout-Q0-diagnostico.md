# P2R: diagnóstico del logout sintético Q0 (05/10/2026)

**Resultado dividido.** La unidad `p2r-logout-q0-review-01.service` completó
Q0 con `Result=success`, ledger `ready` y checkpoint `after_q0` mientras no
había ninguna sesión interactiva de `ichurri`. Por tanto, hay evidencia de
continuidad del supervisor **hasta la frontera Q0** tras logout. La condición
más fuerte, «sin suspensión desde la última sesión interactiva hasta el nuevo
ingreso», **falló**: Debian se suspendió después de Q0 y antes del retorno.
No clasificar los 156 heartbeats como prueba de vigilia durante toda la
ausencia. No hubo unidad P2R histórica ni entrenamiento de mercado.

## Hechos observados (UTC)

| Instante | Registro |
| --- | --- |
| 14:57:04 | Supervisor y Q0 sintética iniciados, invocation `d3e2ba8f26de47af872677c5fde15cbc`. |
| 14:58:46.909658 | logind retiró la sesión interactiva 2 de `ichurri`. La sesión 3 `Class=manager` podía persistir con `Linger=yes`. |
| 14:58:47.016172 | logind creó la sesión del greeter `Debian-gdm`. |
| 15:12:05.811129 | Último heartbeat P2R; los 156 posteriores al logout fueron anteriores al fin de Q0. El mayor intervalo entre heartbeats de la unidad fue 5.184195 s. |
| 15:12:06.230385 | `unit_completed` en `after_q0`; ledger `ready`, contador Q0 de 2 trayectorias y 360 transiciones, checkpoint íntegro. El supervisor salió a las 15:12:06.239843; systemd informó `Result=success`. |
| 15:13:47.765548 | logind: `The system will suspend now!`, 900.749376 s tras crear la sesión GDM. |
| 15:17:37.997056 | logind: `Operation 'suspend' finished`. |
| 15:17:56.777722 | Primera nueva sesión interactiva de `ichurri` (40). |

El intervalo sin sesión interactiva duró aproximadamente 19 min 10 s. La
suspensión ocupó aproximadamente 3 min 50 s de ese intervalo. Q0 había
acabado 1 min 41 s antes de la suspensión; por eso esta prueba **no** demuestra
que una unidad activa sobreviva una suspensión. Tampoco demuestra que un
trabajo P2R histórico sea seguro tras logout prolongado.

## Causa investigada

**Hipótesis principal, muy apoyada pero no demostrada por identidad de
llamador:** suspensión automática del greeter GDM por inactividad. El archivo
local `/etc/gdm3/greeter.dconf-defaults` tiene comentadas las cuatro opciones
de suspensión automática; el esquema instalado de GNOME asigna por defecto
`sleep-inactive-ac-timeout=900` y acción `suspend` (también en batería). La
pantalla GDM apareció a las 14:58:47 y la suspensión se anunció a las
15:13:47, exactamente 15 minutos después. El journal del mismo arranque
muestra otras suspensiones con cadencia cercana a 15 minutos tras despertar.
El propio `/usr/share/doc/gdm3/README.Debian` indica que el greeter usa
GSettings, que `/etc/gdm3/greeter.dconf-defaults` permite fijarlos y que
`invoke-rc.d gdm3 reload` aplica sus cambios. Esta inferencia **no equivale**
a haber leído la configuración efectiva de la cuenta `Debian-gdm` ni el
emisor D-Bus de la orden de suspensión.

**Alternativas menos compatibles:** `systemd-logind` tiene `IdleAction=ignore`
en el `cat-config` local, sin override visible; no explica un temporizador
propio de 900 s. Una acción de tapa, tecla, usuario u otro programa sigue
siendo posible porque el journal de logind registra la operación, pero no el
solicitante. No se dispone de journal completo privilegiado de esa ventana:
la lectura automatizada con `sudo` pidió contraseña. No usar ausencia de
entradas en el journal no privilegiado como evidencia de que no hubo eventos.

Antes de cambiar el host, el usuario puede conservar una copia de solo
lectura del contexto con este comando en su terminal (puede solicitar `sudo`):

```bash
sudo journalctl -b --since '2026-10-05 15:12:30 UTC' \
  --until '2026-10-05 15:14:10 UTC' --utc \
  --output=short-iso-precise --no-pager
```

Buscar mensajes de `gnome-settings-daemon`, `gdm`, `systemd-logind`, tapa,
tecla y `systemd-suspend`. Si no aparece el solicitante, mantener la
atribución a GDM como hipótesis fuerte; no elevarla a certeza.

## Corrección preparada, no aplicada

La corrección preferida es desactivar el **temporizador de suspensión por
inactividad del greeter**, tanto con AC como con batería, sin tocar el umbral
de recursos P2R ni `logind.conf`. Tras revisión administrativa, respaldar
`/etc/gdm3/greeter.dconf-defaults`, activar dentro de
`[org/gnome/settings-daemon/plugins/power]` estas dos claves y dejar
registrados antes/después, hora UTC y hash del archivo:

```ini
sleep-inactive-ac-timeout=0
sleep-inactive-battery-timeout=0
```

El propio archivo Debian documenta que `0=never`. Con sesión y trabajo
salvados, aplicar mediante `sudo invoke-rc.d gdm3 reload` según
`README.Debian`; esa recarga puede afectar la sesión gráfica y **no se hizo
en este diagnóstico**. Confirmar que la sección tenga una sola definición
activa de cada clave, registrar el resultado de la recarga y volver a
comprobar `Linger=yes`, gestor, energía, memoria y disco. Si la lectura
privilegiada revela otra causa, corregir esa causa primero y revisar esta
propuesta; no desactivar a ciegas otras protecciones de suspensión.

Se necesita una repetición sintética con **unidad y raíz nuevas** para
comprobar efectividad: [procedimiento 02](../protocols/P2R-logout-Q0-synthetic-review-02.md).
Mantiene 900 s de espera y Q0 para observar más de 15 minutos sin sesión,
exige ausencia de eventos de suspensión hasta el regreso, hashes y preflight
íntegros. Está **PREPARADA, NO INICIADA**. No reutilizar el ledger ni el
checkpoint de 01, ni cambiar configuración del host durante la unidad.
Una eventual prueba de señal dentro de unidad sigue siendo independiente.

## Conservación de evidencia

Las dos raíces locales de 01 quedan intactas:
`artifacts/p2r-synthetic-logout-q0-review-01` y
`artifacts/p2r-logout-q0-review-01-record`. Huellas SHA-256 comprobadas
de nuevo en esta investigación:

| Archivo | SHA-256 |
| --- | --- |
| `ledger.jsonl` | `522025cd72c5f97edc93e47cbc96868a1888d1d455bb3066086fc7d428438d79` |
| `supervisor.jsonl` | `935e05135f30307b371acb150e8f15166c1c23916b896f26f7581f10cab1fdb9` |
| `run-00-C5/checkpoint-0/state.pt` | `daeeee181be13e8627921edd39d19ad1e8a1daf6c68356f87b8a62b084165868` |
| `logind-journal.txt` | `d4057f7cdb6fcb7a62e2cd5d4a2415083f45726dd2517d5e8a033719a89d1923` |

Los archivos grandes se conservan fuera de Git. Esta revisión solo añadió
documentación; no lanzó otra unidad ni hizo pasos de optimizador.
