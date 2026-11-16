"""Draw printable final figures from the derived CSVs."""

import argparse
import csv
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba
from matplotlib.ticker import FuncFormatter
from secondary_metrics import CONDITIONS, EVIDENCE, FIGURES, REFERENCE, ROOT, output_path

WIDTH = 15 / 2.54
DPI = 300
STYLES = (
    {"color": "#005A9C", "linestyle": "-"},
    {"color": "#B75600", "linestyle": "--"},
    {"color": "#007A61", "linestyle": "-."},
)
HATCHES = ("//", "\\\\", "..")
MARKERS = ("o", "s", "^")
HOLD_STYLE = {"color": "#783D91", "linestyle": ":"}


def columns(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def decimal(value, _):
    return f"{value:g}".replace(".", ",")


def plot_legend(ax, **kwargs):
    ax.legend(loc="best", frameon=True, facecolor="white", framealpha=0.95, **kwargs)


def plot_curve(rows, kind):
    timestamps = [datetime.fromisoformat(row["valuation_utc"]) for row in rows]
    is_exposure = kind == "exposicion-media"
    height = 9.8 if is_exposure else 8.1
    fig, axes = plt.subplots(2 if is_exposure else 1, 1, sharex=True,
                             figsize=(WIDTH, height / 2.54), layout="constrained")
    ax = axes[0] if is_exposure else axes
    factor = 1 if kind == "curva-patrimonio" else 100

    def series(key):
        return np.array([float(row[key]) for row in rows]) * factor

    for condition, style, hatch in zip(CONDITIONS, STYLES, HATCHES, strict=True):
        color = style["color"]
        ax.fill_between(timestamps, series(f"{condition}_p05"), series(f"{condition}_p95"),
                        facecolor=to_rgba(color, 0.10), hatch=hatch,
                        edgecolor=to_rgba(color, 0.29), linewidth=0.1, zorder=1)
    for index, (condition, style) in enumerate(zip(CONDITIONS, STYLES, strict=True)):
        ax.plot(timestamps, series(f"{condition}_median"), label=condition, **style,
                lw=1.4 - 0.15 * index, zorder=4 + index)
        if is_exposure:
            axes[1].plot(timestamps, series(f"{condition}_mean"), **style, lw=1.25)
    if "buy_and_hold" in rows[0]:
        ax.plot(timestamps, series("buy_and_hold"), label=REFERENCE, **HOLD_STYLE, lw=1.35)
    ylabel = {"curva-patrimonio": "Patrimonio (USDT)", "curva-drawdown": "Caída (%)",
              "exposicion-media": "Exposición (%)"}[kind]
    ax.set_ylabel(ylabel)
    ax.set_title(FIGURES[kind] + "\nMediana y banda P5–P95 · 36 semillas por condición", loc="left")
    plot_legend(ax, ncols=2)
    bottom = axes[1] if is_exposure else ax
    if is_exposure:
        bottom.set_title("Media aritmética de las 36 semillas", loc="left")
        bottom.set_ylabel(ylabel)
    bottom.set_xlabel("Fecha de valoración (UTC)")
    bottom.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    bottom.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y", tz=timestamps[0].tzinfo))
    bottom.set_xlim(timestamps[0], timestamps[-1])
    for panel in np.atleast_1d(axes):
        panel.yaxis.set_major_formatter(FuncFormatter(decimal))
    return fig


def plot_sortino(rows):
    fig, ax = plt.subplots(figsize=(WIDTH, 8.1 / 2.54), layout="constrained")
    values = [[float(row["sortino"]) for row in rows if row["condition"] == c] for c in CONDITIONS]
    reference = next(float(r["sortino"]) for r in rows if r["condition"] == REFERENCE)
    artists = ax.boxplot(values, tick_labels=CONDITIONS, showfliers=False, widths=0.36,
                        patch_artist=True)
    for index, (points, style, marker) in enumerate(zip(values, STYLES, MARKERS, strict=True)):
        color = style["color"]
        artists["boxes"][index].set(facecolor=to_rgba(color, 0.10), edgecolor=color)
        artists["medians"][index].set(color=color, linewidth=1.6)
        for component in ("whiskers", "caps"):
            for line in artists[component][2 * index:2 * index + 2]:
                line.set(color=color)
        ax.scatter(index + 1 + np.linspace(-0.135, 0.135, len(points)), points,
                   color=color, marker=marker, s=10, alpha=0.7, zorder=3)
    ax.axhline(reference, **HOLD_STYLE, label=REFERENCE)
    ax.set_ylabel("Sortino anualizado")
    ax.set_xlabel("Condición")
    ax.set_title(FIGURES["sortino-por-condicion"] + "\n36 políticas por condición", loc="left")
    ax.yaxis.set_major_formatter(FuncFormatter(decimal))
    plot_legend(ax)
    return fig


def build(source):
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 8.5,
                         "axes.titlesize": 9.5, "axes.grid": True, "axes.axisbelow": True,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "grid.color": "0.88", "grid.linewidth": 0.4, "legend.fontsize": 7.7}):
        for name in FIGURES:
            rows = columns(source / (name + ".csv"))
            fig = plot_sortino(rows) if name == "sortino-por-condicion" else plot_curve(rows, name)
            with (source / (name + ".png")).open("xb") as stream:
                fig.savefig(stream, format="png", dpi=DPI, facecolor="white",
                            metadata={"Software": f"Matplotlib {matplotlib.__version__}"})
            plt.close(fig)
    print(f"4 PNG escritos en {source} con Matplotlib {matplotlib.__version__}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=EVIDENCE)
    args = parser.parse_args()
    build(output_path(ROOT, args.evidence))
