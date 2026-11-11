"""Print a read-only JSON audit of the original, completed 2021 OOS fold."""

import json

from btc_risk_rl.pilots.oos_v12_audit import audit_legacy_2021

if __name__ == "__main__":
    print(json.dumps(audit_legacy_2021(), sort_keys=True, allow_nan=False, indent=2))
