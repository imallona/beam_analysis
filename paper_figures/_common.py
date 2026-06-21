"""Shared scaffolding for the beam manuscript figures.

Genome Biology asks for figures at most 170 mm wide (85 mm for a half-width
figure) and at most 225 mm tall including the caption, about 300 dpi at final
size, every line wider than 0.25 pt, and fonts embedded. The constants and the
``save_figure`` helper here enforce those, so each ``figureN_*`` module only has
to lay out its panels.

Each figure module exposes one ``build()`` returning a ``matplotlib.figure.Figure``
already sized to the target millimetres. The panels are drawn into ``SubFigure``
hosts via the host-aware builders in ``beam.reporting.figures`` and the small
drawers below, so the composites stay vector and editable.

The dataset preparation lives here too, once, because several figures read the
same runs (the Duo run, the integration benchmarks, the OpenProblems metrics).
The loaders are deterministic; every ``beam.rank`` call passes ``seed=0``.
"""

from __future__ import annotations

from functools import lru_cache

import matplotlib
import numpy as np
from matplotlib.figure import Figure, SubFigure

MM_PER_INCH = 25.4
FULL_WIDTH_MM = 170.0
HALF_WIDTH_MM = 85.0
MAX_HEIGHT_MM = 225.0


def mm(value_mm: float) -> float:
    """Millimetres to inches, the unit matplotlib figure sizes use."""
    return value_mm / MM_PER_INCH


def configure() -> None:
    """Set the rcParams the journal requires: embedded fonts, readable lines.

    Embeds fonts as TrueType (``fonttype`` 42) so the PDF carries them, keeps
    every default line at least 0.5 pt (twice the 0.25 pt floor), and sets a
    compact font scale that stays legible when the figure is shrunk to column
    width.
    """
    matplotlib.rcParams.update(
        {
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "font.size": 7.0,
            "axes.titlesize": 8.0,
            "axes.labelsize": 7.0,
            "xtick.labelsize": 6.0,
            "ytick.labelsize": 6.0,
            "legend.fontsize": 6.0,
            "axes.linewidth": 0.6,
            "lines.linewidth": 1.0,
            "patch.linewidth": 0.5,
            "savefig.dpi": 300,
            "figure.dpi": 300,
        }
    )


def figure(width_mm: float, height_mm: float) -> Figure:
    """A blank figure sized to the given millimetres, height capped at the limit."""
    if height_mm > MAX_HEIGHT_MM:
        raise ValueError(f"height {height_mm} mm exceeds the {MAX_HEIGHT_MM} mm limit")
    return Figure(figsize=(mm(width_mm), mm(height_mm)), layout="constrained")


def panel_label(host: SubFigure, text: str) -> None:
    """Draw a bold panel key (a, b, c) in the top-left of a subfigure.

    The key goes in the graphic, as the journal asks, not in the legend.
    """
    host.text(0.01, 0.99, text, fontsize=10, fontweight="bold", va="top", ha="left")


def save_figure(fig: Figure, path: str) -> str:
    """Write the figure to a vector PDF at its exact size, plus a PNG preview.

    The PDF keeps the figure's millimetre dimensions (no ``tight`` crop) so it
    meets the journal's width requirement; a 300 dpi PNG of the same canvas is
    written alongside for quick visual review.
    """
    fig.savefig(path, format="pdf")
    preview = path[:-4] + ".png" if path.endswith(".pdf") else path + ".png"
    fig.savefig(preview, format="png", dpi=300)
    return path


# Shared palette, kept consistent with beam.reporting.figures.
ANALYST_COLOR = "#ee6677"
DATA_COLOR = "#4477aa"
BENCHMARKER_COLOR = "#228833"


