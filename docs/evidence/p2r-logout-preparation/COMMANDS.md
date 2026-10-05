# Prueba de logout P2R: preparación estática, sin lanzamiento

Fecha local 05/10/2026; rama `codex/p2r-unit-integration`. Se preparó
[el procedimiento manual](../../protocols/P2R-logout-Q0-synthetic-review.md)
para `p2r-logout-q0-review-01.service`. No se ejecutó `systemd-run`, no se
cerró la sesión, no se creó la raíz de prueba y no se generó ninguna
trayectoria. La eliminación local previa de `.python-version` no pertenece a
estos cambios.

## Comprobaciones realizadas

```text
UV_CACHE_DIR=/tmp/uv-p2r-cache uv run --frozen pytest -q tests/test_p2r_logout_preparation.py tests/test_p2r_units.py::test_market_profile_still_rejected_before_output
5 passed in 0.89s

UV_CACHE_DIR=/tmp/uv-p2r-cache uv run --frozen pytest -q tests/test_p2r_infrastructure.py::test_journal_chain_and_recovery tests/test_p2r_infrastructure.py::test_service_context_requires_real_unit_and_linger tests/test_p2r_infrastructure.py::test_market_cli_denied_before_artifacts
5 passed in 0.10s

UV_CACHE_DIR=/tmp/uv-p2r-cache uv run --frozen ruff check .
All checks passed!

UV_CACHE_DIR=/tmp/uv-p2r-cache uv run --frozen python scripts/run_p2r.py --help
mostró --hold-seconds (0–900), --mode algorithm y --max-units; código 0

bash -n sobre los tres bloques bash del procedimiento
bash block 1: OK
bash block 2: OK
bash block 3: OK

git diff --check
sin salida; código 0

test ! -e artifacts/p2r-synthetic-logout-q0-review-01
probe-root-absent
test ! -e artifacts/p2r-logout-q0-review-01-record
evidence-root-absent
```

La prueba nueva se escribió antes del hook y falló inicialmente en colección
porque no existía `p2r_hold`. Después de implementarlo, cuatro casos
estáticos comprueban: espera máxima 900 s y comando sintético, `exec` al
worker sintético en el mismo proceso sin dormir en la prueba, rechazo de
argumentos inseguros y registro/validación de `INVOCATION_ID` en el journal.
El quinto caso comprueba que `--profile market --hold-seconds 900` se rechaza
antes de crear salida. **No son una prueba de logout completo.**

## Lectura del host, sin cambiar configuración

El usuario informó en su propio terminal `Linger=yes` y gestor de usuario
`running`; estos valores deben registrarse nuevamente al iniciar. La consulta
del gestor desde el entorno de herramientas había fallado con
`Operation not permitted`, por lo que no se atribuye a esta ejecución una
medición independiente de `Linger`.

El 05/10/2026 a las 14:13:17 UTC se leyó AC=1, batería=98 %,
`MemAvailable=3981492224` bytes y espacio libre=184778977280 bytes en
`artifacts/`. `check_resources(stage="preflight", disk_path=artifacts)`
devolvió `ValueError: Insufficient P2R memory or disk`: la memoria quedó
**313475072 bytes por debajo de 4 GiB**. No se bajó el umbral ni se
consideró apto al host. La futura ejecución manual debe repetir la lectura
real y detenerse si vuelve a fallar.

El `InvocationID` de la unidad propuesta **no existe todavía**. El
procedimiento registra `NO_ASIGNADO` antes de lanzar y su valor real mediante
`systemctl --user show` inmediatamente después; el journal P2R conservará
el mismo ID para comparar con el journal de systemd tras el logout.
