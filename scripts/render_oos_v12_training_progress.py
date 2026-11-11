"""Render read-only OOS training progress from one verified ledger snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from btc_risk_rl.reporting.oos_progress import (
    read_verified_snapshot,
    render_progress_svg,
    summarize_state,
)
from btc_risk_rl.reporting.oos_tables import completed_run_rows, render_markdown_table

ROOT = Path(__file__).resolve().parents[1]
FREEZE_SHA256 = "0651f396f3157eaa5abd6bb7faf7ec1c6463210d255fa2fbd8a932e2999870a0"


def _write_once(path: Path, content: str) -> None:
    if path.exists():
        if path.read_text(encoding="utf-8") != content:
            raise ValueError("Existing progress output has different bytes")
        return
    with path.open("x", encoding="utf-8") as stream:
        stream.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--profile", choices=("wf-2022", "main-2018-2022"), required=True)
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / "reports/oos-training-progress")
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    output_dir = args.output_dir.resolve()
    if (output_dir.is_relative_to(source_root / "artifacts")
            or output_dir.is_relative_to(source_root / "data")):
        raise ValueError("Progress output must not modify campaign artifacts or data")
    freeze_path = source_root / "docs/protocols/OOS-v1-2-training-freeze-20261110.json"
    if hashlib.sha256(freeze_path.read_bytes()).hexdigest() != FREEZE_SHA256:
        raise ValueError("OOS training protocol hash mismatch")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    roster = [(row["seed"], row["condition"], row["beta"])
              for row in freeze["roster"] if row["source"] == args.profile]
    root = source_root / freeze["campaign_roots"][args.profile]
    ledger = root / "ledger.jsonl"
    raw = ledger.read_bytes()
    state = read_verified_snapshot(raw)
    digest = hashlib.sha256(raw).hexdigest()
    rows = completed_run_rows(args.profile, state, roster, root=root)
    summary = summarize_state(args.profile, state, expected_runs=len(roster))
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{args.profile}-{digest[:16]}"
    markdown = output_dir / f"{stem}.md"
    svg = output_dir / f"{stem}.svg"
    _write_once(markdown, render_markdown_table(rows, profile=args.profile,
                                                 ledger_sha256=digest))
    _write_once(svg, render_progress_svg(summary,
                                         source=f"{ledger} SHA-256 {digest}"))
    print(json.dumps({"profile": args.profile, "status": state["status"],
                      "complete_runs": len(rows), "accepted_units": len(state["units"]),
                      "pending": summary["pending"], "ledger_sha256": digest,
                      "table": str(markdown), "figure": str(svg)}, sort_keys=True))


if __name__ == "__main__":
    main()
