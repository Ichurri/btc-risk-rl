import argparse
import json
from pathlib import Path

from btc_risk_rl.config import load_config
from btc_risk_rl.data.binance import fetch_development
from btc_risk_rl.data.pipeline import prepare_development
from btc_risk_rl.data.recheck import recheck_anomalies


def main():
    parser = argparse.ArgumentParser(description="Development only; final test locked")
    parser.add_argument("--config", type=Path, default=Path("configs/initial.toml"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("config-check")
    fetch = sub.add_parser("fetch-development")
    fetch.add_argument("--output", type=Path, default=Path("data/raw/development"))
    prepare = sub.add_parser("prepare-development")
    prepare.add_argument("--raw", type=Path, default=Path("data/raw/development"))
    prepare.add_argument("--output", type=Path, default=Path("data/processed/development"))
    recheck = sub.add_parser("recheck-anomalies")
    recheck.add_argument("--raw", type=Path, default=Path("data/raw/development"))
    recheck.add_argument("--output", type=Path, default=Path("data/raw/recheck"))
    args = parser.parse_args()
    config = load_config(args.config)
    if args.command == "config-check":
        result = {
            "valid": True,
            "status": config.status,
            "training_enabled": False,
            "final_test_locked": True,
        }
    elif args.command == "fetch-development":
        manifest = fetch_development(config, args.output)
        result = {
            "status": manifest["status"],
            "pages": len(manifest["pages"]),
            "final_test_accessed": False,
        }
    elif args.command == "recheck-anomalies":
        audit = recheck_anomalies(config, args.raw, args.output)
        result = {"counts": audit["counts"], "final_test_accessed": False}
    else:
        manifest = prepare_development(config, args.raw, args.output)
        result = {
            "status": manifest["status"],
            "partitions": manifest["partitions"],
            "final_test_accessed": False,
        }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
