"""Guarded entry to one frozen OOS v1.2 training-only campaign."""

import argparse


def main():
    from btc_risk_rl.pilots.oos_v12_training import run_historical_units

    parser = argparse.ArgumentParser()
    parser.add_argument("profile", choices=("wf-2021", "wf-2022", "main-2018-2022"))
    args = parser.parse_args()
    run_historical_units(args.profile)


if __name__ == "__main__":
    main()
