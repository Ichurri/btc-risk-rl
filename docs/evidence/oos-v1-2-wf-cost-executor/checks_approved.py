"""Read-only audit of the approved cost-study preflight snapshot."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
EXPECTED_SHA256 = "ca4ec844028da895d3ea695dac20427b2c423d9081abf88951d3a82ca9fbf458"
OLD_SHA256 = "79e9b0a0b3d7633b62b51e5d2895be573fd4b6f1df24503b295fe992cfa176eb"
AFTER_SWAYNC_SHA256 = "875f56ba04d5f4f3146aebe62edce337ca7d15c57f032b9ba55a2dd645a870f5"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check() -> dict:
    assert digest(HERE / "preflight.json") == OLD_SHA256
    assert digest(HERE / "preflight-after-swaync.json") == AFTER_SWAYNC_SHA256
    path = HERE / "preflight-approved-20261026.json"
    assert digest(path) == EXPECTED_SHA256
    data = json.loads(path.read_text())
    preflight = data["preflight"]
    assert preflight["status"] == "ready" and preflight["blockers"] == []
    assert preflight["market_execution_enabled"] is True
    assert preflight["root_exists"] is False
    assert preflight["host"]["user_manager"] == "running"
    assert preflight["host"]["linger"] == "yes"
    assert preflight["host"]["power"]["ac"] is True
    assert preflight["host"]["power"]["battery_percent"] >= 50
    assert preflight["host"]["memory_available_bytes"] >= 4 * 1024**3
    assert preflight["host"]["disk_free_bytes"] >= 20 * 1024**3
    assert preflight["budget"]["ok"] is True
    assert preflight["budget"]["active_campaigns"] == []
    assert preflight["budget"]["remaining_before_reserve"] >= 120
    assert preflight["inputs"]["ok"] is True
    assert data["market_trajectories_generated"] == data["optimizer_steps"] == 0
    assert data["shared_h1_csv_opened"] is False
    assert not any("segmented-B-h1/" in name and name.endswith(".csv")
                   for name in data["files_opened"])
    assert not any("validation" in name.lower() or "final" in name.lower()
                   for name in data["files_opened"])
    assert [(data["fold_metadata"][year]["episodes"],
             data["fold_metadata"][year]["fit_rows"])
            for year in ("2021", "2022")] == [(3639, 5764), (4678, 7703)]
    for section in (data["code_sha256"], preflight["inputs"]["sha256"]):
        for name, expected in section.items():
            assert digest(ROOT / name) == expected, name
    for source in preflight["budget"]["sources"]:
        assert digest(ROOT / source["path"]) == source["sha256"]
    approval = ROOT / "docs/protocols/OOS-v1-2-wf-cost-approval.json"
    entry = json.loads(approval.read_text())
    assert entry["active"] is True
    assert entry["protocol_sha256"] == digest(
        ROOT / "docs/proposals/OOS-v1-2-costo-entrenamiento-cortes-v1.md"
    )
    assert entry["design_sha256"] == digest(
        ROOT / "docs/protocols/OOS-v1-2-wf-cost-executor-v1.json"
    )
    assert entry["training_shard_manifest_sha256"] == digest(
        ROOT / "data/processed/p2r-training-h1/manifest.json"
    )
    return {"status": "passed_read_only", "preflight_sha256": EXPECTED_SHA256,
            "opened_files_recorded": len(data["files_opened"]),
            "root_absent_at_preflight": True}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2, sort_keys=True))
