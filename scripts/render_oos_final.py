"""Render small, static chapter-4 exhibits from the accepted final contrast.

Reads only the existing final contrast and its independent audit. It never
loads market rows, checkpoints, or policy weights and never writes campaign
artifacts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
from collections.abc import Sequence
from pathlib import Path

from btc_risk_rl.evaluation.inference import compare_blocks


def _checked_rows(rows: Sequence[tuple[int, float, float, float]]) -> list[tuple[int, float, float, float]]:
    if not rows:
        raise ValueError("No complete paired blocks")
    checked = []
    seen = set()
    for row in rows:
        if len(row) != 4 or type(row[0]) is not int or row[0] in seen:
            raise ValueError("Duplicate or malformed paired block")
        if any(type(value) not in (int, float) or not math.isfinite(value) for value in row[1:]):
            raise ValueError("Missing or nonfinite primary metric")
        seen.add(row[0])
        checked.append(row)
    return checked


def paired_differences_svg(
    rows: Sequence[tuple[int, float, float, float]], *, source: str, period: str,
) -> str:
    """Plot C5/C10 minus C0 within each seed block; x is block, not time."""
    checked = _checked_rows(rows)
    differences = [(c5 - c0, c10 - c0) for _, c0, c5, c10 in checked]
    bound = max(abs(value) for pair in differences for value in pair)
    bound = max(bound * 1.15, 1e-6)
    width, height = 1080, 590
    left, right, top, bottom = 105, 1030, 110, 440
    zero_y = (top + bottom) / 2
    scale = (bottom - top) / (2 * bound)
    n = len(checked)
    def x_at(index: int) -> float:
        return left + (right - left) * (index + 0.5) / n
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Diferencias pareadas de Sortino anualizado">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="70" y="45" font-size="26" font-family="sans-serif" fill="#13243a">Diferencia pareada de Sortino anualizado</text>',
        f'<text x="70" y="75" font-size="16" font-family="sans-serif" fill="#34445a">{n} bloques de semillas · período {html.escape(period)} · evaluación final fuera de muestra</text>',
        f'<line x1="{left}" x2="{right}" y1="{zero_y:.2f}" y2="{zero_y:.2f}" stroke="#4b5563" stroke-width="2"/>',
        f'<text x="{left + 5}" y="{zero_y - 7:.2f}" font-size="14" font-family="sans-serif">Referencia: 0</text>',
        f'<text x="15" y="{top + 4}" font-size="14" font-family="sans-serif">+{bound:.4f}</text>',
        f'<text x="15" y="{bottom}" font-size="14" font-family="sans-serif">−{bound:.4f}</text>',
    ]
    for i, pair in enumerate(differences):
        x = x_at(i)
        for offset, value, color in ((-4, pair[0], "#126782"), (4, pair[1], "#b35b28")):
            y = zero_y - value * scale
            out.append(f'<circle cx="{x + offset:.2f}" cy="{y:.2f}" r="4" fill="{color}"/>')
    out.extend([
        f'<text x="{left}" y="475" font-size="15" font-family="sans-serif">Bloques 1–{n}; cada punto es una semilla, no una fecha</text>',
        '<circle cx="110" cy="505" r="6" fill="#126782"/><text x="125" y="510" font-size="16" font-family="sans-serif">C5 − C0</text>',
        '<circle cx="290" cy="505" r="6" fill="#b35b28"/><text x="305" y="510" font-size="16" font-family="sans-serif">C10 − C0</text>',
        f'<text x="70" y="550" font-size="13" font-family="sans-serif" fill="#34445a">Fuente: {html.escape(source)} · unidad: puntos de Sortino anualizado</text>',
        '</svg>',
    ])
    return "\n".join(out) + "\n"


def inference_svg(comparisons: dict, *, source: str, period: str) -> str:
    """Display means and descriptive paired intervals; decision stays textual."""
    names = ("C5_minus_C0", "C10_minus_C0")
    for name in names:
        row = comparisons[name]
        values = (row["mean_difference"], *row["interval_95"])
        if row["blocks"] != 36 or any(not math.isfinite(value) for value in values):
            raise ValueError("Incomplete or nonfinite contrast")
    bound = max(abs(value) for name in names for value in (
        comparisons[name]["mean_difference"], *comparisons[name]["interval_95"],
    )) * 1.2
    bound = max(bound, 1e-6)
    x0, scale = 540, 400 / bound
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 350" role="img" aria-label="Medias e intervalos pareados">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="55" y="45" font-size="25" font-family="sans-serif">Contraste pareado: 36 bloques</text>',
        f'<text x="55" y="75" font-size="16" font-family="sans-serif">Sortino anualizado, {html.escape(period)} · intervalo descriptivo bootstrap 95 %</text>',
        f'<line x1="{x0}" x2="{x0}" y1="100" y2="255" stroke="#4b5563" stroke-width="2"/>',
        '<text x="550" y="112" font-size="13" font-family="sans-serif">0</text>',
    ]
    for y, name, label, color in ((155, names[0], "C5 − C0", "#126782"),
                                  (225, names[1], "C10 − C0", "#b35b28")):
        row = comparisons[name]
        low, high = row["interval_95"]
        mean = row["mean_difference"]
        out.extend([
            f'<text x="55" y="{y + 5}" font-size="18" font-family="sans-serif">{label}</text>',
            f'<line x1="{x0 + low * scale:.2f}" x2="{x0 + high * scale:.2f}" y1="{y}" y2="{y}" stroke="{color}" stroke-width="5"/>',
            f'<circle cx="{x0 + mean * scale:.2f}" cy="{y}" r="8" fill="{color}"/>',
            f'<text x="55" y="{y + 27}" font-size="13" font-family="sans-serif">media {mean:+.6f}; IC [{low:+.6f}, {high:+.6f}]; Holm p={row["p_holm"]:.4f}</text>',
        ])
    out.extend([
        f'<text x="55" y="295" font-size="13" font-family="sans-serif">Fuente: {html.escape(source)} · unidad: puntos de Sortino anualizado · población: 36 ternas K10</text>',
        '<text x="55" y="320" font-size="13" font-family="sans-serif">No demuestra superioridad financiera ni cumplimiento de CVaR.</text>',
        '</svg>',
    ])
    return "\n".join(out) + "\n"

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(contrast_path: Path, audit_path: Path, output_dir: Path) -> None:
    contrast = json.loads(contrast_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if (audit.get("status") != "verified" or audit.get("final_contrast_sha256") != sha256(contrast_path)
            or not audit.get("comparison_recomputed_exactly")
            or audit.get("report_trace_reaudits") != 108
            or audit.get("accepted_policies") != 108
            or audit.get("steps_per_policy") != 4386
            or audit.get("all_sortino_defined") is not True
            or audit.get("final_ledger_sha256") != contrast.get("final_ledger_sha256")
            or contrast.get("status") != "passed" or contrast.get("complete_policies") != 108
            or contrast.get("blocks") != 36 or audit.get("complete_blocks") != 36):
        raise ValueError("Final contrast and independent audit do not match")
    records = contrast["run_records"]
    if len(records) != 108:
        raise ValueError("Expected 108 accepted final records")
    seeds = list(dict.fromkeys(record["seed"] for record in records))
    if len(seeds) != 36 or any(type(seed) is not int for seed in seeds):
        raise ValueError("Expected 36 distinct seed blocks")
    indexed = {}
    for record in records:
        key = (record["seed"], record["condition"])
        if (key in indexed or record["seed"] not in seeds
                or record["condition"] not in {"C0", "C5", "C10"}
                or not record["run_id"].startswith("run-")
                or len(record["report_sha256"]) != 64):
            raise ValueError("Unexpected or duplicate final run")
        indexed[key] = record["sortino_annualized"]
    try:
        rows = [(seed, indexed[(seed, "C0")], indexed[(seed, "C5")], indexed[(seed, "C10")])
                for seed in seeds]
    except KeyError as exc:
        raise ValueError("Incomplete paired seed block") from exc
    if compare_blocks([row[1:] for row in rows]) != contrast["comparisons"]:
        raise ValueError("Frozen inference differs from the accepted contrast")
    source = str(contrast_path)
    paired_svg = paired_differences_svg(rows, source=source, period="2024–2025")
    contrast_svg = inference_svg(contrast["comparisons"], source=source, period="2024–2025")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "paired-blocks.svg").write_text(paired_svg, encoding="utf-8")
    (output_dir / "paired-inference.svg").write_text(contrast_svg, encoding="utf-8")
    with (output_dir / "paired-blocks.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("block", "seed", "C0_sortino_annualized", "C5_sortino_annualized",
                         "C10_sortino_annualized", "C5_minus_C0", "C10_minus_C0"))
        for block, (seed, c0, c5, c10) in enumerate(rows, start=1):
            writer.writerow((block, seed, repr(c0), repr(c5), repr(c10), repr(c5 - c0), repr(c10 - c0)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contrast", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render(args.contrast, args.audit, args.output)


if __name__ == "__main__":
    main()
