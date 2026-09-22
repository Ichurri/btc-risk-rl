"""Arithmetic/specification checks for v2.1 only; no agents or market data."""

import hashlib
import itertools
import json
import math
import platform
import subprocess
import sys
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path


def near(x, y):
    assert math.isclose(x, y, rel_tol=1e-12, abs_tol=1e-12), (x, y)


def holm_pair(p):
    order = sorted(range(2), key=lambda i: p[i])
    adjusted = [None, None]
    adjusted[order[0]] = min(F(1), 2 * p[order[0]])
    adjusted[order[1]] = min(F(1), max(2 * p[order[0]], p[order[1]]))
    return adjusted, [v <= F(1, 20) for v in adjusted]


def main():
    results = {}
    scores = []
    for returns in ([0.02, -0.01, 0.01, -0.02], [0.03, -0.01, 0.01, -0.02],
                    [0.0] * 4, [0.01] * 4):
        dd = math.sqrt(sum(min(u, 0)**2 for u in returns) / len(returns))
        s4 = sum(returns) / len(returns) / dd if dd else None
        annual = math.sqrt(2190) * s4 if s4 is not None else None
        scores.append({'returns': returns, 'DD': dd, 'S_4h': s4, 'S_annual': annual})
    near(scores[1]['DD'], math.sqrt(0.000125))
    near(scores[1]['S_4h'], math.sqrt(0.05))
    near(scores[1]['S_annual'], math.sqrt(109.5))
    assert scores[0]['S_annual'] == 0
    assert all(r['S_4h'] is None and r['S_annual'] is None for r in scores[2:])
    assert not math.isclose(scores[1]['S_annual'], math.sqrt(4) * scores[1]['S_4h'])
    results['annualization_and_undefined'] = scores

    # Synthetic block scores C0/C5/C10, not observed policy performance.
    blocks = [(10, 9, 8), (20, 21, 20), (30, 33, 32)]
    differences = [[F(c5 - c0), F(c10 - c0)] for c0, c5, c10 in blocks]
    observed = [sum(row[c] for row in differences) / 3 for c in range(2)]
    centered = [[row[c] - observed[c] for c in range(2)] for row in differences]
    assert observed == [1, 0]
    assert all(sum(row[c] for row in centered) == 0 for c in range(2))
    exceed, uncentered_exceed, scaled_exceed = [0, 0], [0, 0], [0, 0]
    draws = list(itertools.product(range(3), repeat=3))
    for draw in draws:
        # The same sampled block indices select BOTH paired difference columns.
        means = [sum(centered[i][c] for i in draw) / 3 for c in range(2)]
        assert means[0] == means[1]  # This fixture has identical centered columns.
        for c in range(2):
            exceed[c] += means[c] >= observed[c]
            raw_mean = sum(differences[i][c] for i in draw) / 3
            uncentered_exceed[c] += raw_mean >= observed[c]
            # Common positive annualization preserves tail comparisons.
            scaled_exceed[c] += math.sqrt(2190) * float(means[c]) >= (
                math.sqrt(2190) * float(observed[c]))
    assert exceed == [4, 17] and scaled_exceed == exceed
    assert uncentered_exceed == [17, 17]  # Missing null centering changes C5's answer.
    exact = [F(n, len(draws)) for n in exceed]
    assert exact == [F(4, 27), F(17, 27)]
    # Only count arithmetic, not a stochastic bootstrap run or proposed B for a study.
    mc_count_example = [F(1 + n, 1 + len(draws)) for n in exceed]
    assert mc_count_example == [F(5, 28), F(18, 28)]
    results['paired_centered_one_sided_bootstrap'] = {
        'synthetic_blocks_C0_C5_C10': blocks, 'observed_mean_differences': observed,
        'centered_differences': centered, 'enumerated_draws': len(draws),
        'exceedances': exceed, 'exact_enumeration_p': exact,
        'uncentered_exceedances_negative_control': uncentered_exceed,
        'MC_count_formula_only': mc_count_example, 'annualization_preserves_exceedances': True,
        'undefined_block_policy': 'pending; no imputation or selective exclusion implemented',
    }

    cases = []
    for raw, expected_adjusted, expected_reject in [
        ([F(2, 100), F(4, 100)], [F(4, 100), F(4, 100)], [True, True]),
        ([F(3, 100), F(4, 100)], [F(6, 100), F(6, 100)], [False, False]),
        ([F(4, 100), F(1, 100)], [F(4, 100), F(2, 100)], [True, True]),
        ([F(25, 1000), F(5, 100)], [F(5, 100), F(5, 100)], [True, True]),
        (exact, [F(8, 27), F(17, 27)], [False, False]),
    ]:
        adjusted, reject = holm_pair(raw)
        assert adjusted == expected_adjusted and reject == expected_reject
        # Independent check using the sequential stopping rule.
        ordered = sorted(range(2), key=lambda i: raw[i])
        sequential = [False, False]
        for rank, i in enumerate(ordered):
            if raw[i] > F(1, 20) / (2 - rank):
                break
            sequential[i] = True
        assert sequential == reject
        cases.append({'raw_p': raw, 'adjusted_p': adjusted, 'reject': reject})
    results['holm_two_contrasts_FWER_005'] = cases

    v2 = Path('docs/proposals/ADR-002-propuesta-v2.md').read_text()
    revised = Path('docs/proposals/ADR-002-propuesta-v2-1.md').read_text()
    sections = {}
    for left, right in [('## 6.', '## 7.'), ('### 7.1', '### 7.2'), ('### 7.3', '## 8.')]:
        original = v2[v2.index(left):v2.index(right)]
        current = revised[revised.index(left):revised.index(right)]
        assert current == original
        sections[left] = hashlib.sha256(current.encode()).hexdigest()
    protected = subprocess.check_output(
        ['git', 'ls-files', 'src', 'configs', 'tests', 'scripts', 'uv.lock', 'pyproject.toml'],
        text=True).splitlines()
    old_docs = subprocess.check_output(
        ['git', 'ls-files', 'docs/evidence/adr002-proposal-v2',
         'docs/proposals/ADR-002-propuesta-v2.md', 'docs/proposals/ADR-002-v2-resumen-academico.md'],
        text=True).splitlines()
    hashes = {}
    for name in protected + old_docs:
        current = Path(name).read_bytes()
        ref = 'cc913b6' if name in protected else '28cda8b'
        assert current == subprocess.check_output(['git', 'show', f'{ref}:{name}']), name
        hashes[name] = hashlib.sha256(current).hexdigest()
    results['preservation_h2_v2_and_reviewed_sections'] = sections
    print(json.dumps({
        'status': 'passed', 'revision': 'v2.1', 'scope': 'synthetic arithmetic/specification only',
        'utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
        'platform': platform.platform(),
        'head_at_run': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'groups': results, 'unchanged_files_sha256': hashes,
        'checks_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'proposal_sha256': hashlib.sha256(revised.encode()).hexdigest(),
    }, indent=2, default=str))


if __name__ == '__main__':
    main()
