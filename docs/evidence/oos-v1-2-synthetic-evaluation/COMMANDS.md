# Comandos y evidencia — evaluación sintética v1.2

Base `1d976d9`; rama `codex/oos-v1-2-synthetic-evaluator`. Todo lo siguiente
usa series fabricadas y una raíz ignorada por Git. El único checkpoint
leído es el P3 fijo por huella, sin selección ni actualización. La
eliminación local previa de `.python-version` no se versiona.

## Pruebas de código ejecutadas

```bash
git status --short --branch
git log -3 --oneline
uv run --frozen pytest -q tests/test_oos_synthetic_evaluation.py
uv run --frozen ruff check .
uv run --frozen pytest -q
```

TDD: cinco pruebas fallaron inicialmente por ausencia del módulo; tras la
implementación, ocho pasaron. Dos comprobaciones adicionales se observaron
fallar antes de corregir el auditor: costo de deslizamiento alterado y acción
que no coincide con exposición posterior a costos. La prueba de ruta completa
también detectó que faltaba publicar la lista de archivos abiertos en el
cierre; se corrigió. Un noveno test alteró el total de comisiones declarado
por el trabajador, comprobó que el padre inicialmente lo aceptaba y luego
que el cierre falla tras el cotejo. Última ejecución focal: **9/9**. Ruff:
**sin hallazgos**. Una suite completa iniciada mientras se cambiaba código
dio 358/359: el test P2R de huella de procedencia falló durante el cambio;
su repetición aislada pasó. La siguiente dio 359/360 por la carrera de
`test_supervisor_death_kills_worker`: `/proc/<pid>/status` desapareció con
`ProcessLookupError`, caso de proceso ya terminado que el test antiguo solo
capturaba como `FileNotFoundError`. Se amplió **solo la excepción del test**;
no cambió el supervisor ni P0. La prueba focal posterior dio 10/10 y la
suite completa final, con código congelado, **360/360 en 255,76 s**.

## Serie sintética medida y control final del código

Se ejecutó en Bash una unidad por fila, secuencialmente. El patrón exacto de
invocación fue el siguiente; `{tag}`, `{steps}` y `{unit}` se sustituyeron con
la tabla. `TIMEFORMAT` es el tiempo de pared del **comando entero**;
`systemd-run --wait` incluye inicio y terminación del servicio.
Los cuatro procesos de esta tabla precedieron únicamente al último cotejo
de totales de costos del padre; la unidad de control posterior verificó ese
código final y conservó la misma traza.

```bash
TIMEFORMAT='elapsed_wall_seconds=%3R user_seconds=%3U system_seconds=%3S'
{ time systemd-run --user --wait --collect --unit={unit} \
    --working-directory=/home/ichurri/Desktop/personal_projects/btc-risk-rl \
    --property=MemoryAccounting=yes --property=CPUAccounting=yes \
    /home/ichurri/Desktop/personal_projects/btc-risk-rl/.venv/bin/python \
    /home/ichurri/Desktop/personal_projects/btc-risk-rl/scripts/run_oos_synthetic_evaluation.py \
    --output /home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-synthetic-evaluation-20261026-final/run-{tag} \
    --steps {steps} \
    > artifacts/oos-synthetic-evaluation-20261026-final/launch-{tag}.log; } \
  2> artifacts/oos-synthetic-evaluation-20261026-final/outer-{tag}-time.txt
```

| `{tag}` | `{steps}` | `{unit}` | `InvocationID` | Resultado |
| --- | ---: | --- | --- | --- |
| `1979` | 1979 | `oos-v12-synthetic-final-1979` | `ced779991a234719bf87d7818e023e93` | success |
| `2190-a` | 2190 | `oos-v12-synthetic-final-2190-a` | `cbf4c42fc7c746debbbcc99cdceb5af0` | success |
| `2190-b` | 2190 | `oos-v12-synthetic-final-2190-b` | `a58f4c84ab1a46e793b0c94f6b8efbd8` | success |
| `4386-final` | 4386 | `oos-v12-synthetic-final-4386` | `6973a288d5ff4a3f989e2ad3069c1fcb` | success |

Para cada unidad se ejecutaron:

```bash
journalctl --user -u {unit}.service --no-pager -o short-iso-precise > artifacts/oos-synthetic-evaluation-20261026-final/journal-{tag}.log
journalctl --user -u {unit}.service --no-pager -o json > artifacts/oos-synthetic-evaluation-20261026-final/journal-{tag}.jsonl
```

La primera serie de cuatro sondas quedó en
`artifacts/oos-synthetic-evaluation-20261026/`; se repitió con unidad y raíz
nuevas después de añadir los cotejos finales de exposición y normalizador.
**Solo** las cuatro unidades `-final` alimentan los tiempos publicados. Antes
del primer lanzamiento se intentó `/usr/bin/time`; no estaba instalado y no
se inició la unidad. Se usó el `time` integrado de Bash. Ninguna sonda
generó trayectorias históricas.

