"""Single supervised night session: metered checks, then frozen training units."""

import argparse
import json


def main():
    from btc_risk_rl.pilots.oos_v12_launch import prepare_and_run

    parser = argparse.ArgumentParser()
    parser.add_argument("profile", choices=("wf-2021", "wf-2022", "main-2018-2022"))
    args = parser.parse_args()
    state = prepare_and_run(args.profile)
    print(json.dumps(dict(status=state["status"], cursor=state["cursor"],
                          accepted_units=len(state["units"]))), flush=True)
    if state["status"] in {"failed", "incomplete"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
