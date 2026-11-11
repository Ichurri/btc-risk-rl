"""Content identity for a future, separately approved OOS evaluator."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REQUIRED = (
    "src/btc_risk_rl/evaluation/access.py",
    "src/btc_risk_rl/evaluation/historical_path.py",
    "src/btc_risk_rl/agents/models.py",
    "src/btc_risk_rl/env/accounting.py",
    "src/btc_risk_rl/features/market.py",
    "src/btc_risk_rl/config.py",
    "src/btc_risk_rl/reporting/oos_contrast.py",
    "pyproject.toml", "uv.lock", "configs/initial.toml",
)


def execution_code_sha256(repo_root: Path) -> str:
    """Hash all package code and evaluation entry points, excluding gate values.

    The two approval declarations are normalized so a later commit can
    enable a separately pinned permit without changing the code identity.
    Every other byte, including algorithms and dependencies, remains pinned.
    """
    root = Path(repo_root)
    for name in REQUIRED:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Evaluation executable file missing: {name}")
    sources = set((root / "src/btc_risk_rl").rglob("*.py"))
    sources.update(root / name for name in REQUIRED)
    sources.update((root / "scripts").glob("run_oos_v12_evaluation*.py"))
    sources.update((root / "ops/systemd").glob("oos-v12-evaluation*.service"))
    mapping = {}
    for path in sorted(sources):
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Evaluation executable file missing: {path}")
        raw = path.read_bytes()
        if path.name == "access.py":
            lines = raw.splitlines(keepends=True)
            found = set()
            for index, line in enumerate(lines):
                for declaration in (b"ENABLED = ", b"REGISTRATION_SHA256 = "):
                    if line.startswith(declaration):
                        if declaration in found:
                            raise ValueError("Duplicate evaluation approval declaration")
                        found.add(declaration)
                        lines[index] = declaration + b"<pinned approval>\n"
            if len(found) != 2:
                raise ValueError("Evaluation approval declarations missing")
            raw = b"".join(lines)
        mapping[path.relative_to(root).as_posix()] = hashlib.sha256(raw).hexdigest()
    return hashlib.sha256(json.dumps(mapping, sort_keys=True).encode()).hexdigest()
