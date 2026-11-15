# Cierre de la comprobación técnica de 2023

**15/11/2026, America/La_Paz.** Permiso separado `technical_2023` en
`77bb44e` (SHA-256 `aa72823f4db557cc9024bfb5cf1c8d685e1bd4c6594a5109747e28f823dcf18a`),
gate activado en `80d763a`. El permiso fija los 108 checkpoints K10, el
manifiesto exportado de 2023, el normalizador, el código y el presupuesto.
El gate final continúa cerrado.

El preflight vigilado nuevo fue `ready` para las 108 políticas: CA sí,
batería 100 %, `MemAvailable=10.731.388.928` B, disco libre
`83.830.833.152` B, `Linger=yes`, gestor `running`, ninguna otra campaña
activa y 47.556,632354 s disponibles antes de reserva. Es una captura del
momento. Su [JSON](../evidence/oos-v12-evaluation-20261115/technical-preflight.json)
tiene SHA-256 `487941554abebf09ff27bf977f7ff394b05a247c6d1a7b302f64f5ca6391dfd9`.

Una única sesión `oos-v12-technical-eval-20261115-01.service`, `Restart=no`,
`InvocationID=95f3fdf186e64bbdb68df9c0a2716ee5`, terminó
`Result=success`, `ExecMainStatus=0`. Ledger `completed`, **108/108**
políticas y **36/36** ternas, `pending=null`; cada recorrido tiene 2.190
transiciones. La auditoría independiente de reportes y huellas de las
108 trazas está en [technical-closure-audit.json](../evidence/oos-v12-evaluation-20261115/technical-closure-audit.json):
ledger SHA-256 `b9b9352f6bcb7e44fb750aff3e8ac4a05b72f49f90d4e7382aeeb6093e0362cd`,
cierre SHA-256 `a2e33b16dc8f6e56e25ca0975afc080ca16348b9c2ee9b1dcfef42afdbd3d5e3`.
El cierre original permanece en `artifacts/oos-v12-technical-2023-01/technical-closure.json`.

La bitácora cargó 984,338637 s por la sesión completa, mientras las unidades
sumaron 440,678586 s (3,773 a 4,618 s por unidad); la diferencia incluye
reverificación de entrenamiento, arranque, carga, reauditorías y cierre.
`systemd` registró 18 min 43,601 s de CPU y 9,6 GiB de pico del cgroup,
incluida caché de archivos. No se eligió política ni checkpoint por Sortino.
La puerta comprueba recorridos, contabilidad, costos, huellas y Sortino
definido en **todas** las políticas. No demuestra rentabilidad, superioridad
de C5/C10 ni cumplimiento poblacional de CVaR.

Comandos ejecutados:

```bash
uv run --frozen pytest -q tests/test_oos_v12_evaluation_access.py tests/test_oos_v12_historical_supervisor.py tests/test_oos_v12_evaluation_code_identity.py
# 18 passed
uv run --frozen ruff check .
# All checks passed!
uv run --frozen python -m btc_risk_rl.evaluation.historical_supervisor technical-preflight > docs/evidence/oos-v12-evaluation-20261115/technical-preflight.json
# ready
systemd-run --user --unit=oos-v12-technical-eval-20261115-01 --property=Restart=no --property=WorkingDirectory=/home/ichurri/Desktop/personal_projects/btc-risk-rl /home/ichurri/.local/bin/uv run --frozen python -m btc_risk_rl.evaluation.historical_supervisor run-2023
# Result=success; 108 accepted; technical closure passed
```

La siguiente etapa requiere un permiso separado para adquirir y auditar
2024–2025 y otro para la evaluación final, fijados después de este cierre.
