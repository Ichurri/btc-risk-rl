"""Small SYNTHETIC optimizer verification; has no market input or training switch."""

import argparse
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import torch

from btc_risk_rl.agents.collector import load_trajectory, save_trajectory
from btc_risk_rl.agents.synthetic import SyntheticMarket, SyntheticSettings
from btc_risk_rl.agents.trainer import SyntheticExperiment
from btc_risk_rl.config import load_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    if torch.version.cuda is not None:
        raise RuntimeError("This verification requires CPU-only PyTorch")
    config = load_config(Path("configs/initial.toml"))
    settings = SyntheticSettings()
    results, experiments = {}, {}
    started = time.perf_counter()
    for label, condition, risk in [
        ("C0", "C0", False),
        ("C5", "C5", True),
        ("C10", "C10", True),
        ("C5_off", "C5", False),
        ("C10_off", "C10", False),
    ]:
        t0 = time.perf_counter()
        experiment = SyntheticExperiment(
            SyntheticMarket(config),
            settings,
            condition=condition,
            risk_enabled=risk,
            run_id=f"h4-synthetic-{label}",
        )
        result = experiment.run()
        result["wall_seconds_measured_synthetic"] = time.perf_counter() - t0
        trajectory = experiment.batches[1][0]
        sample = args.output / f"{label}-sample.npz"
        save_trajectory(sample, trajectory)
        restored = load_trajectory(sample)
        if restored.realization != trajectory.realization:
            raise AssertionError("Serialization mismatch")
        result["sample_sha256"] = sha256(sample.read_bytes()).hexdigest()
        results[label], experiments[label] = result, experiment
    for label in ("C5_off", "C10_off"):
        for field in ("actor", "critic"):
            pairs = zip(
                getattr(experiments["C0"], field).parameters(),
                getattr(experiments[label], field).parameters(),
            )
            if not all(torch.equal(a, b) for a, b in pairs):
                raise AssertionError("Risk-off mismatch")
    paths = sorted(Path("src/btc_risk_rl/agents").glob("*.py"))
    paths += [
        Path(__file__),
        Path("pyproject.toml"),
        Path("uv.lock"),
        Path("configs/initial.toml"),
        *sorted(Path("tests").glob("test_agent*.py")),
        Path("tests/test_collector.py"),
    ]
    result = dict(
        schema_version="h4_synthetic_verification_v1",
        status="passed",
        time_utc=datetime.now(timezone.utc).isoformat(),
        context="local",
        purpose="small_synthetic_updates_not_market_training",
        command=[sys.executable, *sys.argv],
        python=sys.version,
        platform=platform.platform(),
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        git_status=subprocess.check_output(["git", "status", "--short"], text=True),
        packages={
            n: importlib.metadata.version(n)
            for n in ["torch", "numpy", "gymnasium", "pytest", "ruff"]
        },
        torch_cuda_build=torch.version.cuda,
        threads=torch.get_num_threads(),
        synthetic_settings=asdict(settings),
        runs=results,
        risk_off_exact=True,
        total_transitions=sum(r["transitions"] for r in results.values()),
        wall_seconds_measured_synthetic=time.perf_counter() - started,
        code_hashes={str(p): sha256(p.read_bytes()).hexdigest() for p in paths},
        market_data_loaded=False,
        market_training_executed=False,
        pilots_executed=False,
        final_test_accessed=False,
    )
    (args.output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in [
                    "status",
                    "purpose",
                    "risk_off_exact",
                    "total_transitions",
                    "wall_seconds_measured_synthetic",
                    "torch_cuda_build",
                    "market_data_loaded",
                    "final_test_accessed",
                ]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
