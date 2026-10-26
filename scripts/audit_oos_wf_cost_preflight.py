"""Read-only WF cost preflight with an open-file audit; writes JSON to stdout."""

import json
import subprocess
import sys
from pathlib import Path

from btc_risk_rl.pilots.protocol import ROOT


def main():
    opened = []
    shared = (ROOT / "data/processed/segmented-B-h1").resolve()

    def watch(event, args):
        if event != "open":
            return
        raw = args[0]
        if not isinstance(raw, (str, bytes)):
            return
        path = Path(raw.decode() if isinstance(raw, bytes) else raw)
        if not path.is_absolute():
            path = Path.cwd() / path
        path = path.resolve()
        if path.is_relative_to(shared) and path.suffix == ".csv":
            raise PermissionError("Shared H1 CSV opened by WF cost preflight")
        if path.is_relative_to(ROOT):
            opened.append(str(path))

    sys.addaudithook(watch)
    from btc_risk_rl.pilots.wf_cost import digest, inspect_preflight
    from btc_risk_rl.pilots.wf_cost_source import inspect_fold

    result = inspect_preflight()
    folds = {year: inspect_fold(year) for year in ("2021", "2022")}

    def relative(value):
        if isinstance(value, dict):
            return {relative(k): relative(v) for k, v in value.items()}
        if isinstance(value, list):
            return [relative(item) for item in value]
        if isinstance(value, str) and value.startswith(str(ROOT) + "/"):
            return value[len(str(ROOT)) + 1:]
        return value

    payload = dict(preflight=result, fold_metadata=folds,
                   files_opened=sorted(set(opened)),
                   git_commit=subprocess.check_output(
                       ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                   ).strip(),
                   code_sha256={str(path.relative_to(ROOT)): digest(path)
                                for path in (
                                    ROOT / "src/btc_risk_rl/pilots/wf_cost.py",
                                    ROOT / "src/btc_risk_rl/pilots/wf_cost_source.py",
                                    ROOT / "src/btc_risk_rl/pilots/wf_cost_units.py",
                                    ROOT / "src/btc_risk_rl/pilots/wf_cost_worker.py",
                                    ROOT / "scripts/run_oos_wf_cost.py",
                                    ROOT / "scripts/audit_oos_wf_cost_preflight.py",
                                    ROOT / "uv.lock",
                                )},
                   shared_h1_csv_opened=False,
                   market_trajectories_generated=0,
                   optimizer_steps=0)
    print(json.dumps(relative(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
