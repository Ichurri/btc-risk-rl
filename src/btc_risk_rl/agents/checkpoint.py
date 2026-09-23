"""Full checkpoints at after_q0 / after_dual only; journal forbids failed rollback."""

import hashlib
import importlib.metadata
import json
import math
import os
import platform
import subprocess
import time
import uuid
from dataclasses import asdict
from pathlib import Path

import torch

from btc_risk_rl.agents.journal import RunJournal
from btc_risk_rl.agents.models import fingerprint
from btc_risk_rl.agents.synthetic import SyntheticMarket, SyntheticSettings
from btc_risk_rl.agents.telemetry import TimeBudget
from btc_risk_rl.agents.trainer import SyntheticExperiment

SCHEMA = "h5_complete_boundary_v1"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def provenance(source):
    root = Path(__file__).resolve().parents[3]
    files = sorted((root / "src/btc_risk_rl").rglob("*.py")) + [
        root / "uv.lock",
        root / "pyproject.toml",
    ]
    return dict(
        code={str(p.relative_to(root)): digest(p) for p in files},
        packages={
            n: importlib.metadata.version(n) for n in ["torch", "numpy", "pandas", "gymnasium"]
        },
        python=platform.python_version(),
        machine=platform.machine(),
        platform=platform.system(),
        threads=torch.get_num_threads(),
        deterministic=torch.are_deterministic_algorithms_enabled(),
        data=source.identity(),
        config=source.config.model_dump(mode="json"),
    )


def validate_state(run):
    s = run.settings
    n = run.next_iteration
    if run.failed or run.collector.failed or type(n) is not int or not 0 <= n <= s.iterations:
        raise ValueError("Invalid failed/counter checkpoint state")
    boundary = "after_q0" if n == 0 else "after_dual"
    if run.boundary != boundary or run.generation != n or run.initial_q_tail is None:
        raise ValueError("Checkpoint requires a complete Q/A/B boundary")
    used = {(0, "Q")}
    for k in range(n):
        used.update({(k, "A"), (k + 1, "Q"), (k + 1, "B")})
    count = s.n_q + n * (s.n_a + s.n_q + s.n_b)
    batches = math.ceil(s.n_a / s.minibatch)
    if (
        run.collector.used != used
        or run.collector.trajectories != count
        or run.collector.transitions != 180 * count
        or run.actor_updates != n * s.actor_epochs * batches
        or run.critic_updates != n * s.critic_epochs * batches
        or len(run.audits) != n
        or len(run.events) != 1 + 6 * n
    ):
        raise ValueError("Incomplete checkpoint counters/calendar")
    expected_eta = run.audits[-1]["eta"] if n else run.initial_q_tail["eta"]
    expected_lambda = run.audits[-1]["lambda_after"] if n else 0.0
    if run.eta != expected_eta or run.multiplier != expected_lambda or not math.isfinite(run.eta):
        raise ValueError("Incoherent risk state")
    if (
        not math.isfinite(run.multiplier)
        or run.multiplier < 0
        or (not run.enabled and run.multiplier != 0)
    ):
        raise ValueError("Incoherent multiplier")
    for model, opt, updates, lr in [
        (run.actor, run.actor_optimizer, run.actor_updates, s.actor_lr),
        (run.critic, run.critic_optimizer, run.critic_updates, s.critic_lr),
    ]:
        if any(not torch.isfinite(p).all() for p in model.parameters()):
            raise ValueError("Nonfinite parameters")
        for group in opt.param_groups:
            if (
                group["lr"] != lr
                or group["betas"] != (0.9, 0.999)
                or group["eps"] != 1e-8
                or group["weight_decay"] != 0
            ):
                raise ValueError("Incompatible optimizer configuration")
        if updates == 0 and opt.state:
            raise ValueError("Unexpected optimizer state")
        if updates and len(opt.state) != len(list(model.parameters())):
            raise ValueError("Missing optimizer states")
        for p, values in opt.state.items():
            if int(values["step"]) != updates:
                raise ValueError("Optimizer step mismatch")
            for key in ("exp_avg", "exp_avg_sq"):
                if values[key].shape != p.shape or not torch.isfinite(values[key]).all():
                    raise ValueError("Invalid optimizer moments")


