"""P2R synthetic lifecycle probe. Historical execution has no public entrypoint."""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output")
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--fixture-window", action="store_true",
                        help="synthetic lifecycle test window only; never a market budget override")
    args = parser.parse_args()
    if args.profile != "synthetic":
        parser.exit(2, "P2R market NOT AUTHORIZED: no campaign permit or executor.\n")
    if args.output is None or not 0 < args.sleep_seconds <= 60:
        parser.error("Synthetic output and sleep 0–60 seconds required")
    from btc_risk_rl.pilots.p2r import run_fixture_unit
    root = Path(args.output).resolve()
    result = run_fixture_unit(root, [sys.executable, "-c",
                                     f"import time; time.sleep({args.sleep_seconds!r})"],
                              artifacts=root.parent, require_service=True,
                              fixture_window=args.fixture_window)
    print(json.dumps(dict(status=result["status"], units=len(result["units"]))))


if __name__ == "__main__":
    main()
