"""P2R market unit worker; blocked before reading requests until campaign approval."""

import json
import sys
from pathlib import Path


def main():
    from btc_risk_rl.pilots.p2r_market import P2RMarketPermit

    P2RMarketPermit.require_campaign()
    if len(sys.argv) != 2:
        raise SystemExit("Expected one P2R request path")
    import torch

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    if torch.version.cuda is not None:
        raise ValueError("CPU-only PyTorch required")
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.config import load_config
    from btc_risk_rl.pilots.p2_runner import complete_unit
    from btc_risk_rl.pilots.p2r_market import (
        ANCHORS,
        CONFIG,
        MANIFEST,
        PREPARED,
        TRAIN_SHARD,
        TRAIN_SHARD_MANIFEST_SHA256,
        P2RMarketSettings,
    )

    request_path = Path(sys.argv[1])
    request = json.loads(request_path.read_text())
    permit = P2RMarketPermit(request.get("token"))
    permit.validate_request(request_path, request)
    settings = P2RMarketSettings(**request.pop("settings"))
    config_path = Path(request.pop("config"))
    if config_path.resolve() != CONFIG.resolve():
        raise PermissionError("P2R worker requires canonical training configuration")
    request.pop("token")
    permit.validate(settings, request["condition"], request["run_id"])
    source = TrainingMarket(
        load_config(CONFIG), PREPARED, expected_manifest=ANCHORS[MANIFEST],
        training_shard=TRAIN_SHARD,
        expected_shard_manifest=TRAIN_SHARD_MANIFEST_SHA256,
    )
    if (len(source.route_ids) != 7048
            or source.identity()["manifest_sha256"] != ANCHORS[MANIFEST]
            or source.identity().get("training_shard_manifest_sha256")
            != TRAIN_SHARD_MANIFEST_SHA256
            or source.audit["normalizer_refitted"]
            or source.audit["validation_observations_loaded"]):
        raise PermissionError("P2R worker source escaped accepted training")
    result = complete_unit(source, settings, permit=permit, **request)
    print(json.dumps(dict(status=result["status"], resources=result["resources"])))


if __name__ == "__main__":
    main()
