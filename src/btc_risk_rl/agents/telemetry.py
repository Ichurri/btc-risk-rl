"""Measurement only: no metric changes learning, sampling or stopping by performance."""

import math
import resource
import sys
import time
from contextlib import contextmanager


class Telemetry:
    def __init__(self):
        self.records = []
        self.stability = []

    @contextmanager
    def measure(self, phase, iteration, collector, experiment=None):
        wall, cpu = time.monotonic(), time.process_time()
        trajectories, transitions = collector.trajectories, collector.transitions
        actor = getattr(experiment, "actor_updates", 0)
        critic = getattr(experiment, "critic_updates", 0)
        status = "complete"
        try:
            yield
        except BaseException:
            status = "failed"
            raise
        finally:
            self.records.append(
                dict(
                    phase=phase,
                    iteration=iteration,
                    status=status,
                    wall_seconds=time.monotonic() - wall,
                    cpu_seconds=time.process_time() - cpu,
                    rss_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                    * (1 if sys.platform == "darwin" else 1024),
                    trajectories=collector.trajectories - trajectories,
                    transitions=collector.transitions - transitions,
                    actor_updates=getattr(experiment, "actor_updates", 0) - actor,
                    critic_updates=getattr(experiment, "critic_updates", 0) - critic,
                )
            )


class TimeBudget:
    def __init__(self, *, total, reserve, estimates, profile, consumed=0.0, clock=time.monotonic):
        if not all(math.isfinite(x) for x in [total, reserve, consumed, *estimates.values()]):
            raise ValueError("Finite budget values required")
        if (
            not 0 < reserve < total
            or consumed < 0
            or not estimates
            or any(v <= 0 for v in estimates.values())
        ):
            raise ValueError("Invalid budget or estimates")
        self.total, self.reserve, self.estimates, self.profile = (
            total,
            reserve,
            dict(estimates),
            profile,
        )
        self.clock, self.start, self.consumed = clock, clock(), consumed

    def elapsed(self):
        return self.consumed + self.clock() - self.start

    def can_start(self, unit, profile):
        if profile != self.profile:
            raise ValueError("Budget estimate profile mismatch")
        if unit not in self.estimates:
            raise ValueError("Missing unit estimate")
        return self.total - self.elapsed() >= self.reserve + self.estimates[unit]

    def check_reserve(self):
        if self.total - self.elapsed() < self.reserve:
            raise TimeoutError("Unit exceeded budget saving margin; run invalid")

    def snapshot(self):
        return dict(
            total=self.total,
            reserve=self.reserve,
            estimates=self.estimates,
            profile=self.profile,
            consumed=self.elapsed(),
        )
