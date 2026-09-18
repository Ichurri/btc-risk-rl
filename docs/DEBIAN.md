# Extraer y verificar en Debian

Actualización H1 segmentado: la política B está aprobada e implementada; consulte
[ADR-004](decisions/ADR-004-segment-proposal.md) y
[el informe de aceptación](hitos/H1-preparacion-segmentada.md).
En un repositorio ya abierto se trabaja directamente sobre él. No mezclar el ZIP
para revisión académica con un árbol que contenga cambios locales.

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

El verificador ejecuta config-check, Ruff y pytest; registra versiones, commit, estado Git y salidas en artifacts/verification-local-FECHA/. El conteo de pruebas aumenta con los hitos; consultar el informe vigente. Si falla, comparte la salida completa; no uses sudo con uv ni retires guardas.

Para compartir resultados, enviar verification.json y los tres .log de esa carpeta.
La verificación de este equipo ya quedó registrada en docs/evidence/local-*.
Cada nuevo equipo requiere su propia ejecución. La etiqueta local la declara el
operador y el registro incluye la plataforma real.

Opcional, para reproducir el inventario sin red ni acceso al test:

```bash
uv run --frozen python scripts/diagnose_history.py --output artifacts/diagnostico-local
```

El destino debe ser nuevo. prepare-development continúa rechazando los datos
deliberadamente; la política B se aplica exclusivamente con la nueva ruta explícita:

```bash
uv run --frozen btc-risk prepare-segmented-development --output data/processed/segmented-B
uv run --frozen btc-risk verify-segmented-development --prepared data/processed/segmented-B
```

No volver a descargar datos para ejecutar las pruebas ni para reproducir el hito.
Si la caché habitual no es escribible en un entorno restringido, puede usarse
`UV_CACHE_DIR=/tmp/btc-risk-rl-uv-cache` como en la evidencia local.

Para continuar, leer AGENTS.md, docs/HANDOFF.md y ADR-004. B está aprobada;
la aceptación técnica no habilita entrenamiento ni acceso al test. Para compartir
cambios entre entornos se requiere el paquete actualizado o un remoto Git;
no se sincronizan conversaciones automáticamente.
