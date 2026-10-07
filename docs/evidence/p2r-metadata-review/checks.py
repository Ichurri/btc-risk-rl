"""Read-only audit of P2R's historical training-report marker.

Reads only source, JSON ledgers/reports/manifests, and existing checkpoint
states. It never constructs a market source, trajectory, or optimizer.
"""

import ast
import hashlib
import json
from collections import Counter
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[3]
CAMPAIGN = ROOT / "artifacts/p2r-approved-v2"
TRAINER = ROOT / "src/btc_risk_rl/agents/trainer.py"
LEDGER_SHA256 = "fe443e5e32d26a7de075fa6e34771c8f20651bbe566f9097bfdb367d17d0b866"
SUPERVISOR_SHA256 = "dc5d3901ab3ba2ce14dd7db3c4d80e6186b9a20291d27bd5d0b8b1300c091486"
SHARD_SHA256 = "62ad23a6bea365e376c80ecc5be9fd68dfc65a82b3b160e3f763b1e04771e3b9"
CLOSURE = ROOT / "docs/evidence/p2r-market-2026-10-07/results.json"
CLOSURE_SHA256 = "77e784caf50a0d0716ac9b0a7055f9f034b06b0ec4aaa0a43fb172ee2b90fbc6"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reporter_purposes():
    tree = ast.parse(TRAINER.read_text())
    klass = next(node for node in tree.body
                 if isinstance(node, ast.ClassDef) and node.name == "SyntheticExperiment")
    method = next(node for node in klass.body
                  if isinstance(node, ast.FunctionDef) and node.name == "_report")
    returned = next(node.value for node in method.body if isinstance(node, ast.Return))
    assert isinstance(returned, ast.Call) and isinstance(returned.func, ast.Name)
    assert returned.func.id == "dict"
    field = next(key.value for key in returned.keywords
                 if key.arg == "market_training_executed")
    assert isinstance(field, ast.Compare) and len(field.ops) == 1
    assert isinstance(field.ops[0], ast.In) and isinstance(field.comparators[0], ast.Set)
    assert ast.unparse(field.left) == "self.settings.purpose"
    return sorted(ast.literal_eval(value) for value in field.comparators[0].elts)


def optimizer_steps(state, name):
    values = state[f"{name}_optimizer"]["state"].values()
    return sorted({int(item["step"]) for item in values})


