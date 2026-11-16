# WF 2022-01: primer intento detenido antes de Q0

**Fecha:** 07/11/2026, `America/La_Paz`. **Alcance:** medición de costo del
corte de entrenamiento 2022; ninguna actualización histórica completada.
La ventana aprobada para esta sesión fue 01:00–09:00, con los límites
globales y propios originales. El permiso y la raíz se fijaron antes de
lanzar; la aprobación histórica no se editó tras el fallo.

## Cronología y resultado observado

| Hora La Paz | Hecho | Evidencia |
| --- | --- | --- |
| 00:58 | Preflight vigilado de solo lectura `ready`: CA conectada, batería 100 %, memoria 9.094.168.576 B, disco libre 129.157.259.264 B, gestor `running`, `Linger=yes`, 4.678 episodios y 7.703 filas de ajuste del corte. No abrió CSV compartidos ni productos de validación/final. | `docs/evidence/oos-wf-2022-integration/preflight-20261107-before-launch.json` |
| 01:00:05 | Arranca `oos-wf-cost-2022-01-session-01.service`, `Restart=no`, `InvocationID=d1d9f440f25e4dfe98d610c96ac848da`. El intento durable empieza a las 01:00:06. | `systemd.txt`, bitácora de intentos |
| 01:07:26 | La suite formal termina **503 passed, 1 failed** en 439,41 s; la sesión termina `Result=exit-code`, código 1. | `journal.txt`, bitácora de comprobaciones |
| Después | Gate `2022-01` cerrado prospectivamente en `0dbe214`. | commit y prueba de rechazo del comando público |

La prueba fallida fue
`test_separate_historical_command_requires_user_service_before_data_access`.
Su proceso hijo heredó el `InvocationID` y el cgroup de la unidad que corría
la suite. La prueba esperaba el rechazo «requires a systemd user service»,
pero el proceso alcanzó la inspección de presupuesto y encontró el bloqueo
global mantenido por la propia suite: «Another pilot holds the global daily
budget». Esto prueba una dependencia de la prueba respecto al contexto de
ejecución; **no** prueba un defecto del cálculo Q/A/B+D ni de la fuente de
mercado. La corrección prospectiva fija `INVOCATION_ID=""` en el hijo y
ejercita el rechazo incluso con el bloqueo ocupado.

No se ejecutó Ruff formal ni el preflight formal posterior a la suite, no
se creó `artifacts/oos-v12-wf-cost-only-2022-01/`, no se abrió ledger, no
hubo Q0, checkpoint ni trayectoria histórica nueva. El preflight de las
00:58 fue una fotografía favorable, **no** reemplaza la puerta formal que
quedó sin ejecutar.

## Presupuesto y decisión

La bitácora original
`artifacts/shared-pilot-budget/wf-2022-only-01-attempts.jsonl` tiene `start`
y `end status=failed`; el intervalo real fue **440,610179 s**. La bitácora
de comprobaciones registra solo `suite`, con duración **440,358696 s** y
estado `failed`. `reconcile()` devuelve `blocked=True`. Según la regla
conservadora vigente, `shared_attempt_debit()` asigna **10.800 s globales**
al 07/11 para otras campañas. Ese cargo es normativo, no tiempo de cómputo
observado. `inspect_budget(campaign=2022-01)` excluye el cargo de su propia
campaña y muestra 0 s externos, pero `admit()` de esa misma campaña rechaza
el estado `blocked`; no interpretar ese cero como saldo utilizable. El día
no admite otro lanzamiento. El intento y su raíz **no se reanudan ni se
reescriben**.

Para continuar el estudio se necesita una raíz y aprobación nuevas, el
mismo diseño científico, y contabilidad compartida que conserve el cargo
de `2022-01` en su fecha. La prueba corregida debe pasar dentro de una
suite supervisada con bloqueo global; después se requieren Ruff, preflight
vigilado y admisión en una fecha nueva. Ninguna de estas condiciones se
convalida con la captura previa al fallo. La evaluación v1.2 sigue pendiente
de armonización académica; no se abrió 2023 ni 2024–2025.

## Reproducción y huellas

Comando de sesión ejecutado:

```bash
systemd-run --user --on-calendar='2026-11-07 01:00:00' \
  --unit=oos-wf-cost-2022-01-session-01 --property=Restart=no \
  /usr/bin/systemd-inhibit --what=sleep:idle --mode=block \
  --why='WF 2022: conservar supervisor despierto' \
  /usr/bin/bash -c 'cd /home/ichurri/Desktop/personal_projects/btc-risk-rl && /home/ichurri/.local/bin/uv run --frozen python scripts/run_oos_wf_cost_2022.py --prepare && /home/ichurri/.local/bin/uv run --frozen python scripts/run_oos_wf_cost_2022.py --run'
```

| Archivo original o captura | SHA-256 |
| --- | --- |
| `artifacts/shared-pilot-budget/wf-2022-only-01-attempts.jsonl` | `1ae8a7d967cca4d07974fb3f1743dc6c6222f28a54e8fb561e6709ccbdebfb1a` |
| `artifacts/shared-pilot-budget/wf-2022-only-01-checks.jsonl` | `edff22ca2f5d3b9a482cccbfe365140613d2734e8e364184ee61ef87f1b234a7` |
| `docs/evidence/oos-wf-2022-integration/preflight-20261107-before-launch.json` | `335206958920190de787f43316fa3c50323142da96667a527353219e6b7c6f78` |
| `docs/evidence/oos-wf-2022-integration/launch-20261107-failed/journal.txt` | `5bb50854387eaabda9667690407d7cd358725e646fb601318ed263c6e509f9a6` |
| `docs/evidence/oos-wf-2022-integration/launch-20261107-failed/systemd.txt` | `728922917cc0ef482dee9a140530114c391de6211b8d01b50bb917540d106b54` |

`systemd` observó **1,3 GiB de memoria pico** y 8 min 33,358 s de CPU
acumulada durante la suite; ambas son mediciones de esa sesión, no del
entrenamiento del corte 2022. El código y las pruebas posteriores se
verifican por separado; no se atribuyen a la sesión fallida.

## Verificación prospectiva de la corrección

Se ejecutó la prueba focal de la guarda de terminal bajo bloqueo global:
**1 passed en 1,27 s**. La suite focal del ejecutor 2022 más esa prueba dio
**16 passed en 112,10 s**. `ruff check .` dio `All checks passed`.
Las pruebas de cierre del gate verifican que el comando y el trabajador
rechazan el permiso. Estos resultados no convierten en `ready` el intento
fallido ni autorizan `2022-02`. La suite completa de desarrollo ejecutada
después de corregir las pruebas y cerrar el gate dio **504 passed en
434,88 s**; Ruff volvió a pasar. Sus salidas están en
`docs/evidence/oos-wf-2022-integration/launch-20261107-failed/`.

Una ejecución de desarrollo intermedia recibió señales de interrupción
enviadas durante una prueba del supervisor y no se usa como verificación:
terminó con 503 passed y una falla ligada a esa señal. La ejecución limpia
posterior es la que sustenta el resultado de 504 pruebas. Ninguna de estas
ejecuciones reemplaza la suite formal fallida del intento `2022-01`.
