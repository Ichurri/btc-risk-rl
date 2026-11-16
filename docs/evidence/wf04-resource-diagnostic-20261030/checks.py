"""Read-only checks for the historical WF 04 resource-guard failure."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "artifacts"
EVIDENCE = ROOT / "docs/evidence/oos-v1-2-wf-cost-04-session-02-20261030"
EXPECTED_ROOTS = {
    "01": "b93caafafd20b7a61f86214b5cbecba3ff7942d3862a467e1748d636b74a010a",
    "02": "e11a6cfa872ed91ed5f9d0b30f429071b884846125c4df2a4a9d694a664257fd",
    "03": "34270a3a26901de2472d203662e1717827cc93d8073a7f996b01f0b8174bbb57",
    "04": "3c22543a9238b07f84ae790e92fcd8b627d53483898e15204d9a8a5fb6a859da",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def root_hash(number):
    base = ARTIFACTS / f"oos-v12-wf-cost-only-{number}"
    mapping = {str(path.relative_to(base)): digest(path)
               for path in sorted(base.rglob("*")) if path.is_file()}
    return len(mapping), hashlib.sha256(json.dumps(mapping, sort_keys=True).encode()).hexdigest()


def main():
    roots = {}
    for number, expected in EXPECTED_ROOTS.items():
        count, actual = root_hash(number)
        assert actual == expected, f"Historical WF root {number} changed"
        roots[number] = {"files": count, "mapping_sha256": actual}
    ledger = json.loads((ARTIFACTS / "oos-v12-wf-cost-only-04/ledger.jsonl")
                        .read_text().splitlines()[-1])
    assert ledger["status"] == "failed" and len(ledger["units"]) == 8
    assert ledger["pending"]["unit"] == 8
    journal = ARTIFACTS / "oos-v12-wf-cost-only-04/supervisor.jsonl"
    rows = [json.loads(line) for line in journal.read_text().splitlines()]
    final = [row for row in rows if row.get("unit") == 8][-10:]
    assert final[-1]["event"] == "supervisor_exit" and final[-1]["status"] == "failed"
    assert final[-2]["event"] == "heartbeat"
    assert final[-2]["utc"] == "2026-10-30T06:13:10.930718+00:00"
    assert not any(row["event"] == "resource_guard_failed" for row in rows)
    assert digest(journal) == json.loads((EVIDENCE / "audit.json").read_text())["supervisor_sha256"]
    preflight = json.loads((EVIDENCE / "preflight.json").read_text())["preflight"]
    after = json.loads((EVIDENCE / "host-after.json").read_text())
    print(json.dumps({
        "historical_roots": roots,
        "ledger_status": ledger["status"],
        "accepted_units": len(ledger["units"]),
        "partial_unit": ledger["pending"]["unit"],
        "failure": ledger["failure"],
        "supervisor_sha256": digest(journal),
        "unit_8_last_events": [
            {key: row.get(key) for key in ("utc", "event", "phase", "unit", "status",
                                          "rss_worker", "rss_supervisor", "counters")}
            for row in final
        ],
        "contemporaneous_resource_values_recorded": False,
        "preflight_observed_utc": preflight["observed_utc"],
        "preflight_host": {
            "power": preflight["host"]["power"],
            "memory_available_bytes": preflight["host"]["memory_available_bytes"],
            "disk_free_bytes": preflight["host"]["disk_free_bytes"],
        },
        "post_failure_host": after,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
