"""Audit the second, read-only WF cost preflight without changing the first."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OLD_SHA256 = "79e9b0a0b3d7633b62b51e5d2895be573fd4b6f1df24503b295fe992cfa176eb"
NEW_SHA256 = "875f56ba04d5f4f3146aebe62edce337ca7d15c57f032b9ba55a2dd645a870f5"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check() -> dict:
    old_path = HERE / "preflight.json"
    new_path = HERE / "preflight-after-swaync.json"
    assert sha256(old_path) == OLD_SHA256
    assert sha256(new_path) == NEW_SHA256
    old = json.loads(old_path.read_text())
    new = json.loads(new_path.read_text())
    assert old["preflight"]["host"]["user_manager"] == "degraded"
    assert new["git_commit"] == "813c647d98dd7b5c2dc8843e15c4813b6cde61f2"
    assert new["preflight"]["status"] == "blocked"
    assert new["preflight"]["blockers"] == ["Cost-study campaign has no active approval"]
    assert new["preflight"]["host"]["user_manager"] == "running"
    assert new["preflight"]["host"]["linger"] == "yes"
    assert new["preflight"]["market_execution_enabled"] is False
    assert new["preflight"]["root_exists"] is False
    assert not (ROOT / "artifacts/oos-v12-wf-cost-only-01").exists()
    assert new["preflight"]["inputs"]["ok"] is True
    assert new["preflight"]["budget"]["ok"] is True
    assert new["preflight"]["budget"]["active_campaigns"] == []
    assert new["market_trajectories_generated"] == new["optimizer_steps"] == 0
    assert new["shared_h1_csv_opened"] is False
    assert not any("segmented-B-h1/" in path and path.endswith(".csv")
                   for path in new["files_opened"])
    assert not any("validation" in path.lower() or "final" in path.lower()
                   for path in new["files_opened"])
    for section in (new["code_sha256"], new["preflight"]["inputs"]["sha256"]):
        for name, expected in section.items():
            assert sha256(ROOT / name) == expected, name
    for source in new["preflight"]["budget"]["sources"]:
        assert sha256(ROOT / source["path"]) == source["sha256"]
    return {
        "status": "passed_read_only",
        "old_sha256": OLD_SHA256,
        "new_sha256": NEW_SHA256,
        "opened_files_recorded": len(new["files_opened"]),
        "blockers": new["preflight"]["blockers"],
    }


if __name__ == "__main__":
    print(json.dumps(check(), indent=2, sort_keys=True))
