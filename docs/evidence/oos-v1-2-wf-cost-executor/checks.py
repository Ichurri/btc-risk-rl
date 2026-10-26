"""Read-only audit of the unapproved cost-study preflight and frozen inputs."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).with_name("preflight.json")
EXPECTED_LEDGERS = {
    "p0-approved-v1": "1d1ee72ca0ac49529f205b30942a68f381d86037e336091c490c624098339b8c",
    "p1-approved-v1": "926eab40bc764e1cae88a74e6718ba70b50e2df0626e8e34964078cc4ba55755",
    "p2-approved-v1": "e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8",
    "p2r-approved-v2": "fe443e5e32d26a7de075fa6e34771c8f20651bbe566f9097bfdb367d17d0b866",
    "p3-approved-v1": "86b111b5365cda1760441d2f73d42e0463a4b4b2a7ddbc6e0e41f2a78751fcfe",
}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check():
    data = json.loads(EVIDENCE.read_text())
    preflight = data["preflight"]
    assert preflight["status"] == "blocked"
    assert preflight["market_execution_enabled"] is False
    assert preflight["root_exists"] is False
    assert not (ROOT / "artifacts/oos-v12-wf-cost-only-01").exists()
    assert preflight["budget"]["global_spent"] == 0
    assert preflight["budget"]["active_campaigns"] == []
    assert data["market_trajectories_generated"] == data["optimizer_steps"] == 0
    assert data["shared_h1_csv_opened"] is False
    assert not any("segmented-B-h1/" in path and path.endswith(".csv")
                   for path in data["files_opened"])
    assert not any("validation" in path.lower() or "final" in path.lower()
                   for path in data["files_opened"])
    assert [(data["fold_metadata"][year]["episodes"],
             data["fold_metadata"][year]["fit_rows"])
            for year in ("2021", "2022")] == [(3639, 5764), (4678, 7703)]
    assert all(data["fold_metadata"][year]["latest_target_ms"]
               < data["fold_metadata"][year]["cutoff_ms"]
               for year in ("2021", "2022"))
    for name, expected in data["code_sha256"].items():
        assert digest(ROOT / name) == expected, name
    for name, expected in preflight["inputs"]["sha256"].items():
        assert digest(ROOT / name) == expected, name
    for name, expected in EXPECTED_LEDGERS.items():
        assert digest(ROOT / "artifacts" / name / "ledger.jsonl") == expected
    assert digest(ROOT / "data/processed/p2r-training-h1/manifest.json") == (
        "62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9"
    )
    return dict(status="passed_read_only", preflight_sha256=digest(EVIDENCE),
                code_files=len(data["code_sha256"]), opened_files=len(data["files_opened"]),
                prior_ledgers=len(EXPECTED_LEDGERS), protected_csv_opened=False,
                root_absent=True)


if __name__ == "__main__":
    print(json.dumps(check(), indent=2, sort_keys=True))
