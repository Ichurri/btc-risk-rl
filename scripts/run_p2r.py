"""P2R synthetic lifecycle and algorithm probes; no historical entrypoint."""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--mode", choices=("fixture", "algorithm"), default="fixture")
    parser.add_argument("--output")
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--hold-seconds", type=int, default=0,
                        help="0–900 seconds inside the supervised synthetic algorithm unit")
    parser.add_argument("--max-units", type=int)
    parser.add_argument("--fixture-window", action="store_true",
                        help="synthetic lifecycle test window only; never a market budget override")
    args = parser.parse_args()
    if args.profile != "synthetic":
        parser.exit(2, "P2R market NOT AUTHORIZED: no campaign permit or executor.\n")
    if args.output is None:
        parser.error("Synthetic output required")
    root = Path(args.output).resolve()
    if args.mode == "fixture":
        if args.hold_seconds:
            parser.error("Hold is available only for the synthetic algorithm probe")
        if not 0 < args.sleep_seconds <= 60:
            parser.error("Synthetic sleep must be 0–60 seconds")
        from btc_risk_rl.pilots.p2r import run_fixture_unit
        result = run_fixture_unit(root, [sys.executable, "-c",
                                         f"import time; time.sleep({args.sleep_seconds!r})"],
                                  artifacts=root.parent, require_service=True,
                                  fixture_window=args.fixture_window)
    else:
        from btc_risk_rl.pilots.p2 import P2SyntheticSettings
        from btc_risk_rl.pilots.p2r_units import run_synthetic_units
        settings = P2SyntheticSettings(iterations=2, hidden=4, n_a=1, n_q=2,
                                       n_b=2, actor_epochs=1, critic_epochs=4,
                                       seed=610031)
        result = run_synthetic_units(root, Path("configs/initial.toml"), settings,
                                     "C5", max_units=args.max_units,
                                     fixture_window=args.fixture_window,
                                     require_service=True,
                                     synthetic_hold_seconds=args.hold_seconds)
    print(json.dumps(dict(status=result["status"], units=len(result["units"]))))
    if result["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
