"""Read-only replacement preflight with protected-file open surveillance."""

import json
import subprocess
import sys
from pathlib import Path

from btc_risk_rl.pilots.protocol import ROOT


def main():
    opened = []
    shared = (ROOT / "data/processed/segmented-B-h1").resolve()

    def watch(event, args):
        if event != "open" or not isinstance(args[0], (str, bytes)):
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
            protected = (path.is_relative_to(shared) and path.suffix == ".csv")
            protected |= (path.suffix in {".csv", ".parquet"}
                          and ("validation" in path.parts or "final" in path.parts))
            if protected:
                raise PermissionError(f"Protected market file opened: {path}")

    sys.addaudithook(watch)
    from btc_risk_rl.pilots.wf_cost_replacement_04_exec import inspect_preflight
    from btc_risk_rl.pilots.wf_cost_source import inspect_fold

    result = inspect_preflight()
    folds = {year: inspect_fold(year) for year in ("2021", "2022")}
    payload = dict(preflight=result, fold_metadata=folds,
                   files_opened=sorted(set(opened)),
                   git_commit=subprocess.check_output(
                       ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                   protected_or_shared_csv_opened=False,
                   market_trajectories_generated=0, optimizer_steps=0)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
