# P3 — sesión 02 y auditoría de cierre

El 13/10/2026, con la rama `codex/p3-market-campaign` en
`7dd4459` y solo la eliminación local previa de `.python-version`, se
repitieron las guardas de Git, ledger `ready`, `pending=null`, 116
unidades, ausencia de otra unidad P3 activa, CA, batería, `Linger` y
gestor de usuario. Se ejecutó:

```bash
uv run --frozen python docs/evidence/p3-market-2026-10-13/preflight-session02.py
sha256sum docs/evidence/p3-market-2026-10-13/preflight-session02.json
systemd-run --user --unit=p3-market-v1-session-02.service --service-type=exec \
  --description='P3 v1.1 approved historical development diagnostic session 02' \
  --working-directory=/home/ichurri/Desktop/personal_projects/btc-risk-rl \
  --setenv=PYTHONUNBUFFERED=1 \
  /home/ichurri/Desktop/personal_projects/btc-risk-rl/.venv/bin/python \
  /home/ichurri/Desktop/personal_projects/btc-risk-rl/scripts/run_p3_market.py
systemctl --user show p3-market-v1-session-02.service \
  -p ActiveState -p SubState -p Result -p ExecMainStatus -p InvocationID
```

El preflight dio `read_only_ready_campaign_enabled`; no abrió CSV H1
compartidos ni generó trayectorias. Su SHA-256 fue
`f0dbb3ad0577ca5cec652b8a67be6271c4a047241ad6bee0abf76d34bff6adcc`.
El servicio recibió `InvocationID=629b6812dc79470e876a5ec7670e801a`.

Tras `completed` y salida de systemd con código 0, los comandos de
lectura ejecutados fueron:

```bash
uv run --frozen python docs/evidence/p3-market-2026-10-13/final-audit.py \
  > docs/evidence/p3-market-2026-10-13/final-closure.json
journalctl --user -u p3-market-v1-session-02.service \
  -o short-iso-precise --no-pager \
  > docs/evidence/p3-market-2026-10-13/systemd-session02.txt
uv run --frozen python docs/evidence/p3-market-2026-10-13/final-audit.py \
  | cmp - docs/evidence/p3-market-2026-10-13/final-closure.json
uv run --frozen ruff check docs/evidence/p3-market-2026-10-13/preflight-session02.py \
  docs/evidence/p3-market-2026-10-13/final-audit.py
sha256sum docs/evidence/p3-market-2026-10-13/preflight-session02.json \
  docs/evidence/p3-market-2026-10-13/final-closure.json \
  docs/evidence/p3-market-2026-10-13/systemd-session02.txt
git diff --check
```

La primera versión del auditor comprobó erróneamente igualdad directa
entre claves enteras de `blocks` recalculadas y claves de texto
serializadas en JSON; falló sin alterar la campaña. Se corrigió la
comparación con una ida y vuelta JSON. La auditoría posterior pasó dos
veces con salida idéntica. Ruff pasó; no se repitió Pytest porque el
algoritmo no cambió. Huellas: cierre JSON
`1d96dd5ed2cb4af27a0f3993501ea7c40ece67ccc5862fe0f9d7b0049c033c6d`,
journal de systemd
`71de380c7018808fde9a8ffdb74211f1382b0329ce1148ad6d375758450111a2`.
