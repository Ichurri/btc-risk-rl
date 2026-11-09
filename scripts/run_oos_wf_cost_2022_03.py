"""Separately approved 2022-only WF cost study; never opens validation/final."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from btc_risk_rl.pilots.wf_cost_2022_03_exec import (
    CAMPAIGN,
    EXPECTED_FIT_ROWS,
    EXPECTED_ROUTES,
    inspect_preflight,
    require_campaign,
)
from btc_risk_rl.pilots.wf_cost_2022_03_orchestrator import BudgetAttempt, PreflightBlocked


def _checked_command(args, *, name):
    result = subprocess.run(args, capture_output=True, text=True, check=False,
                            timeout=900 if name == "suite" else 120)
    if result.returncode:
        raise ValueError(f"WF 2022 {name} failed: {result.stderr[-2000:]}\n{result.stdout[-2000:]}")
    return dict(command=args, stdout=result.stdout[-2000:], stderr=result.stderr[-2000:])


def prepare():
    """Charge the complete code and host checks before creating any market root."""
    from btc_risk_rl.pilots.wf_cost import inspect_budget

    require_campaign()

    def external(now):
        budget = inspect_budget(now=now, campaign=CAMPAIGN)
        if not budget["ok"]:
            raise PreflightBlocked("Another campaign is active")
        return budget["global_spent"]

    with BudgetAttempt(CAMPAIGN.parent, gate=require_campaign,
                       authorize=require_campaign, external_spent=external) as attempt:
        if attempt.admit({}, unit=0) != "start":
            raise PreflightBlocked("WF 2022 budget cannot reserve Q0 and closure")
        root = Path(__file__).resolve().parents[1]
        checks = {}
        checks["suite"] = attempt.run_check(
            "suite", lambda: _checked_command(
                [sys.executable, "-m", "pytest", "-q"], name="suite"))
        checks["ruff"] = attempt.run_check(
            "ruff", lambda: _checked_command(
                [sys.executable, "-m", "ruff", "check", str(root)], name="ruff"))

        def watched_preflight():
            output = subprocess.run(
                [sys.executable, str(root / "scripts/audit_oos_wf_cost_2022_03_preflight.py")],
                capture_output=True, text=True, check=False, timeout=180, cwd=root,
            )
            if output.returncode:
                raise ValueError(f"WF 2022 watched preflight failed: {output.stderr[-2000:]}")
            result = json.loads(output.stdout)
            if result["preflight"]["status"] != "ready":
                raise PreflightBlocked(json.dumps(result["preflight"]["blockers"],
                                                   ensure_ascii=False))
            if result["protected_or_shared_csv_opened"] is not False:
                raise ValueError("WF 2022 protected market access")
            return result

        checks["preflight"] = attempt.run_check("preflight", watched_preflight)

        def fold():
            result = checks["preflight"]["fold_metadata"]
            if (result["episodes"] != EXPECTED_ROUTES
                    or result["fit_rows"] != EXPECTED_FIT_ROWS
                    or result["source_profile"] != "accepted_train_collection_only"
                    or result["validation_observations_loaded"]):
                raise ValueError("WF 2022 fold integrity mismatch")
            return result

        checks["fold"] = attempt.run_check("fold", fold)
        decision = attempt.admit({}, unit=0)
        if decision != "start":
            raise PreflightBlocked(f"WF 2022 budget after checks: {decision}")
        print(json.dumps(dict(status="ready", observed_epoch=time.time(), checks=checks,
                              metered_attempt=attempt.token), indent=2, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--preflight", action="store_true")
    actions.add_argument("--prepare", action="store_true")
    actions.add_argument("--run", action="store_true")
    parser.add_argument("--stop-after-q0", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(inspect_preflight(), indent=2, sort_keys=True))
        return
    if args.prepare:
        prepare()
        return
    if args.stop_after_q0 not in {True, False}:
        raise SystemExit("Invalid Q0 pause option")
    try:
        require_campaign()
    except PermissionError as exc:
        raise SystemExit(str(exc)) from exc
    from btc_risk_rl.pilots.wf_cost_2022_03_units import run_units

    state = run_units(stop_after_q0=args.stop_after_q0)
    print(json.dumps(dict(status=state["status"], units=len(state["units"]))))
    if state["status"] in {"failed", "incomplete"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
