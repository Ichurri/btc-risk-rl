# WF 2022-02: cierre del intento independiente

**09/11/2026, America/La_Paz. Estado `failed`; no reanudar.** Esta fue una medición de costo de entrenamiento sobre el derivado exclusivo de entrenamiento, no una evaluación financiera. La propuesta v1.2, validación 2023 y prueba final siguieron cerradas.

## Preparación y ejecución

Rama `codex/oos-wf-2022-02`. El perfil aislado quedó en `7da17ad` y su autorización independiente en `a118476`, con aprobación SHA-256 `940d5da7088b6b93901f7747dd1201f013ede7eabd9ddc43f4afa3ffd1be051f`. `2022-01` conservó su cierre y su cargo del 07/11; WF05 conservó su ledger. Antes del lanzamiento, la prueba de suite bajo `systemd --user` con bloqueo global reprodujo una falla contextual (504 passed, 1 failed). Se corrigió esa prueba y una sonda `systemd --user` con el mismo bloqueo pasó (1 passed). La suite completa fuera del servicio pasó (505 passed) y Ruff pasó.

Comando histórico ejecutado el 09/11 a las 01:23, con `Restart=no`:

```bash
systemd-run --user --wait --unit=oos-wf-cost-2022-02-session-01 --property=Restart=no /usr/bin/systemd-inhibit --what=sleep:idle --mode=block --why='WF 2022-02: conservar supervisor despierto' /usr/bin/bash -c 'cd /home/ichurri/Desktop/personal_projects/btc-risk-rl && /home/ichurri/.local/bin/uv run --frozen python scripts/run_oos_wf_cost_2022.py --prepare && /home/ichurri/.local/bin/uv run --frozen python scripts/run_oos_wf_cost_2022.py --run'
```

`InvocationID=df1313adea4e400996fa4982229099ca`. La suite **formal dentro del servicio** pasó: **505 passed in 503,45 s** (comprobación duradera 505,073 s); Ruff pasó en 0,040 s. El preflight vigilado pasó en 2,936 s, sin aperturas de CSV H1 compartidos ni protegidos; CA conectada, batería 100 %, `MemAvailable=5.817.507.840 B`, disco libre 128.164.413.440 B, `Linger=yes`, gestor `running` y admisión presupuestaria conforme. El corte de entrenamiento fue reconstruido y verificado. La primera bitácora de preparación midió **508,788 s** y cerró `ready`.

La segunda bitácora cubrió el supervisor y terminó `failed` después de **612,339 s**; su sesión interior midió **611,202 s**. El servicio cerró 01:41:54, `Result=exit-code`, código 1, con **1123,821 s** de tiempo de pared total y memoria pico de **1.195.008.000 B** atribuida al servicio. Los dos intentos durables suman **1121,127 s medidos**; no se suman nuevamente los 611,202 s interiores. Estas cifras son costo de proceso, no rendimiento del modelo.

## Unidades y causa

El ledger acepta **8/11 unidades**: Q0 y Q/A/B+D 1–7. Sus tiempos medidos de admisión a aceptación, en segundos, fueron `31,704; 72,023; 72,353; 73,245; 81,069; 76,624; 87,308; 79,115`, suma **573,441 s**. Los contadores aceptados son 56 actualizaciones de actor, 112 de crítico, 448 trayectorias diagnósticas y 6.448 trayectorias de aprendizaje. La unidad 8 empezó, quedó `pending` y **no tiene reporte ni checkpoint aceptado**. La última frontera completa es `checkpoint-7`, `after_dual_and_D`, con `state_sha256=618f9b45c42cf7e0976c1b8d6caadde39fddcfe1586a1173f3a5506295c9b0e1`, coincidente con el ledger. Conservarlo no habilita reanudar un ledger `failed`.

