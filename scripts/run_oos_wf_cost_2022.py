"""Closed public boundary for a future 2022-only WF cost study."""

import argparse

from btc_risk_rl.pilots.wf_cost_2022_orchestrator import require_campaign


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", required=True)
    parser.parse_args()
    try:
        require_campaign()
    except PermissionError as exc:
        raise SystemExit(str(exc)) from exc
    raise SystemExit("WF 2022 historical executor is not implemented")


if __name__ == "__main__":
    main()