Tras añadir el cotejo final de costos se lanzó otra unidad sintética,
`oos-v12-synthetic-guard-2190.service`, con salida nueva
`artifacts/oos-synthetic-evaluation-20261026-guard/run-2190`.
El comando ejecutado fue:

```bash
TIMEFORMAT='elapsed_wall_seconds=%3R user_seconds=%3U system_seconds=%3S'
{ time systemd-run --user --wait --collect \
    --unit=oos-v12-synthetic-guard-2190 \
    --working-directory=/home/ichurri/Desktop/personal_projects/btc-risk-rl \
    --property=MemoryAccounting=yes --property=CPUAccounting=yes \
    /home/ichurri/Desktop/personal_projects/btc-risk-rl/.venv/bin/python \
    /home/ichurri/Desktop/personal_projects/btc-risk-rl/scripts/run_oos_synthetic_evaluation.py \
    --output /home/ichurri/Desktop/personal_projects/btc-risk-rl/artifacts/oos-synthetic-evaluation-20261026-guard/run-2190 \
    --steps 2190 \
    > artifacts/oos-synthetic-evaluation-20261026-guard/launch-2190.log; } \
  2> artifacts/oos-synthetic-evaluation-20261026-guard/outer-2190-time.txt
```

`InvocationID=0da25de4b6434fd38ac5e06d5d0a4109`, `Result=success`,
wall externo 7,916 s y pico systemd 622,7 MB. Se guardaron también journal
legible y JSON. La traza coincide byte por byte con las dos de 2.190 pasos
anteriores. No se reemplazaron las mediciones anteriores; las tres entran en
la media aritmética de la extrapolación sintética. Los hashes de todos los
logs y cierres constan en [results.json](results.json).

## Auditoría y rechazos ejecutados

```bash
uv run --frozen python docs/evidence/oos-v1-2-synthetic-evaluation/checks.py
uv run --frozen python scripts/run_oos_synthetic_evaluation.py --output artifacts/oos-synthetic-evaluation-20261026/forbidden-market --steps 1979 --market-path forbidden
uv run --frozen python scripts/run_oos_synthetic_evaluation.py --output artifacts/p3-approved-v1/oos-intrusion --steps 1979
uv run --frozen python -m btc_risk_rl.evaluation.synthetic_runner --worker artifacts/p3-approved-v1
uv run --frozen python docs/evidence/p3-permit-closure/audit_artifact_tree.py
sha256sum artifacts/p0-approved-v1/ledger.jsonl artifacts/p1-approved-v1/ledger.jsonl artifacts/p2-approved-v1/ledger.jsonl artifacts/p2r-approved-v2/ledger.jsonl artifacts/p3-approved-v1/ledger.jsonl data/processed/p2r-training-h1/manifest.json
du -sb artifacts/oos-synthetic-evaluation-20261026-final
```

Los tres comandos de rechazo devolvieron respectivamente códigos **2, 1 y
1**, antes de crear salidas protegidas. `checks.py` cotejó cierre, journal,
traza, auditoría, SHA, reproducibilidad y semillas del protocolo documental;
su [JSON](results.json) da rutas, memoria, tiempos y huellas individuales.
SHA-256 del JSON: `ed24b454a509c4b2a6c2108338b7d505600b64b70c3585b3c20e623d9a9b32e9`.
SHA-256 de `synthetic.py`:
`5d7cfe88e1d8332ffd3bcf25aa8743b2d214183e45c84b2b7502b21bcdd30d1e`;
de `synthetic_runner.py`:
`19427664ae5d66089386864b2005112377ea3b99db1eaa8788ea5d56037d7cae`.
Las raíces de medición final y control de guardia ocuparon, respectivamente,
3.269.017 y 668.232 B.

Los ledgers originales leídos conservan estas SHA-256:

| Evidencia | SHA-256 |
| --- | --- |
| P0 | `1d1ee72ca0ac49529f205b30942a68f381d86037e336091c490c624098339b8c` |
| P1 | `926eab40bc764e1cae88a74e6718ba70b50e2df0626e8e34964078cc4ba55755` |
| P2 | `e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8` |
| P2R | `fe443e5e32d26a7de075fa6e34771c8f20651bbe566f9097bfdb367d17d0b866` |
| P3 | `86b111b5365cda1760441d2f73d42e0463a4b4b2a7ddbc6e0e41f2a78751fcfe` |
| Manifiesto H1 exclusivo de entrenamiento | `62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9` |

Datos originales y trazas sintéticas voluminosas quedan locales, fuera de Git.
Los documentos, el script de auditoría y los resultados pequeños sí se
versionan. No hay raíz ni permiso para la medición de entrenamiento propuesta.
