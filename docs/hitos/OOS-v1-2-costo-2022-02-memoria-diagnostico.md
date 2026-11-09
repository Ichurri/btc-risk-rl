# Memoria en el fallo WF 2022-02 y puerta para 2022-03

**Diagnóstico de desarrollo, 09/11/2026.** Solo se leyeron el ledger, el supervisor, `systemd` y los artefactos existentes de `2022-02`. La raíz `2022-02`, su unidad parcial, el checkpoint 7 y las huellas del cierre no se modificaron. WF05 y `2022-01` permanecen cerrados.

## Observaciones del fallo

| Medición | Momento y fuente | Valor |
| --- | --- | ---: |
| `MemAvailable` | preflight histórico, 01:31:42; `preflight-321dcf05f18d4ee28e182b27bb03e07f.json` | 5.817.507.840 B |
| `MemAvailable` | guarda durante unidad 8, 01:41:53,967; `supervisor.jsonl` | 4.278.210.560 B |
| Mínimo exigido | contrato vigente | 4.294.967.296 B |
| Déficit en el fallo | cálculo sobre guarda | 16.756.736 B |
| Pico de memoria del cgroup de servicio | `systemctl --user show`, agregado de toda la sesión | 1.195.008.000 B |
| RSS del supervisor y trabajador | último heartbeat antes del fallo, 01:41:49,828 | 331.685.888 B y 516.231.168 B |

Entre preflight y fallo, `MemAvailable` cayó **1.539.297.280 B**. El servicio tuvo un pico agregado de 1.195.008.000 B, que no está fechado en el instante exacto del fallo. La suma de RSS del último heartbeat no es el consumo único del cgroup: puede contar páginas compartidas y omite caché y otros procesos del servicio. El RSS del trabajador creció desde unos 360 MB en la unidad 1 hasta 516 MB en la 8; el supervisor pasó de unos 280 MB a 332 MB. Estos valores demuestran mayor memoria residente de los procesos relevantes durante la sesión. No permiten atribuir el resto de la caída a un proceso concreto, ni dividir con exactitud memoria del servicio frente al resto del sistema.

El registro del supervisor identifica **la guarda de memoria**, no un OOM del kernel. CA, batería y disco seguían conformes. No se conservó una serie contemporánea de los demás procesos ni de caché, intercambio o presión de memoria durante la sesión histórica. `journalctl -k` sin privilegios no mostró eventos accesibles y `sudo -n journalctl` pidió contraseña; por tanto no hay una comprobación concluyente del kernel. Una lista de procesos tomada **después** del fallo figura en la evidencia de la sonda, solo como contexto actual, no como causa histórica.

Hipótesis abiertas: (1) crecimiento del trabajador y del cgroup, (2) demanda simultánea de aplicaciones ajenas, (3) cambios en caché/memoria recuperable y (4) combinación de ellas. La primera tiene apoyo parcial en los RSS; no hay datos contemporáneos para confirmar ni descartar las demás. No se modifican controladores, swap ni umbrales.

## Sonda controlada

La sonda se ejecutó bajo `systemd --user` con unidad y archivos independientes de cualquier campaña histórica. Duró **1125,926 s**, equivalente a la sesión fallida de 1123,821 s: primero la suite de base y luego carga anónima residente con objetivo de 1.195.008.000 B. Registró `MemAvailable` y `memory.current` del cgroup cada 2 s (máximo intervalo 2,029 s). La admisión de cada bloque de 16 MiB se detuvo si no quedaban 4 GiB + 512 MiB de margen. Alcanzar la carga objetivo y mantener ese margen durante suite y fase posterior es la puerta técnica conservadora propuesta para `2022-03`; el umbral operativo del supervisor sigue siendo 4 GiB. La puerta se documentó durante el diagnóstico, antes de activar cualquier permiso `2022-03`; no fue un criterio preinscrito antes de la sonda.

Los intentos de arranque de sonda 01–03 se conservan en `docs/evidence/oos-wf-2022-03-memory/`: 01 no encontró `pytest` al no fijar el directorio de trabajo; 02 y 03 fueron detenidos antes de completarse al corregir el comando y el tamaño de carga. La sonda 04 fue la primera observación completa. Sus archivos `probe-04.py.txt` y `probe-04.jsonl` permiten repetir el cálculo de mínimo, duración y memoria del cgroup. La suite en la sonda 04 ignoró únicamente la nueva prueba roja del perfil `2022-03`, aún no implementado al lanzarla; no es la suite formal de una campaña. Los scripts ejecutados se archivaron como `.py.txt`, sin cambiar sus bytes, para que Ruff no trate evidencia histórica como código operativo.

**Resultado de la sonda 04:** `InvocationID=a84c7ddf23024b5bb5a914b3159401c3`, 09/11 de 01:54:43 a 02:13:29 La Paz, `Result=success` como programa de medición. La suite de base registró **504 passed y 1 failed** en 493,00 s: la falla fue una aserción de prueba que esperaba ausente la raíz histórica `2022-02`; se corrigió después de la sonda para comprobar que el comando cerrado no la modifica. Esto no altera la medición de memoria; esa suite no se presenta como verificación formal correcta. La sonda ignoró solo la nueva prueba roja del perfil `2022-03`, todavía en implementación al lanzarla.

| Fase de sonda 04 | Muestras | Mínimo `MemAvailable` | Pico `memory.current` del cgroup | Muestras bajo 4 GiB | Muestras bajo 4 GiB + 512 MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| Suite, 0–494 s | 246 | **3.995.463.680 B** a 01:58:06 | 1.320.923.136 B | **34** | 101 |
| Carga posterior, 494–1126 s | 314 | 5.292.421.120 B a 02:04:24 | 2.068.516.864 B | 0 | 0 |

