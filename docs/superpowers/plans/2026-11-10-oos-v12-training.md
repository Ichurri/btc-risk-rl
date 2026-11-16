# OOS v1.2 training implementation plan

> **For agentic workers:** implement each checked step with a failing synthetic test first, then verify and record its output. The market campaign remains closed until the whole entry path passes.

**Goal:** train complete C0/C5/C10 seed blocks within the existing daily budget, preserving the 36-block confirmatory design and keeping 2023/final inaccessible.

**Architecture:** a new campaign profile and approval gate uses the existing Q/A/B+D worker and supervisor. Separate roots and ledgers hold the 2021 and 2022 walk-forward diagnostics and the 36-block main campaign. A shared, durable pre-ledger attempt journal charges checks and launch gaps without double counting accepted unit time. Each campaign has its own source identity, normalizer and immutable roster. Failures remain permanent.

**Tech stack:** Python 3.12, uv, PyTorch CPU, pytest, Ruff, systemd --user.

---

## 1. Freeze before market execution

- [ ] Record the candidate v1.2 decisions as adopted **for training only**: β=0, critic four epochs, K=10, D64, Q/A/B, ADR-002, d, all 36 principal seeds, three auxiliary seeds, order, fold cutoffs, checkpoint K10, analysis and failure rules. Pin protocol, H1 derivative, code, config and roster hashes in a new approval record; leave 2023/final permissions off.
- [ ] Reconcile the measured WF05 and 2022-03 unit times with P3 and calculate an explicit upper-bound block count through 16/11. Preserve 20-day campaign cap and 3 h global/day with 2.700 s reserve; no automatic reduction of 36 blocks.

## 2. New train-only runner

**Files:** new `src/btc_risk_rl/pilots/oos_v12_training.py`, `oos_v12_worker.py`, `oos_v12_budget.py`, `scripts/run_oos_v12_training.py`; explicit allowlists in `agents/trainer.py`, `agents/checkpoint.py`, `pilots/p2.py`, `pilots/p2_runner.py`, `pilots/p2r_units.py`; tests in `tests/test_oos_v12_training.py`.

- [ ] First add failing synthetic tests for source/permit mismatch, order, completion, resume, forged request, changed checkpoint, and closed market gate.
- [ ] Implement one immutable roster per source: 2021 and 2022 diagnostic folds (three seed triplets each) and main 2018–2022 (36 seed triplets). No historical checkpoint reuse.
- [ ] Add a 20-active-day ledger with the existing Q0 and Q/A/B+D complete boundaries, 09:00 local deadline, 2.700 s closing reserve and unchanged per-unit caps. Require full power, memory, disk and budget guards before each unit. Shared global lock prevents concurrent campaigns.
- [ ] Meter suite, Ruff, watched preflight, loading and audit from a durable attempt journal opened before the first check; merge intervals with the ledger and systemd session without double count. Test midnight and interrupted attempts.
- [ ] Add worker gate before request or market reads. Use only accepted training shard; fold refit is confined to the corresponding training prefix. Keep 2023 and final unreachable.
- [ ] Verify synthetic Q0 → checkpoint → process restart → iteration 1 and completion of one small synthetic triplet; test fail-closed partial unit and invalid identity.

## 3. Entry and run

- [ ] Run focal tests, full suite and Ruff; retain exact outputs. Run watched read-only preflight and verify opened paths. Pin approval in its own commit only after code and tests are stable.
- [ ] Start at most one systemd --user session (`Restart=no`) inside 01:00–09:00 La Paz after admission. Check the remaining day before every unit and pause at a complete frontier. Never resume `failed` or `incomplete`.
- [ ] Audit every accepted unit against checkpoint/report hashes, ledger chain, counters, time and resource records. Update `reporte-codex.md` and HANDOFF after each session; prepare cost and completion tables and graphs from accepted evidence only.

## 4. Interpretation

- [ ] Label walk-forward outputs and incomplete principal blocks as development/partial. Do not perform primary paired inference unless all 36 complete triplets are available and the predeclared 2023 technical gate and separate final access have passed.
- [ ] Freeze evaluation code and its technical gate before any 2023 read. Keep final 2024–2025 closed until the complete protocol and dataset access conditions hold.
