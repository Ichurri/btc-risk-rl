"""Replacement fold-cost worker; denied before request or data access."""

import json
import sys
from pathlib import Path


def main():
    from btc_risk_rl.pilots.wf_cost_replacement_05_exec import require_campaign

    require_campaign()  # Must precede request read, torch import, and source construction.
    if len(sys.argv) != 2:
        raise SystemExit("Expected one registered WF cost request")
    import torch

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    if torch.version.cuda is not None:
        raise ValueError("CPU-only PyTorch required")
    from btc_risk_rl.pilots.p2_runner import complete_unit
    from btc_risk_rl.pilots.wf_cost_replacement_05_exec import WFCostPermit, WFCostSettings
    from btc_risk_rl.pilots.wf_cost_source import build_fold_source

    request_path = Path(sys.argv[1])
    request = json.loads(request_path.read_text())
    permit = WFCostPermit(request.get("token"))
    permit.validate_request(request_path, request)
    fold = request.pop("fold")
    settings = WFCostSettings(**request.pop("settings"))
    request.pop("token")
    request.pop("config")
    source = build_fold_source(fold)
    permit.validate_d(source, settings.seed, request["run_id"])
    complete_unit(source, settings, permit=permit, n_d=64, **request)


if __name__ == "__main__":
    main()
