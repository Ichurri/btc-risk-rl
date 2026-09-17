# Extraer y verificar en Debian

Descarga btc-risk-rl-iteracion-02.zip. En el gestor de archivos, usa «Extraer aquí» en una carpeta nueva; no mezcles esta copia con otra modificada. Abre una terminal dentro de btc-risk-rl (la carpeta que contiene pyproject.toml).

Si ya tienes uv:

```bash
uv sync --frozen
uv run --frozen python scripts/verify_installation.py --context local
```

Si uv no está disponible, instala sus requisitos y una copia aislada (sin modificar Python del sistema):

```bash
sudo apt update
sudo apt install git python3-venv
python3 -m venv ~/.local/share/btc-uv
~/.local/share/btc-uv/bin/python -m pip install uv
export PATH="$HOME/.local/share/btc-uv/bin:$PATH"
uv sync --frozen
uv run --frozen python scripts/verify_installation.py --context local
```

La instalación requiere Internet. El proyecto fija dependencias en uv.lock; uv es el gestor, no una dependencia experimental. No hacen falta CUDA ni drivers NVIDIA para esta etapa.

Para extraer por terminal, sustituye RUTA_AL_ZIP por la ruta del archivo descargado:

```bash
python3 -m zipfile -e RUTA_AL_ZIP btc-iteracion-02
cd btc-iteracion-02/btc-risk-rl
```

El verificador ejecuta config-check, Ruff y pytest; registra versiones, commit, estado Git y salidas en artifacts/verification-local-FECHA/. Esperado: 32 pruebas aprobadas y Ruff sin errores. Si falla, comparte la salida completa; no uses sudo con uv ni retires guardas.

Envíame verification.json y los tres .log de esa carpeta. Hasta recibirlos, la ejecución en tu Debian queda PENDIENTE. La etiqueta local la declara el operador y el registro incluye la plataforma real.

Opcional, para reproducir el inventario sin red ni acceso al test:

```bash
uv run --frozen python scripts/diagnose_history.py --output artifacts/diagnostico-local
```

El destino debe ser nuevo. prepare-development continúa rechazando los datos deliberadamente: la política segmentada aún no se ha aplicado. No vuelvas a descargar datos para ejecutar las pruebas.

Para Codex local: «Lee AGENTS.md, docs/HANDOFF.md y docs/DIAGNOSTICO-HISTORICO.md. La política B está propuesta, aún no aprobada ni aplicada. No entrenes ni accedas al test. Ejecuta y registra verificación local». Para compartir cambios entre entornos se requiere el paquete actualizado o configurar un remoto Git; no se sincronizan conversaciones automáticamente.
