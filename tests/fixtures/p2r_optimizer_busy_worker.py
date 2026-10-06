"""Synthetic-only interrupt target: stay in gradient computation, never market."""

import json
import os
import sys
import time
from pathlib import Path

import torch

from btc_risk_rl.agents.trainer import SyntheticExperiment
from btc_risk_rl.pilots import p2_runner


def main():
    request_path, marker = map(Path, sys.argv[1:])
    if json.loads(request_path.read_text())["unit"] != 1:
        raise ValueError("Optimizer probe requires synthetic Q/A/B+D unit 1")

    def busy_gradient_norm(loss, model, optimizer):
        if not torch.isfinite(loss):
            raise ValueError("Nonfinite synthetic probe loss")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        grads = [p.grad for p in model.parameters()]
        if any(g is None or not torch.isfinite(g).all() for g in grads):
            raise ValueError("Invalid synthetic probe gradient")
        for iteration in range(100000):
            norm = torch.sqrt(sum(torch.sum(g.detach() ** 2) for g in grads))
            if iteration % 50 == 0:
                state = dict(
                    phase="optimizer_gradient_norm_after_backward_before_adam_step",
                    iterations=iteration + 1, norm=float(norm), pid=os.getpid(),
                    utc_epoch=time.time(),
                )
                stage = marker.with_suffix(".tmp")
                stage.write_text(json.dumps(state) + "\n")
                os.replace(stage, marker)
        optimizer.step()
        return float(norm)

    SyntheticExperiment._optimizer_step = staticmethod(busy_gradient_norm)
    sys.argv = ["p2_runner.py", "--synthetic-request", str(request_path)]
    p2_runner.main()


if __name__ == "__main__":
    main()
