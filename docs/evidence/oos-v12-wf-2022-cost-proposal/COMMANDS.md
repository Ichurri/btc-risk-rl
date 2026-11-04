# Comprobaciones de la propuesta de costo 2022

Ejecutadas desde la rama `codex/oos-wf-2022-cost-protocol`, con base
`977e852`. Son comprobaciones documentales, aritméticas y sintéticas;
**no** se ejecutó suite completa, preflight de campaña, unidad
`systemd --user` ni entrenamiento. No se abrió validación ni prueba final.

```bash
git status --short --branch
git log -6 --oneline --decorate
sha256sum docs/protocols/OOS-v1-2-wf-cost-executor-v1.json \
  docs/protocols/OOS-v1-2-wf-cost-05-profile-v1.json \
  docs/hitos/OOS-v1-2-costo-cortes-05-cierre-incomplete.md \
  docs/evidence/oos-v1-2-wf-cost-05-closure-20261103/results.json
python3 docs/evidence/oos-v12-wf-2022-cost-proposal/checks.py \
  > docs/evidence/oos-v12-wf-2022-cost-proposal/results.json
python3 -m json.tool docs/evidence/oos-v12-wf-2022-cost-proposal/results.json \
  > /dev/null
uv run --frozen ruff check \
  docs/evidence/oos-v12-wf-2022-cost-proposal/checks.py
test ! -e artifacts/oos-v12-wf-cost-only-2022-01 && \
  test ! -e docs/protocols/OOS-v1-2-wf-cost-2022-only-approval.json
grep -n '^MARKET_EXECUTION_ENABLED' \
  src/btc_risk_rl/pilots/wf_cost_replacement_05_exec.py
git diff --check
sha256sum docs/proposals/OOS-v1-2-costo-2022-exclusivo-v1.md \
  docs/evidence/oos-v12-wf-2022-cost-proposal/checks.py \
  docs/evidence/oos-v12-wf-2022-cost-proposal/results.json
```

`checks.py` terminó con código 0. Recalculó el mapa SHA-256 de los **2.647
archivos** de WF05, el ledger y los 11 reportes aceptados de la auditoría;
la huella del mapa siguió
`0d034efccb2138c4fb975c86e504763ff69ce331f2a5fdbb9919f4e1d06931eb`.
La raíz y aprobación propuestas están ausentes; el gate WF05 sigue `False`.
El caso sintético de intervalos `[0,390)`, `[380,600)`, `[500,700)` dio
**700 s de unión**, frente a 810 s de suma incorrecta. Un cruce sintético
de medianoche en `America/La_Paz` repartió 30 s a cada fecha. Los escenarios,
mediciones y SHA-256 de fuentes están en [`results.json`](results.json).
`json.tool` y `git diff --check` terminaron con código 0; Ruff informó
`All checks passed!` para el script nuevo.

Las cifras 300 s de otras tareas, 600 s de reserva y factores 1/1,5/2 son
supuestos de diseño; el costo real del corte 2022 sigue sin medir. El
orquestador de presupuesto previo al ledger y el ejecutor histórico de
esta nueva raíz **no existen todavía**: estas comprobaciones no sustituyen
sus pruebas de integración ni un preflight futuro.
