"""Run only the registered P0 campaign; no parameter/budget/output overrides."""

import argparse
import json
import time

INVOKED_AT = time.time()


def main():
    from btc_risk_rl.pilots.protocol import PROTOCOL, approved

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True)
    args = parser.parse_args()
    try:
        approved(args.protocol)
    except (ValueError, OSError):
        print(
            json.dumps(
                dict(
                    status="blocked",
                    reason="Unregistered protocol",
                    market_data_loaded=False,
                    parameter_updates=0,
                )
            )
        )
        return 2
    from btc_risk_rl.pilots.runner import run_campaign

    assert PROTOCOL.exists()
    state = run_campaign(INVOKED_AT)
    print(
        json.dumps(
            dict(status=state["status"], cursor=state["cursor"], resources=state["resources"])
        )
    )
    return 1 if state["status"] in {"failed", "incomplete"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
