"""Read-only audit of the stopped WF replacement session before Q0."""

import json
import time

from btc_risk_rl.pilots.wf_cost_replacement_exec import (
    CAMPAIGN,
    MARKET_EXECUTION_ENABLED,
    REGISTRATION,
    digest,
)
from btc_risk_rl.pilots.wf_cost_session import WFCostSessionJournal


def main():
    assert MARKET_EXECUTION_ENABLED is False
    assert REGISTRATION.is_file()
    assert sorted(p.name for p in CAMPAIGN.iterdir()) == ["sessions.jsonl", "sessions.lock"]
    assert not (CAMPAIGN / "ledger.jsonl").exists()
    assert not (CAMPAIGN / "wf-2021").exists()
    with WFCostSessionJournal(CAMPAIGN / "sessions.jsonl", campaign=CAMPAIGN.name,
                              read_only=True) as sessions:
        assert len(sessions.sessions) == 1
        start = sessions.sessions[0]["start"]
        end = sessions.sessions[0]["end"]
        assert start["event"] == "start" and end["event"] == "end"
        assert end["status"] == "failed"
        assert end["reason"] == "WF cost root exists without a valid ledger"
        charges = sessions.charges({}, now=time.time())
        assert charges.blocked
        result = dict(status="failed_before_q0", campaign=CAMPAIGN.name,
                      invocation_id=start["invocation_id"],
                      started_utc=start["utc"], ended_utc=end["utc"],
                      session_wall_seconds=end["wall_seconds"],
                      reason=end["reason"], session_chain_valid=True,
                      session_sha256=digest(CAMPAIGN / "sessions.jsonl"),
                      registration_sha256=digest(REGISTRATION),
                      ledger_exists=False, units_started=0, checkpoints_accepted=0,
                      reentry_blocked=charges.blocked,
                      session_days=sorted(charges.session_days),
                      gate_closed=not MARKET_EXECUTION_ENABLED)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
