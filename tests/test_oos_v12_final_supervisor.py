"""Synthetic gates for final acquisition and evaluation; no market access."""

import pytest


def _host(**changes):
    result = {"power": {"ac": True, "battery_percent": 70},
              "memory_available_bytes": 8 * 1024**3,
              "disk_free_bytes": 40 * 1024**3,
              "linger": "yes", "user_manager": "running"}
    result.update(changes)
    return result


def test_final_sessions_reenter_shared_evaluation_journal_identity():
    from btc_risk_rl.evaluation import historical_final_supervisor as final
    from btc_risk_rl.evaluation import historical_supervisor as technical

    assert final.SESSION_JOURNAL == technical.SESSION_JOURNAL
    assert final.SESSION_NAME == technical.SESSION_NAME


def test_final_prerequisite_audit_rejects_changed_technical_ledger_or_context(
    monkeypatch, tmp_path,
):
    import hashlib
    import json

    from btc_risk_rl.evaluation import historical_final_supervisor as target

    technical = tmp_path / "technical"
    technical.mkdir()
    ledger = technical / "ledger.jsonl"
    ledger.write_text("synthetic completed ledger\n")
    export = tmp_path / "technical-export"
    export.mkdir()
    bars = export / "bars.csv"
    bars.write_text("synthetic technical bars\n")
    manifest = export / "manifest.json"
    manifest.write_text(json.dumps({"bars_sha256": hashlib.sha256(bars.read_bytes()).hexdigest()}))
    closure = technical / "technical-closure.json"
    closure.write_text(json.dumps({
        "status": "passed", "partition": "technical_2023", "complete_policies": 108,
        "evaluation_ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
        "export_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
    }))
    monkeypatch.setattr(target, "TECH_CAMPAIGN", technical)
    monkeypatch.setattr(target, "TECH_CLOSURE", closure)
    monkeypatch.setattr(target, "TECH_EXPORT", export)
    approval = {"technical_closure_sha256": hashlib.sha256(closure.read_bytes()).hexdigest(),
                "technical_export_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest()}
    target._audit_technical_prerequisites(approval)
    ledger.write_text("tampered\n")
    with pytest.raises(ValueError, match="ledger"):
        target._audit_technical_prerequisites(approval)
    ledger.write_text("synthetic completed ledger\n")
    bars.write_text("tampered bars\n")
    with pytest.raises(ValueError, match="bars"):
        target._audit_technical_prerequisites(approval)


def test_final_source_preflight_rejects_closed_gate_before_any_market_open(
    monkeypatch, tmp_path,
):
    from btc_risk_rl.evaluation import access
    from btc_risk_rl.evaluation import historical_final_supervisor as target

    monkeypatch.setitem(access.ENABLED, "final_2024_2025_source", False)
    monkeypatch.setattr(target, "ROOT", tmp_path)
    monkeypatch.setattr(target, "verify_complete_main_roster",
                        lambda _root: pytest.fail("training roster opened"))
    with pytest.raises(PermissionError, match="disabled"):
        target.final_source_preflight()
    assert list(tmp_path.iterdir()) == []


def test_final_worker_rejects_closed_gate_before_ledger_or_export(monkeypatch, tmp_path):
    from btc_risk_rl.evaluation import access
    from btc_risk_rl.evaluation import historical_final_supervisor as target

    monkeypatch.setitem(access.ENABLED, "final_2024_2025", False)
    monkeypatch.setattr(target, "ROOT", tmp_path)
    monkeypatch.setattr(target, "_read_ledger_identity",
                        lambda: pytest.fail("ledger opened"))
    with pytest.raises(PermissionError, match="disabled"):
        target.worker("run-00-C0-b0", session_token="x" * 32, parent_pid=12345)


def test_final_source_preflight_requires_new_roots(monkeypatch, tmp_path):
    from btc_risk_rl.evaluation import historical_final_supervisor as target

    monkeypatch.setattr(target, "RAW", tmp_path / "raw")
    monkeypatch.setattr(target, "EXPORT", tmp_path / "export")
    monkeypatch.setattr(target, "_verified_final_prerequisites", lambda _scope: {
        "verified": {"ledger_sha256": "a" * 64},
    })
    monkeypatch.setattr(target, "sha", lambda _path: "b" * 64)
    monkeypatch.setattr(target, "host_budget", lambda **_kw: {
        "status": "ready", "blockers": [], "host": {},
        "budget": {"remaining_before_reserve": 1200.0},
    })
    assert target.final_source_preflight()["status"] == "ready"
    (tmp_path / "raw").mkdir()
    blocked = target.final_source_preflight()
    assert blocked["status"] == "blocked"
    assert any("root" in message.lower() for message in blocked["blockers"])


def test_final_source_reserves_full_fetch_unit_before_network(monkeypatch, tmp_path):
    from btc_risk_rl.evaluation import historical_final_supervisor as target

    monkeypatch.setattr(target, "RAW", tmp_path / "raw")
    monkeypatch.setattr(target, "EXPORT", tmp_path / "export")
    monkeypatch.setattr(target, "_verified_final_prerequisites", lambda _scope: {
        "verified": {"ledger_sha256": "a" * 64},
    })
    monkeypatch.setattr(target, "sha", lambda _path: "b" * 64)
    monkeypatch.setattr(target, "host_budget", lambda **_kw: {
        "status": "ready", "blockers": [], "host": {},
        "budget": {"remaining_before_reserve": 899.9},
    })
    blocked = target.final_source_preflight()
    assert blocked["status"] == "blocked"
    assert "budget" in " ".join(blocked["blockers"]).lower()


def test_final_source_block_does_not_fetch_or_create_roots(monkeypatch, tmp_path):
    from contextlib import nullcontext

    from btc_risk_rl.evaluation import historical_final_supervisor as target

    monkeypatch.setattr(target, "RAW", tmp_path / "raw")
    monkeypatch.setattr(target, "EXPORT", tmp_path / "export")
    monkeypatch.setattr(target, "read_pinned_approval", lambda *_args: {})
    monkeypatch.setattr(target, "invocation_id", lambda: "1" * 32)
    monkeypatch.setattr(target, "exclusive_campaign", lambda: nullcontext())
    monkeypatch.setattr(target, "final_source_preflight", lambda **_kwargs: {
        "status": "blocked", "blockers": ["memory"],
    })
    monkeypatch.setattr(target, "fetch_final_pages",
                        lambda *_args, **_kwargs: pytest.fail("final fetch reached"))

    class Journal:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def start(self, **_kwargs):
            return "token"

        def end(self, _token, **kwargs):
            assert kwargs["status"] == "ready"

    monkeypatch.setattr(target, "WFCostSessionJournal", Journal)
    result = target.acquire_final_source()
    assert result["status"] == "blocked"
    assert list(tmp_path.iterdir()) == []


def test_final_supervisor_pauses_then_reenters_only_at_complete_boundary(
    monkeypatch, tmp_path,
):
    import json

    from btc_risk_rl.evaluation import historical_final_supervisor as target
    from btc_risk_rl.evaluation.ledger import EvaluationLedger

    runs = [{"run_id": f"run-{index:02d}-{condition}-b0", "seed": 101,
             "condition": condition, "checkpoint_sha256": str(index + 1) * 64}
            for index, condition in enumerate(("C0", "C5"))]
    campaign = tmp_path / "final"
    export = tmp_path / "export"
    export.mkdir()
    (export / "manifest.json").write_text("synthetic export")
    monkeypatch.setattr(target, "CAMPAIGN", campaign)
    monkeypatch.setattr(target, "EXPORT", export)
    monkeypatch.setattr(target, "ROOT", tmp_path)
    monkeypatch.setattr(target, "final_preflight", lambda: {
        "verified": {"runs": runs, "ledger_sha256": "a" * 64},
    })
    monkeypatch.setattr(target, "host_budget", lambda **_kw: {
        "status": "ready", "blockers": [],
        "budget": {"remaining_before_reserve": 1200.0},
    })
    monkeypatch.setattr(target, "sha", lambda _path: "b" * 64)
    monkeypatch.setattr(target, "execution_code_sha256", lambda _root: "c" * 64)
    flags = {"pause": False, "visited": []}
    monkeypatch.setattr(target, "inspect_host", lambda: (
        _host(memory_available_bytes=0) if flags["pause"] else _host()
    ))

    def supervised(command, **_kwargs):
        run_id = command[command.index("--worker") + 1]
        identity = json.loads((campaign / "ledger.jsonl").read_text().splitlines()[0])["identity"]
        ledger = EvaluationLedger.open(campaign, identity)
        run = identity["roster"][ledger.state["cursor"]]
        assert run_id == run["run_id"]
        ledger.begin(run, token="invented")
        ledger.accept(run, token="invented", report_sha256="d" * 64,
                      trace_sha256="e" * 64, seconds=1.0)
        flags["visited"].append(run_id)
        if len(flags["visited"]) == 1:
            flags["pause"] = True
        return {"status": "passed", "wall_seconds": 1.0}

    monkeypatch.setattr(target, "supervise", supervised)
    monkeypatch.setattr(target, "_close_final", lambda _ledger, **_kw: {"status": "passed"})

    class Journal:
        def __init__(self):
            self.ends = []

        def end(self, _token, **kwargs):
            self.ends.append(kwargs["status"])

    first_journal = Journal()
    first = target._run_final_session(first_journal, "synthetic", 0.0)
    assert first["status"] == "ready" and first["accepted"] == 1
    assert first_journal.ends == ["ready"]
    flags["pause"] = False
    second_journal = Journal()
    second = target._run_final_session(second_journal, "synthetic", 0.0)
    assert second["status"] == "passed" and second["accepted"] == 2
    assert flags["visited"] == [run["run_id"] for run in runs]
    assert second_journal.ends == ["ready"]
