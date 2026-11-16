"""Markdown tables for the frozen 36-block final OOS contrast."""

from __future__ import annotations

from collections.abc import Sequence

from btc_risk_rl.evaluation.inference import compare_audited_records


def _number(value: float | None, *, signed: bool = False) -> str:
    if value is None:
        return "indefinido"
    spec = "+.3f" if signed else ".3f"
    return format(value, spec).replace("-", "−").replace(".", ",")


def render_contrast_table(records: Sequence[dict], *, expected_seeds: Sequence[int],
                          source: str) -> str:
    """Require all 108 audited rows before rendering any primary contrast."""
    if not source or "\n" in source:
        raise ValueError("Contrast source label invalid")
    result = compare_audited_records(records, expected_seeds=expected_seeds)
    indexed = {(row["seed"], row["condition"]): row for row in records}
    lines = ["# Contraste final fuera de muestra: 36 bloques pareados", "",
             "Métrica: Sortino anualizado de retornos simples netos de 4 h, "
             "MAR=0; desviación bajista sobre todos los períodos. "
             "La anualización es una convención de reporte.",
             f"Fuente: {source}. Población: evaluación fuera de muestra "
             "2024–2025; 36 semillas, tres condiciones por semilla.", "",
             "| Semilla | C0 | C5 | C10 | C5−C0 | C10−C0 |",
             "| ---: | ---: | ---: | ---: | ---: | ---: |"]
    for seed in expected_seeds:
        base, c5, c10 = (indexed[(seed, condition)]["sortino_annualized"]
                         for condition in ("C0", "C5", "C10"))
        lines.append(f"| {seed} | {_number(base)} | {_number(c5)} | {_number(c10)} | "
                     f"{_number(c5 - base, signed=True)} | "
                     f"{_number(c10 - base, signed=True)} |")
    lines += ["", "Bootstrap pareado unilateral, 19.999 remuestras centradas "
              "bajo la hipótesis nula, índices comunes y corrección de Holm "
              "con significancia familiar 0,05. Los intervalos son descriptivos "
              "y no se usan como prueba unilateral.", "",
              "| Comparación | Diferencia media | IC descriptivo 95 % | dᶻ | p unilateral | "
              "p Holm | Rechaza H₀ | Efecto ≥ +0,50 |",
              "| --- | ---: | --- | ---: | ---: | ---: | --- | --- |"]
    for name, label in (("C5_minus_C0", "C5−C0"), ("C10_minus_C0", "C10−C0")):
        row = result[name]
        lo, hi = row["interval_95"]
        lines.append(
            f"| {label} | {_number(row['mean_difference'], signed=True)} | "
            f"[{_number(lo, signed=True)}, {_number(hi, signed=True)}] | "
            f"{_number(row['paired_dz'])} | {row['p_one_sided']:.5f} | "
            f"{row['p_holm']:.5f} | {'sí' if row['reject_null'] else 'no'} | "
            f"{'sí' if row['meets_minimum_effect'] else 'no'} |"
        )
    lines += ["", "Un Sortino mayor no demuestra cumplimiento poblacional de CVaR. "
              "La variación inferencial proviene de semillas de entrenamiento "
              "sobre un único período final fijo.", ""]
    return "\n".join(lines)
