"""Read-only P3 training-shard preflight with process-wide H1 CSV open denial."""

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    shared = (root / "data/processed/segmented-B-h1").resolve()
    forbidden = {shared / name for name in (
        "bars.csv", "observations.csv", "features.csv", "episodes.csv", "transitions.csv",
    )}
    opened = Counter()
    forbidden_attempts = []

    def observe(event, arguments):
        if event != "open" or not arguments or not isinstance(arguments[0], (str, bytes)):
            return
        path = Path(arguments[0]).resolve()
        if path in forbidden:
            forbidden_attempts.append(str(path))
            raise RuntimeError(f"Shared H1 CSV opened in P3 preflight: {path}")
        if path.is_relative_to(root):
            opened[str(path.relative_to(root))] += 1

    sys.addaudithook(observe)
    from btc_risk_rl.pilots.p3_market import (
        MARKET_EXECUTION_ENABLED,
        REGISTRATION_SHA256,
        inspect_preflight,
    )

    if MARKET_EXECUTION_ENABLED or REGISTRATION_SHA256 is not None:
        raise RuntimeError("P3 campaign permission unexpectedly active")
    result = inspect_preflight()
    if (result["status"] not in {"read_only_ready_campaign_disabled", "read_only_resources_blocked"}
            or result["source"]["accepted_starts"] != 7048
            or result["market_trajectories_generated"] != 0
            or result["optimizer_updates"] != 0):
        raise RuntimeError("P3 read-only preflight state mismatch")
    data_prefixes = ("data/processed/segmented-B-h1/", "data/processed/p2r-training-h1/")
    evidence = dict(
        checked_utc=datetime.now(timezone.utc).isoformat(),
        scope="read_only_preflight_repository_open_audit",
        status=result["status"],
        opened_repository_files=dict(sorted(opened.items())),
        opened_training_product_files={name: count for name, count in sorted(opened.items())
                                       if name.startswith(data_prefixes)},
        shared_csv_attempts=forbidden_attempts,
        accepted_starts=result["source"]["accepted_starts"],
        training_shard_manifest_sha256=result["source"]["training_shard_manifest_sha256"],
        protocol_sha256=result["protocol_sha256"],
        adoption_sha256=result["adoption_sha256"],
        design_sha256=result["design_sha256"],
        config_sha256=result["config_sha256"],
        entrypoint_sha256=result["entrypoint_sha256"],
        product_hashes=result["source"]["product_hashes"],
        code_file_hashes_sha256=hashlib.sha256(
            json.dumps(result["provenance"]["code"], sort_keys=True).encode()
        ).hexdigest(),
        validation_observations_loaded=result["source"]["validation_observations_loaded"],
        trajectories_generated=result["market_trajectories_generated"],
        optimizer_updates=result["optimizer_updates"],
        market_execution_enabled=result["market_execution_enabled"],
        shared_budget=result["shared_budget"],
        resources=result["resources"],
        power=result["power"],
        resource_blocker=result["resource_blocker"],
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps(dict(status=evidence["status"],
                          data_files=evidence["opened_training_product_files"],
                          shared_csv_attempts=forbidden_attempts,
                          accepted_starts=evidence["accepted_starts"]), sort_keys=True))


if __name__ == "__main__":
    main()