def variance_bars(host, report, *, annotate: bool = True, title: str | None = None) -> None:
    """Draw a rank-variance decomposition as labelled bars onto a host.

    The four bars are the weighting, the aggregation, the dataset (when the input
    is a tensor) and the interaction share of the rank variance, each in [0, 1].
    The dataset bar is coloured as data, the choice bars as analyst choice, and
    the interaction grey, so the bar colours match the attribution figure.
    """
    ax = host.subplots() if isinstance(host, SubFigure) else host
    order = ["weighting", "aggregation", "dataset", "interaction"]
    shares = dict(report.factor_shares)
    shares["interaction"] = report.interaction_share
    names = [k for k in order if k in shares and np.isfinite(shares[k])]
    values = [float(shares[k]) for k in names]
    color_of = {
        "weighting": ANALYST_COLOR,
        "aggregation": ANALYST_COLOR,
        "dataset": DATA_COLOR,
        "interaction": "#bbbbbb",
    }
    colors = [color_of[k] for k in names]
    x = np.arange(len(names))
    ax.bar(x, values, color=colors)
    if annotate:
        for xi, v in zip(x, values, strict=True):
            ax.annotate(f"{v:.3f}", (xi, v), textcoords="offset points", xytext=(0, 2),
                        ha="center", fontsize=6)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=20, ha="right")
    ax.set_ylim(0, 1)
    ax.set_ylabel("share of rank variance")
    if title:
        ax.set_title(title)


def grouped_rank_bars(host, methods, series, *, ylabel: str, title: str | None = None) -> None:
    """Grouped bars of mean rank per method, drawn rank 1 at the top.

    ``series`` is a list of ``(label, values)`` pairs, one bar group per method.
    Ranks are drawn with the axis inverted so a taller bar is a better (smaller)
    rank, matching how a reader expects "ranks first" to look.
    """
    ax = host.subplots() if isinstance(host, SubFigure) else host
    methods = list(methods)
    n = len(series)
    width = 0.8 / n
    x = np.arange(len(methods))
    palette = [DATA_COLOR, ANALYST_COLOR, BENCHMARKER_COLOR, "#aa3377"]
    for i, (label, values) in enumerate(series):
        offset = (i - (n - 1) / 2.0) * width
        ax.bar(x + offset, np.asarray(values, dtype=float), width=width,
               label=label, color=palette[i % len(palette)])
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=20, ha="right")
    ax.set_ylabel(ylabel)
    ax.invert_yaxis()
    ax.legend(loc="upper right")
    if title:
        ax.set_title(title)


# Shared dataset preparation, cached so a figure that reads the Duo run does not
# rebuild it and the driver can build several figures in one process.

DUO_METRICS = ("ari", "runtime", "shannon_entropy_diff")


@lru_cache(maxsize=1)
def duo_run():
    """The Duo 2018 run on the three analysis metrics, plus its dataset names."""
    import beam
    from beam.datasets import load_duo2018

    duo = load_duo2018()
    scores = beam.Scores(
        values=duo.tensor(DUO_METRICS),
        tool_names=tuple(duo.method_names),
        metric_ids=DUO_METRICS,
        dataset_names=duo.dataset_names,
        layout="long",
    )
    run = beam.rank(scores, weights="equal", method="saw", seed=0)
    return duo, run


@lru_cache(maxsize=1)
def duo_rank_sensitivity():
    """Rank-sensitivity over the Duo tool by dataset by metric tensor."""
    from beam.mcda import rank_sensitivity

    duo, run = duo_run()
    ctx = run.context
    return rank_sensitivity(
        duo.tensor(DUO_METRICS),
        ctx.polarity,
        normalization=list(ctx.normalization),
        bounds=list(ctx.bounds),
        baselines=list(ctx.baselines),
        targets=list(ctx.targets),
        missing="worst",
        tool_names=duo.method_names,
        dataset_names=duo.dataset_names,
    )


@lru_cache(maxsize=1)
def openproblems_metric_quality():
    """The validity, reliability and dimensionality reports on the scIB metrics."""
    from beam.cards import polarities_for
    from beam.datasets import load_openproblems
    from beam.mcda import metric_dimensionality, metric_reliability, metric_validity

    op = load_openproblems("batch_integration")
    metrics = [m for m in op.metric_ids if m != "hvg_overlap"]
    tensor = op.tensor(tuple(metrics))
    keep = (~np.isnan(tensor).all(axis=1)).all(axis=1)
    tensor = tensor[keep]
    bio = {
        "ari", "nmi", "asw_label", "isolated_label_f1", "isolated_label_asw",
        "cell_cycle_conservation", "hvg_overlap", "clisi",
    }
    groups = ["bio" if m in bio else "batch" for m in metrics]
    pol = polarities_for(metrics)
    validity = metric_validity(tensor, pol, groups, metric_ids=list(metrics))
    reliability = metric_reliability(tensor, pol, groups, metric_ids=list(metrics))
    dimensionality = metric_dimensionality(tensor, pol, groups, metric_ids=list(metrics))
    return validity, reliability, dimensionality
