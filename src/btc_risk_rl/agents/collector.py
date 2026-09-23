"""Complete immutable realizations; failed batches are never selectively replenished."""

import json
from dataclasses import dataclass

import numpy as np

from btc_risk_rl.agents.market_source import TrainingMarket
from btc_risk_rl.agents.synthetic import SyntheticMarket
from btc_risk_rl.config import STEP_MS, guard_development

ARRAYS = ("observations", "actions", "log_probs", "rewards", "times", "terminated", "truncated")
ROLES = {"A": 1, "Q": 2, "B": 3}


def immutable(x):
    a = np.asarray(x)
    return np.frombuffer(a.tobytes(), dtype=a.dtype).reshape(a.shape)


@dataclass(frozen=True)
class Fragment:
    realization: str
    route_id: str
    policy_version: str
    start: int
    observations: np.ndarray
    actions: np.ndarray
    log_probs: np.ndarray
    rewards: np.ndarray
    times: np.ndarray
    terminated: np.ndarray
    truncated: np.ndarray
    end_reason: str = "collection_window"

    def __post_init__(self):
        for name in ARRAYS:
            object.__setattr__(self, name, immutable(getattr(self, name)))

    def fragment(self, start, stop):
        if not 0 <= start < stop <= len(self.rewards):
            raise ValueError("Invalid fragment interval")
        states = {"observations", "times"}
        return Fragment(
            self.realization,
            self.route_id,
            self.policy_version,
            self.start + start,
            end_reason=self.end_reason if stop == len(self.rewards) else "collection_window",
            **{k: getattr(self, k)[start : stop + (1 if k in states else 0)] for k in ARRAYS},
        )


def assemble(fragments):
    if not fragments:
        raise ValueError("Empty realization")
    first = fragments[0]
    expected = 0
    previous = None
    for f in fragments:
        if (f.realization, f.route_id, f.policy_version) != (
            first.realization,
            first.route_id,
            first.policy_version,
        ):
            raise ValueError("Mixed realization, route or policy")
        n = len(f.rewards)
        if f.start != expected or n == 0:
            raise ValueError("Gap, overlap or empty fragment")
        for k in ARRAYS:
            shape = (n + 1, 13) if k == "observations" else (n + 1,) if k == "times" else (n,)
            a = getattr(f, k)
            if a.shape != shape or not np.isfinite(a).all():
                raise ValueError(f"Invalid fragment {k}")
        if previous is not None and (
            not np.array_equal(previous.observations[-1], f.observations[0])
            or previous.times[-1] != f.times[0]
        ):
            raise ValueError("Discontinuous fragment state")
        if f.end_reason not in {"collection_window", "segment_boundary", "partition_boundary"}:
            raise ValueError("Unknown end provenance")
        if expected + n < 180 and f.end_reason != "collection_window":
            raise ValueError("Censored fragment at segment or partition boundary")
        expected += n
        previous = f
    if expected != 180:
        raise ValueError("Incomplete finite-horizon realization")
    data = {}
    for key in ARRAYS:
        data[key] = np.concatenate(
            [
                getattr(f, key)
                if i == 0 or key not in {"observations", "times"}
                else getattr(f, key)[1:]
                for i, f in enumerate(fragments)
            ]
        )
    if not np.array_equal(data["observations"][:, 12], (180 - np.arange(181)) / 180):
        raise ValueError("Clock mismatch")
    if not (np.diff(data["times"]) == STEP_MS).all():
        raise ValueError("Temporal discontinuity")
    if not ((data["actions"] > 0) & (data["actions"] < 1)).all():
        raise ValueError("Action outside distribution support")
    if data["terminated"][:-1].any() or not data["terminated"][-1] or data["truncated"].any():
        raise ValueError("Censored or nonterminal realization")
    if not np.array_equal(data["observations"][0, 10:12], [0.0, 0.0]):
        raise ValueError("Invalid initial portfolio observation")
    if not np.allclose(
        data["rewards"], np.diff(data["observations"][:, 11]), rtol=1e-12, atol=1e-12
    ):
        raise ValueError("Inconsistent reward and portfolio observations")
    guard_development(int(data["times"][0]), int(data["times"][-1]) + STEP_MS)
    return Fragment(
        first.realization,
        first.route_id,
        first.policy_version,
        0,
        end_reason=fragments[-1].end_reason,
        **data,
    )


class BatchAbort(RuntimeError):
    def __init__(self, diagnostic):
        self.diagnostic = diagnostic
        super().__init__(f"Batch aborted: {diagnostic}")


