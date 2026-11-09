"""One-shot, fail-closed admission for the independent 2022-03 study."""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime

from btc_risk_rl.pilots.budget import LA_PAZ
from btc_risk_rl.pilots.wf_cost_2022_03_exec import (
    CAMPAIGN,
    require_campaign,
)

# Worst-case preparation timeouts, Q0 cap and existing closure reserve.
MIN_START_WINDOW_SECONDS = 900 + 120 + 180 + 120 + 600


def launch_once(*, now: float, preflight: Callable[[], dict],
                invoke: Callable[[str], object]) -> dict:
    """Admit a first session only; the worker retains every budget guard."""
    require_campaign()
    local = datetime.fromtimestamp(now, LA_PAZ)
    if local.date().isoformat() != "2026-11-10" or not 1 <= local.hour < 9:
        return {"status": "outside_window"}
    seconds_left = (9 - local.hour) * 3600 - local.minute * 60 - local.second
    if seconds_left < MIN_START_WINDOW_SECONDS:
        return {"status": "insufficient_window", "seconds_left": seconds_left}
    if CAMPAIGN.exists():
        return {"status": "root_exists"}
    result = preflight()
    if result.get("status") != "ready":
        return {"status": "blocked", "preflight": result}
    invoke("prepare")
    invoke("run")
    return {"status": "launched", "preflight": result,
            "observed_epoch": time.time()}
