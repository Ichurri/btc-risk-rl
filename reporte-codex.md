# Reporte Codex — 07/11/2026, 01:32 (America/La_Paz)

- Rama: `codex/oos-wf-2022-confirmatory-prep`; cierre prospectivo del gate
  WF 2022-01: commit `0dbe214`. La eliminación local de `.python-version`
  permanece fuera de los commits.
- Ventana aprobada: **01:00–09:00 La Paz**. Conserva 3 h globales por día,
  2.700 s de reserva global, 3.600 s propios diarios, 4.800 s acumulados,
  600 s de reserva propia y máximo dos días activos.
- Preflight vigilado previo 00:58: `ready`, CA conectada, batería 100 %, memoria
  9.094.168.576 B, disco 129.157.259.264 B, gestor y `Linger` conformes;
  verificó el derivado exclusivo de entrenamiento sin abrir CSV compartidos.
- Servicio `oos-wf-cost-2022-01-session-01.service`, `InvocationID`
  `d1d9f440f25e4dfe98d610c96ac848da`: arrancó 01:00:05 y falló 01:07:26
  durante la suite formal. Resultado: **503 passed, 1 failed**, 439,41 s.
  Una prueba de P2R heredó contexto del servicio y observó el bloqueo
  global en vez del rechazo de terminal esperado. La bitácora mide
  440,610179 s de intento; `systemd` registró 1,3 GiB de memoria pico.
- No se ejecutaron Ruff ni preflight formales después de esa suite. **Cero
  unidades históricas, cero checkpoints**; la raíz `2022-01` sigue ausente.
  La bitácora terminó `failed` y no se reanuda. Su cargo global
  conservador el 07/11 es **10.800 s**; no cabe otra campaña ese día.
- La prueba contextual fue corregida prospectivamente; verificación focal:
  **16 passed en 112,10 s**. Suite completa de desarrollo limpia:
  **504 passed en 434,88 s**; Ruff: **All checks passed**. Una ejecución
  intermedia de desarrollo recibió señales de interrupción y no se usa como
  verificación. Nada de ello cambia la suite formal fallida de la unidad.
- Evidencias: `docs/hitos/OOS-v1-2-costo-2022-primer-intento-fallido.md`,
  `docs/evidence/oos-wf-2022-integration/launch-20261107-failed/`,
  `artifacts/shared-pilot-budget/wf-2022-only-01-attempts.jsonl` y
  `wf-2022-only-01-checks.jsonl`. WF05 sigue cerrado e intacto.
- Siguiente acción: terminar la verificación de la corrección y preparar
  un perfil/permiso **independiente** `2022-02` bajo la propuesta
  `docs/proposals/OOS-v1-2-costo-2022-reemplazo-02-v1.md`. En fecha local
  posterior, repetir suite, Ruff y preflight vigilado dentro de su propia
  bitácora; iniciar Q0 solo con todas las guardas `ready` y reservas.
- Evaluación v1.2 y prueba final siguen cerradas. Santiago eligió prórroga
  para los 36 bloques; faltan fecha y armonización de la tesis. No se abrió
  validación 2023 ni prueba final 2024–2025.
