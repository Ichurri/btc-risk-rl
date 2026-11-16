# Fuente técnica OOS 2023: exportación y auditoría

**15/11/2026, America/La_Paz.** Esta etapa no evaluó políticas. El permiso
`technical_2023_source` autorizó únicamente copiar desde H1 las velas
exactas de 2023 y el contexto necesario, después de la adjudicación
documentada en [`OOS-v1-2-adjudicacion-pre-evaluacion-20261114.md`](OOS-v1-2-adjudicacion-pre-evaluacion-20261114.md).

El entrenamiento principal fue verificado de nuevo como 108 K10 completos
y 1.188 unidades, ledger SHA-256
`c3e1d793997e6379739d01223876962260d988c892ed44c7b161878adfc81e6b`.
La propuesta metodológica de la tesis en Drive ya describe 2023 como una
comprobación técnica sin selección por rendimiento; no se editó la tesis.

## Permisos y comprobaciones

- Código de evaluación SHA-256
  `c4de7aedce1f6e2499853ebd75d7e258a0c8f0db7c24d0a49a71e949f12e8bd8`,
  igual al del permiso de fuente v2. La primera versión del registro quedó
  sin activar y se conserva como antecedente.
- Suite estable: **684 passed**, dos `DeprecationWarning` de `fork` en una
  prueba sintética; Ruff: `All checks passed!`. Pruebas focales después de
  activar el gate: 17 passed, Ruff. La prueba adicional de pausa/reingreso
  del supervisor, ejecutada después de la suite, dio 11 passed y Ruff.
- [Preflight de solo lectura](../evidence/oos-v12-evaluation-20261115/source-preflight.json),
  SHA-256 `b9a8b032ecfbc3eb0af3d644485198405a9fd862f69c62d0027b1b6e07ceeb40`:
  `ready`; CA, batería 100 %, 9.116.581.888 B de `MemAvailable`, 83.826.311.168 B
  libres, `Linger=yes`, `systemd --user=running`; presupuesto del 15/11
  sin cargo previo en ese instante y 47.700 s antes de reserva. Son
  mediciones del momento.
- Se activó **solo** el permiso de exportación. El permiso de evaluación
  `technical_2023` y el final `final_2024_2025` permanecían cerrados.

## Servicio y producto

Una sesión `oos-v12-technical-source-20261115-01.service`, `Restart=no`,
`InvocationID=a24ab8da288c4df4ba5030c475099b59`, terminó
`Result=success`, `ExecMainStatus=0`. La bitácora durable de evaluación
cargó **143,367646 s** para la sesión completa. `systemd` informó 2 min
2,007 s de CPU y 6,7 GB de pico de memoria del servicio. Esas mediciones
no son una estimación de las 108 evaluaciones.

El producto local ignorado por Git está en
`data/processed/oos-v12-technical-2023-01/`. H1 fue auditado antes de
leer `bars.csv`: manifiesto
`d7cd59b7cda003a0f69883a83a0bacf06a65c37f3653a2f466c249ddf41a6998`,
manifiesto crudo fijado y cobertura de 2.190 velas sin exclusiones. El
exportador abrió `manifest.json`, `coverage.json` y `bars.csv` de H1; no
abrió la partición final. Escribió 2.233 filas sin relleno de precios.
El manifiesto exportado tiene SHA-256
`59333b75248d7ae5f0e028c9d93d7bf7db941481370a34c97ece43970135ce0d`;
su `bars.csv`,
`c06720ef3f1143e1eb73b0281898b5216bc5ba0f73181daeb8ddadfc300dcea6`.
La [auditoría](../evidence/oos-v12-evaluation-20261115/source-export-audit.json)
recontó filas, horario y SHA-256. El journal de servicio y su estado están
en la misma carpeta de evidencia. **Políticas evaluadas: 0.**

## Comandos realmente ejecutados

```bash
uv run --frozen pytest -q
# 684 passed, 2 warnings, 972.30 s
uv run --frozen ruff check .
# All checks passed!
uv run --frozen pytest -q tests/test_oos_v12_evaluation_access.py tests/test_oos_v12_historical_supervisor.py tests/test_oos_v12_evaluation_code_identity.py
# 17 passed
uv run --frozen python -m btc_risk_rl.evaluation.historical_supervisor source-preflight > docs/evidence/oos-v12-evaluation-20261115/source-preflight.json
# ready
systemd-run --user --unit=oos-v12-technical-source-20261115-01 --property=Restart=no --property=WorkingDirectory=/home/ichurri/Desktop/personal_projects/btc-risk-rl /home/ichurri/.local/bin/uv run --frozen python -m btc_risk_rl.evaluation.historical_supervisor export-2023
# InvocationID a24ab8da288c4df4ba5030c475099b59; Result=success
uv run --frozen pytest -q tests/test_oos_v12_historical_supervisor.py
# 11 passed, incluyendo pausa/reingreso sintéticos
```

Siguiente puerta: permiso `technical_2023` separado y fijado a la huella
del manifiesto exportado; después, una sola evaluación continua por cada
uno de los 108 checkpoints K10. No usar métricas de 2023 para seleccionar.
