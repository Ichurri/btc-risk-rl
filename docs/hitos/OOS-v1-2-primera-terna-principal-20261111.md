# Primera terna principal OOS v1.2 — 11/11/2026

## Estado observado

La sesión histórica original `oos-v12-training.service` continuaba activa al
capturar este informe; `InvocationID=097bd51bfa774984a3913721e364f67e`.
No se inició otra sesión. El ledger principal había aceptado la primera terna
de la semilla `1869792951`, **C0, C5 y C10**, con K=10 y 33 unidades completas.
El supervisor ya había comenzado el siguiente bloque. El estado final de la
campaña no se infiere de esta captura.

| Condición | Tiempo medido de Q0 y diez unidades (s) | RSS máximo de trabajador (MiB) | SHA-256 estado K10 |
| --- | ---: | ---: | --- |
| C0 | 772,220 | 629,5 | `1ecc4be37436f2db928511a1346e0f08383b145c5342f7fc44f95ff3d3a5c4fd` |
| C5 | 748,023 | 638,9 | `638113d2df49d70613daf4f950553fd13de75e0117c88b43ebe5324114004de4` |
| C10 | 738,626 | 598,7 | `2aaee9fe8610635ca14e8e39e136a7e427f33d01e782aecebddb2de841ad0c4f` |

El total **medido de unidades** de esta terna fue **2.258,869 s**. No incluye
suite, carga, preflight, brechas entre unidades, auditoría ni cierre. El
auditor verificó la cadena de 107 estados de la captura, el roster congelado,
la identidad K10 y las huellas de los **33 checkpoints, 33 reportes y 33
solicitudes**. [Cálculo reproducible](../evidence/oos-v12-main-first-triplet-20261111/checks.py)
y [resultado](../evidence/oos-v12-main-first-triplet-20261111/audit.json).
En el worktree aislado de evaluación se verificó además que los tres actores
K10 cargan con frontera y contadores correctos, y que su identidad de origen
coincide con el manifiesto exclusivo de entrenamiento H1. Esto fue lectura de
pesos, **sin evaluación de mercado**. La [tabla, figura y huellas de esa
captura](https://github.com/Ichurri/btc-risk-rl/tree/7f0b582/docs/evidence/oos-v12-main-progress-20261111)
se publicaron en la rama aislada `codex/oos-v12-evaluation-infrastructure`.

La captura de presupuesto a las **14:20:18 America/La_Paz** cargó
**21.118,462 s** globales del día y dejó **26.581,538 s** antes de la
reserva de 2.700 s. Es un débito observado mientras la bitácora de preparación
sigue abierta; el cargo del ledger principal se cerrará después. El indicador
`blocked_for_other_session=true` es correcto mientras esta sesión ocupa el
bloqueo y no significa fallo de la sesión actual. [Captura](../evidence/oos-v12-main-first-triplet-20261111/budget-snapshot.json).

## Proyección condicionada

Quedan **35 ternas** de las 36 principales. Si cada una repitiera los
2.258,869 s medidos en la primera, serían **79.060,411 s de unidades**.
Es una extrapolación de **una** semilla, no una duración observada de la
campaña. Las nuevas sesiones necesitan además suite formal (la del perfil
principal actual midió 601,399 s), Ruff, preflight, carga y cierre. Con el
saldo observado de hoy y hasta 47.700 s productivos por día posterior bajo
el límite de 50.400 s y la reserva de 2.700 s, el entrenamiento podría
terminar alrededor del **13/11**, si se mantienen ritmo, recursos y guardas.
No se promete esa fecha ni se usa la proyección para omitir admisiones.

La evaluación histórica aún no tiene un costo de extremo a extremo medido,
permiso de acceso ni exportaciones auditadas 2023/2024–2025. El repositorio
local no mostró archivos identificados como fuente final 2024–2025 en una
inspección de nombres. El método de inferencia quedó fijado antes de abrir
datos protegidos, y el worktree de evaluación tiene pruebas sintéticas;
**ningún resultado financiero fuera de muestra se puede presentar todavía**.
La fecha del 16/11 sigue condicionada por esas puertas técnicas y académicas.

## Comandos y límites de la verificación

```bash
systemctl --user show oos-v12-training.service -p ActiveState -p SubState -p MainPID -p InvocationID -p Result
uv run --frozen python docs/evidence/oos-v12-main-first-triplet-20261111/checks.py > docs/evidence/oos-v12-main-first-triplet-20261111/audit.json
uv run --frozen ruff check docs/evidence/oos-v12-main-first-triplet-20261111/checks.py
```

El script de progreso del worktree aislado leyó la **misma captura** de ledger
y generó una tabla y SVG locales sin alterar artefactos. La primera consulta
manual de presupuesto buscó un campo `stage` que no existe en la bitácora y
terminó en `StopIteration`; se corrigió la lectura del intervalo `start`
abierto y se conservó solo el resultado correcto de la segunda consulta.
No se entrenó con comandos de auditoría ni se abrió validación o prueba final.

Próximo paso: dejar al supervisor admitir unidades completas hasta la pausa
o cierre; verificar ledger, checkpoints y débito final. Una segunda sesión
solo procede después del cierre de esta, en frontera válida y con preflight
nuevo. Un ledger `failed` no se reanuda.
