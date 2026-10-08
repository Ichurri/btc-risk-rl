"""P3 unit wiring around the shared Q0/Q-A-B-D supervisor and P3 ledger."""

import json
import sys
from pathlib import Path

from btc_risk_rl.agents.synthetic import SyntheticMarket
from btc_risk_rl.config import load_config
from btc_risk_rl.pilots.p2 import file_hash
from btc_risk_rl.pilots.p2r_units import _run_units
from btc_risk_rl.pilots.p3_budget import P3Ledger
from btc_risk_rl.pilots.p3_critic import P3SyntheticSettings
from btc_risk_rl.pilots.p3_metrics import assess_campaign


def assess_completed_campaign(root, state):
    """Adjudicate every accepted P3 report; no checkpoint selection."""
    from btc_risk_rl.pilots.p3_market import roster, run_id_for

    rows = roster()
    units = state["units"]
    if state["cursor"] != len(rows) or len(units) != len(rows) * 11:
        return dict(decision="not_evaluable", reason="Incomplete P3 unit matrix")
    reports = []
    try:
        for index, (seed, condition, beta) in enumerate(rows):
            run_id = run_id_for(index, rows[index])
            work = Path(root) / run_id
            accepted = units[index * 11 : (index + 1) * 11]
            for unit, evidence in enumerate(accepted):
                point = work / f"checkpoint-{unit}"
                payload_path = work / f"unit-{unit}.json"
                payload = json.loads(payload_path.read_text())
                if (evidence["run_id"] != run_id or evidence["unit"] != unit
                        or evidence["report_sha256"] != file_hash(payload_path)
                        or evidence["checkpoint_sha256"] != file_hash(point / "state.pt")
                        or payload["checkpoint_sha256"] != evidence["checkpoint_sha256"]
                        or payload["beta"] != beta
                        or payload["report"]["settings"]["critic_beta"] != beta):
                    raise ValueError("Accepted P3 report/checkpoint identity mismatch")
            last = json.loads((work / "unit-10.json").read_text())
            diagnostic = last["report"]["diagnostic"]
            if (len(diagnostic["records"]) != 10
                    or diagnostic["trajectories"] != 640
                    or diagnostic["transitions"] != 640 * 180):
                raise ValueError("Incomplete P3 diagnostic")
            reports.append(dict(seed=seed, condition=condition, beta=beta,
                                status="passed", records=diagnostic["records"]))
    except (KeyError, OSError, TypeError, ValueError) as exc:
        return dict(decision="not_evaluable", reason=f"P3 evidence invalid: {exc}")
    return assess_campaign(reports)


def run_synthetic_units(root, config_path, rows, settings_for_row, *, max_units=None,
                        power_root=None, memory_available=None, disk_free=None,
                        fixture_window=False, heartbeat_seconds=5.0):
    """Small fabricated-route fixture; no TrainingMarket or market permit."""
    rows = tuple(rows)
    if not rows or len(rows) > 18 or len(set(rows)) != len(rows):
        raise ValueError("Distinct P3 synthetic identities required")
    configured = [settings_for_row(row) for row in rows]
    if any(type(s) is not P3SyntheticSettings
           or (s.seed, row[1], s.critic_beta) != row
           or s.iterations != configured[0].iterations
           for s, row in zip(configured, rows, strict=True)):
        raise PermissionError("P3 synthetic settings must match each run identity")
    root = Path(root).resolve()
    if not root.name.startswith("p3-synthetic-"):
        raise ValueError("P3 synthetic units require a separate p3-synthetic-* root")
    source = SyntheticMarket(load_config(Path(config_path).resolve()))
    return _run_units(
        root, config_path, configured[0], roster=rows, source=source,
        settings_for=lambda seed, condition, beta: settings_for_row((seed, condition, beta)),
        command_for=lambda request: [sys.executable, "-m", "btc_risk_rl.pilots.p3_worker",
                                     "--synthetic-request", str(request)],
        profile="p3_synthetic_units", diagnostic_n=2, max_units=max_units,
        power_root=power_root, memory_available=memory_available, disk_free=disk_free,
        fixture_window=fixture_window, heartbeat_seconds=heartbeat_seconds,
        ledger_type=P3Ledger,
    )


def run_historical_units():
    """Guarded P3 training-only executor; authorization remains disabled."""
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.pilots.p2r import check_service_context
    from btc_risk_rl.pilots.p3_market import (
        ADOPTION,
        ANCHORS,
        BASE_DESIGN,
        CAMPAIGN,
        CONFIG,
        DESIGN,
        ENTRYPOINT,
        MANIFEST,
        PREPARED,
        PROTOCOL,
        TRAIN_SHARD,
        TRAIN_SHARD_MANIFEST_SHA256,
        P3MarketPermit,
        P3MarketSettings,
        inspect_preflight,
        roster,
    )

    P3MarketPermit.require_campaign()
    check_service_context(require_linger=True)
    preflight = inspect_preflight()  # Identity and resources only; no route collection.
    if preflight["status"] != "read_only_ready_campaign_enabled":
        raise ValueError(f"P3 historical preflight not ready: {preflight['status']}")
    source = TrainingMarket(
        load_config(CONFIG), PREPARED, expected_manifest=ANCHORS[MANIFEST],
        training_shard=TRAIN_SHARD,
        expected_shard_manifest=TRAIN_SHARD_MANIFEST_SHA256,
    )
    rows = roster()
    return _run_units(
        CAMPAIGN, CONFIG, P3MarketSettings(seed=rows[0][0], critic_beta=rows[0][2]),
        roster=rows, source=source,
        settings_for=lambda seed, condition, beta: P3MarketSettings(
            seed=seed, critic_beta=beta,
        ),
        command_for=lambda request: [sys.executable, "-m", "btc_risk_rl.pilots.p3_worker",
                                     str(request)],
        profile="p3_market_units", diagnostic_n=64,
        require_service=True, require_linger=True,
        ledger_type=P3Ledger, completion_assessment=assess_completed_campaign,
        protocol_identity={str(path.relative_to(PROTOCOL.parents[2])): ANCHORS[path]
                           for path in (PROTOCOL, ADOPTION, DESIGN, BASE_DESIGN, MANIFEST, CONFIG)}
                          | {str(ENTRYPOINT.relative_to(PROTOCOL.parents[2])):
                             file_hash(ENTRYPOINT),
                             "p3_training_shard_manifest_sha256": TRAIN_SHARD_MANIFEST_SHA256},
    )
