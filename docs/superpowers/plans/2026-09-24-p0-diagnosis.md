# P0 diagnosis plan

Goal: explain critic warnings and risk activation without optimizer steps.
Architecture: standalone read-only reconstruction from all 27 existing checkpoints;
training-only source, exact coordinate RNG replay of 18 original A batches; no runner.
Tech stack: frozen uv environment, CPU float64, NumPy/PyTorch, JSON evidence.

- Verify local/remote e0a2dfc and preserve prior .python-version deletion.
- Read instrumentation and adopted contract. Identify measurement timing/scope.
- Create docs/evidence/p0-diagnosis/reconstruct.py: hash originals before/after,
  load weights_only checkpoint state directly (no resume journal), reconstruct A,
  assert route/policy IDs, original fixed_digest and first actor gradient norm.
- Recover denominators for all eight critic minibatches; retain original losses.
  Compute whole-A before/after predictions with endpoint checkpoints only.
- Compare risk coefficients and gradients at frozen starting weights; compare
  actual checkpoint parameter deltas and existing optimizer states, never step.
- Emit new exclusive results.json, document limits (no intermediate weights),
  tables by seed/condition/iteration, academic summary and bounded P1 proposal.
- Run reconstruction, Ruff and analytical-only tests; preserve command logs.
  Publish documentation/evidence branch, no operational source changes.

Executed all diagnostic steps. Full pytest deliberately excluded because it runs
learning updates; 16 analytical tests selected without optimizer steps.
