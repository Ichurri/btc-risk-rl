"""Run only frozen P1; shared daily debits, no parameter or output overrides."""

import time

INVOKED_AT = time.time()


def main():
    import argparse
    import json

    from btc_risk_rl.pilots.p1_protocol import approved
    from btc_risk_rl.pilots.runner import run_campaign

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True)
    args = parser.parse_args()
    approved(args.protocol)
    state = run_campaign(INVOKED_AT, p1=True)
    print(
        json.dumps(
            dict(status=state["status"], cursor=state["cursor"], resources=state["resources"])
        )
    )
    return 1 if state["status"] in ("failed", "incomplete") else 0


if __name__ == "__main__":
    raise SystemExit(main())
