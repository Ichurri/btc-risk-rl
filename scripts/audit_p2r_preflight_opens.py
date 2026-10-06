"""Read-only P2R preflight with a process-wide shared-table open guard."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    shared = (root / "data/processed/segmented-B-h1").resolve()
    shard = (root / "data/processed/p2r-training-h1").resolve()
    names = {"bars.csv", "observations.csv", "features.csv",
             "episodes.csv", "transitions.csv"}
    forbidden = {shared / name for name in names}
    opened = []

    def observe(event, args):
        if event != "open" or not args or not isinstance(args[0], (str, bytes)):
            return
        path = Path(args[0]).resolve()
        if path in forbidden:
            raise RuntimeError(f"Shared H1 CSV opened in P2R preflight: {path}")
        if path.parent in {shared, shard}:
            opened.append(str(path))

    sys.addaudithook(observe)
    from btc_risk_rl.pilots import p2r_market

    if p2r_market.MARKET_EXECUTION_ENABLED or p2r_market.REGISTRATION_SHA256 is not None:
        raise RuntimeError("P2R market permission unexpectedly active")
    result = p2r_market.inspect_preflight()
    if (result["status"] != "read_only_ready_campaign_disabled"
            or result["source"]["accepted_starts"] != 7048
            or result["market_trajectories_generated"] != 0
            or result["optimizer_updates"] != 0):
        raise RuntimeError("P2R read-only preflight state mismatch")
    print(json.dumps(dict(
        checked_utc=datetime.now(timezone.utc).isoformat(),
        status=result["status"], opened_product_files=sorted(set(opened)),
        shared_csv_open_count=0, accepted_starts=result["source"]["accepted_starts"],
        training_shard_manifest_sha256=result["training_shard_manifest_sha256"],
        validation_observations_loaded=result["source"]["validation_observations_loaded"],
        market_trajectories_generated=result["market_trajectories_generated"],
        optimizer_updates=result["optimizer_updates"],
        market_execution_enabled=result["market_execution_enabled"],
        shared_budget=result["shared_budget"], resources=result["resources"],
    ), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
