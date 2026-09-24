# Comprobación del protocolo propuesto P0-technical-v1

Base documental H5: 1118129b90d0760cf47f1538f1487dee9d7cd9e5.
Rama: codex/p0-protocol-proposal. Configuración NO AUTORIZADA.

Comandos realmente ejecutados para estos entregables:

```bash
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff format docs/evidence/p0-proposal/checks.py
UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache uv run --frozen ruff check docs/evidence/p0-proposal/checks.py
python3 docs/evidence/p0-proposal/checks.py --output docs/evidence/p0-proposal/results.json
git diff --check
```

Resultados: 8 grupos aprobados (checks.log/results.json); Ruff sin errores
(ruff.log). El verificador utiliza solo biblioteca estándar, JSON/documentos y
metadatos Git. Nunca importa el agente ni abre datos. Para repetir, elegir otra
ruta de output: se usa creación exclusiva y no se sobrescriben resultados.

Grupos: bloqueo/autorización; contrato; semillas/rotación; conteos completos;
conversión de d; admisión con relojes ficticios; registro acumulado ficticio;
ausencia de cambios operativos y concordancia de totales documentados.

Los segundos 1000/1400/etc. de los ejemplos son artificiales. No son tiempos
medidos, estimaciones aprobadas ni ejecución del TimeBudget H5. La regla de
admisión y el registro diario son propuestas cuya implementación futura requiere
pruebas propias. No se repitieron pytest ni verificadores H5, no se cargó mercado,
no se aprendieron parámetros y no se habilitó ningún comando operativo.
Las huellas de la configuración, protocolo y comprobador están en results.json.

La revisión documental comprobó cobertura de configuración, dos iteraciones por
corrida, cota pendiente, arranque sin estimación, tres horas diarias, interrupciones,
criterios de parada y necesidades de implementación antes de autorización.
La eliminación previa de .python-version permanece sin incluirse en el commit.
