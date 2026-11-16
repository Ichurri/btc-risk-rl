"""Read-only WF 2022 preflight with a closed market-data open allowlist."""

import json
import subprocess
import sys
from pathlib import Path

from btc_risk_rl.pilots.protocol import ROOT


def main():
    opened = []
    training_shard = (ROOT / "data/processed/p2r-training-h1").resolve()
    data = (ROOT / "data").resolve()

    def watch(event, args):
        if event != "open" or not args or not isinstance(args[0], (str, bytes)):
            return
        raw = args[0]
        path = Path(raw.decode() if isinstance(raw, bytes) else raw)
        if not path.is_absolute():
            path = Path.cwd() / path
        path = path.resolve()
        if path.is_relative_to(ROOT):
            relative = path.relative_to(ROOT)
            if relative.parts[0] not in {".venv", "src"}:
                opened.append(str(relative))
            if path.is_relative_to(data) and not path.is_relative_to(training_shard):
                raise PermissionError(f"WF 2022 protected market file opened: {path}")

    sys.addaudithook(watch)
    from btc_risk_rl.pilots.wf_cost_2022_03_exec import inspect_preflight
    from btc_risk_rl.pilots.wf_cost_source import inspect_fold

    result = inspect_preflight()
    fold = inspect_fold("2022")
    payload = dict(preflight=result, fold_metadata=fold,
                   files_opened=sorted(set(opened)),
                   git_commit=subprocess.check_output(
                       ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                   protected_or_shared_csv_opened=False,
                   market_trajectories_generated=0, optimizer_steps=0)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
