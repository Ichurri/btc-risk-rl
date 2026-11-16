"""Synthetic-only P3 critic arms; no historical profile or campaign entrypoint."""

from dataclasses import dataclass
from typing import ClassVar

from btc_risk_rl.pilots.p2 import P2SyntheticSettings


@dataclass(frozen=True)
class P3SyntheticSettings(P2SyntheticSettings):
    purpose: str = "p3_synthetic_tests_only"
    expected_purpose: ClassVar[str] = "p3_synthetic_tests_only"
    critic_beta: int = 0

    def __post_init__(self):
        super().__post_init__()
        if type(self.critic_beta) is not int or self.critic_beta not in {0, 1}:
            raise ValueError("critic_beta must be 0 or 1")
