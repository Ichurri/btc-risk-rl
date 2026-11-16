# P2R — señal SIGTERM durante Q0 sintética

**Resultado:** la señal enviada al proceso principal mientras Q0 estaba
activa invalidó permanentemente la unidad. Ambos ledgers acabaron en `failed`
con `interrupted_supervisor_or_unit`, sin `unit_completed` y con **cero
checkpoints completos y aceptados**. Como Q0 era la primera unidad, no había
un checkpoint anterior que conservar: esta sonda no prueba la conservación de
uno previo a una interrupción posterior. La primera ejecución reveló un
defecto en el estado de salida de la CLI; se corrigió y repitió solo la
comprobación de señal con unidad y raíz nuevas. En la repetición systemd
registró `Result=exit-code`, estado 1.

## Alcance y cronología

Ambas unidades usaron exclusivamente `scripts/run_p2r.py --profile synthetic
--mode algorithm --hold-seconds 120 --max-units 1`, condición sintética C5,
configuración `configs/initial.toml` y rutas `SyntheticMarket`. La espera de
120 s dejaba Q0 abierta para la señal; no se completó ninguna transición de
aprendizaje aceptada. Antes de cada lanzamiento, la guarda de recursos dio
`ready`, el gestor de usuario estaba `running`, la unidad y la raíz no
existían y no había otra unidad P2R activa. El ledger consignó cero segundos
externos del presupuesto P2R en el día. No se usaron histórico, validación ni
prueba final.

| Sonda | Código | Unidad / `InvocationID` | Inicio Q0 UTC | SIGTERM UTC | Cierre supervisor UTC | Ledger / systemd |
| --- | --- | --- | --- | --- | --- | --- |
| 04 | `c105816` | `p2r-signal-q0-review-04.service` / `38c31c62089643b78dc517b8a145adad` | 19:18:04.058151 | 19:18:30.288424 | 19:18:30.358666 | `failed` / `success` (defecto) |
| 05 | `08c0fda` | `p2r-signal-q0-review-05.service` / `925cd90d9584425bac73d3612c7cb278` | 19:25:41.041686 | 19:26:03.068285 | 19:26:03.199927 | `failed` / `exit-code`, estado 1 |

Las horas son del 05/10/2026 UTC. En 04 el journal systemd sitúa el envío
al PID principal 60099 a las 19:18:30.288409 UTC; en 05 lo sitúa al PID
61402 a las 19:26:03.068183 UTC. El comando fue, respectivamente,
`systemctl --user kill --kill-whom=main --signal=SIGTERM
p2r-signal-q0-review-04.service` y el mismo con sufijo `05`; ambos devolvieron
0. El ledger estaba `running`, con `pending.unit=0`, cero unidades aceptadas
y heartbeats Q0 antes de la señal. Los workers devolvieron `-15`, el
supervisor emitió `signal`, `unit_failed` y `supervisor_exit` de la misma
invocación. Hubo siete y seis heartbeats, respectivamente. En la sonda 05,
los cinco intervalos completos registrados fueron de 4.126–4.156 s; no se
relajó el límite de 5 s.

El defecto de la primera sonda era externo al ledger: `run_p2r.py` imprimía
`{"status":"failed","units":0}` pero terminaba con código cero. systemd
consideró exitosa la unidad aunque el supervisor la hubiera invalidado. El
commit `08c0fda` añade salida no cero si el resultado es `failed` y una
regresión para la CLI. La repetición 05 confirmó la correspondencia entre
ledger y systemd. La raíz y el journal de 04 permanecieron intactos.

## Integridad y evidencias

El [validador de solo lectura](../evidence/p2r-signal-q0/checks.py) comprobó
ambas cadenas SHA-256 (`P2RJournal` y ledger), secuencia y tiempos de eventos,
un único `InvocationID` por sonda, señal 15, fallo irreversible, cero
`unit_completed`, cero entradas `units` y ausencia de directorios de
checkpoint. Sus [resultados](../evidence/p2r-signal-q0/results.json) y el
[manifiesto de 28 archivos](../evidence/p2r-signal-q0/SHA256SUMS.txt) están
versionados. `sha256sum -c` dio 28/28. Las raíces completas están fuera de
Git:

- `artifacts/p2r-synthetic-signal-q0-review-04` y
  `artifacts/p2r-signal-q0-review-04-record`;
- `artifacts/p2r-synthetic-signal-q0-review-05` y
  `artifacts/p2r-signal-q0-review-05-record`.

Los SHA-256 de los ledgers son `e9b845ee065aaf1a09cfeb87e1941aa9877fcea285ff3fd69c8a41d6ee006d85`
(04) y `d59721dfadaafd9bd47de2efbf148d99cbffc92f628f89071f47b161f925859d`
(05). El manifiesto incluye también los journals, requests, logs de worker,
comandos, estados y capturas del journal de systemd. Se comprobaron además
18/18 hashes de la sonda 03, 32/32 de la 02 y las cuatro huellas principales
de la 01, sin editar esas raíces. Se mantuvo fuera de los commits la
eliminación local previa de `.python-version`.

## Pruebas y límite de la conclusión

La prueba nueva de salida no cero falló inicialmente, pasó tras la corrección;
el test existente de señal dentro de unidad pasó. `uv run --frozen pytest -q`
dio **267 passed** en 180.85 s y `uv run --frozen ruff check .` pasó tras
ordenar un import de la nueva prueba. Los comandos exactos y distinción entre
pruebas y sondas están en
[COMMANDS.md](../evidence/p2r-signal-q0/COMMANDS.md).

Esta evidencia demuestra el rechazo de una **Q0 sintética** interrumpida por
SIGTERM al proceso principal en este host y la propagación correcta del fallo
a systemd después de la corrección. No prueba una interrupción del host, una
señal durante Q/A/B+D, conservación de un checkpoint previo ante fallo de una
unidad siguiente, aprendizaje con mercado ni rentabilidad o CVaR. La campaña
histórica P2R sigue sin permiso ni ejecutor; P2 fallido no se reanuda. Antes de
un eventual histórico hacen falta la adopción del protocolo P2R, ejecutor
train-only con huellas y preflight propios, verificación completa de ambas
fronteras y autorización explícita. La tesis no se modificó.
