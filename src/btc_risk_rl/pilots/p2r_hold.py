"""Bounded synthetic hold before the existing P2 synthetic worker.

The process remains the supervised child throughout the wait and then execs
the worker in the same PID. It has no market-request option.
"""

import os
import sys
import time
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        raise ValueError("Synthetic hold requires seconds and one request")
    try:
        seconds = int(sys.argv[1])
    except ValueError as exc:
        raise ValueError("Invalid synthetic hold seconds") from exc
    request = Path(sys.argv[2])
    if not 0 <= seconds <= 900 or not request.is_absolute() or request.suffix != ".json":
        raise ValueError("Invalid synthetic hold or request")
    time.sleep(seconds)
    os.execv(sys.executable, [sys.executable, "-m", "btc_risk_rl.pilots.p2_runner",
                              "--synthetic-request", str(request)])


if __name__ == "__main__":
    main()
