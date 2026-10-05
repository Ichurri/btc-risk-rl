# P2R unidades sintéticas: comandos y evidencia (05/10/2026)

Base `e1e98dd`; rama `codex/p2r-unit-integration`. Se ejecutó únicamente
`SyntheticMarket` de pruebas. La configuración mínima de estas pruebas
(`K=2`, `Q=2`, `A=1`, `B=2`, `D=2`, actor 1 época, crítico 4, semilla 610031)
**no** es una configuración aprobada para una campaña P2R. El perfil de
mercado de la CLI se rechazó sin crear salida. No se cargaron entrenamiento,
validación ni prueba final y no hubo entrenamiento con histórico.

## Comprobaciones ejecutadas

```text
UV_CACHE_DIR=/tmp/uv-p2r-cache uv run --frozen pytest -q tests/test_p2r_units.py
8 passed in 48.23s

UV_CACHE_DIR=/tmp/uv-p2r-cache uv run --frozen pytest -q tests/test_p2r_units.py::test_resume_from_complete_boundary_matches_continuous
2 passed in 32.10s

UV_CACHE_DIR=/tmp/uv-p2r-cache uv run --frozen ruff check .
All checks passed!

UV_CACHE_DIR=/tmp/uv-p2r-cache uv run --frozen pytest
259 passed in 152.17s (0:02:32)

git diff --check
sin salida; código 0
```

Al iniciar el desarrollo, la prueba nueva falló en colección porque aún no
existía `p2r_units`. Una pasada intermedia obtuvo `5 passed, 1 failed`:
la prueba de rechazo CLI comenzó antes de que se guardara la nueva opción
`--mode`. Tras el cambio, `6 passed`, y tras añadir integridad de checkpoint
y progreso entre unidades, `8 passed`. Estos fallos intermedios no son
resultados de la versión entregada.

Los casos finales comprobaron: equivalencia de estado completo con
`complete_unit` directo; Q0 con 2 trayectorias/360 transiciones y sin pasos
de optimizador; iteración con 5 trayectorias de aprendizaje/900
transiciones, 2 D/360 transiciones, 1 paso actor y 4 crítico; manifiestos
`after_q0` y `after_dual_and_D`; reanudación tras unidad 0 o 1, con D ya
escrito sin regenerarlo; `SIGTERM` durante Q0 o durante iteración con ledger
`failed` permanente, sin checkpoint de la unidad interrumpida; corrupción del
checkpoint previo; marcador de progreso anterior no contado como actual;
rechazo temprano de `--profile market`.

## Integridad de campañas anteriores

`sha256sum` antes y después de las pruebas dio exactamente:

```text
1d1ee72ca0ac49529f205b30942a68f381d86037e336091c490c624098339b8c  artifacts/p0-approved-v1/ledger.jsonl
926eab40bc764e1cae88a74e6718ba70b50e2df0626e8e34964078cc4ba55755  artifacts/p1-approved-v1/ledger.jsonl
db4ffacfaa4f150c778c5f51335851a80a9c9a7aadba3a875615414d4fa118c5  artifacts/p1-preparation-approved-v1/ledger.jsonl
e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8  artifacts/p2-approved-v1/ledger.jsonl
bb2af51c8192303d062b095646a772948072e4eeb36c039f1aa8f9e0037af2b3  artifacts/p2-approved-v1/run-05-C0/progress.json
45ef6ad0421e062a7a1b150f5711cfbf07bfec8d47e5e3a72dabf2a149f6002b  artifacts/p2-approved-v1/run-05-C0/journal/events.jsonl
```

## Host: solo lectura, sin aprobación de aptitud

El 05/10/2026 a las `13:50:14 UTC` se midieron `MemAvailable=4687536128`
bytes y `184845860864` bytes libres en el filesystem del repositorio;
`ADP1/online=1`, `BAT1/capacity=98`. La consulta
`loginctl show-user "$UID" -p Linger -p State` desde este entorno falló con
`Operation not permitted`; la última lectura documentada anteriormente era
`Linger=no`. No se ejecutó logout completo ni se modificó configuración del
sistema. Esas lecturas puntuales no constituyen preflight histórico. El
[procedimiento del host](../../protocols/P2R-host-preflight-review.md) separa
las verificaciones pendientes y mantiene los umbrales existentes.
