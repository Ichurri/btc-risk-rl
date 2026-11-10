"""One scheduled OOS training session, with frozen roster and complete pauses."""

import json

from btc_risk_rl.pilots.oos_v12_launch import run_nightly


def main():
    print(json.dumps({"nightly_result": run_nightly()}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
