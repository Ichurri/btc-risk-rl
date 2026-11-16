# P2 histórico — plan de activación y ejecución

> **Ejecución:** la autorización del usuario en esta conversación ya indica ejecución directa; los pasos se realizan aquí sin pedir una segunda aprobación.

**Objetivo:** activar únicamente el permiso P2 de entrenamiento 2018–2022, ejecutar las unidades aprobadas bajo el presupuesto global y publicar evidencias de desarrollo sin acceder a validación/final.

**Arquitectura:** se conserva el algoritmo Q/A/B+D y el protocolo inmutable. El registro P2 pasa a activo con un identificador de autorización; el guardia de código fija su huella. El supervisor existente mantiene el ledger, lease por worker, límites y checkpoints completos.

**Tecnología:** Python 3.12, uv lock, PyTorch CPU, pytest, Ruff, Git.

---

### Tarea 1: Activación registrada y comprobable

**Archivos:** `docs/protocols/P2-market-registration-v1.json`, `docs/protocols/P2-market-approval-2026-09-30.md`, `src/btc_risk_rl/pilots/p2_market.py`, `tests/test_p2_market_integration.py`, `tests/test_p2.py`.

- [ ] Cambiar el registro a `active: true`, `campaign_permit: p2-market-training-only-2026-09-30`, `approval_record: docs/protocols/P2-market-approval-2026-09-30.md`; conservar SHA de diseño y manifiesto.
- [ ] Fijar en código la nueva huella SHA256 del registro y `MARKET_ACTIVATED=True`; hacer que el preflight exija el registro activo y devuelva `ready_for_authorized_execution` sin generar rutas.
- [ ] Mantener pruebas CLI negativas con protocolo no registrado; ninguna prueba debe invocar el comando canónico activo.
- [ ] Ejecutar prueba roja del permiso antes del cambio y suite sintética/Ruff después; crear commit de activación separado.

### Tarea 2: Preflight de entrada y campaña

**Archivos:** `scripts/preflight_p2.py`, `scripts/run_p2.py`, `docs/evidence/p2-execution/`.

- [ ] Verificar HEAD/origin, 108 huellas P0/P1, ledgers terminados, ningún proceso de piloto activo y presupuesto disponible.
- [ ] Ejecutar `UV_CACHE_DIR=/tmp/uv-cache uv run --frozen python scripts/preflight_p2.py` y conservar JSON/estado de salida; comprobar configuración, manifiesto, scaler, 7048 rutas, memoria, disco y registro.
- [ ] Solo si todo pasa, ejecutar `UV_CACHE_DIR=/tmp/uv-cache uv run --frozen python scripts/run_p2.py --profile market --protocol docs/protocols/P2-infrastructure-v1.json` con salida durable. No modificar parámetros ni reiniciar un fallo.
- [ ] Tras cada unidad, leer ledger, tiempos, RSS, contadores y fase D. Si el supervisor pausa por presupuesto, conservar la frontera y detener esta sesión; reanudar otro día con la misma autorización.

### Tarea 3: Cierre sin aprendizaje

**Archivos:** `docs/hitos/P2-ejecucion.md`, `docs/hitos/P2-ejecucion-resumen-academico.md`, `docs/HANDOFF.md`, `docs/evidence/p2-execution/`.

- [ ] Exportar resultados solo de logs/manifiestos/checkpoints ya existentes; comprobar hashes, fronteras, topes, integridad y ausencia de validación/final.
- [ ] Publicar informe, resumen de OE3, comandos y resultados pequeños; conservar artefactos voluminosos fuera de Git.
- [ ] Crear commit documental y publicar rama sin force push. Describir cualquier pausa o fallo con sus límites y sin inferir generalización/CVaR poblacional.
