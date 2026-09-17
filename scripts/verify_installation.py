"""Capture verification on the machine that actually runs this script."""

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--context", choices=["local", "remote"], required=True)
args = parser.parse_args()
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
out = Path("artifacts") / f"verification-{args.context}-{stamp}"
out.mkdir(parents=True, exist_ok=False)
report = {
    "context_declared_by_operator": args.context,
    "platform": platform.platform(),
    "python": sys.version,
    "time_utc": stamp,
    "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "git_status": subprocess.check_output(["git", "status", "--short"], text=True),
    "training_executed": False,
    "final_test_accessed": False,
    "commands": [],
}
commands = [
    ["uv", "run", "--frozen", "btc-risk", "config-check"],
    ["uv", "run", "--frozen", "ruff", "check", "."],
    ["uv", "run", "--frozen", "pytest", "-q"],
]
for i, cmd in enumerate(commands):
    r = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out / f"{i}.log").write_text(r.stdout)
    print(r.stdout)
    report["commands"].append({"command": cmd, "exit_code": r.returncode, "log": f"{i}.log"})
report["status"] = "passed" if all(c["exit_code"] == 0 for c in report["commands"]) else "failed"
(out / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
print(out / "verification.json")
sys.exit(0 if report["status"] == "passed" else 1)
