"""Build the offline thesis experiment report from accepted local evidence."""

import argparse
from pathlib import Path

from btc_risk_rl.reporting.experiments import build


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True,
                        help="Checkout that contains the original local artifacts")
    parser.add_argument("--output", type=Path, required=True,
                        help="HTML path outside the original artifacts")
    args = parser.parse_args()
    campaigns = build(args.source_root, args.output)
    for campaign in campaigns:
        print(f"{campaign.name}: {campaign.state['status']}; "
              f"{campaign.complete_runs} complete runs; {len(campaign.units)} accepted units; "
              f"ledger SHA-256 {campaign.ledger_sha256}")
    print(f"HTML: {args.output.resolve()}")


if __name__ == "__main__":
    main()
