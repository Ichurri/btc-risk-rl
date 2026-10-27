"""Read-only guard for the stopped historical WF cost study."""

import hashlib
import json
from pathlib import Path

from btc_risk_rl.pilots import wf_cost

ROOT = Path(__file__).resolve().parents[3]
EXPECTED = {
    "artifacts/oos-v12-wf-cost-only-01/ledger.jsonl":
        "b6bc9a30d25387813d664708edfa07347c21174d2df216fc6f6be2d844ec6af6",
    "artifacts/oos-v12-wf-cost-only-01/wf-2021/checkpoint-0/state.pt":
        "22f9f60484db6ae5a04b7b35f4ebe2149debb16ac357437536c24f571bf8bca7",
    "artifacts/oos-v12-wf-cost-only-01/wf-2021/unit-0.json":
        "1ba4d95998624d0f0c8a46cdc37ddb51b8a2e04a32c5a14d85eff4f6639a934f",
    "artifacts/oos-v12-wf-cost-only-01/supervisor.jsonl":
        "211ec9a948970de4e00dc59524d7da9aa39ac78017f31ad279415835acb21731",
    "docs/protocols/OOS-v1-2-wf-cost-approval.json":
        "b36e32521f43af3f0b7b363f2555d1bee19fa5200c3cee30b5e8987068984369",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    assert wf_cost.MARKET_EXECUTION_ENABLED is False
    actual = {name: digest(ROOT / name) for name in EXPECTED}
    assert actual == EXPECTED
    ledger = json.loads((ROOT / "artifacts/oos-v12-wf-cost-only-01/ledger.jsonl")
                        .read_text().splitlines()[-1])
    assert ledger["status"] == "ready"
    assert len(ledger["units"]) == 1 and ledger["pending"] is None
    assert not (ROOT / "artifacts/oos-v12-wf-cost-only-01/wf-2021/checkpoint-1").exists()
    print(json.dumps({"status": "frozen_historical_study_verified",
                      "ledger_status": ledger["status"], "units": len(ledger["units"]),
                      "market_execution_enabled": False, "sha256": actual},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
