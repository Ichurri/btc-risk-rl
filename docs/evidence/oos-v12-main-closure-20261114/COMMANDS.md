# Comandos del cierre OOS principal — 14/11/2026

Ejecutados en `/home/ichurri/Desktop/personal_projects/btc-risk-rl`.

```bash
systemctl --user start --no-block oos-v12-training.service
systemctl --user show oos-v12-training.service -p ActiveState -p SubState -p Result -p InvocationID
tail -n1 artifacts/oos-v12-training-main-01/ledger.jsonl
sha256sum artifacts/oos-v12-training-main-01/run-103-C10-b0/checkpoint-0/state.pt
uv run --frozen python -c 'from btc_risk_rl.pilots.oos_v12_training import read_budget; import json; x=read_budget("main-2018-2022"); print(json.dumps({k:x[k] for k in ("day_la_paz","global_spent","remaining_before_reserve","ok","active_campaigns") if k in x},sort_keys=True))'
journalctl --user -u oos-v12-training.service --since '2026-11-14 11:14:00' --until '2026-11-14 11:17:00' --no-pager -o short-iso > docs/evidence/oos-v12-main-closure-20261114/service-close-journal.txt
systemctl --user show oos-v12-training.service -p ActiveState -p SubState -p Result -p ExecMainCode -p ExecMainStatus -p ExecMainExitTimestamp -p ExecStopPost -p StateChangeTimestamp -p TimeoutStartUSec > docs/evidence/oos-v12-main-closure-20261114/service-state.txt
sha256sum docs/evidence/oos-v12-main-closure-20261114/*
```

La auditoría de la cadena y de todos los checkpoints se ejecutó con
`uv run --frozen python - <<'PY'` mediante el siguiente código. Se escribió
`closure.json` de forma atómica después de superar todas las comprobaciones:

```python
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from btc_risk_rl.pilots.p2_budget import state_hash

root = Path("artifacts/oos-v12-training-main-01")
ledger = root / "ledger.jsonl"
out = Path("docs/evidence/oos-v12-main-closure-20261114/closure.json")
previous = None
rows = 0
ledger_digest = hashlib.sha256()
with ledger.open("rb") as stream:
    for raw in stream:
        ledger_digest.update(raw)
        state = json.loads(raw)
        if state.get("previous_hash") != previous or state.get("state_hash") != state_hash(state):
            raise ValueError(f"ledger chain mismatch at row {rows + 1}")
        previous = state["state_hash"]
        rows += 1
if state["status"] != "completed" or state["cursor"] != 108 or state["pending"] is not None or len(state["units"]) != 1188:
    raise ValueError("final roster not complete")
by_run = {}
checkpoint_bytes = 0
for unit in state["units"]:
    run_id = unit["run_id"]
    by_run.setdefault(run_id, []).append(unit["unit"])
    checkpoint = Path(unit["checkpoint"]) / "state.pt"
    if not checkpoint.is_file():
        raise ValueError(f"missing checkpoint {checkpoint}")
    digest = hashlib.sha256()
    with checkpoint.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    if digest.hexdigest() != unit["checkpoint_sha256"]:
        raise ValueError(f"checkpoint mismatch {checkpoint}")
    checkpoint_bytes += checkpoint.stat().st_size
if len(by_run) != 108 or any(units != list(range(11)) for units in by_run.values()):
    raise ValueError("run order/units mismatch")
conditions = Counter(run_id.split("-")[2] for run_id in by_run)
if conditions != {"C0": 36, "C5": 36, "C10": 36}:
    raise ValueError(f"condition balance mismatch: {conditions}")
result = {
    "audited_utc": datetime.now(timezone.utc).isoformat(),
    "ledger": str(ledger),
    "ledger_sha256": ledger_digest.hexdigest(),
    "ledger_rows": rows,
    "final_state_hash": previous,
    "status": state["status"],
    "cursor": state["cursor"],
    "pending": state["pending"],
    "accepted_units": len(state["units"]),
    "runs": len(by_run),
    "conditions": dict(conditions),
    "complete_triplets": 36,
    "checkpoint_files_verified": len(state["units"]),
    "checkpoint_bytes_verified": checkpoint_bytes,
    "last_checkpoint": state["units"][-1]["checkpoint"],
    "last_checkpoint_sha256": state["units"][-1]["checkpoint_sha256"],
    "charged_wall_seconds_by_day": {day: value.get("charged_wall_seconds") for day, value in state["days"].items()},
}
tmp = out.with_suffix(".json.tmp")
with tmp.open("w") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
os.replace(tmp, out)
print(json.dumps(result, sort_keys=True))
```

La segunda consulta a `read_budget("main-2018-2022")` guardó en
`budget.json` solo las fuentes con cargo positivo, con sello UTC. La ejecución
fue de solo lectura sobre ledgers y bitácoras; la única escritura fue la
evidencia nueva en `docs/evidence/`.
