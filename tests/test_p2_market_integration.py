"""P2 historical profile guards; accepted H1 fixture is fabricated, never real market."""
import json
import subprocess
import sys

import pytest
from test_simulator import accepted_synthetic as accepted_fixture

accepted_synthetic = accepted_fixture


def test_market_settings_exact_roster_and_risk_bound():
    from btc_risk_rl.pilots.p2_market import P2MarketSettings, design, roster
    s = P2MarketSettings(seed=610031)
    assert (s.iterations, s.critic_epochs, s.n_a, s.n_q, s.n_b) == (10, 4, 64, 400, 400)
    assert s.bound == 0.10536051565782628
    assert roster() == [(610031, 'C0'), (610031, 'C5'), (610031, 'C10'),
                        (610047, 'C5'), (610047, 'C10'), (610047, 'C0'),
                        (610081, 'C10'), (610081, 'C0'), (610081, 'C5')]
    assert design()['market_execution_authorized'] is False
    with pytest.raises(ValueError):
        P2MarketSettings(seed=610031, n_q=399)
    with pytest.raises(ValueError):
        P2MarketSettings(seed=410031)


def test_market_cli_rejects_edited_json_before_loader_or_output(tmp_path):
    path = tmp_path / 'edited.json'
    path.write_text(json.dumps({'authorized': True, 'market_execution_authorized': True}))
    output = tmp_path / 'never-created'
    proc = subprocess.run([sys.executable, 'scripts/run_p2.py', '--profile', 'market',
        '--protocol', str(path), '--config', '/missing/config', '--output', str(output)],
        capture_output=True, text=True)
    assert proc.returncode == 2 and 'NOT AUTHORIZED' in proc.stderr
    assert not output.exists()


def test_public_market_command_rejects_canonical_protocol_before_loader(tmp_path):
    from btc_risk_rl.pilots.p2_market import PROTOCOL

    output = tmp_path / 'never-created'
    proc = subprocess.run([sys.executable, 'scripts/run_p2.py', '--profile', 'market',
        '--protocol', str(PROTOCOL), '--config', '/missing/config',
        '--output', str(output)], capture_output=True, text=True)
    assert proc.returncode == 2 and 'NOT AUTHORIZED' in proc.stderr
    assert not output.exists()


def test_permit_inactive_and_direct_training_blocked_without_source_load(accepted_synthetic, monkeypatch):
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.agents.trainer import SyntheticExperiment
    from btc_risk_rl.data.binance import sha256
    from btc_risk_rl.pilots.p2_market import P2MarketPermit, P2MarketSettings
    c, _, prepared, _ = accepted_synthetic
    source = TrainingMarket(c, prepared, expected_manifest=sha256(prepared / 'manifest.json'))
    monkeypatch.setattr(source, 'environment', lambda *_: pytest.fail('trajectory created'))
    with pytest.raises(PermissionError):
        SyntheticExperiment(source, P2MarketSettings(seed=610031), condition='C5', run_id='x')
    with pytest.raises(PermissionError):
        P2MarketPermit.require_registration()


