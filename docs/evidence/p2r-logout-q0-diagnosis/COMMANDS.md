# Comprobaciones de solo lectura, 05/10/2026

Rama inicial `codex/p2r-unit-integration`, HEAD `bbef10a`; estado inicial:
` D .python-version` (cambio local ajeno conservado). La rama local seguía a
`origin/codex/p2r-unit-integration`; no se hizo `fetch` en esta revisión.

- `sha256sum` de ledger, journal P2R, checkpoint y journal logind: los cuatro
  hashes coincidieron con `docs/hitos/P2R-logout-Q0-diagnostico.md`.
- Lectura Python de `supervisor.jsonl`: 176 heartbeats totales;
  156 posteriores a la retirada de sesión 2; último a
  `2026-10-05T15:12:05.811129+00:00`; máximo intervalo consecutivo
  5.184195 s; `unit_completed` a 15:12:06.230385 y `supervisor_exit` a
  15:12:06.239843. No había supervisor activo al suspenderse el equipo.
- Lectura de `logind-journal.txt`: retirada de sesión 2 a 14:58:46.909658,
  creación de `Debian-gdm` a 14:58:47.016172, anuncio de suspensión a
  15:13:47.765548, fin de suspensión a 15:17:37.997056 y sesión 40 a
  15:17:56.777722 UTC.
- `systemd-analyze cat-config systemd/logind.conf`: `IdleAction=ignore`
  aparece como valor por defecto comentado, sin drop-in local visible.
- Lectura de `/etc/gdm3/greeter.dconf-defaults`: opciones de suspensión
  comentadas; el propio archivo documenta `0=never`.
- Lectura de `/usr/share/glib-2.0/schemas/org.gnome.settings-daemon.plugins.power.gschema.xml`:
  tiempo AC por defecto 900 s y acción `suspend`.
- Lectura de `/usr/share/doc/gdm3/README.Debian`: ese archivo configura
  GSettings del greeter; los cambios requieren `invoke-rc.d gdm3 reload`.
- La consulta del journal completo con `sudo` desde la herramienta no pudo
  proseguir: solicitó contraseña. No se obtuvo identidad D-Bus del solicitante.
- Relectura independiente de hashes, ledger, manifiesto y secuencia UTC:
  `hashes=4/4`, `ledger=ready`, `boundary=after_q0`,
  `heartbeat_count_during_logout=156`, GDM→suspensión `900.749376 s`,
  Q0→suspensión `101.535163 s`, suspensión→reanudar `230.231508 s`,
  logout→retorno `1149.868064 s`.
- Extracción de los tres bloques `bash` de la repetición 02 y `bash -n`:
  `3/3` sintaxis válida; comprobadas la raíz/unidad 02, rechazo si existen,
  mínimo de 960 s y veto de suspensión. Enlaces relativos del informe y
  protocolos: existentes. `git diff --check`: sin errores.

No se ejecutaron pruebas sintéticas nuevas, supervisor, unidad ni entrenamiento.
La evidencia original bajo `artifacts/` no se editó.