def main():
    assert sha256(CAMPAIGN / "ledger.jsonl") == LEDGER_SHA256
    assert sha256(CAMPAIGN / "supervisor.jsonl") == SUPERVISOR_SHA256
    assert sha256(CLOSURE) == CLOSURE_SHA256
    closure = json.loads(CLOSURE.read_text())
    assert closure["numerical_technical_decision"] == "review"
    state = json.loads((CAMPAIGN / "ledger.jsonl").read_text().splitlines()[-1])
    assert state["status"] == "completed" and state["cursor"] == 9
    assert state["pending"] is None and len(state["units"]) == 99
    assert len(state["runs"]) == 9
    purposes = reporter_purposes()
    assert purposes == ["authorized_p0_only", "authorized_p1_only"]
    trainer_sha = sha256(TRAINER)
    flags = Counter()
    report_profiles = Counter()
    checkpoint_profiles = Counter()
    boundaries = Counter()
    source_profiles = Counter()
    route_ids = 0
    changed_actor = changed_critic = 0
    q0_without_updates = 0
    iteration_with_updates = 0
    previous_hashes = {}
    previous_counters = {}
    for entry in state["units"]:
        run_id, unit = entry["run_id"], entry["unit"]
        run_root = CAMPAIGN / run_id
        payload = json.loads((run_root / f"unit-{unit}.json").read_text())
        report = payload["report"]
        manifest = json.loads((run_root / f"checkpoint-{unit}/manifest.json").read_text())
        state_path = run_root / f"checkpoint-{unit}/state.pt"
        assert payload["status"] == "passed" and payload["resources"] == entry["resources"]
        assert payload["checkpoint_sha256"] == entry["checkpoint_sha256"]
        assert manifest["state_sha256"] == entry["checkpoint_sha256"] == sha256(state_path)
        assert manifest["provenance"]["code"]["src/btc_risk_rl/agents/trainer.py"] == trainer_sha
        assert manifest["provenance"]["data"]["training_shard_manifest_sha256"] == SHARD_SHA256
        assert manifest["provenance"]["data"]["profile"] == "accepted_train_collection_only"
        assert manifest["provenance"]["data"]["scaler_sha256"] == (
            manifest["provenance"]["data"]["files"]["scaler.json"]
        )
        assert report["purpose"] == manifest["profile"] == "authorized_p2r_only"
        assert report["final_test_accessed"] is False
        assert report["actor_updates"] == unit * 8
        assert report["critic_updates"] == unit * 16
        assert report["next_iteration"] == unit
        assert report["boundary"] == manifest["boundary"] == (
            "after_q0" if unit == 0 else "after_dual_and_D"
        )
        assert report["market_training_executed"] is (report["purpose"] in purposes)
        checkpoint = torch.load(state_path, map_location="cpu", weights_only=True)
        assert checkpoint["attrs"]["actor_updates"] == report["actor_updates"]
        assert checkpoint["attrs"]["critic_updates"] == report["critic_updates"]
        assert optimizer_steps(checkpoint, "actor") == ([] if unit == 0 else [unit * 8])
        assert optimizer_steps(checkpoint, "critic") == ([] if unit == 0 else [unit * 16])
        if unit == 0:
            assert entry["resources"]["actor_updates"] == 0
            assert entry["resources"]["critic_updates"] == 0
            q0_without_updates += 1
        else:
            assert entry["resources"]["actor_updates"] == 8
            assert entry["resources"]["critic_updates"] == 16
            assert previous_counters[run_id] == (8 * (unit - 1), 16 * (unit - 1))
            changed_actor += report["actor_sha256"] != previous_hashes[run_id][0]
            changed_critic += report["critic_sha256"] != previous_hashes[run_id][1]
            iteration_with_updates += 1
        previous_hashes[run_id] = (report["actor_sha256"], report["critic_sha256"])
        previous_counters[run_id] = (report["actor_updates"], report["critic_updates"])
        for event in report["events"]:
            if event["event"] in {"Q", "A", "B"}:
                assert len(event["route_ids"]) == event["count"]
                assert all(route.startswith("accepted-train:") for route in event["route_ids"])
                route_ids += len(event["route_ids"])
        flags[str(report["market_training_executed"])] += 1
        report_profiles[report["purpose"]] += 1
        checkpoint_profiles[manifest["profile"]] += 1
        source_profiles[manifest["provenance"]["data"]["profile"]] += 1
        boundaries[manifest["boundary"]] += 1
    assert changed_actor == changed_critic == iteration_with_updates == 90
    assert q0_without_updates == 9
    assert flags == {"False": 99}
    assert state["resources"]["actor_updates"] == 720
    assert state["resources"]["critic_updates"] == 1440
    print(json.dumps({
        "audit_kind": "read_only_existing_artifacts",
        "campaign_status": state["status"],
        "ledger_sha256": LEDGER_SHA256,
        "supervisor_sha256": SUPERVISOR_SHA256,
        "trainer_sha256": trainer_sha,
        "training_shard_manifest_sha256": SHARD_SHA256,
        "reporter_true_purposes": purposes,
        "p2r_purpose_in_true_set": "authorized_p2r_only" in purposes,
        "report_flags": dict(flags),
        "report_profiles": dict(report_profiles),
        "checkpoint_profiles": dict(checkpoint_profiles),
        "source_profiles": dict(source_profiles),
        "boundaries": dict(boundaries),
        "q0_units_without_optimizer_updates": q0_without_updates,
        "iteration_units_with_optimizer_steps": iteration_with_updates,
        "iteration_units_with_actor_hash_change": changed_actor,
        "iteration_units_with_critic_hash_change": changed_critic,
        "ledger_actor_updates": state["resources"]["actor_updates"],
        "ledger_critic_updates": state["resources"]["critic_updates"],
        "cumulative_learning_route_id_occurrences_inspected": route_ids,
        "route_id_count_interpretation": "cumulative_per_unit_reports_not_unique_trajectories",
        "numerical_gate_unchanged": closure["numerical_technical_decision"],
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
