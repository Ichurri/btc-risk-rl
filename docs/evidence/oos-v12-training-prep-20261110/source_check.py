"""Read-only source audit before OOS training; never collects a trajectory."""

import json
import sys

from btc_risk_rl.pilots.oos_v12_training import PROFILES, source_for, watch_open

opened = []
sys.addaudithook(lambda event, args: watch_open(event, args, opened))
sources = {}
for profile in PROFILES:
    source = source_for(profile)
    sources[profile] = {
        "routes": len(source.route_ids),
        "identity": source.identity(),
        "validation_observations_loaded": source.audit.get("validation_observations_loaded"),
        "normalizer_refitted": source.audit.get("normalizer_refitted"),
        "trajectories_generated": 0,
    }
print(json.dumps({"sources": sources, "files_opened": sorted(set(opened))},
                 sort_keys=True, indent=2))
