"""Separate, prospectively pinned gates for technical and final evaluation.

Both gates are closed. Editing a JSON file cannot enable access. Enabling a
partition later requires a code commit with its specific approval hash.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

METHOD_SHA256 = "906570c6bad573ac399dd92155910fbc38c46e60e325685c07033fc88e7cf2f2"
TRAINING_SHA256 = "0651f396f3157eaa5abd6bb7faf7ec1c6463210d255fa2fbd8a932e2999870a0"
METHOD_PATH = Path("docs/protocols/OOS-v1-2-evaluation-method-freeze-20261111.json")
TRAINING_PATH = Path("docs/protocols/OOS-v1-2-training-freeze-20261110.json")
ENABLED = {"technical_2023": False, "final_2024_2025": False}
REGISTRATION_SHA256 = {"technical_2023": None, "final_2024_2025": None}
APPROVAL_PATHS = {
    "technical_2023": Path("docs/protocols/OOS-v1-2-technical-2023-approval.json"),
    "final_2024_2025": Path("docs/protocols/OOS-v1-2-final-2024-2025-approval.json"),
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_pinned_approval(partition: str, repo_root: Path) -> dict:
    """Check the closed gate and immutable approval before protected reads."""
    if partition not in ENABLED or not ENABLED[partition]:
        raise PermissionError("OOS evaluation partition disabled")
    for relative_path, expected_sha in (
        (METHOD_PATH, METHOD_SHA256), (TRAINING_PATH, TRAINING_SHA256)
    ):
        pinned_path = Path(repo_root) / relative_path
        if (pinned_path.is_symlink() or not pinned_path.is_file()
                or _sha(pinned_path) != expected_sha):
            raise PermissionError("OOS frozen protocol hash mismatch")
    expected_approval_sha = REGISTRATION_SHA256[partition]
    approval_path = APPROVAL_PATHS[partition]
    if not approval_path.is_absolute():
        approval_path = Path(repo_root) / approval_path
    if (expected_approval_sha is None or approval_path.is_symlink()
            or not approval_path.is_file()
            or _sha(approval_path) != expected_approval_sha):
        raise PermissionError("OOS evaluation approval hash mismatch")
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    if (type(approval) is not dict or approval.get("status") != "approved"
            or approval.get("partition") != partition
            or approval.get("method_freeze_sha256") != METHOD_SHA256
            or approval.get("training_freeze_sha256") != TRAINING_SHA256):
        raise PermissionError("OOS evaluation approval identity mismatch")
    return approval


def require_evaluation_access(partition: str, repo_root: Path, *,
                              training_ledger_sha256: str,
                              export_manifest_sha256: str,
                              source_manifest_sha256: str,
                              scaler_sha256: str, code_sha256: str,
                              technical_closure_path: Path | None = None) -> dict:
    """Reject a partition unless its independent approval pins every input."""
    approval = read_pinned_approval(partition, repo_root)
    required = {
        "status": "approved", "partition": partition,
        "method_freeze_sha256": METHOD_SHA256,
        "training_freeze_sha256": TRAINING_SHA256,
        "training_ledger_sha256": training_ledger_sha256,
        "export_manifest_sha256": export_manifest_sha256,
        "source_manifest_sha256": source_manifest_sha256,
        "scaler_sha256": scaler_sha256,
        "code_sha256": code_sha256,
    }
    if any(approval.get(key) != value for key, value in required.items()):
        raise PermissionError("OOS evaluation approval identity mismatch")
    if partition == "final_2024_2025":
        if (technical_closure_path is None or technical_closure_path.is_symlink()
                or not technical_closure_path.is_file()
                or _sha(technical_closure_path)
                != approval.get("technical_closure_sha256")):
            raise PermissionError("OOS technical closure absent or hash mismatch")
        closure = json.loads(technical_closure_path.read_text(encoding="utf-8"))
        if (type(closure) is not dict
                or closure.get("status") != "passed"
                or closure.get("partition") != "technical_2023"
                or closure.get("complete_policies") != 108):
            raise PermissionError("OOS technical closure not passed")
    return approval
