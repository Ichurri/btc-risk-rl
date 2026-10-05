# Comandos y resultados reales — cadencia P2R 03

Fecha 05/10/2026, host Debian local. Base `76757ed`, rama
`codex/p2r-unit-integration`. Estado previo: ` D .python-version` ajeno,
conservado. La entrada `scripts/run_p2r.py` aceptó solamente
`--profile synthetic`; no se ejecutó ningún comando de mercado.

## Diagnóstico y pruebas

1. Lectura de `supervisor.jsonl` de sonda 02: 175 heartbeats, 174 intervalos,
   todos >5 s (máximo 5.212391 s). Lectura de código: `run_synthetic_units`
   esperó 5 s antes de volver a escribir; `run_fixture_unit` usó margen de
   4 s; `supervise` sondeó cada 0.2 s. No se cambiaron huellas de 01/02.
2. Antes de editar el código, se ejecutó
   `UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen pytest -q
   tests/test_p2r_units.py::test_default_heartbeat_is_recorded_within_five_seconds`:
   **falló** con intervalos registrados `[5.012508, 5.015442]`.
   El mismo comando sin `UV_CACHE_DIR` no llegó a pytest: la caché habitual
   de uv fue de solo lectura.
3. La primera inyección de una pausa dentro de `on_poll` se rechazó por
   `clock_discontinuity` del supervisor y no aisló la causa. Se cambió la
   inyección para pausar el **sondeo entre iteraciones**. Tras esa corrección
   de prueba, una pausa de 5.2 s provocó `ValueError` por intervalo tardío,
   ledger `failed` y ningún checkpoint aceptado. No fue una sonda de señal.
4. Después del cambio:

   ```bash
   UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen pytest -q tests/test_p2r_units.py tests/test_p2r_infrastructure.py
   UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen ruff check .
   UV_CACHE_DIR=/tmp/uv-cache-btc-p2r uv run --frozen pytest -q
   ```

   Resultados: **28 passed** en 71.39 s; Ruff **All checks passed**;
   **266 passed** en 167.35 s. El código probado quedó fijado en
   `40bbd93113b3b32dc11d09f7d9f75c6f578df462` antes de la sonda.

## Preflight y único lanzamiento bajo systemd

`check_resources(stage="preflight", disk_path=artifacts)` devolvió `ready`.
`P2RSharedBudget` indicó día `2026-10-05`, cero segundos externos y cero
fuentes. La lectura inicial de `systemctl --user` en sandbox falló con
`Operation not permitted`; la misma lectura autorizada fuera del sandbox
dio gestor `running`, unidad `LoadState=not-found`, ninguna otra unidad P2R
activa. No apareció otro proceso de campaña en la lectura de procesos.
`prelaunch.txt` registró UTC, commit, perfil y raíz nueva.

Comando de lanzamiento ejecutado **una vez**:

```bash
systemd-run --user --unit=p2r-heartbeat-q0-short-03.service --service-type=exec \
  --description='P2R synthetic short heartbeat Q0 probe' \
  --working-directory=/home/ichurri/Desktop/personal_projects/btc-risk-rl \
  --setenv=PYTHONUNBUFFERED=1 \
  /home/ichurri/Desktop/personal_projects/btc-risk-rl/.venv/bin/python \
  /home/ichurri/Desktop/personal_projects/btc-risk-rl/scripts/run_p2r.py \
  --profile synthetic --mode algorithm --hold-seconds 25 --max-units 1 \
  --output /home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/p2r-synthetic-heartbeat-q0-short-03
```

Salida: unidad `p2r-heartbeat-q0-short-03.service`, invocation
`0f328e5678ee4ab49ea8ded6f8c1c16b`. Se consultaron estado activo,
estado final (`inactive`, `Result=success`) y journal de `systemd --user`;
sus copias están en `artifacts/p2r-heartbeat-q0-short-03-record`. El journal
registró `ready`, una unidad, 4.566 s CPU y 388.3 MB de pico de memoria.

## Auditoría posterior

Un verificador de solo lectura reconstruyó la cadena `P2RJournal`, el único
`InvocationID`, ledger `ready` sin `pending`, frontera `after_q0`, recursos
Q0 y hash coincidente de checkpoint/manifest/ledger. Escribió
`heartbeat-intervals.json` **en el registro nuevo**, copiado aquí como
[intervals.json](intervals.json). Los seis intervalos UTC y monotónicos
resultaron ≤5 s; máximo UTC 4.143739 s. `unit_started` → primer heartbeat
fue 0.010087 s; último heartbeat → fin Q0, 2.434755 s.

`SHA256SUMS.txt` contiene los 18 archivos originales de la sonda/registro
03 y pasó `sha256sum -c` (18/18). Los 32 hashes de sonda 02 pasaron de nuevo,
y las cuatro huellas principales de sonda 01 siguieron idénticas. Los tres
conjuntos de artefactos permanecen fuera de Git e intactos. No hubo logout,
otra unidad, señal, entrenamiento histórico ni acceso a validación/final.
