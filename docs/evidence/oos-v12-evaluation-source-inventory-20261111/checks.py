"""Recheck captured OOS source metadata without opening market-row files."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    evidence = json.loads((HERE / "metadata.json").read_text())
    if evidence["scope"] != "metadata_and_file_names_only_no_market_rows_opened":
        raise ValueError("Inventory scope differs")
    checked = {}
    for name, row in evidence["manifests"].items():
        path = Path(row["path"])
        if path.suffix != ".json":
            raise ValueError("Inventory checker refuses non-JSON input")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != row["sha256"]:
            raise ValueError(f"Source metadata changed: {name}")
        checked[name] = actual
    coverage = json.loads(Path(evidence["manifests"]["h1_coverage"]["path"]).read_text())
    validation = coverage["validation"]
    if (validation["expected_bars"] != 2190
            or validation["received_bars"] != 2190
            or validation["exclusions"] != {"missing": 0, "early_close": 0,
                                             "reopening": 0}):
        raise ValueError("H1 validation coverage metadata differs")
    print(json.dumps({"status": "matched_metadata_only", "checked": checked}, sort_keys=True))


if __name__ == "__main__":
    main()
