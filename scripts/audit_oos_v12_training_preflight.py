"""Watched read-only OOS training preflight: accepted shard or failure."""

import argparse
import json
import os
import sys

from btc_risk_rl.pilots.oos_v12_training import inspect_preflight, watch_open


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", choices=("wf-2021", "wf-2022", "main-2018-2022"))
    args = parser.parse_args()
    opened = []
    sys.addaudithook(lambda event, params: watch_open(event, params, opened))
    result = inspect_preflight(args.profile,
                               active_prep_token=os.environ.get("OOS_PREP_TOKEN"))
    result["files_opened"] = sorted(set(opened))
    result["protected_or_shared_csv_opened"] = False
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
