"""One-time H1 training-only export/re-audit; never authorizes market execution."""

import argparse
import json

from btc_risk_rl.config import load_config
from btc_risk_rl.data.training_shard_export import (
    audit_training_shard,
    export_training_shard,
)
from btc_risk_rl.pilots.p2r_market import ANCHORS, CONFIG, MANIFEST, PREPARED, TRAIN_SHARD


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("export", "audit"))
    args = parser.parse_args()
    config = load_config(CONFIG)
    if args.mode == "export":
        result = export_training_shard(
            config, PREPARED, TRAIN_SHARD, expected_manifest=ANCHORS[MANIFEST]
        )
    else:
        export_record = json.loads((TRAIN_SHARD / "export-audit.json").read_text())
        result = audit_training_shard(
            config, PREPARED, TRAIN_SHARD,
            expected_manifest=ANCHORS[MANIFEST],
            expected_shard_manifest=export_record["training_shard_manifest_sha256"],
        )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
