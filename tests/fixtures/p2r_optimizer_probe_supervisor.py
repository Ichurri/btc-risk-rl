"""Resume one synthetic P2R unit with a worker computing gradient norms."""

import json
import sys
from pathlib import Path

from btc_risk_rl.agents.synthetic import SyntheticMarket
from btc_risk_rl.config import load_config
from btc_risk_rl.pilots.p2 import P2SyntheticSettings
from btc_risk_rl.pilots.p2r_units import _run_units


def main():
    root, power, marker = map(Path, sys.argv[1:])
    settings = P2SyntheticSettings(
        iterations=1, hidden=4, n_a=1, n_q=2, n_b=2,
        actor_epochs=1, critic_epochs=4, seed=610031,
    )
    config = Path("configs/initial.toml")
    worker = Path(__file__).with_name("p2r_optimizer_busy_worker.py").resolve()
    result = _run_units(
        root, config, settings, roster=[(settings.seed, "C5")],
        source=SyntheticMarket(load_config(config)),
        settings_for=lambda _seed: settings,
        command_for=lambda request: [sys.executable, str(worker), str(request), str(marker)],
        profile="p2r_synthetic_units", diagnostic_n=2,
        power_root=power, memory_available=4 * 1024**3,
        disk_free=10 * 1024**3, fixture_window=True, heartbeat_seconds=.05,
    )
    print(json.dumps(dict(status=result["status"], accepted_units=len(result["units"]))))
    if result["status"] == "failed":
        raise SystemExit(1)
    else:
        raise SystemExit("Optimizer signal probe did not fail as expected")


if __name__ == "__main__":
    main()
