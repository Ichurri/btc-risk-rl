# Tres primeras ternas principales OOS v1.2 — captura del 11/11/2026

La única sesión `oos-v12-training.service` seguía activa al capturar el
ledger, con `InvocationID=097bd51bfa774984a3913721e364f67e`.
La captura `07a750e4bc5f068032223f5b40f66c879ecf2061c05b9840bd5366621df19bc9`
tenía `status=running`, `cursor=9`, 100 unidades aceptadas y la unidad 1
del siguiente bloque pendiente. **Tres ternas (9 corridas, 99 unidades)**
estaban completas; el siguiente bloque aún no lo estaba. El estado final
de la campaña no se deduce de esta captura.

| Bloque | Semilla | Orden | Tiempo medido de 33 unidades (s) |
| ---: | ---: | --- | ---: |
| 0 | 1869792951 | C0, C5, C10 | 2.258,869 |
| 1 | 309092095 | C5, C10, C0 | 2.246,075 |
| 2 | 391604748 | C10, C0, C5 | 2.266,412 |

Media medida: **2.257,119 s por terna**; rango 2.246,075–2.266,412 s.
El [auditor reproducible](../evidence/oos-v12-main-three-triplets-20261111/checks.py)
verificó la cadena del ledger, roster, fronteras K10, identidades y
**99/99 huellas** de cada clase: checkpoint, reporte y solicitud. El
[JSON de auditoría](../evidence/oos-v12-main-three-triplets-20261111/audit.json)
tiene SHA-256 `8054c5b5c3594f712f515fed6b5b08a5df2981c1a0f5498fa41f82547277e245`.
La tabla y el SVG de la misma captura están en la rama aislada de
evaluación, bajo `docs/evidence/oos-v12-main-progress-20261111/`.
El mayor RSS de trabajador registrado entre estas unidades fue
672.030.720 B; no equivale a memoria total del sistema.

La [captura del presupuesto](../evidence/oos-v12-main-three-triplets-20261111/budget-snapshot.json)
fue a las **15:35:50 America/La_Paz** (`19:35:50 UTC`), SHA-256
`c548a2627f9adfdc23c21961be2d1d0acb74945988961400ed06b405b9a7136a`.
La unión observada cargaba **25.650,515 s** globales del 11/11 y dejaba
**22.049,485 s** antes de la reserva de 2.700 s. La sesión estaba abierta:
es un saldo instantáneo, no un cargo final. `blocked_for_other_session=true`
se debe a su propio ledger activo y protege contra un segundo lanzamiento.

## Proyección separada de la medición

Quedan 33 ternas. Multiplicar su número por la media de las tres observadas
produce **74.484,917 s (20,690 h) de unidades**: extrapolación, no gasto
real. Cada sesión futura añade suite formal, Ruff, preflight vigilado,
carga, auditoría y cierre. Si los tiempos se mantienen y las guardas
admiten unidades, el entrenamiento podría cerrar hacia el 13/11. La fecha
de evaluación es distinta: faltan fuente final auditada, integración
supervisada, permisos separados y armonización académica. El estimado
sintético anterior para 108 recorridos **no incluye** esos costos.

No se abrió validación 2023 ni prueba final 2024–2025, no se eligió
checkpoint por rendimiento y no se ejecutó otra sesión. El corte 2021
permanece solo como diagnóstico descriptivo por la exclusividad de bloqueo
no demostrada; el corte 2022 auxiliar ya cerró con auditoría propia.

## Comandos realmente ejecutados

```bash
uv run --frozen python docs/evidence/oos-v12-main-three-triplets-20261111/checks.py > docs/evidence/oos-v12-main-three-triplets-20261111/audit.json
uv run --frozen ruff check docs/evidence/oos-v12-main-three-triplets-20261111/checks.py
sha256sum docs/evidence/oos-v12-main-three-triplets-20261111/{audit.json,budget-snapshot.json}
systemctl --user show oos-v12-training.service -p ActiveState -p SubState -p MainPID -p InvocationID
```

El auditor rechazó primero la captura de ocho corridas porque no había tres
ternas completas; después pasó con nueve. La tabla y el SVG se generaron
en el worktree aislado mediante `scripts/render_oos_v12_training_progress.py`
con `--source-root` apuntando al repositorio histórico, en modo de lectura.
Siguiente acción: dejar terminar o pausar la sesión actual, auditar el
ledger y el cargo de cierre, y solo entonces considerar otro lanzamiento.