A las **01:41:53,967** el supervisor registró `resource_guard_failed` para `memory`: `MemAvailable=4.278.210.560 B`, inferior al mínimo de **4.294.967.296 B** por **16.756.736 B**. Registró CA `true`, batería 100 % y disco libre 128.101.511.168 B; esos tres controles no fallaron. La lectura inicial del preflight y la lectura durante el fallo son momentos distintos. La excepción fue `WF 2022 resources lost during unit`. El supervisor marcó el ledger `failed`, `pending=8`; `systemd` indicó `Result=exit-code`. No queda proceso trabajador activo. No se repitió la unidad 8 ni se seleccionó un checkpoint por desempeño.

El cargo propio medido incluye las dos bitácoras anteriores. Para la **contabilidad global conservadora del 09/11**, el ledger fallido con unidad pendiente consume **10.800 s** y deja **0 s disponibles** ese día; el intervalo medido no sustituye ese cargo. No se lanza otra campaña el 09/11. El gate `2022-02` se cerró prospectivamente en `dbadf34`; la aprobación y los artefactos originales siguen intactos. El comando público y el trabajador rechazan el permiso antes de cargar datos.

## Huellas y comandos de auditoría

| Archivo original, no modificado en este cierre | SHA-256 |
| --- | --- |
| `artifacts/oos-v12-wf-cost-only-2022-02/ledger.jsonl` | `9206afe1cf7a833d236977d0a71b8168648294e3c0a49d9827471aac5fb0e745` |
| `artifacts/oos-v12-wf-cost-only-2022-02/sessions.jsonl` | `9064da09da150f390606773449a20df49b7be103d4eb69724e5c2531156f79c9` |
| `artifacts/oos-v12-wf-cost-only-2022-02/supervisor.jsonl` | `ffc6b8f9f236e54c64b995708118f66d2bbeacd674d094d3e9024adaa02b2188` |
| `artifacts/shared-pilot-budget/wf-2022-only-02-attempts.jsonl` | `4861a7ab5c884e0d782cf6f607aabb6372956ab4aff80a1f9d0b760e649ed17c` |
| `artifacts/shared-pilot-budget/wf-2022-only-02-checks.jsonl` | `c31d59c725276330555262052180a07eac42ae332b37e073c09853e9781e8786` |
| Preflight histórico `preflight-321dcf05f18d4ee28e182b27bb03e07f.json` | `eba200d2a39a8ce87b4bd52d4ee2c64383b7b9005c34b9286a1b2a64652c89a5` |
| `2022-01` intentos; comprobaciones | `1ae8a7d967cca4d07974fb3f1743dc6c6222f28a54e8fb561e6709ccbdebfb1a`; `edff22ca2f5d3b9a482cccbfe365140613d2734e8e364184ee61ef87f1b234a7` |
| WF05 ledger | `218ae4d4efad8f3440bb898a1f30f6ca33a09a26045c2b0bff0fe15c0303c1ba` |

Journal y estado `systemd` exportados **sin alterar** los originales en `docs/evidence/oos-wf-2022-02-preparation/`. Para repetir la auditoría de solo lectura: `sha256sum artifacts/oos-v12-wf-cost-only-2022-02/{ledger,sessions,supervisor}.jsonl`; `systemctl --user show oos-wf-cost-2022-02-session-01.service -p Result -p InvocationID -p ExecMainStatus -p MemoryPeak`; `journalctl --user -u oos-wf-cost-2022-02-session-01.service --no-pager -o short-iso`.

Tras el cierre se ejecutaron **3 pruebas focales correctas** y Ruff sobre el gate cerrado; `uv run --frozen python scripts/run_oos_wf_cost_2022.py --run` rechazó con `WF 2022 market cost study NOT AUTHORIZED` y código 1. No se volvió a ejecutar la suite completa después del cierre porque el cambio fue únicamente la desactivación prospectiva y su aserción de prueba; la suite formal anterior sí pertenece a esta ejecución y fue previa al fallo de recursos.

## Próxima decisión

La medición 2022 queda **incompleta**, aunque las unidades aceptadas ofrecen tiempos parciales. Una nueva medición íntegra necesitaría raíz, aprobación y presupuesto independientes, y resolver la estabilidad de `MemAvailable ≥4 GiB` sin reducir el umbral. La evaluación confirmatoria v1.2 no se habilita con esta evidencia; su armonización académica y el plazo prorrogado siguen pendientes.