def save_checkpoint(run, path):
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    validate_state(run)
    if run.journal is None or run.status not in {"paused", "passed"}:
        raise ValueError("Checkpoint requires planned pause/completion and a run journal")
    if run.journal.last()["status"] not in {"ready", "completed", "loaded"}:
        raise ValueError("Run journal does not permit checkpointing")
    t0 = time.monotonic()
    run.journal.append(status="checkpointing", next_iteration=run.next_iteration)
    path.mkdir(parents=True, exist_ok=False)
    checkpoint_id = uuid.uuid4().hex
    attrs = (
        "eta",
        "multiplier",
        "generation",
        "next_iteration",
        "boundary",
        "initial_q_tail",
        "events",
        "audits",
        "actor_updates",
        "critic_updates",
    )
    state = dict(
        actor=run.actor.state_dict(),
        critic=run.critic.state_dict(),
        actor_optimizer=run.actor_optimizer.state_dict(),
        critic_optimizer=run.critic_optimizer.state_dict(),
        attrs={k: getattr(run, k) for k in attrs},
        collector=dict(
            used=sorted(run.collector.used),
            transitions=run.collector.transitions,
            trajectories=run.collector.trajectories,
            diagnostics=run.collector.diagnostics,
        ),
        telemetry=dict(records=run.telemetry.records, stability=run.telemetry.stability),
        rng=dict(
            strategy="coordinate_seedsequence_PCG64_v1",
            seed=run.settings.seed,
            next_iteration=run.next_iteration,
            torch_cpu=torch.random.get_rng_state(),
        ),
        budget=run.budget.snapshot() if run.budget else None,
    )
    with (path / "state.pt").open("xb") as f:
        torch.save(state, f)
        f.flush()
        os.fsync(f.fileno())
    manifest = dict(
        schema_version=SCHEMA,
        git_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        checkpoint_id=checkpoint_id,
        boundary=run.boundary,
        state_sha256=digest(path / "state.pt"),
        provenance=provenance(run.collector.source),
        settings=asdict(run.settings),
        condition=run.condition,
        risk_enabled=run.enabled,
        run_id=run.collector.run_id,
        journal=str(run.journal.path),
        checkpoint_wall_seconds=time.monotonic() - t0,
    )
    with (path / "manifest.json").open("x") as f:
        json.dump(manifest, f, indent=2, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    run.journal.append(
        status="paused",
        checkpoint_id=checkpoint_id,
        manifest_sha256=digest(path / "manifest.json"),
        next_iteration=run.next_iteration,
    )
    return manifest


def load_checkpoint(path, source, *, journal):
    if type(source) is not SyntheticMarket:
        raise PermissionError("Market optimization/resume remains blocked")
    path = Path(path)
    try:
        manifest = json.loads((path / "manifest.json").read_text())
        if manifest["schema_version"] != SCHEMA or manifest["state_sha256"] != digest(
            path / "state.pt"
        ):
            raise ValueError("Checkpoint schema/hash mismatch")
        if manifest["provenance"] != provenance(source):
            raise ValueError("Incompatible checkpoint code/data/scaler/runtime")
        log = RunJournal(journal, create=False)
        last = log.last()
        if (
            str(log.path) != manifest["journal"]
            or last["status"] != "paused"
            or last.get("checkpoint_id") != manifest["checkpoint_id"]
            or last.get("manifest_sha256") != digest(path / "manifest.json")
        ):
            raise ValueError("Run journal forbids stale/failed/interrupted checkpoint")
        state = torch.load(path / "state.pt", map_location="cpu", weights_only=True)
        run = SyntheticExperiment(
            source,
            SyntheticSettings(**manifest["settings"]),
            condition=manifest["condition"],
            risk_enabled=manifest["risk_enabled"],
            run_id=manifest["run_id"],
        )
        for name in ("actor", "critic", "actor_optimizer", "critic_optimizer"):
            getattr(run, name).load_state_dict(state[name])
        required_attrs = {
            "eta",
            "multiplier",
            "generation",
            "next_iteration",
            "boundary",
            "initial_q_tail",
            "events",
            "audits",
            "actor_updates",
            "critic_updates",
        }
        if set(state["attrs"]) != required_attrs:
            raise ValueError("Incomplete/unknown checkpoint attributes")
        for key, value in state["attrs"].items():
            setattr(run, key, value)
        run.collector.used = {tuple(x) for x in state["collector"]["used"]}
        for key in ("transitions", "trajectories", "diagnostics"):
            setattr(run.collector, key, state["collector"][key])
        run.telemetry.records = state["telemetry"]["records"]
        run.telemetry.stability = state["telemetry"]["stability"]
        rng = state["rng"]
        if (
            rng["strategy"] != "coordinate_seedsequence_PCG64_v1"
            or rng["seed"] != run.settings.seed
            or rng["next_iteration"] != run.next_iteration
        ):
            raise ValueError("Incompatible RNG strategy/state")
        if state["budget"]:
            budget = state["budget"]
            budget["consumed"] += manifest["checkpoint_wall_seconds"]
            run.budget = TimeBudget(**budget)
        if run.boundary != manifest["boundary"]:
            raise ValueError("Boundary mismatch")
        validate_state(run)
        if (
            run.audits
            and run.audits[-1]["policy_version"]
            != f"policy-{run.generation}:{fingerprint(run.actor)}"
        ):
            raise ValueError("Policy generation/hash mismatch")
        run.journal = log
        run.status = "paused"
        # Only after every check succeeded, consume this resume token.
        torch.random.set_rng_state(rng["torch_cpu"])
        log.append(
            status="loaded",
            checkpoint_id=manifest["checkpoint_id"],
            next_iteration=run.next_iteration,
        )
        return run
    except (KeyError, TypeError, OSError, RuntimeError) as exc:
        raise ValueError(f"Incomplete or corrupt checkpoint: {exc}") from exc
