"""Read-only replacement WF preflight or separately authorized campaign."""

import argparse
import json

from btc_risk_rl.pilots.wf_cost_replacement_05_exec import inspect_preflight, run_historical_units


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--preflight", action="store_true")
    choice.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(inspect_preflight(), indent=2, sort_keys=True))
        return
    try:
        state = run_historical_units()
    except PermissionError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(dict(status=state["status"], units=len(state["units"]))))
    if state["status"] in {"failed", "incomplete"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
