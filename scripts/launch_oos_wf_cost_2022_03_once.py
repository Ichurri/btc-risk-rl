"""Scheduled first admission; never retries a partial or failed campaign."""

import json
import subprocess
import sys
import time

from btc_risk_rl.pilots.protocol import ROOT
from btc_risk_rl.pilots.wf_cost_2022_03_launch import launch_once


def main() -> None:
    entry = ROOT / "scripts/run_oos_wf_cost_2022_03.py"

    def invoke(action: str) -> None:
        subprocess.run([sys.executable, str(entry), f"--{action}"],
                       cwd=ROOT, check=True)

    print(json.dumps(launch_once(now=time.time(), invoke=invoke),
                     sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
