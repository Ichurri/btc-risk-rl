# Fuente final 2024–2025: adquisición y auditoría

**15/11/2026, America/La_Paz.** El cierre técnico 2023 con 108/108
políticas se fijó antes de abrir el final. El permiso de adquisición
independiente `OOS-v1-2-final-source-approval.json` se registró en
`b1cb99b`, SHA-256
`df2ac42d077a38fc6716892b07d1ee5a5c6d7c2d2a3c97447e60df4f99df0d5e`,
y se activó **solo ese gate** en `d3d0d35`. El permiso de evaluación final
permanecía cerrado durante esta etapa.

El preflight nuevo dio `ready`: CA sí, batería 96 %, memoria disponible
12.779.606.016 B, disco libre 83.577.225.216 B, `Linger=yes`, gestor
`running`, sin otra campaña y con raíz cruda/exportada ausente. Archivo
[final-source-preflight.json](../evidence/oos-v12-evaluation-20261115/final-source-preflight.json),
SHA-256 `cc04bf328b2bcedff63f165aaa35557b0dd1bc75b5f2d1d353a3e3212efece28`.
El preflight tardó 136,136440 s. Las comprobaciones de preparación
anteriores se cargaron **conservadoramente** como intervalos de pared
reconstruidos, no como tiempo exacto de CPU; 3.425,648182 s en
[final-preparation-budget-debit.json](../evidence/oos-v12-evaluation-20261115/final-preparation-budget-debit.json).
No se cargó el intervalo de inactividad entre 04:12 y 09:45.

Una sola sesión `oos-v12-final-source-20261115-01.service`, `Restart=no`,
`RuntimeMaxSec=900s`, `InvocationID=b36f87291c7e4623a8674c99801107f3`,
terminó `Result=success`. La bitácora durable cargó 134,826421 s; `systemd`
informó 1 min 55,922 s de CPU y pico de 6,4 GiB del cgroup. Se conservaron
cinco páginas crudas en `data/raw/oos-v12-final-2024-2025-01/`, manifiesto
SHA-256 `85ab10e5d189e3bec0508bfd29f8da2d64ff8a6139c4d4363040c1e0a5232dbe`.
El exportado inmutable en `data/processed/oos-v12-final-2024-2025-01/`
tiene 4.429 velas: 43 de contexto idénticas a la exportación técnica 2023
y 4.386 transiciones finales. Manifiesto SHA-256
`db842235decd93fef2e04e49fbfb4f20752e9239f1c99eecb84f9e3e6e742436`,
CSV SHA-256
`d123935a385001082a0c7915071980d5d85706970e509ff856ff1f024775759d`.
La [auditoría independiente](../evidence/oos-v12-evaluation-20261115/final-source-audit.json)
releyó las cinco páginas, verificó sus huellas, continuidad, OHLCV, el
contexto, el normalizador congelado y la reconstrucción de características.
**Políticas finales evaluadas en esta etapa: cero.**

El [saldo posterior](../evidence/oos-v12-evaluation-20261115/final-source-budget-after.json)
es una medición del momento: 4.688,180886 s cargados el 15/11 y
43.011,819114 s antes de la reserva de cierre de 2.700 s, sin otra campaña.
La fuente final es apta para un permiso de evaluación separado; este
informe no contiene resultados financieros ni decisiones de hipótesis.

Comandos ejecutados:

```bash
uv run --frozen pytest -q
# 694 passed, 2 warnings, 939.21 s
uv run --frozen ruff check .
# All checks passed!
uv run --frozen python -m btc_risk_rl.evaluation.historical_final_supervisor source-preflight
# ready; salida en final-source-preflight.json
systemd-run --user --unit=oos-v12-final-source-20261115-01 --property=Restart=no --property=RuntimeMaxSec=900s --property=WorkingDirectory=/home/ichurri/Desktop/personal_projects/btc-risk-rl /home/ichurri/.local/bin/uv run --frozen python -m btc_risk_rl.evaluation.historical_final_supervisor fetch-final
# exported; cinco páginas; Result=success
```
