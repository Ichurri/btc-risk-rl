# Reglas para Codex: tesis BTC

## Autoridad y alcance
- P2 histórico: se autoriza SOLO integrar el perfil de entrenamiento aceptado y
  verificar controles con fixtures, pruebas sintéticas y preflight de solo lectura.
  Rama de integración desde `5e81594`. El registro de campaña permanece inactivo:
  NO iniciar P2, NO generar nuevas trayectorias históricas ni actualizar parámetros
  con mercado. Requiere autorización posterior, revisión del registro y activación
  de código por commit separado. Validación/final siguen bloqueados. Ver
  docs/hitos/P2-integracion-historica.md y docs/protocols/P2-market-registration-v1.json.
- P2: diseño de 7357aa1 aceptado (9 corridas, K=10, semillas 610031/610047/610081,
  crítico provisional de 4 épocas, D=64, umbrales §7, hasta 3 días activos).
  La autorización vigente permite implementar infraestructura y verificar SOLO con
  datos sintéticos. NO permite P2 sobre mercado ni generar trayectorias históricas.
  Mercado/validación 2023/final 2024–2025 siguen bloqueados antes de cargar datos.
  No repetir P0/P1. Conservar d, ADR-002 y Q/A/B. No modificar la tesis.
  La futura ejecución exige autorización posterior; aprobar infraestructura no
  registra permiso de campaña. Ver docs/protocols/P2-infrastructure-v1.md.

- P1 terminó: 18 corridas, criterio técnico cumplido en 3/3 semillas. La autorización
  se consumió con esta campaña; no repetirla ni inferir autorización de P2.
  Revisar docs/hitos/P1-epocas-critico.md antes de proponer otro piloto.
- Leer README.md, docs/HANDOFF.md y configs/initial.toml antes de modificar código.
- Este repositorio implementa la tesis de Santiago Andrés Iturri Vargas.
- Preservar C0 (PPO), C5 y C10 (CVaR-PPO). Mismo entorno y recompensa.
- P1 aprobado desde 42152c3 autoriza implementar, verificar sintéticamente y ejecutar
  18 corridas K=2: crítico 2/4 épocas, semillas 510031/510047/510081, orden aprobado.
  Descontar consumo de otras campañas del día; P0 cerrado no se repite.
  Rutas nuevas; mismo d, actor y Q/A/B. Validación/final siguen bloqueados.
- P0-approved-v1 autoriza el piloto acotado sobre entrenamiento aceptado 2018–2022,
  después de verificar sintéticamente ejecutor, supervisor y persistencia.
- Presupuesto GLOBAL de campaña: 3h/día America/La_Paz, timestamps UTC; varias
  corridas consecutivas sin concurrencia ni reinicio de contadores al cambiar proceso.
- Configuración, semillas, orden y K=2 aprobados solo para P0; d=-ln(0.90) común.
  Validación/final no accesibles al ejecutor. No repetir selectivamente fallos.
- Se permite PyTorch CPU fijado en el lock. No instalar CUDA ni modificar drivers.
- Fuera de P0/P1 aprobados siguen prohibidos entrenamientos de mercado, pilotos
  posteriores y evaluación confirmatoria. Conservar límites y guardas.
- No modificar la tesis: entregar evidencia para el chat académico.
- ADR-002 v2.1 está adoptado; H4 autoriza su implementación, sin cambiar su metodología.

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
