"""Check the rounded report tables against the exact cross-D result JSON."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "docs/evidence/p3-cross-diagnostic/results.json"
REPORT = ROOT / "docs/hitos/P3-diagnostico-cruzado-D.md"


def main():
    results = json.loads(RESULTS.read_text())
    report = REPORT.read_text().replace("−", "-").replace(",", ".")
    count = 0
    for pair in results["pairs"]:
        heading = f"### {pair['seed']} · {pair['condition']}"
        section = report.split(heading, 1)[1].split("### ", 1)[0]
        cells = pair["cells"]
        z0 = cells["critic_b0_on_D_b0"]["zero_mse"]
        z1 = cells["critic_b0_on_D_b1"]["zero_mse"]
        assert f"Z_D0={z0:.8f}; Z_D1={z1:.8f}" in section
        for beta in (0, 1):
            left = cells[f"critic_b{beta}_on_D_b0"]
            right = cells[f"critic_b{beta}_on_D_b1"]
            row = (f"| β={beta} | {left['mse']:.8f} / {left['bias']:+.8f} | "
                   f"{right['mse']:.8f} / {right['bias']:+.8f} |")
            assert row in section, (heading, row)
            count += 2
    for block in results["seed_blocks"]:
        cells = block["cells"]
        columns = [
            str(block["seed"]),
            f"{cells['critic_b0_on_D_b0']['zero_mse']:.8f}",
            f"{cells['critic_b0_on_D_b1']['zero_mse']:.8f}",
        ]
        for critic, d in ((0, 0), (1, 0), (0, 1), (1, 1)):
            cell = cells[f"critic_b{critic}_on_D_b{d}"]
            columns.append(f"{cell['mse']:.8f} / {cell['bias']:+.8f}")
        row = "| " + " | ".join(columns) + " |"
        assert row in report, (block["seed"], row)
    print(f"{count} matrix cells and 3 seed-block summaries match results.json")


if __name__ == "__main__":
    main()