class Collector:
    def __init__(self, source, *, seed, run_id):
        if type(source) not in {SyntheticMarket, TrainingMarket}:
            raise ValueError("Only synthetic or accepted training collection sources permitted")
        if type(seed) is not int or seed < 0 or not isinstance(run_id, str) or not run_id:
            raise ValueError("Invalid run identity or seed")
        self.source, self.seed, self.run_id = source, seed, run_id
        self.used = set()
        self.failed = False
        self.transitions = 0
        self.trajectories = 0
        self.diagnostics = []

    def collect(self, policy, *, role, iteration, count, fragment_steps=180):
        if self.failed:
            raise ValueError("Collector belongs to a failed run")
        if role not in ROLES or type(iteration) is not int or iteration < 0:
            raise ValueError("Invalid collection role/iteration")
        if (
            type(count) is not int
            or count < 1
            or type(fragment_steps) is not int
            or not 1 <= fragment_steps <= 180
        ):
            raise ValueError("Invalid batch/fragment size")
        key = (iteration, role)
        if key in self.used:
            raise ValueError("Collection role/iteration reused")
        self.used.add(key)
        starts = np.random.default_rng(
            np.random.SeedSequence([self.seed, ROLES[role], iteration, 0])
        )
        actions = np.random.default_rng(
            np.random.SeedSequence([self.seed, ROLES[role], iteration, 1])
        )
        result, replica, step = [], 0, 0
        exposure, fees, slippage = [], [], []
        try:
            policy.check()
            for replica in range(count):
                step = 0
                route = int(starts.choice(self.source.route_ids))
                env = self.source.environment(route)
                obs, info = env.reset()
                if info["cash"] != 10000 or info["btc"] != 0 or info["partition"] != "train":
                    raise ValueError("Invalid initial distribution")
                arrays = {name: [] for name in ARRAYS}
                arrays["observations"].append(obs)
                arrays["times"].append(info["observation_open_time_ms"])
                fragments, offset = [], 0
                identity = f"{self.run_id}/{iteration}/{role}/{replica}"
                route_id = self.source.route_identity(route, env.path)
                for step in range(180):
                    action, logp = policy.sample(obs, actions)
                    obs, reward, terminal, cut, info = env.step(action)
                    self.transitions += 1
                    exposure.append(float(obs[10]))
                    fees.append(info["commission"])
                    slippage.append(info["slippage_cost"])
                    last = step == 179
                    if (
                        terminal != last
                        or cut
                        or info["cvar_eligible"] != last
                        or info["bootstrap_mask"] != int(not last)
                        or info["trace_mask"] != int(not last)
                    ):
                        raise ValueError("Invalid H3 terminality or masks")
                    for name, value in [
                        ("observations", obs),
                        ("times", info["observation_open_time_ms"]),
                        ("actions", action),
                        ("log_probs", logp),
                        ("rewards", reward),
                        ("terminated", terminal),
                        ("truncated", cut),
                    ]:
                        arrays[name].append(value)
                    if (step + 1) % fragment_steps == 0 or last:
                        policy.check()
                        f = Fragment(
                            identity,
                            route_id,
                            policy.version,
                            offset,
                            end_reason=info["end_reason"] if last else "collection_window",
                            **{k: np.array(v) for k, v in arrays.items()},
                        )
                        fragments.append(f)
                        offset = step + 1
                        if not last:
                            checkpoint, status = env.collection_checkpoint()
                            if not np.array_equal(checkpoint, obs) or status["cvar_eligible"]:
                                raise ValueError("Invalid collection checkpoint")
                            arrays = {
                                k: [obs]
                                if k == "observations"
                                else [info["observation_open_time_ms"]]
                                if k == "times"
                                else []
                                for k in ARRAYS
                            }
                complete = assemble(fragments)
                if not np.isclose(
                    complete.rewards.sum(), complete.observations[-1, 11], rtol=1e-12, atol=1e-12
                ):
                    raise ValueError("Non-telescoping return")
                result.append(complete)
                self.trajectories += 1
            policy.check()
        except Exception as exc:
            self.failed = True
            raise BatchAbort(
                dict(
                    run_id=self.run_id,
                    role=role,
                    iteration=iteration,
                    replica=replica,
                    step=step,
                    policy_version=policy.version,
                    completed_trajectories=len(result),
                    transitions_consumed=self.transitions,
                    error=f"{type(exc).__name__}: {exc}",
                )
            ) from exc
        self.diagnostics.append(
            dict(
                role=role,
                iteration=iteration,
                profile=self.source.profile,
                trajectories=count,
                transitions=180 * count,
                mean_exposure=float(np.mean(exposure)),
                commission_total=float(sum(fees)),
                slippage_total=float(sum(slippage)),
                mean_log_return=float(np.mean([t.rewards.sum() for t in result])),
            )
        )
        return tuple(result)


def save_trajectory(path, trajectory):
    """No overwrite; allow_pickle=False compatible numeric archive, schema v1."""
    t = assemble([trajectory])
    metadata = dict(
        schema_version="h4_trajectory_v1",
        realization=t.realization,
        route_id=t.route_id,
        policy_version=t.policy_version,
        start=t.start,
        end_reason=t.end_reason,
    )
    with path.open("xb") as stream:
        np.savez(
            stream,
            metadata=np.frombuffer(json.dumps(metadata).encode(), dtype=np.uint8),
            **{key: getattr(t, key) for key in ARRAYS},
        )


def load_trajectory(path):
    """Audit-only roundtrip, not an input to the authorized synthetic runner."""
    with np.load(path, allow_pickle=False) as data:
        if set(data.files) != set(ARRAYS) | {"metadata"}:
            raise ValueError("Trajectory schema fields mismatch")
        metadata = json.loads(data["metadata"].tobytes())
        if metadata.pop("schema_version", None) != "h4_trajectory_v1":
            raise ValueError("Unknown trajectory schema")
        t = Fragment(**metadata, **{key: data[key] for key in ARRAYS})
    return assemble([t])
