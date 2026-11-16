# Integración histórica P2 — comandos y evidencia

Todos los comandos se ejecutaron en `codex/p2-market-integration` desde la base
`5e81594`; `base-commits.txt` conserva el HEAD y la referencia remota inicial,
idénticos. La eliminación preexistente de `.python-version` no se incorporó.

## Verificaciones finales

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --frozen ruff check .
UV_CACHE_DIR=/tmp/uv-cache uv run --frozen pytest
UV_CACHE_DIR=/tmp/uv-cache uv run --frozen python scripts/preflight_p2.py
```

Salidas versionadas: [Ruff](ruff.log), [pytest](pytest.log) y
[preflight JSON](preflight.json). El directorio de caché temporal hizo que `uv`
pudiera adquirir su lock en el sandbox; se usó el entorno y lock existentes,
sin sincronización ni nuevas dependencias. La primera invocación sin
`UV_CACHE_DIR` fue rechazada por filesystem de solo lectura en `~/.cache/uv`;
no fue un fallo de las pruebas.
Resultado final: **234 pruebas aprobadas en 98,61 s**; Ruff aprobó.

El preflight lee el producto aceptado y verifica el **prefijo numérico de
entrenamiento** junto con huellas de archivos completos. No solicita
`environment()`, no construye episodios y no actualiza pesos. `status` es
`ready_for_review_not_execution`, con registro inactivo y comando bloqueado.
Las cifras de memoria/disco y presupuesto son una fotografía de la hora UTC
consignada en el JSON, no una reserva para una futura campaña.

La equivalencia Q/A/B con D encendido/apagado y la reanudación están cubiertas
por pruebas con fuentes sintéticas. La pequeña recolección D de la nueva suite
usa un fixture H1 **fabricado**, nunca el histórico real. Los rechazos de CLI
son pruebas negativas: el comando termina antes de cargar configuración o
datos y antes de crear salida.

La campaña futura no se ejecutó. El cálculo `p1_learning_only_proxy_seconds`
usa tiempos observados en P1 y no incluye D; `p2_d_cost_seconds_measured=null`
es deliberado. No se consultaron validación ni final.
