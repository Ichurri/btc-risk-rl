# H0 técnico: repositorio y especificación

Commit de implementación: b215268 (chore: initialize thesis repository and protected working specification).

## Decisiones adoptadas
Especificación de trabajo en configs/initial.toml y ADR-001. Estado no confirmatorio.
PPO neutral/C5/C10 preservados. Datos de desarrollo 2018–2023 y calentamiento
diciembre 2017. Prueba 2024–2025 bloqueada. Sin entrenamientos.
Costos base, exposición continua, recompensa neta y horizonte de 180 registrados.
Valores definitivos de pilotos pendientes en campos explícitos, sin defaults de PPO.

## Implementación y comprobaciones realmente realizadas
- Git main inicializado; sin remoto.
- AGENTS.md y handoff para coordinación local/remota.
- Pydantic rechaza desbloqueo de test y habilitación de entrenamiento.
- uv sync: dependencias instaladas y uv.lock generado.
- uv run --frozen pytest -q tests/test_config.py: 4 passed, 0.17 s.
- Ruff: revisión y formato ejecutados.

## Evidencias
Commit, configuración, lock y tests/test_config.py. Runtime del entorno de
construcción en docs/evidence/runtime.json. No son mediciones del Debian del usuario.

## Traslado al documento
Registrar recursos reportados (VRAM aún no medida), presupuesto 3 h/día,
coordinación mediante Git y distinción entre especificación inicial y congelación.
No declarar piloto de rendimiento, simulador ni agente implementado.
