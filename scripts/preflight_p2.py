"""Read-only P2 accepted-training preflight; never starts a campaign."""
import json

from btc_risk_rl.pilots.p2_market import inspect_preflight

if __name__ == "__main__":
    print(json.dumps(inspect_preflight(), sort_keys=True, allow_nan=False))
