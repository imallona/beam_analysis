"""Figure 4: integration benchmarks disagree, and a same-data contrast isolates
the analyst.

Layout ``(a | b) / (c | d)``: the reported rankings and the beam consensus, the
cross-source variance decomposition, the network meta-analysis forest, and the
pancreas same-data contrast. The reading is that independent integration
benchmarks rank shared methods differently, a large part of the spread is the
method-by-benchmark interaction rather than the method, and holding the data
constant leaves the analysts' choices as the remaining disagreement.

Panels b and c fit R models (lme4, netmeta); build() raises RNotAvailableError
when the R toolchain is absent, so the driver skips the figure cleanly.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np
from matplotlib.figure import Figure
from scipy.stats import rankdata

from beam.datasets import (
    load_integration_benchmarks,
    load_integration_published_ranks,
    load_pancreas_contrast,
)
from beam.heterogeneity import (
    RNotAvailableError,
    netmeta_available,
    network_meta_analysis,
    r_available,
    source_variance_decomposition,
)
from beam.reporting.figures import network_forest_plot, rank_bump

from . import _common as C

CANON = ["combat", "harmony", "fastmnn", "scanorama", "liger"]
BENCH = ["Tran", "scIB", "OpenProblems"]
THREE_SOURCES = {"Tran", "scIB", "OpenProblems"}
FOUR_SOURCES = THREE_SOURCES | {"Tyler"}
FIVE_SOURCES = FOUR_SOURCES | {"BatchBench"}


def _consensus_ranks(ib, published):
    """The three reported rank columns plus the beam consensus, as a rank matrix.

    The consensus pools beam's consistent per-benchmark mean ranks over the four
    shared metrics, so the columns are the published orders and beam's own.
    """
    cell = defaultdict(list)
    for benchmark, _dataset, method, _metric, rank in zip(
        ib.benchmark, ib.dataset, ib.method, ib.metric, ib.rank, strict=True
    ):
        cell[(benchmark, method)].append(rank)
    beam_mean = {(b, m): float(np.mean(cell[(b, m)])) for b in BENCH for m in CANON}
    consensus = dict(
        zip(
            CANON,
            rankdata(
                [np.mean([beam_mean[(b, m)] for b in BENCH]) for m in CANON],
                method="ordinal",
            ),
            strict=True,
        )
    )
    columns = [f"{b}\n(reported)" for b in BENCH] + ["beam\nconsensus"]
    ranks = np.array([[published[b][m] for b in BENCH] + [int(consensus[m])] for m in CANON])
    return tuple(columns), ranks


def _source_variance(ib, keep):
    """Fit the cross-source variance model on the benchmarks in ``keep``."""
    methods, datasets, benchmarks, scores = ib.mean_rank_records()
    idx = [i for i in range(len(benchmarks)) if benchmarks[i] in keep]
    return source_variance_decomposition(
        [methods[i] for i in idx],
        [datasets[i] for i in idx],
        [benchmarks[i] for i in idx],
        [scores[i] for i in idx],
    )


def _safe_share(ib, keep):
    """method-by-benchmark share on a benchmark subset, nan if the fit fails."""
    try:
        return _source_variance(ib, keep).method_benchmark_share
    except Exception:
        return float("nan")


def _variance_panel(host, ib):
    """Bar the five-source variance components, highlighting method-by-benchmark.

    The method-by-benchmark bar is the disagreement attributable to the
    benchmarker; it is coloured as the benchmarker and annotated with how it
    rises as sources are added (three to five), the part of the spread that is
    the benchmark rather than the method.
    """
    report = _source_variance(ib, FIVE_SOURCES)
    s3 = _safe_share(ib, THREE_SOURCES)
    s4 = _safe_share(ib, FOUR_SOURCES)
    s5 = report.method_benchmark_share

    components = report.variance_components
    names = list(components)
    total = sum(components.values())
    shares = [components[k] / total if total > 0 else 0.0 for k in names]
    colors = [
        C.BENCHMARKER_COLOR
        if k == "method:benchmark"
        else ("#bbbbbb" if k.lower() == "residual" else C.DATA_COLOR)
        for k in names
    ]
    ax = host.subplots()
    ax.bar(range(len(names)), shares, color=colors)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=25, ha="right")
    ax.set_ylim(0, 1)
    ax.set_ylabel("share of variance")
    ax.set_title("cross-source variance")
    ax.text(
        0.97,
        0.96,
        f"method:benchmark\n{s3:.2f} / {s4:.2f} / {s5:.2f} (3 / 4 / 5 sources)",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6,
    )


def build() -> Figure:
    if not (r_available() and netmeta_available()):
        raise RNotAvailableError(
            "figure 4 needs the R toolchain (lme4 and netmeta); "
            "provision it with envs/heterogeneity.yml"
        )
    ib = load_integration_benchmarks()
    published = load_integration_published_ranks()
    columns, ranks = _consensus_ranks(ib, published)

    fig = C.figure(C.FULL_WIDTH_MM, 165.0)
    top, bottom = fig.subfigures(2, 1, height_ratios=[1.0, 1.0])
    top_left, top_right = top.subfigures(1, 2, width_ratios=[1.0, 1.0])
    bottom_left, bottom_right = bottom.subfigures(1, 2, width_ratios=[1.2, 1.0])

    rank_bump(tuple(CANON), columns, ranks, divider_after=2, host=top_left)
    C.panel_label(top_left, "a")

    _variance_panel(top_right, ib)
    C.panel_label(top_right, "b")

    nma = network_meta_analysis(*ib.network_arms())
    network_forest_plot(nma, host=bottom_left)
    C.panel_label(bottom_left, "c")

    pc = load_pancreas_contrast()
    C.grouped_rank_bars(
        bottom_right,
        pc.methods,
        [("Tran D4", pc.tran_mean_rank), ("scIB pancreas", pc.scib_mean_rank)],
        ylabel="mean rank (1 ranks first)",
    )
    ax_d = bottom_right.axes[0]
    ax_d.set_title("same pancreas data, two pipelines")
    ax_d.text(
        0.5,
        0.02,
        f"cross-pipeline Spearman {pc.spearman():+.2f}",
        transform=ax_d.transAxes,
        ha="center",
        va="bottom",
        fontsize=6,
    )
    C.panel_label(bottom_right, "d")
    return fig