La carga posterior alcanzó **1.207.959.552 B** en bloques de 16 MiB, ligeramente por encima del objetivo por redondeo. Parte de esta fase coincidió con pruebas de desarrollo del perfil nuevo fuera del cgroup de la sonda; `MemAvailable` incluye esa actividad externa. El mínimo de la suite ocurrió **antes** de esas pruebas concurrentes. La sonda evidencia que el equipo puede cruzar el umbral aun durante la suite y que, en este intento, la fase posterior sostuvo la carga. **No cumple el criterio de margen sostenido para todo el intervalo**, y por tanto **no habilita `2022-03`**. No identifica cuál proceso ajeno causó la caída histórica: el cgroup y `MemAvailable` no descomponen los demás consumidores. No se cambian umbral ni límites. Una sonda nueva, limpia y conforme sería necesaria antes de activar el gate.

La **sonda 05** repitió el diseño sin pruebas de desarrollo concurrentes, con suite corregida, bloqueo global e inhibición de suspensión. `InvocationID=e8dfc608faf34c11b7e084903e26ed3b`; 09/11 de 08:08:11 a 08:26:58 La Paz, **1127,131 s**, `Result=success`. La suite dio **543 passed in 529,62 s**; la carga llegó también a **1.207.959.552 B**. En 264 muestras de suite, el mínimo fue **6.531.559.424 B**; en 296 muestras bajo carga, **4.870.426.624 B**. El pico `memory.current` bajo carga fue **1.530.118.144 B**. Máximo intervalo entre registros: **2,168 s**. Ninguna muestra estuvo bajo 4 GiB + 512 MiB (4.831.838.208 B); el mínimo quedó **38.588.416 B** por encima de ese margen. Esta repetición **sí cumple la puerta técnica medida**, de forma estrecha. Una nueva comprobación vigente de CA, memoria, gestor, presupuesto y huellas sigue siendo obligatoria en la fecha de lanzamiento.

Las dos sondas no son intercambiables ni se selecciona retrospectivamente solo la favorable: la 04 demostró un cruce real del umbral durante la suite; la 05 demostró que, con el estado posterior del host, una sesión de duración y carga equivalentes mantuvo el margen. En una captura durante la suite 04 figuraba `claude-desktop` con RSS aproximado de 895 MB; en otra posterior durante la carga 05 no figuraba entre los 25 mayores. Esto indica que la carga de aplicaciones visibles cambió entre capturas, pero no registra el momento de salida ni explica causalmente el fallo histórico de `2022-02`. La memoria de cgroup y `MemAvailable` también cambiaron de forma no proporcional; no puede asignarse el resto de memoria a un proceso concreto.

## Procedencia y reproducibilidad

- `artifacts/oos-v12-wf-cost-only-2022-02/supervisor.jsonl`: SHA-256 `ffc6b8f9f236e54c64b995708118f66d2bbeacd674d094d3e9024adaa02b2188`.
- `artifacts/oos-v12-wf-cost-only-2022-02/ledger.jsonl`: SHA-256 `9206afe1cf7a833d236977d0a71b8168648294e3c0a49d9827471aac5fb0e745`.
- Checkpoint 7: estado SHA-256 `618f9b45c42cf7e0976c1b8d6caadde39fddcfe1586a1173f3a5506295c9b0e1`.
- Comandos de lectura: `systemctl --user show oos-wf-cost-2022-02-session-01.service -p MemoryPeak -p Result -p InvocationID`; `python3` sobre las líneas JSON de `supervisor.jsonl` y la última línea de `ledger.jsonl`; `journalctl --user -u oos-wf-cost-2022-02-session-01.service --no-pager`.
- Sonda 04 ejecutada: `systemd-run --user --wait --unit=oos-wf-2022-03-memory-probe-04 --property=Restart=no /usr/bin/python3 /home/ichurri/Desktop/personal_projects/btc-risk-rl/docs/evidence/oos-wf-2022-03-memory/probe-04.py` (fuente archivada como `.py.txt`).
- Script de sonda 04 SHA-256 `36c865acae96d0139a03676517c61f757cbf9f4b311888d5c39aef351ddcb53f`; serie JSONL SHA-256 `450c41827b7f17f1d9b8ecb2032833fa61d01caf6e3bb895a2a7b1cb8c165c7a`.
- Sonda 05 ejecutada: `systemd-run --user --wait --unit=oos-wf-2022-03-memory-probe-05 --property=Restart=no /usr/bin/systemd-inhibit --what=sleep:idle --mode=block --why='WF 2022-03 controlled memory probe' /usr/bin/bash -c 'cd /home/ichurri/Desktop/personal_projects/btc-risk-rl && flock -n artifacts/shared-pilot-budget/global.lock /usr/bin/python3 docs/evidence/oos-wf-2022-03-memory/probe-05.py'` (fuente archivada como `.py.txt`). Script SHA-256 `9f945713f6ed3a24c1dd142db77950ec8dc88ee6c6938af5e4d84be8efe78356`; serie SHA-256 `207f5b3820aaa980b75000235f8b7963b82c96a8127694d5743be98eb7215e8a`.

El nuevo perfil se define en `docs/proposals/OOS-v1-2-costo-2022-reemplazo-03-v1.md`. Este diagnóstico no es una autorización para reingresar en `2022-02` ni una evaluación de políticas.
