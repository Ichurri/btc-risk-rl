"""P3 historical supervisor entry, disabled until separate reviewed approval."""

import json

from btc_risk_rl.pilots.p3_market import run_market_units


def main():
    try:
        state = run_market_units()
    except PermissionError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(dict(status=state["status"], units=len(state["units"]))))
    if state["status"] in {"failed", "incomplete"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
