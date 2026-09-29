"""P2 infrastructure only. Market command remains blocked before all data access."""

import argparse
import json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--protocol")
    parser.add_argument("--output", default="artifacts/p2-approved-v1-synthetic")
    parser.add_argument("--config", default="configs/initial.toml")
    args = parser.parse_args()
    if args.profile != "synthetic":
        from btc_risk_rl.pilots.p2_market import P2MarketPermit
        try:
            P2MarketPermit.require_registration(args.protocol)
        except (PermissionError, ValueError, TypeError, OSError, KeyError):
            parser.exit(2, "P2 market NOT AUTHORIZED: no registered campaign permit.\n")
    from btc_risk_rl.pilots.p2 import entrypoint
    result = entrypoint(profile=args.profile, output=args.output, config=args.config,
                        protocol=args.protocol)
    print(json.dumps(dict(status=result["status"], resources=result["resources"])))


if __name__ == "__main__":
    main()
