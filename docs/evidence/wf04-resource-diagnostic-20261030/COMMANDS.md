# Comandos realmente ejecutados — diagnóstico WF `...04`

Directorio: `/home/ichurri/Desktop/personal_projects/btc-risk-rl`.
Base `f9f4c94`, rama nueva `codex/oos-wf04-resource-observability`.
` D .python-version` era un cambio local previo y permanece fuera de Git.

## Lectura histórica, sin alterar artefactos

```bash
git status --short --branch
git log -3 --oneline
python3 docs/evidence/oos-v1-2-wf-cost-04-session-02-20261030/audit.py
journalctl -b --since '2026-10-30 02:12:30' \
  --until '2026-10-30 02:13:45' -o short-iso-precise --no-pager
journalctl -b -k --since '2026-10-30 02:12:30' \
  --until '2026-10-30 02:13:45' -o short-iso-precise --no-pager
sudo -n journalctl -b --since '2026-10-30 02:12:30' \
  --until '2026-10-30 02:13:45' -o short-iso-precise --no-pager
journalctl -b -u upower.service --since '2026-10-30 02:10:00' \
  --until '2026-10-30 02:16:00' -o short-iso-precise --no-pager
journalctl -b -u systemd-logind.service --since '2026-10-30 02:10:00' \
  --until '2026-10-30 02:16:00' -o short-iso-precise --no-pager
stat -c '%n modified=%y' /var/log/sysstat/sa30
sar -r -f /var/log/sysstat/sa30 -s 02:10:00 -e 02:15:00
```

La ventana general accesible contiene el traceback y fallo de `systemd`,
pero no los cuatro valores de la guarda. El journal del kernel sin
privilegios y los dos servicios de alimentación/sesión devolvieron
`-- No entries --`; esto **no** demuestra ausencia de eventos privilegiados.
`sudo -n` terminó con código 1 (`a password is required`). `sa30` tenía
cabecera **09/30/26** y fecha de modificación 30/09, por lo que no cubre
el 30/10. No se pidió contraseña ni se modificó el sistema.

La auditoría histórica y la comparación de huellas se reprodujeron con:

```bash
python3 docs/evidence/wf04-resource-diagnostic-20261030/checks.py \
  > docs/evidence/wf04-resource-diagnostic-20261030/results.json
```

`checks.py` abre solo ledger, supervisor, evidencias pequeñas y los archivos
de las cuatro raíces para calcular SHA-256. No carga datos de mercado ni
genera trayectorias. La comparación inicial y final dio los mismos mapas:
`...01 b93caafa…`, `...02 e11a6cfa…`, `...03 34270a3a…`,
`...04 3c22543a…`.

## Red, verde y regresión

Se ejecutó `uv run --frozen pytest -q tests/test_wf_resource_observability.py`
antes de modificar código: **6 fallos esperados** por ausencia del evento.
Tras el primer cambio: **6 passed**. Una nueva prueba del sensor ilegible
falló con `KeyError: values_observed`; tras etiquetar el valor sustituto:
**7 passed**.
Ruff detectó orden de imports en los dos archivos de comprobación nuevos;
se aplicó su ordenación automática y luego pasó. No se cambió código
operativo para satisfacer esa regla de estilo.

```bash
uv run --frozen pytest -q tests/test_wf_resource_observability.py
uv run --frozen pytest -q > /tmp/wf04-resource-full-pytest.log 2>&1
uv run --frozen ruff check .
```

La prueba focal final dio **7 passed en 0,83 s**, la suite completa
**454 passed en 302,01 s** y Ruff `All checks passed!`. Los logs
versionados conservan esas salidas. Las
cuatro banderas `MARKET_EXECUTION_ENABLED` se comprobaron `False` mediante
importación de sus módulos. No se ejecutó el comando público de campaña,
ningún trabajador histórico ni una unidad `systemd`.
