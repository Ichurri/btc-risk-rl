# P3 v1.1 — cierre prospectivo del permiso histórico

**Estado:** cierre operativo verificado, sin reabrir ni modificar la campaña.
Base: `842fdd1`, rama `codex/p3-close-market-permit`. La campaña P3 sigue
`completed`, 18/18 corridas y 198/198 unidades, con decisión `review` como
diagnóstico de desarrollo. Este hito no revisa esa decisión.

## Cambio

`MARKET_EXECUTION_ENABLED=False` en `p3_market.py` hace que
`P3MarketPermit.require_campaign()` rechace antes de leer el registro, el
ledger o cualquier solicitud. El comando público invoca esa guarda antes
de importar el supervisor y cargar el mercado. El trabajador histórico la
invoca antes de leer su solicitud, importar PyTorch y cargar la fuente. Las
entradas sintéticas de prueba conservan su contrato independiente.

El registro histórico `docs/protocols/P3-market-approval.json` **permanece
sin cambios y con SHA-256 fijado en código**. Su campo `active=true` describe
la autorización que sustentó la ejecución de octubre; no se usa para
reactivar la campaña porque la guarda operativa está cerrada. Editar o
falsificar ese JSON tampoco cruza la guarda. La auditoría de solo lectura
`final-audit.py` sigue accesible y reproduce el cierre bit a bit.

## Verificación y evidencia

Los dos ensayos de rechazo se escribieron primero: con el permiso aún
abierto fallaron por los motivos esperados (contexto de `systemd` y lectura
del registro falsificado); tras el cierre pasaron **6/6** pruebas focales.
La prueba con JSON falsificado vigila que la guarda se active **antes** de
leerlo. Los comandos reales `scripts/run_p3_market.py` y
`btc_risk_rl.pilots.p3_worker` con solicitud inexistente salieron con
código 1 y `P3 market campaign NOT AUTHORIZED`; no cargaron mercado ni
crearon una raíz. La suite completa dio **347/347** y Ruff general pasó.
El comando `systemctl --user list-units 'p3-market*' --all` no mostró
unidades P3 en el momento de la comprobación.

La auditoría `final-audit.py | cmp` pasó **antes y después** del cambio:
verificó cadena de ledger/journal, 198 reportes y 198 checkpoints aceptados,
recalculó la adjudicación y produjo el mismo JSON de cierre. Además, se
calcularon SHA-256 de **todos los 47.487 archivos** de
`artifacts/p3-approved-v1` (5.326.594.447 bytes) antes y después. La
huella agregada fue idéntica:
`73949350733bf3f8e3939e2dfcf7a28920668e738b0e5d910bd070a010fdcbec`.
Ledger `86b111b5365cda1760441d2f73d42e0463a4b4b2a7ddbc6e0e41f2a78751fcfe`;
journal `3edba2fc24bbf6288423d6f0fad90e40d2d8db361dbf505ba9634f6738076b82`;
registro de aprobación `66675a4931ae8aea2175c20c1c38f2cba2d5db0512ecc84da61ef6dfeba54597`;
cierre `1d96dd5ed2cb4af27a0f3993501ea7c40ece67ccc5862fe0f9d7b0049c033c6d`.
Los [comandos y salidas](../evidence/p3-permit-closure/COMMANDS.md) son la
evidencia reproducible.

## Alcance

Este cierre impide nuevas unidades por las entradas históricas P3
versionadas; no es una barrera contra editar deliberadamente el código.
No se cambió el registro de autorización, protocolo, configuración,
derivado H1, algoritmo, reportes, checkpoints ni artefactos P0/P1/P2/P2R.
No se hizo entrenamiento ni acceso a validación 2023 o prueba final
2024–2025. Una futura campaña requeriría permiso, raíz y revisión propios;
P3 no se reanuda.
