"""P3 session 02 read-only preflight with durable blocker evidence."""

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

root = Path.cwd().resolve()
shared = (root / "data/processed/segmented-B-h1").resolve()
forbidden = {shared / name for name in (
    "bars.csv", "observations.csv", "features.csv", "episodes.csv", "transitions.csv",
)}
opened = Counter()
attempts = []


def watch(event, args):
    if event != "open" or not args or not isinstance(args[0], (str, bytes)):
        return
    path = Path(args[0]).resolve()
    if path in forbidden:
        attempts.append(str(path))
        raise RuntimeError(f"Forbidden H1 shared CSV open: {path}")
    if path.is_relative_to(root):
        opened[str(path.relative_to(root))] += 1


sys.addaudithook(watch)
from btc_risk_rl.pilots.p3_market import (  # noqa: E402
    REGISTRATION,
    REGISTRATION_SHA256,
    P3MarketPermit,
    digest,
    inspect_preflight,
)

approval = P3MarketPermit.require_campaign()
result = inspect_preflight()
assert digest(REGISTRATION) == REGISTRATION_SHA256
assert result["status"] in {
    "read_only_ready_campaign_enabled", "read_only_resources_blocked"
}
assert result["source"]["accepted_starts"] == 7048
assert not result["source"]["validation_observations_loaded"]
assert result["market_trajectories_generated"] == result["optimizer_updates"] == 0
assert not attempts
product_prefixes = ("data/processed/segmented-B-h1/", "data/processed/p2r-training-h1/")
out = {
    "checked_utc": datetime.now(timezone.utc).isoformat(),
    "scope": "approved_p3_session02_read_only_preflight_no_trajectory",
    "status": result["status"],
    "approval_sha256": REGISTRATION_SHA256,
    "approval_scope": approval["scope"],
    "campaign": approval["campaign"],
    "protocol_sha256": result["protocol_sha256"],
    "adoption_sha256": result["adoption_sha256"],
    "design_sha256": result["design_sha256"],
    "config_sha256": result["config_sha256"],
    "entrypoint_sha256": result["entrypoint_sha256"],
    "training_shard_manifest_sha256": result["source"]["training_shard_manifest_sha256"],
    "product_hashes": result["source"]["product_hashes"],
    "code_file_hashes_sha256": hashlib.sha256(
        json.dumps(result["provenance"]["code"], sort_keys=True).encode()
    ).hexdigest(),
    "prior_ledgers": result["prior_ledgers"],
    "source_profile": result["source"]["profile"],
    "accepted_starts": result["source"]["accepted_starts"],
    "validation_observations_loaded": result["source"]["validation_observations_loaded"],
    "normalizer_refitted": result["source"]["normalizer_refitted"],
    "market_trajectories_generated": result["market_trajectories_generated"],
    "optimizer_updates": result["optimizer_updates"],
    "market_execution_enabled": result["market_execution_enabled"],
    "shared_budget": result["shared_budget"],
    "power": result["power"],
    "resources": result["resources"],
    "resource_blocker": result["resource_blocker"],
    "opened_repository_files": dict(sorted(opened.items())),
    "opened_training_product_files": {
        key: value for key, value in sorted(opened.items()) if key.startswith(product_prefixes)
    },
    "shared_csv_attempts": attempts,
}
p = root / "docs/evidence/p3-market-2026-10-09/preflight-blocked.json"
p.parent.mkdir(parents=True, exist_ok=True)
if p.exists():
    raise FileExistsError(p)
p.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    key: out[key] for key in (
        "checked_utc", "status", "accepted_starts", "power", "resources",
        "resource_blocker", "shared_budget", "shared_csv_attempts",
    )
}, sort_keys=True))
