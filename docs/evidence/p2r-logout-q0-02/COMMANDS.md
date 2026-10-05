# Cierre documental Q0 sintética 02 — comprobaciones ejecutadas

El 05/10/2026 se inspeccionaron **en modo lectura** las raíces originales
`artifacts/p2r-synthetic-logout-q0-review-02` y
`artifacts/p2r-logout-q0-review-02-record`. Estado Git previo:
`codex/p2r-unit-integration` en `918c1d0`, con ` D .python-version` ajeno
conservado. No se llamó al ejecutor, no se inició una unidad, no se generaron
trayectorias ni se cargó mercado.

1. Se leyeron `prelaunch.txt`, estados de unidad, journal de `systemd --user`,
   journal exportado de logind, archivos de sesiones, ledger, manifiesto y
   journal P2R. La comprobación independiente con `.venv/bin/python` validó
   la cadena mediante `P2RJournal`, un único `InvocationID`, estado `ready`,
   ausencia de `pending`, frontera `after_q0` y coincidencia de SHA-256 de
   `state.pt` en manifiesto y ledger.
2. Se reconstruyó el intervalo a partir del journal de logind: retirada de
   sesión 40 `15:57:37.582970Z`, creación de sesión 54
   `16:51:58.504184Z`, duración `3260.921214 s`, 139 heartbeats P2R
   durante la ausencia, ningún evento de suspensión en ese intervalo. Q0
   terminó `16:09:34.879911Z`, antes del reingreso. `Result=success` quedó
   registrado en `after-unit.txt`.
3. Se calcularon todos los intervalos entre heartbeats: 174/174 >5 s;
   mínimo `5.033190 s`, mediana `5.1798705 s`, máximo `5.212391 s`.
   Lectura de `p2r_units.py`: `tick` compara contra 5 s y `supervise`
   sondea cada 0.2 s. Esto es una incidencia frente al requisito ≤5 s
   del protocolo, distinta del criterio de logout/no suspensión.
4. `find ... -type f -print0 | sort -z | xargs -0 sha256sum` produjo
   [SHA256SUMS.txt](SHA256SUMS.txt) para los **32 archivos originales**.
   `sha256sum -c` confirmó 32/32. Los cuatro hashes principales de la
   prueba 01 se recalcularon y coincidieron con el diagnóstico anterior.
   El archivo del greeter conserva las dos claves de timeout activas a 0
   y su SHA-256 coincide con `prelaunch.txt` de la prueba 02.

No se ejecutó la suite pytest ni Ruff: este cambio es documental y las
verificaciones pertinentes fueron de integridad, cronología y sintaxis del
informe. Los archivos originales bajo `artifacts/` no se editaron.
