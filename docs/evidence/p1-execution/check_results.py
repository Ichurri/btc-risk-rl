"""Post-run read-only verification of P1, paired checkpoints and preserved P0."""

import hashlib
import json
import math
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CAMPAIGN = ROOT / "artifacts/p1-approved-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model_sha(state):
    h = hashlib.sha256()
    for key, value in state.items():
        h.update(key.encode())
        h.update(value.numpy().tobytes())
    return h.hexdigest()


def finite(value):
    if isinstance(value, float):
        assert math.isfinite(value)
    elif isinstance(value, dict):
        for v in value.values():
            finite(v)
    elif isinstance(value, list):
        for v in value:
            finite(v)


def main():
    data = json.loads((OUT / "campaign-results/results.json").read_text())
    assert data["status"] == "completed" and data["failure"] is None
    assert len(data["runs"]) == 18
    assert data["resources"] == dict(
        trajectories=38304, transitions=6894720, actor_updates=288, critic_updates=432
    )
    assert not data["validation_accessed"] and not data["final_accessed"]
    finite(data)
    for name, hash_ in data["identity"]["code"].items():
        assert sha(ROOT / name) == hash_
    originals = json.loads((ROOT / "docs/evidence/p0-diagnosis/results.json").read_text())
    for name, hash_ in originals["original_files_sha256"].items():
        assert sha(ROOT / name) == hash_
    for item in data["artifacts"]:
        path = CAMPAIGN / item["path"]
        assert sha(path) == item["sha256"]
        if "state_sha256" in item:
            assert sha(path.parent / "state.pt") == item["state_sha256"]
    for d in data["days"].values():
        assert d["charged_wall_seconds"] + d["external_seconds"] <= 10800
    assert sha(CAMPAIGN / "ledger.jsonl") == data["ledger_sha256"]
    first = {}
    for r in data["runs"]:
        assert r["status"] == "completed" and r["complete_iterations"] == 2
        e = r["critic_epochs"]
        assert e in (2, 4)
        assert r["resources"] == dict(
            trajectories=2128, transitions=383040, actor_updates=16, critic_updates=8 * e
        )
        assert len(r["days"]) == 1
        assert r["settings"]["bound"] == -math.log(0.9)
        assert r["settings"]["critic_epochs"] == e
        for u in r["measured_units"]:
            assert u["supervisor"]["status"] == "passed"
            assert u["supervisor"]["rss_peak_bytes"] < 10 * 1024**3
            assert u["supervisor"]["work_seconds"] <= (1800 if u["unit"] == 0 else 2700)
        point = CAMPAIGN / r["run_id"] / "checkpoint-1/state.pt"
        state = torch.load(point, map_location="cpu", weights_only=True)
        assert all(int(v["step"]) == 4 * e for v in state["critic_optimizer"]["state"].values())
        metrics = [s for s in r["stability"] if s["phase"] == "fixed_A" and s["iteration"] == 0]
        pre, post_actor, post_critic = metrics
        assert [m["measurement"] for m in metrics] == [
            "before_actor",
            "after_actor_before_critic",
            "after_critic",
        ]
        assert len({m["batch_sha256"] for m in metrics}) == 1
        assert pre["mse"] == post_actor["mse"]
        assert pre["risk_penalty_nonzero"] == 0
        assert (
            model_sha(state["actor"]) == post_actor["actor_sha256"] == post_critic["actor_sha256"]
        )
        assert model_sha(state["critic"]) == post_critic["critic_sha256"]
        first[(r["seed"], r["condition"], e)] = (pre, post_critic)
    independent = []
    for seed in (510031, 510047, 510081):
        pairs = []
        for c in ("C0", "C5", "C10"):
            pre2, post2 = first[(seed, c, 2)]
            pre4, post4 = first[(seed, c, 4)]
            assert pre2["batch_sha256"] == pre4["batch_sha256"]
            assert post2["actor_sha256"] == post4["actor_sha256"]
            pairs.append((post2["mse"], post4["mse"]))
        assert pairs[0] == pairs[1] == pairs[2]
        a, b = pairs[0]
        independent.append(dict(seed=seed, mse_e2=a, mse_e4=b, criterion=b <= 0.8 * a))
    assert sum(x["criterion"] for x in independent) == 3
    assert data["primary"]["successful_seeds"] == 3 and data["primary"]["criterion_met"]
    output = dict(
        status="passed",
        checkpoint_actor_and_critic_hashes_verified=18,
        artifact_hashes=len(data["artifacts"]),
        independent_seeds=independent,
        global_daily_limit_passed=True,
        p0_unchanged=True,
        source_unchanged=True,
        optimizer_steps_executed=0,
        scope="logs_and_existing_checkpoint_read_only",
        results_sha256=sha(OUT / "campaign-results/results.json"),
    )
    with (OUT / "closure-checks.json").open("x") as f:
        json.dump(output, f, indent=2)
    print(json.dumps(output))


if __name__ == "__main__":
    main()
