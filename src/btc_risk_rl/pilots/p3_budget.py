"""P3 chained ledger with 18 runs and a maximum of 54 run-sessions."""

from btc_risk_rl.pilots.p2_budget import P2Ledger


class P3Ledger(P2Ledger):
    iterations = 10

    def begin(self, run_id, kind, now):
        if self.state["status"] != "ready":
            raise ValueError("Campaign not ready")
        run = self.state["runs"].setdefault(run_id, {"days": [], "resources": {}})
        sessions = run.setdefault("sessions", [])
        if self.day_key not in run["days"]:
            if (len(run["days"]) >= 3
                    or sum(len(r["days"]) for r in self.state["runs"].values()) >= 54):
                self.state["status"] = "incomplete"
                self.persist(now)
                raise ValueError("P3 active day/run limit exhausted")
            run["days"].append(self.day_key)
        if self.session_id not in sessions:
            if (len(sessions) >= 3
                    or sum(len(r.get("sessions", [])) for r in self.state["runs"].values()) >= 54):
                self.state["status"] = "incomplete"
                self.persist(now)
                raise ValueError("P3 session limit exhausted")
            sessions.append(self.session_id)
        self.state.update(status="running", pending=dict(run_id=run_id, kind=kind, start=now))
        self.persist(now)