def test_registration_json_edit_cannot_activate_market(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import p2_market

    altered = tmp_path / 'registration.json'
    altered.write_text(json.dumps({'active': True, 'approval_record': 'fabricated',
                                   'campaign_permit': 'fabricated'}))
    monkeypatch.setattr(p2_market, 'REGISTRY', altered)
    with pytest.raises(PermissionError, match='reviewed code'):
        p2_market.P2MarketPermit.require_registration()
    monkeypatch.setattr(p2_market, 'inspect_training_source',
                        lambda *_args, **_kwargs: pytest.fail('market source loaded'))
    with pytest.raises(ValueError, match='registration identity'):
        p2_market.inspect_preflight()


def test_changed_market_config_rejects_before_training_view(tmp_path, monkeypatch):
    from btc_risk_rl.pilots import p2_market

    changed = tmp_path / 'initial.toml'
    changed.write_text('changed configuration')
    monkeypatch.setattr(p2_market, 'CONFIG', changed)
    monkeypatch.setattr(p2_market, 'inspect_training_source',
                        lambda *_args, **_kwargs: pytest.fail('market source loaded'))
    with pytest.raises(ValueError, match='configuration identity'):
        p2_market.inspect_preflight()
    with pytest.raises(PermissionError, match='configuration identity'):
        p2_market.P2MarketPermit.require_registration()


def test_readonly_preflight_fixture_identity_and_no_trajectory(accepted_synthetic, monkeypatch):
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.pilots.p2_market import inspect_training_source
    c, _, prepared, _ = accepted_synthetic
    monkeypatch.setattr(TrainingMarket, 'environment', lambda *_: pytest.fail('trajectory created'))
    result = inspect_training_source(c, prepared, expected_manifest=__import__('hashlib').sha256(
        (prepared/'manifest.json').read_bytes()).hexdigest())
    assert result['accepted_starts'] == 7048
    assert result['validation_observations_loaded'] is False
    assert result['normalizer_refitted'] is False
    assert result['scaler_sha256'] == __import__('hashlib').sha256(
        (prepared/'scaler.json').read_bytes()).hexdigest()
    assert result['first_target_ms'] < result['last_target_ms'] < 1672531200000
    assert not hasattr(result, 'validation_path')


def test_market_d_requires_live_registered_permit_even_for_fixture(accepted_synthetic):
    from btc_risk_rl.agents.collector import Collector
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.agents.models import Actor, FrozenPolicy
    from btc_risk_rl.data.binance import sha256
    c, _, prepared, _ = accepted_synthetic
    source = TrainingMarket(c, prepared, expected_manifest=sha256(prepared / 'manifest.json'))
    col = Collector(source, seed=610031, run_id='fixture')
    with pytest.raises(PermissionError):
        col.collect(FrozenPolicy(Actor(hidden=4, seed=1), generation=0), role='D',
                    iteration=0, count=1)


def test_fabricated_accepted_fixture_collects_d_with_frozen_policy_only(
    accepted_synthetic, monkeypatch
):
    from btc_risk_rl.agents.collector import Collector
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.agents.models import Actor, FrozenPolicy, fingerprint
    from btc_risk_rl.data.binance import sha256
    from btc_risk_rl.pilots.p2_market import P2MarketPermit

    c, _, prepared, _ = accepted_synthetic
    source = TrainingMarket(c, prepared, expected_manifest=sha256(prepared / 'manifest.json'))
    policy = FrozenPolicy(Actor(hidden=4, seed=7), generation=3)
    before = fingerprint(policy._actor)
    permit = P2MarketPermit('fixture-only')
    monkeypatch.setattr(permit, 'validate_d', lambda *_: None)
    collector = Collector(source, seed=610031, run_id='fixture', diagnostic_permit=permit)
    batch = collector.collect(policy, role='D', iteration=0, count=2)
    assert len(batch) == 2
    assert collector.trajectories == 2 and collector.transitions == 360
    assert all(t.policy_version == policy.version and len(t.rewards) == 180 for t in batch)
    assert fingerprint(policy._actor) == before
    assert source.audit['validation_observations_loaded'] is False


def test_market_checkpoint_restoration_rejects_without_permit_before_loading(accepted_synthetic, tmp_path):
    from btc_risk_rl.agents.checkpoint import load_checkpoint
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.data.binance import sha256
    c, _, prepared, _ = accepted_synthetic
    source = TrainingMarket(c, prepared, expected_manifest=sha256(prepared / 'manifest.json'))
    with pytest.raises(PermissionError):
        load_checkpoint(tmp_path/'nonexistent', source, journal=tmp_path/'journal')


def test_readonly_budget_snapshot_la_paz_and_no_outputs(tmp_path):
    from datetime import datetime, timezone

    from btc_risk_rl.pilots.p2_market import inspect_shared_budget
    now = datetime(2026, 9, 25, 12, tzinfo=timezone.utc).timestamp()
    path = tmp_path/'p0-approved-v1'
    path.mkdir()
    (path/'ledger.jsonl').write_text(json.dumps({'status':'completed',
        'days': {'2026-09-25': {'charged_wall_seconds': 1200}}})+'\n')
    snap = inspect_shared_budget(tmp_path, now=now)
    assert snap['day_local'] == '2026-09-25'
    assert snap['external_seconds'] == 1200
    assert snap['remaining_seconds'] == 9600
    assert not (tmp_path/'shared-pilot-budget').exists()


def test_market_unit_and_diagnostic_cannot_create_artifacts_without_lease(accepted_synthetic, tmp_path):
    from btc_risk_rl.agents.market_source import TrainingMarket
    from btc_risk_rl.data.binance import sha256
    from btc_risk_rl.pilots.p2 import Diagnostic
    from btc_risk_rl.pilots.p2_market import P2MarketSettings
    from btc_risk_rl.pilots.p2_runner import complete_unit
    c, _, prepared, _ = accepted_synthetic
    source = TrainingMarket(c, prepared, expected_manifest=sha256(prepared/'manifest.json'))
    settings = P2MarketSettings(seed=610031)
    output = tmp_path/'blocked'
    with pytest.raises(PermissionError):
        complete_unit(source, settings, root=output, condition='C0', run_id='run-00-C0',
                      unit=0)
    assert not output.exists()
    with pytest.raises(PermissionError):
        Diagnostic(tmp_path/'D', n=64).bind(source, settings.seed, 'run-00-C0')
    assert not (tmp_path/'D').exists()


def test_market_entrypoint_stays_blocked_with_canonical_protocol(tmp_path):
    from btc_risk_rl.pilots.p2 import entrypoint
    from btc_risk_rl.pilots.p2_market import PROTOCOL
    output = tmp_path/'never-created'
    with pytest.raises(PermissionError):
        entrypoint(profile='market', output=output, config='/missing', protocol=PROTOCOL)
    assert not output.exists()
