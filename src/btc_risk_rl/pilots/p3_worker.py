"""P3 synthetic or gated historical unit worker on the common Q/A/B+D algorithm."""

import json
import sys
from pathlib import Path


def main():
    from btc_risk_rl.pilots.p3_market import P3MarketPermit

    synthetic = len(sys.argv) == 3 and sys.argv[1] == "--synthetic-request"
    if not synthetic:
        P3MarketPermit.require_campaign()  # Before request reads or torch/source imports.
    if (synthetic and len(sys.argv) != 3) or (not synthetic and len(sys.argv) != 2):
        raise SystemExit("Expected one P3 request path")

    import torch

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    if torch.version.cuda is not None:
        raise ValueError("CPU-only PyTorch required")
    from btc_risk_rl.agents.synthetic import SyntheticMarket
    from btc_risk_rl.config import load_config
    from btc_risk_rl.pilots.p2_runner import complete_unit
    from btc_risk_rl.pilots.p3_critic import P3SyntheticSettings
    from btc_risk_rl.pilots.p3_market import (
        ANCHORS,
        CONFIG,
        MANIFEST,
        PREPARED,
        TRAIN_SHARD,
        TRAIN_SHARD_MANIFEST_SHA256,
        P3MarketSettings,
    )

    request_path = Path(sys.argv[2] if synthetic else sys.argv[1])
    request = json.loads(request_path.read_text())
    if synthetic:
        settings = P3SyntheticSettings(**request.pop("settings"))
        if request.pop("beta") != settings.critic_beta:
            raise PermissionError("P3 synthetic arm/request mismatch")
        root = Path(request["root"]).resolve()
        if not root.parent.name.startswith("p3-synthetic-"):
            raise PermissionError("P3 synthetic request outside separate fixture root")
        request.pop("token", None)
        permit = None
        source = SyntheticMarket(load_config(Path(request.pop("config"))))
    else:
        permit = P3MarketPermit(request.get("token"))
        permit.validate_request(request_path, request)
        settings = P3MarketSettings(**request.pop("settings"))
        if request.pop("beta") != settings.critic_beta:
            raise PermissionError("P3 historical arm/request mismatch")
        if Path(request.pop("config")).resolve() != CONFIG.resolve():
            raise PermissionError("P3 worker requires canonical training configuration")
        request.pop("token")
        permit.validate(settings, request["condition"], request["run_id"])
        from btc_risk_rl.agents.market_source import TrainingMarket

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
            raise PermissionError("P3 worker source escaped accepted training")
    result = complete_unit(source, settings, permit=permit, **request)
    print(json.dumps(dict(status=result["status"], beta=settings.critic_beta,
                          resources=result["resources"])))


if __name__ == "__main__":
    main()
