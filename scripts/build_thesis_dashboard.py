"""Generate the offline experimental progress dashboard; never run campaigns."""

from pathlib import Path

from btc_risk_rl.reporting.dashboard import ROOT, build

if __name__ == "__main__":
    print(build(Path(ROOT / "reports/avance-tesis/index.html")))
