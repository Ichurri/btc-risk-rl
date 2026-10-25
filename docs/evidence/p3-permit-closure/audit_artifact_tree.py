"""Read-only aggregate SHA-256 for every original P3 artifact file."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CAMPAIGN = ROOT / "artifacts/p3-approved-v1"


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit() -> dict[str, object]:
    digest = hashlib.sha256()
    count = total_bytes = 0
    for path in sorted(CAMPAIGN.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Unexpected symlink in P3 evidence: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(CAMPAIGN).as_posix()
        size = path.stat().st_size
        digest.update(json.dumps(
            [relative, size, file_digest(path)], separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8") + b"\n")
        count += 1
        total_bytes += size
    if count == 0:
        raise ValueError("P3 evidence root is empty")
    return {
        "root": "artifacts/p3-approved-v1",
        "file_count": count,
        "file_bytes": total_bytes,
        "tree_sha256": digest.hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
