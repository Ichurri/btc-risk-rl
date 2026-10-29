# Corrección prospectiva del primer arranque WF de reemplazo

**Alcance:** código y pruebas sintéticas. La campaña histórica `...02` permanece
fallida antes de Q0, sin ledger ni checkpoint; su permiso está cerrado. Este
hito no la reanuda, no ejecuta unidades y no modifica las raíces `...01`/`...02`.
Pruebas: `cefa2ab`; corrección: `2294420`.

## Causa y corrección

El [informe del fallo inicial](OOS-v1-2-costo-cortes-reemplazo-fallo-inicial.md)
y el traceback muestran que `run_units()` creaba la raíz para la bitácora
`sessions.jsonl` antes de `_launch_readiness()`. Esta última rechazaba toda
raíz existente sin ledger, incluso la que acababa de crear el mismo proceso.

Ahora `run_units()` toma `P2RSharedBudget` y **bajo ese bloqueo** comprueba la
existencia previa de la raíz. Si ya existe sin `ledger.jsonl`, falla antes de
crear o alterar la bitácora. Si no existe, la crea y abre la bitácora durable;
los fallos posteriores, incluidos los anteriores a abrir el ledger, quedan
registrados como `end failed`. La comprobación de host, entradas y presupuesto
permanece en `_launch_readiness()`. No se rebajó ningún umbral ni se cambió la
admisión de unidades.

## Pruebas realmente ejecutadas

La prueba nueva de primer arranque llama al **`run_units()` real** con raíz
temporal ausente, bloqueo y ledger reales, guardas y fuentes sintéticas. El
supervisor crea `sessions.jsonl` y `ledger.jsonl`, queda `ready` sin unidades
ni `pending`, y se detiene antes del trabajador por la guarda sintética de
recursos. Esto verifica el orden de arranque; no mide Q0 ni prueba `systemd`.
Una prueba rechaza una raíz huérfana sin escribirle. Otra reingresa por
`run_units()` con ledger y conserva identidad, cero unidades y ambas sesiones
durables. La prueba previa en procesos separados sigue cubriendo la
normalización de roster al reingresar; otra comprueba que un fallo posterior
al inicio de una raíz nueva, pero anterior al ledger, cierra la bitácora en
`failed`.

Antes de cambiar el código, dos pruebas nuevas fallaron por el defecto
observado: primer arranque rechazado y escritura en raíz huérfana. Tras la
corrección, la prueba focal completa dio **13 passed** y la suite completa
**419 passed** (283,16 s); `uv run --frozen ruff check .` dio
`All checks passed!`. Los comandos y logs están en
[COMMANDS.md](../evidence/oos-v1-2-wf-first-start-fix/COMMANDS.md).

## Preservación y límites

Se comparó cada archivo regular antes y después: 15/15 de `...01` y 2/2 de
`...02` idénticos. La huella SHA-256 del mapa de archivos de `...01` es
`b93caafafd20b7a61f86214b5cbecba3ff7942d3862a467e1748d636b74a010a`;
la de `...02` es
`e11a6cfa872ed91ed5f9d0b30f429071b884846125c4df2a4a9d694a664257fd`.
El ledger original `...01` conserva
`b6bc9a30d25387813d664708edfa07347c21174d2df216fc6f6be2d844ec6af6`;
su estado Q0 conserva
`22f9f60484db6ae5a04b7b35f4ebe2149debb16ac357437536c24f571bf8bca7`.
La bitácora fallida `...02` conserva
`72e790c0daf96a8da188e47b3791d759de625d170813fdc98c60d6ae888cb276`.
El registro de aprobación histórico conserva
`c0d6973d98951dabe1cbc0cfef2f79304c2662cba01e09ff58276547c453f242`.

`MARKET_EXECUTION_ENABLED=False` continúa en el perfil de reemplazo y en el
perfil `...01`. La huella actual del código del ejecutor es
`6208c1a739f3bbe8c58e598cf9aaccf410f77b0657f6d96c198bb24a991d0ab4`;
el registro histórico no autoriza este código ni una nueva ejecución. La
eliminación local de `.python-version` no se versionó. Una eventual medición
requerirá otra raíz, otro permiso y preflight actualizado; esta corrección no
establece viabilidad temporal de Q0 ni de Q/A/B+D.
