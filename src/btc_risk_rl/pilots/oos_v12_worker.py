"""Training-only OOS worker; closed gate precedes request and market reads."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def run_request(profile: str, path: str | Path):
    from btc_risk_rl.pilots.oos_v12_training import (
        OOSPermit,
        OOSSettings,
        require_campaign,
        source_for,
    )

    require_campaign()
    import torch

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    if torch.version.cuda is not None:
        raise ValueError("CPU-only PyTorch required")
    from btc_risk_rl.pilots.p2_runner import complete_unit

    path = Path(path)
    request = json.loads(path.read_text())
    permit = OOSPermit(request.get("token"), profile)
    permit.validate_request(path, request)
    settings = OOSSettings(**request.pop("settings"))
    beta = request.pop("beta")
    if type(beta) is not int or beta != 0:
        raise PermissionError("OOS worker critic beta changed")
    request.pop("token")
    request.pop("config")
    permit.validate(settings, request["condition"], request["run_id"])
    source = source_for(profile)
    permit.validate_d(source, settings.seed, request["run_id"])
    return complete_unit(source, settings, permit=permit, n_d=64, **request)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Expected OOS profile and registered request path")
    run_request(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
