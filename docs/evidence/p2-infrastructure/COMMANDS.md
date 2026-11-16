# P2: comandos y alcance real

Base inspeccionada: `7357aa16de671049dde8164d502f04182690a4b9`, rama nueva
`codex/p2-infrastructure`. `git fetch origin` y comparación de HEAD con
origin/codex/p2-proposal coincidieron antes de editar. Se conserva la eliminación
previa local de `.python-version`. No se hizo reset/force push.

Se leyeron AGENTS, README, HANDOFF, configuración H3, propuesta P2 completa y
contratos de agentes/checkpoint/supervisor. El diseño P2 está registrado como
infraestructura autorizada, mercado no autorizado; propuesta original intacta.

## Pruebas realmente ejecutadas

En los comandos uv se antepuso `UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache`
en la misma línea; esta carpeta temporal fue solo caché de dependencias.

1. `uv run --frozen pytest tests/test_p2.py -q`: primera pasada roja de nueve
   pruebas al faltar módulos P2, conservada en `red.log`. Pasadas específicas
   adicionales comprobaron los defectos y sus correcciones (preservación de
   fragmentos, ruta canónica, configuración Path, reloj hacia atrás y gradiente).
2. `uv run --frozen pytest -q --junitxml=docs/evidence/p2-infrastructure/pytest.xml`:
   primera suite completa, **218 passed en82.22s**, log inicial conservado. El
   fichero XML/log inicial se renombró después de ejecutar para conservarlo.
3. Se añadieron pruebas del supervisor público (Q0+dos iteraciones pequeñas en
   procesos independientes), y del gradiente sobre A completo en pesos iniciales.
   Tras el commit de código `41fcef3`, la suite completa volvió a pasar:
   **221 pruebas en 94.31 s** y Ruff sin errores. Los logs son `pytest.log`,
   `pytest.xml` y `ruff.log`. Los casos y tiempos precisos constan allí.
4. Comprobaciones estáticas/algebraicas y huellas históricas:

```bash
uv run --frozen ruff check .
uv run --frozen pytest -q --junitxml=docs/evidence/p2-infrastructure/pytest.xml
uv run --frozen python docs/evidence/p2-infrastructure/checks.py --output docs/evidence/p2-infrastructure/results.json
```

`checks.py` pasó después del commit de código: verificó **282 archivos** de
evidencia P0/P1 por SHA y registró 221 pruebas aprobadas. No carga tensores ni
datos de mercado: calcula sumas conocidas y compara el diseño aprobado con la
propuesta. Registra runtime, hashes de código y resultado JUnit de esta ejecución.
Los logs intermedios de desarrollo en /tmp no se presentan como evidencia final.
La revisión independiente fue estática; sus hallazgos y regresiones constan en el
informe. Las pruebas unitarias usan carpetas temporales nuevas, nunca artefactos
históricos ni validación/final.

## Interpretación

Los tiempos son de pruebas sintéticas en esta máquina, no de P2 mercado. Las
pruebas de presupuesto usan relojes/consumos inventados identificados en fixtures;
los watchdogs también matan procesos sintéticos deliberadamente. Los nombres de
fechas/semillas en fixtures no implican carga de histórico. No se ejecutó la campaña
sintética completa de nueve corridas desde CLI ni P0/P1 de nuevo.

La CLI se invocó en tests con `--profile market` y rutas inexistentes para verificar
exit2 antes de configuración/datos; **no hubo ejecución de campaña de mercado**.
El futuro comando del informe está NO EJECUTADO como campaña y continúa bloqueado.
La autorización de infraestructura no se convierte en un permiso de mercado.
