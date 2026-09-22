"""Synthetic arithmetic/specification only: no agent, optimizer, market or H2 imports."""

import hashlib
import json
import math
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def near(a, b):
    assert math.isclose(a, b, rel_tol=0, abs_tol=1e-12), (a, b)


def f_value(losses, alpha, eta):
    return eta + sum(max(loss - eta, 0) for loss in losses) / (alpha * len(losses))


def quantile_tail(losses, alpha):
    ordered = sorted(losses)
    eta = ordered[math.ceil((1 - alpha) * len(ordered)) - 1]
    above = sum(loss > eta for loss in losses)
    ties = sum(loss == eta for loss in losses)
    fraction = (alpha * len(losses) - above) / ties
    assert 0 <= fraction <= 1
    weights = [1.0 if loss > eta else fraction if loss == eta else 0.0 for loss in losses]
    near(sum(weights), alpha * len(losses))
    tail = sum(loss * weight for loss, weight in zip(losses, weights, strict=True))
    tail /= alpha * len(losses)
    near(tail, f_value(losses, alpha, eta))
    near(tail, min(f_value(losses, alpha, candidate) for candidate in losses))
    return {"eta": eta, "weights": weights, "tail_mass": sum(weights), "cvar": tail}


def main():
    old_script = ROOT / 'docs/evidence/adr002-proposal/checks.py'
    old = json.loads(subprocess.check_output([sys.executable, str(old_script)], cwd=ROOT))
    recorded = json.loads((old_script.parent / 'results.json').read_text())
    assert old['results'] == recorded['results']
    (Path(__file__).parent / 'v1-reproduction.json').write_text(json.dumps(old, indent=2) + '\n')
    algebra, specification = {}, {}

    cases = []
    for losses, alpha in [([0.2, 0.1, -0.02, -0.1], 0.375),
                          ([0.2, 0.2, -0.1, -0.1], 0.375),
                          ([-0.1] * 4, 0.05), ([0.2, 0.1, 0, -0.1], 0.5),
                          ([0.2, 0.1, -0.02, -0.1], 0.05),
                          ([0.2, 0.1, -0.02, -0.1], 0.1)]:
        cases.append({"losses": losses, "alpha": alpha, **quantile_tail(losses, alpha)})
    assert cases[1]['weights'] == [0.75, 0.75, 0, 0]
    near(cases[0]['eta'], 0.1)
    near(cases[0]['cvar'], 1 / 6)
    algebra['quantile_ties_fractional_mass'] = cases

    # Exact enumeration of a population. Q has one draw; no Monte Carlo or learning.
    population = [0.2, -0.1, -0.1, -0.1]
    alpha = 0.5
    rho = min(f_value(population, alpha, eta) for eta in population)
    expected_f = sum(f_value(population, alpha, eta) for eta in population) / 4
    expected_empirical = sum(population) / 4
    near(rho, 0.05)
    near(expected_f, 0.0875)
    near(expected_empirical, -0.025)
    # Enumerating every independent one-draw B recovers population F at fixed eta.
    for eta in (-0.1, 0.2):
        near(sum(f_value([loss], alpha, eta) for loss in population) / 4,
             f_value(population, alpha, eta))
    audit = [-0.1, -0.1]  # A possible finite B can underestimate even population rho.
    assert f_value(audit, alpha, -0.1) < rho
    algebra['population_vs_empirical_vs_fixed_eta'] = {
        'rho_population': rho, 'expected_F_independent_Q': expected_f,
        'expected_empirical_CVaR_Q': expected_empirical,
        'possible_F_B': f_value(audit, alpha, -0.1),
    }

    rows = []
    for h, equity, btc in [(1, 10000, 0), (0.5, 11000, 55),
                           (1, 11000, 55), (1, 9000, 67.5), (1, 11000, 0)]:
        cash = equity - btc * 100
        weight, z = btc * 100 / equity, math.log(equity / 10000)
        outside_at_h1 = h == 1 and (weight != 0 or z != 0)
        rows.append({'h': h, 'equity': equity, 'btc': btc, 'cash': cash,
                     'weight': weight, 'log_equity': z, 'outside_support_at_h1': outside_at_h1})
        near(cash + btc * 100, equity)
    assert [r['outside_support_at_h1'] for r in rows] == [False, False, True, True, True]
    # Action functions are mathematical witnesses, not a policy class or trained agent.
    for j in range(181):
        h = (180 - j) / 180
        for w in ([0.0] if j == 0 else [0, 0.5, 1]):
            gate = max(0.0, 180 * h - 179)
            near(0.25 + 0.5 * gate * w, 0.25)
    counterexample = {'same_training_support': True, 'h': 1, 'weight': 0.5,
                      'function_1': 0.25, 'function_2': 0.50}
    assert counterexample['function_1'] != counterexample['function_2']
    specification['joint_support_not_policy_transfer'] = {'states': rows, 'witness': counterexample}

    # Fixed arithmetic across minibatch permutations. No PPO update is executed.
    advantages, losses = [0.02, -0.03], [0.2, -0.1]
    eta, multiplier, alpha = 0.1, 0.4, 0.5
    d_values = [a - multiplier * max(loss - eta, 0) / alpha
                for a, loss in zip(advantages, losses, strict=True)]
    near(d_values[0], -0.06)
    near(d_values[1], -0.03)
    for permutation in ([0, 1], [1, 0]):
        assert sorted((i, d_values[i]) for i in permutation) == list(enumerate(d_values))
    zero_risk = list(advantages)
    assert zero_risk == advantages
    # Finite audit: F at eta=.1 exceeds empirical CVaR; dual follows F, not rho_hat.
    b = [0.2, -0.1]
    rho_b = min(f_value(b, alpha, candidate) for candidate in b)
    # With alpha=.5 this sample has an interval of minimizers: use another eta witness.
    eta_audit = quantile_tail([0.25, 0.4], alpha)['eta']
    f_b = f_value(b, alpha, eta_audit)
    near(f_b, 0.25)
    near(rho_b, 0.2)
    lam_next = max(0, 0.4 + 0.1 * (f_b - 0.22))
    near(lam_next, 0.403)
    assert max(0, 0.4 + 0.1 * (rho_b - 0.22)) < 0.4
    specification['frozen_coefficients_dual_and_risk_off'] = {
        'D': d_values, 'risk_off': zero_risk, 'audit_eta': eta_audit,
        'F_B': f_b, 'empirical_CVaR_B': rho_b, 'lambda_next': lam_next,
    }

    # A trace of proposed roles/order, not a mock trainer or rollout implementation.
    trace = ['Q0/pi0', 'eta0', 'A0/pi0', 'actor1', 'critic1', 'Q1/pi1', 'eta1',
             'B1/pi1', 'dual1', 'A1/pi1', 'actor2', 'critic2', 'Q2/pi2', 'eta2',
             'B2/pi2', 'dual2']
    for k in (0, 1):
        assert trace.index(f'eta{k}') < trace.index(f'A{k}/pi{k}')
        assert trace.index(f'A{k}/pi{k}') < trace.index(f'actor{k+1}')
        assert trace.index(f'actor{k+1}') < trace.index(f'critic{k+1}')
        assert trace.index(f'critic{k+1}') < trace.index(f'Q{k+1}/pi{k+1}')
        assert trace.index(f'Q{k+1}/pi{k+1}') < trace.index(f'eta{k+1}')
        assert trace.index(f'eta{k+1}') < trace.index(f'B{k+1}/pi{k+1}')
        assert trace.index(f'B{k+1}/pi{k+1}') < trace.index(f'dual{k+1}')
    n_a, n_q, n_b, iterations = 4, 2, 4, 2
    trajectories = n_q + iterations * (n_a + n_q + n_b)
    assert trajectories == 22
    assert 180 * trajectories == 3960
    cuts_v2 = []
    for role in ('A', 'Q', 'B'):
        for case in old['results']['cut_examples_specification_only']:
            complete = case['length'] == 180
            waiting = not complete and case['reason'] == 'collection_window'
            status = 'complete' if complete else 'await_complete' if waiting else 'reject'
            masks = (0, 0) if complete else None
            assert complete == case['cvar']
            if waiting:
                assert masks is None  # v2 constructs no partial target or bootstrap.
            cuts_v2.append({'role': role, 'length': case['length'], 'reason': case['reason'],
                            'status_v2': status, 'last_masks_v2': masks, 'cvar': complete})
    specification['sample_roles_and_resource_accounting'] = {
        'proposed_trace': trace, 'cuts_v2': cuts_v2, 'trajectories_per_condition': trajectories,
        'transitions_per_condition': 180 * trajectories,
        'C0_auxiliary_trajectories': n_q + iterations * (n_q + n_b),
    }

    sortinos = []
    for returns in ([0.02, -0.01, 0.01, -0.02], [0.03, -0.01, 0.01, -0.02], [0.0]*4):
        downside = math.sqrt(sum(min(u, 0)**2 for u in returns) / len(returns))
        score = sum(returns) / len(returns) / downside if downside else None
        sortinos.append({'returns_simple': returns, 'downside': downside, 'sortino': score})
    near(sortinos[0]['sortino'], 0)
    near(sortinos[1]['sortino'], 0.22360679774997896)
    assert sortinos[2]['sortino'] is None
    algebra['sortino_arithmetic_not_cvar_guarantee'] = sortinos

    evidence_files = [Path(__file__), old_script,
                      ROOT / 'docs/proposals/ADR-002-propuesta-v2.md']
    report = {
        'status': 'passed', 'scope': 'synthetic algebra and proposal specification only',
        'utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
        'platform': platform.platform(), 'prior_proposal_commit': '082db3e',
        'head_at_run': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'v1_reproduced_groups': old['groups'], 'v1_results_equal_recorded': True,
        'new_algebra_groups': algebra, 'new_specification_groups': specification,
        'h2_suite': 'separate pytest.log; no H2 code imported by these checks',
        'unchanged_h2_files_sha256': old['unchanged_h2_files_sha256'],
        'checked_files_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in evidence_files},
    }
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
