# Primera terna principal: vista de entrenamiento

Esta carpeta contiene una **captura** de solo lectura del ledger principal
activo el 11/11/2026. SHA-256 del ledger en la captura:
`854f99aa962d662740cb5553bebae5eb5e6aa3c8bf6fcbaca6d83e505c651a6c`.
Había tres corridas y 33 unidades completas, con la unidad 1 de la cuarta
corrida pendiente. La tabla y el SVG excluyen esa unidad parcial.

| Archivo | SHA-256 | Alcance |
| --- | --- | --- |
| `main-2018-2022-854f99aa962d6627.md` | `66acbaafb15e0c3d62d3e71ae345ee60e5bce0d62672d9a2763bc0908a5dbe95` | Tiempos, recursos y huellas de C0/C5/C10, semilla 1869792951. |
| `main-2018-2022-854f99aa962d6627.svg` | `d41b8e6595ab32a37790a76174febc4381119ee911fcfe2ba57c4d77c3e9da08` | Avance de corridas completas, sin rendimiento financiero. |
| `actor-checks.json` | `41978da642123dae468ddd24720c2248f3466b359f22f778d3018cf070408bcc` | Lectura de checkpoints K10 congelados; no se evaluó una política. |

Comando de tabla y figura realmente ejecutado:

```bash
uv run --frozen python scripts/render_oos_v12_training_progress.py \
  --source-root /home/ichurri/Desktop/personal_projects/btc-risk-rl \
  --profile main-2018-2022 \
  --output-dir docs/evidence/oos-v12-main-progress-20261111
```

Para `actor-checks.json` se ejecutó `uv run --frozen python -` con un
programa de solo lectura que tomó los tres K10 aceptados del ledger, cotejó
el SHA-256 del manifiesto H1 exclusivo de entrenamiento y llamó a
`load_oos_final_actor` con seed, condición, contadores y huella esperados.
Esta evidencia demuestra compatibilidad de carga, no viabilidad técnica de
2023 ni resultado fuera de muestra. La campaña principal continúa y el
ledger final tendrá otra huella.
