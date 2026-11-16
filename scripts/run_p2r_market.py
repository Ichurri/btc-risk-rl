"""P2R historical supervisor entry; disabled until separate campaign approval."""

import json

from btc_risk_rl.pilots.p2r_market import run_market_units


def main():
    try:
        result = run_market_units()
    except PermissionError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(dict(status=result["status"], units=len(result["units"]))))
    if result["status"] in {"failed", "incomplete"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
