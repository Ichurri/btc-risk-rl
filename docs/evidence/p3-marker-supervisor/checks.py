"""Read-only evidence anchors for the prospective P3 marker change."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "artifacts"
P2R_LEDGER = "fe443e5e32d26a7de075fa6e34771c8f20651bbe566f9097bfdb367d17d0b866"
P2R_JOURNAL = "dc5d3901ab3ba2ce14dd7db3c4d80e6186b9a20291d27bd5d0b8b1300c091486"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    roots = {
        "p0-approved-v1": ("completed", 27),
        "p1-approved-v1": ("completed", 54),
        "p2-approved-v1": ("failed", 57),
        "p2r-approved-v2": ("completed", 99),
    }
    ledgers = {}
    for name, (status, units) in roots.items():
        ledger = ARTIFACTS / name / "ledger.jsonl"
        state = json.loads(ledger.read_text().splitlines()[-1])
        assert (state["status"], len(state["units"])) == (status, units)
        ledgers[name] = dict(status=status, units=units, sha256=sha256(ledger))
    assert ledgers["p2r-approved-v2"]["sha256"] == P2R_LEDGER
    journal = ARTIFACTS / "p2r-approved-v2" / "supervisor.jsonl"
    assert sha256(journal) == P2R_JOURNAL
    reports = sorted((ARTIFACTS / "p2r-approved-v2").rglob("unit-*.json"))
    assert len(reports) == 99
    assert all(json.loads(path.read_text())["report"]["market_training_executed"] is False
               for path in reports)
    aggregate = hashlib.sha256()
    for path in reports:
        aggregate.update(str(path.relative_to(ARTIFACTS)).encode())
        aggregate.update(sha256(path).encode())
    result = dict(
        scope="read_only_original_artifacts_no_market_data_loaded",
        ledgers=ledgers,
        p2r_supervisor_sha256=sha256(journal),
        p2r_report_count=len(reports),
        p2r_report_marker_false_count=len(reports),
        p2r_report_path_hash_aggregate_sha256=aggregate.hexdigest(),
    )
    output = Path(__file__).with_name("results.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("Original artifact anchors unchanged; 99 P2R reports retained")


if __name__ == "__main__":
    main()
