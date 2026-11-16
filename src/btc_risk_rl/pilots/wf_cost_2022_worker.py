"""Historical WF 2022 worker; rejects closed permits before reading a request."""

import json
import sys
from pathlib import Path


def run_request(path):
    from btc_risk_rl.pilots.wf_cost_2022_exec import require_campaign

    require_campaign()
    import torch

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    if torch.version.cuda is not None:
        raise ValueError("CPU-only PyTorch required")
    from btc_risk_rl.pilots.p2_runner import complete_unit
    from btc_risk_rl.pilots.wf_cost import WFCostSettings
    from btc_risk_rl.pilots.wf_cost_2022_exec import WF2022Permit
    from btc_risk_rl.pilots.wf_cost_source import build_fold_source

    path = Path(path)
    request = json.loads(path.read_text())
    permit = WF2022Permit(request.get("token"))
    permit.validate_request(path, request)
    request.pop("fold")
    settings = WFCostSettings(**request.pop("settings"))
    request.pop("token")
    request.pop("config")
    source = build_fold_source("2022")
    permit.validate_d(source, settings.seed, request["run_id"])
    return complete_unit(source, settings, permit=permit, n_d=64, **request)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Expected one registered WF 2022 request")
    run_request(sys.argv[1])


if __name__ == "__main__":
    main()
