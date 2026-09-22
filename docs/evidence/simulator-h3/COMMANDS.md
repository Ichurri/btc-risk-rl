# H3 — comandos y evidencia local nueva

Fecha: 22-09-2026. Base e4e2e8fada77f9b1116f3b265368e82c1e82cedd.
Adopción: 10d92fa. Implementación comprobada: ebb3914bfff4d59cc9ed0f8e8f7e0e5af96c90da.
Rama codex/adopt-adr002-v2-1. La eliminación previa de .python-version no se incluyó.
Todos los comandos se ejecutaron desde el repositorio local, con dependencias
existentes y UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache para los comandos uv.

## Inspección y Git

Se ejecutaron git status --short --branch, git log -5 --oneline y
git ls-remote --heads origin con SSH BatchMode y ConnectTimeout=10.
Local main y origin/main apuntaban a e4e2e8f; el remoto solo publicó main en esa base.
No hubo commits posteriores que integrar. Se creó la rama de trabajo con
git switch -c codex/adopt-adr002-v2-1. No reset, rebase, force push ni cambio de visibilidad.

La primera comprobación remota agotó el plazo del revisor automático de permisos;
el reintento autorizado devolvió la referencia indicada. Un comando preparatorio
usó python, no disponible en PATH; se corrigió a python3 antes de escribir archivos.
El intento asociado de git add/commit falló por falta del plan aún no escrito;
el commit se creó después correctamente. No son fallos abiertos.

## Ejecuciones

| Comando (prefijo uv run --frozen) | Evidencia | Resultado |
|---|---|---|
| pytest -q tests/test_temporal_contract.py, antes de implementar | temporal-red.log | 14 fallos esperados y 3 aprobadas |
| mismo comando, después de implementar | temporal-green.log | 17 aprobadas en .18 s |
| ruff format sobre los archivos modificados | salida de sesión | formateo completado |
| ruff check . | ruff-first.log | sin errores |
| pytest | pytest-first.log | 117 aprobadas en 23.73 s, sin fallos |
| ruff format docs/evidence/simulator-h3/check_compatibility.py | salida de sesión | completado |
| ruff check . (incluye nuevo verificador de compatibilidad) | ruff.log | sin errores |
| python scripts/verify_simulator.py --context local --output artifacts/simulator-h3/real | real-run.log, simulation-summary.json | passed; 7048 índices, 31 recorridos, 7590 pasos |
| python docs/evidence/simulator-h3/check_compatibility.py --new-summary artifacts/simulator-h3/real/summary.json --new-ledger artifacts/simulator-h3/real/ledger.csv --old-ledger artifacts/simulator-h2/real/ledger.csv --output docs/evidence/simulator-h3/compatibility-results.json | compatibility.log, compatibility-results.json | igualdad exacta contable y de observaciones H2 |
| btc-risk config-check | config-check.log | válido; training_enabled=false, final_test_locked=true |

El revisor independiente ejecutó adicionalmente pytest tests/test_temporal_contract.py
-q (17 aprobadas en .17 s) y git diff --check, sin errores. Su salida se comunicó
en la sesión; no se presenta como un log capturado por el proceso principal.
No encontró defectos accionables. Obligaciones de política y lotes pertenecen
al recolector futuro.

## Separación de evidencia

- La suite pytest utiliza fixtures sintéticos y oráculos contables independientes
  (bisección Decimal). Verifica implementación del simulador, no un agente.
- check_compatibility.py ejecuta de nuevo el código H2 de cc913b6 y H3 con
  180+2190 transiciones sintéticas; exige igualdad exacta en los 12 componentes
  previos al reloj, recompensas y campos contables.
- El auditor nuevo carga únicamente desarrollo aceptado y usa acciones prefijadas.
  Revalida H1, sin refit, y comprueba reloj, flags, máscaras, contabilidad y
  hashes antes/después. No descarga mercado ni selecciona una estrategia.
- La comparación de 7590 filas de mercado usa el libro H3 recién generado y el
  libro **histórico** H2, tras verificar su hash contra la evidencia versionada.
  No se atribuye una ejecución nueva de mercado H2 a esta sesión.
- No se volvieron a ejecutar los cálculos algebraicos de propuestas v1/v2/v2.1:
  se preservan como antecedentes, no se cuentan entre estas pruebas nuevas.
- simulation-summary.json identifica commit, código, entradas, versiones,
  fecha, comando, estado Git y libro completo. Su auditoría registra compatibilidad
  h1_schema1_to_adr002_v2_1, normalizer_refitted=false y 10073 observaciones de fit.
  La versión de schema cambia; los productos de datos no.

El libro nuevo artifacts/simulator-h3/real/ledger.csv no se versiona; su SHA-256 es
6780ae000a478b21505c89ddd9e0602c74fa8aa46acd601bf5beaccdea2eb968.
Para repetir usar destinos nuevos. El script comparativo requiere historia Git
H2 y el libro local histórico; el auditor principal no depende de ese libro.

No agentes, entrenamientos, evaluación confirmatoria, acceso final, instalación
de PyTorch/CUDA, modificaciones de drivers o de la tesis. No se generó ZIP.

Control de entrega: delivery-checks.json registra la conservación de propuestas,
lock, módulos contables y del historial HANDOFF. git diff --cached --check detectó
cuatro espacios finales emitidos por pytest en temporal-red.log; se conserva el
log original y se excluye solo ese archivo de la revisión de espacios. El resto
pasa el control. No se alteraron salidas de pruebas para hacer pasar la revisión.
