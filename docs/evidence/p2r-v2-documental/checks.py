"""Read-only cross-checks for the P2R v2 academic proposal."""

import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTS = (
    ROOT / "docs/proposals/P2R-protocolo-v2.md",
    ROOT / "docs/proposals/P2R-v2-resumen-academico.md",
    ROOT / "docs/proposals/P2R-v2-cambios.md",
)
EXPECTED_HASHES = {
    "docs/proposals/P2R-protocolo-v1.md":
        "6f4644a13868e3066d52b89d9ad236972fb2dd35b098fc3e81baf0f283051ab1",
    "docs/proposals/P2R-infraestructura-addendum-v1.md":
        "06a22a9f96adf4f628cadb4f0fc829cb0361bf6ef86e0530bd15209d55a8240f",
    "docs/protocols/P2-infrastructure-v1.json":
        "d5fa2f2726cd6458df3c290e7b58c591f11310c7a9b645c47a5fb6bd419e5238",
    "artifacts/p2-approved-v1/ledger.jsonl":
        "e6dedc6b0de39d71ca842fe60e7fb398495c3de88a0fcdfdd02a72752721c7b8",
    "artifacts/p2-approved-v1/run-05-C0/progress.json":
        "bb2af51c8192303d062b095646a772948072e4eeb36c039f1aa8f9e0037af2b3",
    "artifacts/p2-approved-v1/run-05-C0/journal/events.jsonl":
        "45ef6ad0421e062a7a1b150f5711cfbf07bfec8d47e5e3a72dabf2a149f6002b",
    "artifacts/p2r-synthetic-logout-q0-review-01/ledger.jsonl":
        "522025cd72c5f97edc93e47cbc96868a1888d1d455bb3066086fc7d428438d79",
    "artifacts/p2r-synthetic-logout-q0-review-01/supervisor.jsonl":
        "935e05135f30307b371acb150e8f15166c1c23916b896f26f7581f10cab1fdb9",
    "artifacts/p2r-synthetic-logout-q0-review-01/run-00-C5/checkpoint-0/state.pt":
        "daeeee181be13e8627921edd39d19ad1e8a1daf6c68356f87b8a62b084165868",
    "artifacts/p2r-logout-q0-review-01-record/logind-journal.txt":
        "d4057f7cdb6fcb7a62e2cd5d4a2415083f45726dd2517d5e8a033719a89d1923",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_manifest(path):
    checked = 0
    for line in path.read_text().splitlines():
        expected, name = line.split(maxsplit=1)
        assert sha256(ROOT / name) == expected, name
        checked += 1
    return checked


def main():
    source = json.loads((ROOT / "docs/protocols/P2-infrastructure-v1.json").read_text())
    blocks = source["blocks"]
    candidate = source["training_candidate"]
    diagnostic = source["diagnostic_candidate"]
    assert [(b["seed"], b["order"]) for b in blocks] == [
        (610031, ["C0", "C5", "C10"]),
        (610047, ["C5", "C10", "C0"]),
        (610081, ["C10", "C0", "C5"]),
    ]
    assert candidate["iterations"] == 10 and candidate["horizon"] == 180
    assert candidate["gamma"] == candidate["gae_lambda"] == 1
    assert candidate["critic_epochs"] == 4 and diagnostic["n"] == 64
    assert source["data"]["partition"] == "train"
    assert source["data"]["accepted_starts"] == 7048
    assert source["continuation_candidate"]["boundaries"] == [
        "after_q0", "after_dual_and_D"]
    assert math.isclose(source["risk"]["bound_selected"], -math.log(.90),
                        rel_tol=0, abs_tol=1e-15)
    runs = sum(len(block["order"]) for block in blocks)
    learning = runs * (candidate["n_q"] + candidate["iterations"] * (
        candidate["n_a"] + candidate["n_q"] + candidate["n_b"]))
    d_count = runs * candidate["iterations"] * diagnostic["n"]
    actor_steps = runs * candidate["iterations"] * candidate["actor_epochs"] * (
        candidate["n_a"] // candidate["minibatch_trajectories"])
    critic_steps = runs * candidate["iterations"] * candidate["critic_epochs"] * (
        candidate["n_a"] // candidate["minibatch_trajectories"])
    assert (runs, learning, d_count, actor_steps, critic_steps) == (
        9, 81360, 5760, 720, 1440)

    checked_hashes = 0
    for name, expected in EXPECTED_HASHES.items():
        assert sha256(ROOT / name) == expected, name
        checked_hashes += 1
    manifests = {
        "02": "docs/evidence/p2r-logout-q0-02/SHA256SUMS.txt",
        "03": "docs/evidence/p2r-heartbeat-cadence-03/SHA256SUMS.txt",
        "04_05": "docs/evidence/p2r-signal-q0/SHA256SUMS.txt",
    }
    manifest_counts = {label: check_manifest(ROOT / path)
                       for label, path in manifests.items()}
    assert manifest_counts == {"02": 32, "03": 18, "04_05": 28}

    links = 0
    for index, document in enumerate(DOCUMENTS):
        text = document.read_text()
        if index < 2:
            assert "PROPUESTA PARA REVISIÓN" in text
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
            if "://" in target:
                continue
            assert (document.parent / target.split("#", 1)[0]).exists(), target
            links += 1
    return {
        "kind": "documentary_static_check_no_units_or_market_data",
        "runs": runs,
        "learning_trajectories": learning,
        "learning_transitions": learning * candidate["horizon"],
        "diagnostic_trajectories": d_count,
        "diagnostic_transitions": d_count * candidate["horizon"],
        "actor_steps": actor_steps,
        "critic_steps": critic_steps,
        "historical_and_source_hashes_checked": checked_hashes,
        "probe_manifest_files_checked": manifest_counts,
        "local_document_links_checked": links,
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
