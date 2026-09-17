import runpy
from pathlib import Path

api = runpy.run_path(str(Path("scripts/diagnose_history.py")))
impact = api["impact"]


def test_180_transitions_need_223_bars():
    assert impact(list(range(222)), set(), 0, 222)["candidate_starts_180"] == 0
    assert impact(list(range(223)), set(), 0, 223)["candidate_starts_180"] == 1


def test_gap_never_bridged_and_warmup_restarts():
    result = impact(list(range(500)), {250}, 0, 500)
    assert result["segments"] == 2
    assert result["usable_transitions"] == (250 - 43) + (249 - 43)
    assert result["candidate_starts_180"] == 28 + 27


def test_prior_context_can_warm_partition_without_scoring_it():
    r = impact(list(range(300)), set(), 100, 200)
    assert r["usable_transitions"] == 100
    assert r["retained_partition_bars"] == 100


def test_short_run_contributes_no_complete_episode():
    r = impact(list(range(50)), set(), 0, 50)
    assert r["usable_transitions"] == 7
    assert r["candidate_starts_180"] == 0
