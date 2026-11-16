# Sonda 06 — comandos ejecutados (06/10/2026, UTC)

Base `d840d6a32334ca4ddd104efa9e60358a29c19928`, rama
`codex/p2r-qabd-signal-06`. Solo perfil sintético. Raíces nuevas, locales y
excluidas de Git: `artifacts/p2r-synthetic-signal-qabd-review-06` y
`artifacts/p2r-signal-qabd-review-06-record`. El manifiesto `SHA256SUMS.txt`
ancla sus 25 archivos. No invocar de nuevo la CLI sobre la raíz fallida.
Se versionan copias exactas de las lecturas antes/después y del journal de
systemd; el verificador comprueba que coinciden con las originales locales.

Antes del lanzamiento se comprobó que no existían la raíz ni la unidad,
que `systemd --user` estaba `running`, los recursos `ready`, la alimentación
disponible y ninguna otra unidad P2R activa. Salida: `prelaunch.txt`.

```bash
systemd-run --user --unit=p2r-signal-qabd-review-06.service --service-type=exec --description='P2R synthetic Q/A/B+D SIGTERM with prior Q0 checkpoint' --working-directory=/home/ichurri/Desktop/personal_projects/btc-risk-rl --setenv=PYTHONUNBUFFERED=1 /home/ichurri/Desktop/personal_projects/btc-risk-rl/.venv/bin/python /home/ichurri/Desktop/personal_projects/btc-risk-rl/scripts/run_p2r.py --profile synthetic --mode algorithm --hold-seconds 75 --max-units 2 --output /home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/p2r-synthetic-signal-qabd-review-06
```

La unidad es `p2r-signal-qabd-review-06.service`; `InvocationID`:
`797f0e422bac4b138c13a0829261a752`. Se comprobó por lectura de
`ledger.jsonl`, `supervisor.jsonl`, el estado de systemd y las huellas que Q0
estaba completo y aceptado, que la unidad 1 estaba activa, y que no había
`checkpoint-1`. Instantánea: `before-signal.json` y
`before-signal-unit.txt`. Los comandos de consulta no escribieron la raíz.

```bash
systemctl --user kill --kill-whom=main --signal=SIGTERM p2r-signal-qabd-review-06.service
```

Solicitud entre `05:05:29.087819574` y `05:05:29.098881520` UTC. El
journal registra la entrega a las `05:05:29.096722` UTC. Se capturaron
`after-signal.json`, `after-unit.txt` y `systemd-journal.txt` por lectura.
El estado final fue `Result=exit-code`, `ExecMainStatus=1`, ledger `failed`.

Comprobaciones ejecutadas tras la sonda:

```bash
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen pytest -q 'tests/test_p2r_units.py::test_signal_inside_unit_fails_permanently[1]' tests/test_p2r_units.py::test_q0_and_iteration_match_existing_algorithm 'tests/test_p2r_units.py::test_resume_from_complete_boundary_matches_continuous[1]'
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen python docs/evidence/p2r-signal-qabd-06/checks.py
sha256sum -c docs/evidence/p2r-signal-qabd-06/SHA256SUMS.txt
UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen pytest
```

Las tres pruebas pytest pasaron (`3 passed in 22.49s`); son casos sintéticos
separados, no más sondas de systemd. `checks.py` pasó y confirmó cadenas de
hash, cronología, integridad del checkpoint previo y ausencia de
`checkpoint-1`. Los 25 archivos de esta sonda dieron `OK` al verificar el
manifiesto. También se revalidaron manifiestos previos 02 (32/32), 03
(18/18), 04/05 (28/28), y se contrastaron las cuatro huellas clave de 01;
no se alteraron las raíces anteriores.
`UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen ruff check .` y
`git diff --check` pasaron.
La suite completa pasó: `267 passed in 202.83s`.

La espera supervisada de 75 s sirve para enviar la señal de manera
reproducible. `worker-1.log` tiene 0 bytes: la señal llegó antes de los
cálculos Q/A/B+D. No demuestra un corte dentro de un paso de optimizador.
