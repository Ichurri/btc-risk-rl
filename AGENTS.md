# Reglas para Codex: tesis BTC

## Autoridad y alcance
- Leer README.md, docs/HANDOFF.md y configs/initial.toml antes de modificar código.
- Este repositorio implementa la tesis de Santiago Andrés Iturri Vargas.
- Preservar C0 (PPO), C5 y C10 (CVaR-PPO). Mismo entorno y recompensa.
- No ejecutar entrenamientos en esta etapa. No instalar PyTorch/CUDA ni modificar drivers.
- No modificar la tesis: entregar evidencia para el chat académico.
- No implementar CVaR-PPO mientras la decisión ADR-002 siga pendiente.

## Datos y evaluación
- Prueba final reservada: [2024-01-01, 2026-01-01) UTC. No descargarla,
  cargarla, graficarla o usarla para selección durante desarrollo.
- Los comandos de desarrollo solo admiten datos anteriores a 2024-01-01.
- No retirar las guardas para completar una tarea. Una futura campaña final
  requiere protocolo congelado, revisión explícita y un comando separado.
- Transformadores: ajuste solo en entrenamiento, persistencia y reutilización sin refit.
- No interpolar huecos, eliminar extremos ni fabricar barras.
- No unir segmentos separados como si fueran contiguos.
- Identificar los datos sintéticos de pruebas; no presentarlos como mercado real.
- No reportar pruebas, tiempos o resultados que no se hayan ejecutado.

## Desarrollo y coordinación
- Una tarea de implementación activa por desarrollador; commits pequeños por hito.
- Local y remoto coordinan mediante Git y docs/HANDOFF.md, no mediante memoria de chats.
- Antes de editar: git status, leer último handoff; no sobrescribir trabajo ajeno.
- Usar ramas por tarea cuando exista trabajo concurrente. No force push.
- Al cerrar hito: pruebas, versión/commit, evidencia y cambios metodológicos pendientes.
- Datos voluminosos fuera de Git; manifiestos y huellas en evidencia versionada.
- No credenciales, claves de exchange ni datos personales en archivos versionados.

## Verificación
uv run --frozen ruff check .
uv run --frozen pytest

El entorno debe ser causal y mantener contabilidad float64. No simplificar
el cobro de costos ni ocultar errores con clipping indiscriminado.
