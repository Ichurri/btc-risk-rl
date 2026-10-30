# WF `...04`: preflight bloqueado el 29/10/2026 local

**Dictamen: no lanzar.** Se partió de `b386334` en la rama
`codex/oos-wf-cost-only-04-profile`, coincidente con origin. La raíz
histórica `artifacts/oos-v12-wf-cost-only-04/` estaba y sigue ausente.
La eliminación local previa de `.python-version` no se incorporó.

La suite completa terminó **447 passed en 322,70 s** y Ruff dio
`All checks passed!`. Inmediatamente después se generó un
[preflight vigilado nuevo](../evidence/oos-v1-2-wf-cost-04-check-20261029/preflight.json)
a las **00:18:04 UTC del 30/10**, todavía **20:18:04 del 29/10 en
`America/La_Paz`**. SHA-256 de la captura:
`e55a0c854a7a942a98eff96f4d884f3a1e6e51d5d7667b330c573d673a1fad36`.

El preflight informó `status=blocked` por tres puertas:

1. Memoria disponible **3.750.830.080 B**, menor que **4 GiB =
   4.294.967.296 B**. El mensaje agrupa alimentación, batería, memoria y
   disco; la memoria es la subcondición que falló en esta captura.
2. Presupuesto global del **29/10** agotado: `global_spent=10.800 s` por
   el cargo conservador de la campaña fallida `...03` y
   `remaining_before_reserve=0 s`; Q0 no era admisible.
3. La aprobación fija `not_before_day_la_paz=2026-10-30`; el código rechazó
   el día local 29/10. La huella del registro permaneció correcta; el
   bloqueo fue temporal, no una autorización faltante.

CA conectada, batería **98 %**, disco libre **145.003.634.688 B**,
`Linger=yes` y `systemd --user=running` pasaron en esa medición. La
integridad de entradas dio `ok`; la huella del código fue
`e7f869525309946b6c87f33149501ef5f7bc306cf11ecb582b766d5f39440ed6`,
igual a la aprobación fijada. El vigilante registró **57 rutas abiertas**
en el JSON, sin CSV H1 compartidos, validación ni prueba final; cero
trayectorias y pasos de optimizador.

El [cotejo de raíces](../evidence/oos-v1-2-wf-cost-04-check-20261029/frozen-roots.json)
dio 15/15 archivos idénticos en `...01`, 2/2 en `...02` y 10/10 en
`...03`. No se creó la raíz `...04`, no se inició `systemd --user`, Q0 ni
unidad 1. Los [comandos y logs](../evidence/oos-v1-2-wf-cost-04-check-20261029/COMMANDS.md)
permiten reproducir el dictamen.

La autorización específica `...04` no se consumió ni se cerró por un
preflight bloqueado. Una ejecución posterior requiere suite, Ruff y
preflight **nuevos** en un día local admisible y memoria suficiente; este
resultado del 29/10 no puede usarse como admisión de lanzamiento.
